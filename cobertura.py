"""Que se recolecto y que no. Es lo que decide si una ausencia informa.

Sin este modulo, "no encontre el evento" es una sola cosa. Con el son dos muy distintas:

  **No paso**, y se puede demostrar que se estaba mirando -- la fuente que lo habria
  registrado cubria la ventana y registra esa clase de hecho.

  **No se sabe** -- no hay evento y tampoco hay cobertura demostrada. No se afirma nada.

La ausencia de evidencia no es evidencia de ausencia salvo que se demuestre que se estaba
mirando. Es la misma estructura del deny explicito contra el implicito.

La observabilidad tiene **tres valores y no dos**, y esa es la decision de disenio que
sostiene todo el modulo. Lo desconocido no puede caer del lado de "si, lo habriamos visto",
porque eso convierte cualquier hueco de conocimiento en una afirmacion sobre el mundo. Cae
del lado de INDETERMINADO, que es una respuesta honesta y distinta de las otras dos.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from eventos import ACCIONES_POR_FUENTE, clase_operacion

SI = "SI"
NO = "NO"
INDETERMINADO = "INDETERMINADO"


def _t(s) -> datetime:
    if isinstance(s, datetime):
        return s
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


@dataclass(frozen=True)
class Fuente:
    """Una fuente y la ventana que efectivamente cubre.

    El inicio de la ventana casi nunca es el inicio de la actividad: es donde llega la
    retencion. Confundir la fecha del primer evento observado con la fecha del primer
    evento es el error mas caro que se comete leyendo un log rotado.
    """

    nombre: str
    desde: str
    hasta: str
    motivo_inicio: str
    motivo_fin: str
    activa: bool = True

    def cubre(self, desde, hasta) -> bool:
        return self.activa and _t(self.desde) <= _t(desde) and _t(hasta) <= _t(self.hasta)


@dataclass(frozen=True)
class Carencia:
    """Algo que la fuente NO registra por como esta configurada.

    El archivo esta completo y el hecho es inobservable igual. No es un hueco de
    recoleccion: es una decision de configuracion tomada meses antes del incidente.
    """

    clave: str
    fuente: str
    descripcion: str
    consecuencia: str


# La cobertura declarada del caso. Sale del acta de adquisicion, no de mirar los datos:
# derivarla de los propios eventos seria circular -- "cubre desde el primer evento que hay"
# es verdadero por construccion y no informa nada.
FUENTES = {
    "windows": Fuente(
        "windows", "2026-03-02T00:00:00Z", "2026-03-12T06:00:00Z",
        motivo_inicio="limite de retencion del Security log (rotacion por tamanio)",
        motivo_fin="momento de la recoleccion"),
    "cloudtrail": Fuente(
        "cloudtrail", "2026-03-02T00:00:00Z", "2026-03-12T06:00:00Z",
        motivo_inicio="inicio de la ventana solicitada al proveedor",
        motivo_fin="momento de la recoleccion"),
    "syslog": Fuente(
        "syslog", "2026-03-02T00:00:00Z", "2026-03-12T06:00:00Z",
        motivo_inicio="rotacion de auth.log (logrotate semanal, dos generaciones)",
        motivo_fin="momento de la recoleccion"),
}

CARENCIAS = {
    "4688_command_line": Carencia(
        "4688_command_line", "windows",
        "El campo CommandLine de los eventos 4688.",
        "Se sabe QUE binario se ejecuto, no CON QUE argumentos. Toda afirmacion sobre "
        "argumentos de proceso es indeterminada con esta configuracion, no falsa."),
    "s3_data_events": Carencia(
        "s3_data_events", "cloudtrail",
        "Los eventos de nivel objeto de S3 (GetObject, PutObject, DeleteObject).",
        "Se ve que alguien listo los buckets, no que haya descargado nada. La ausencia de "
        "GetObject NO es evidencia de que no hubo exfiltracion."),
}


@dataclass
class Observabilidad:
    valor: str  # SI / NO / INDETERMINADO
    motivo: str
    fuente: str | None = None

    @property
    def informa_la_ausencia(self) -> bool:
        """Solo un SI rotundo permite convertir 'no hay evento' en 'no ocurrio'."""
        return self.valor == SI

    def __str__(self) -> str:
        return f"{self.valor}: {self.motivo}"


def fuentes_que_registran(accion: str) -> set[str]:
    return {f for f, acciones in ACCIONES_POR_FUENTE.items() if accion in acciones}


def observable(accion: str, objeto: str, desde, hasta,
               carencias: set[str] | None = None) -> Observabilidad:
    """¿Habriamos visto este hecho, de haber ocurrido, en esta ventana?

    Se responde en tres pasos, y ninguno puede saltearse delegando en el siguiente:

      1. ¿Alguna fuente registra esa clase de hecho? Si ninguna lo hace, la pregunta es
         incontestable por construccion y ninguna cobertura la resolveria jamas.
      2. ¿Esa fuente cubria la ventana? Si no, la pregunta es legitima y la evidencia no
         alcanza.
      3. ¿Alguna carencia de configuracion la vuelve ciega a ese hecho en particular?

    El paso 3 es el que consume `clase_operacion()`, y es donde aparece el tercer valor:
    una operacion que el catalogo no clasifica no se puede declarar observable ni
    inobservable. Decir que si seria afirmar cobertura que no se tiene.
    """
    carencias = CARENCIAS.keys() if carencias is None else carencias

    posibles = fuentes_que_registran(accion)
    if not posibles:
        return Observabilidad(
            NO, f"ninguna fuente de este caso registra la accion '{accion}': la pregunta "
                f"es incontestable por construccion, no insuficientemente respaldada")

    cubren = [f for f in posibles if FUENTES[f].cubre(desde, hasta)]
    if not cubren:
        detalle = "; ".join(
            f"{f}: cubre {FUENTES[f].desde} .. {FUENTES[f].hasta} "
            f"({FUENTES[f].motivo_inicio})" for f in sorted(posibles))
        return Observabilidad(
            NO, f"ninguna fuente que registre '{accion}' cubre la ventana pedida. {detalle}")

    fuente = cubren[0]

    # Paso 3: carencias de configuracion.
    if accion == "llamo-api" and ":" in objeto:
        servicio, operacion = objeto.split(":", 1)
        clase = clase_operacion(servicio, operacion)
        if clase == "data":
            if "s3_data_events" in carencias and servicio == "s3":
                return Observabilidad(
                    NO, f"'{objeto}' es un data event de S3 y el trail no los registra: "
                        f"{CARENCIAS['s3_data_events'].consecuencia}", fuente)
            return Observabilidad(
                INDETERMINADO,
                f"'{objeto}' es un data event y este caso no modela el interruptor de "
                f"data events de '{servicio}'. Se habilitan por tipo de recurso: tener "
                f"los de S3 no implica tener los de {servicio}.", fuente)
        if clase == "desconocida":
            return Observabilidad(
                INDETERMINADO,
                f"el catalogo no clasifica '{objeto}': puede ser management o data, y de "
                f"eso depende si el trail lo habria registrado. No se puede afirmar "
                f"cobertura.", fuente)

    if accion == "ejecuto-proceso" and "4688_command_line" in carencias:
        return Observabilidad(
            SI, f"{fuente} cubre la ventana y registra la ejecucion. Atencion: sin "
                f"CommandLine, cualquier afirmacion sobre los ARGUMENTOS del proceso es "
                f"indeterminada.", fuente)

    return Observabilidad(
        SI, f"{fuente} cubre la ventana ({FUENTES[fuente].desde} .. "
            f"{FUENTES[fuente].hasta}) y registra la accion '{accion}'", fuente)


def resumen() -> list[str]:
    lineas = ["FUENTES"]
    for f in FUENTES.values():
        estado = "activa" if f.activa else "APAGADA"
        lineas.append(f"  {f.nombre:<12} {f.desde} .. {f.hasta}  [{estado}]")
        lineas.append(f"  {'':<12} inicio: {f.motivo_inicio}")
        lineas.append(f"  {'':<12} fin   : {f.motivo_fin}")
    lineas.append("")
    lineas.append("CARENCIAS DE AUDITORIA")
    for c in CARENCIAS.values():
        lineas.append(f"  {c.clave:<20} ({c.fuente})")
        lineas.append(f"  {'':<20} {c.descripcion}")
        lineas.append(f"  {'':<20} {c.consecuencia}")
    return lineas
