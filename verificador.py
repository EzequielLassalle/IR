"""Verificacion de hallazgos contra la evidencia.

Un hallazgo entra al caso solo si se puede sostener. Este modulo decide eso, y es
deterministico a proposito: lo escribe un modelo, lo verifica una funcion.

Verifica tres cosas distintas, y conviene no confundirlas porque fallan distinto:

  1. **Vocabulario.** La afirmacion tiene que estar expresada en terminos observables. Un
     sujeto tiene que ser una cuenta, una credencial o un host -- nunca "el atacante", que
     es una persona y los logs no registran personas. Una accion tiene que ser un hecho
     registrado -- nunca "movimiento-lateral" o "exfiltracion", que son interpretaciones
     sobre un conjunto de eventos. Aceptarlas seria devolver la conclusion del analista con
     formato de hecho.

  2. **Existencia de la cita.** Los identificadores citados tienen que existir.

  3. **Sosten.** Los eventos citados tienen que coincidir con lo que la afirmacion dice.
     Citar W1483 para afirmar algo sobre una cuenta que no aparece en W1483 es una cita
     real que no sostiene nada, y es el modo de falla mas peligroso porque a simple vista
     el hallazgo se ve impecable.

Lo que este modulo NO verifica, y hay que tenerlo presente: la inferencia que encadena
varias citas correctas en una conclusion falsa. Un hallazgo que cita tres eventos reales,
los describe bien, y concluye algo que la evidencia no sostiene, pasa limpio. Por eso la
afirmacion se exige en el DSL cerrado de cuatro campos: lo que no se puede expresar en el
DSL no se puede verificar, y lo que no se puede verificar no entra.

Y tampoco verifica lo que el hallazgo se callo. Eso no es cuestion de verificacion sino de
medicion: ver `deteccion.medir` y `deteccion.eventos_perdidos`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from eventos import ACCIONES, Evento

# Terminos que el motor rechaza por construccion, con el motivo. El rechazo es informativo:
# dice por que ese termino no se puede someter a la evidencia, no que el analista se haya
# equivocado de sintaxis.
SUJETOS_PROHIBIDOS = {
    "el atacante": "un log registra credenciales, cuentas y hosts, nunca personas",
    "atacante": "un log registra credenciales, cuentas y hosts, nunca personas",
    "el intruso": "un log registra credenciales, cuentas y hosts, nunca personas",
    "adversario": "un log registra credenciales, cuentas y hosts, nunca personas",
    "usuario malicioso": "la intencion no es un atributo registrado",
}

ACCIONES_PROHIBIDAS = {
    "movimiento-lateral": "es una inferencia sobre un patron de eventos, no un evento",
    "exfiltracion": "es una inferencia sobre un patron de eventos, no un evento",
    "persistencia": "es una interpretacion del proposito, no un hecho registrado",
    "escalamiento-privilegios": "es una interpretacion sobre un conjunto de operaciones",
    "compromiso": "no hay ningun registro que afirme un compromiso",
    "acceso-no-autorizado": "la autorizacion no es un atributo del evento de acceso",
}

VERIFICADO = "VERIFICADO"
FUERA_DE_VOCABULARIO = "FUERA-DE-VOCABULARIO"
CITA_INEXISTENTE = "CITA-INEXISTENTE"
CITA_NO_SOSTIENE = "CITA-NO-SOSTIENE"
SIN_CITA = "SIN-CITA"


@dataclass
class Afirmacion:
    """El DSL cerrado. Cuatro campos y una ventana obligatoria.

    La ventana es obligatoria porque una afirmacion sin acotar no es falsable: siempre hay
    alguna ventana de diez dias en la que algo ocurrio.
    """

    sujeto: str
    accion: str
    objeto: str
    desde: str
    hasta: str

    @classmethod
    def desde_dict(cls, d: dict) -> "Afirmacion":
        faltan = {"sujeto", "accion", "objeto", "desde", "hasta"} - set(d)
        if faltan:
            raise ValueError(f"faltan campos en la afirmacion: {sorted(faltan)}")
        return cls(**{k: d[k] for k in ("sujeto", "accion", "objeto", "desde", "hasta")})

    def __str__(self) -> str:
        return (f"{self.sujeto} {self.accion} {self.objeto}  "
                f"[{self.desde} .. {self.hasta}]")


@dataclass
class Resultado:
    afirmacion: Afirmacion
    veredicto: str
    motivo: str
    citas_validas: list[str] = field(default_factory=list)
    citas_rechazadas: dict[str, str] = field(default_factory=dict)

    @property
    def admitido(self) -> bool:
        return self.veredicto == VERIFICADO

    def __str__(self) -> str:
        lineas = [f"  {self.afirmacion}", f"  -> {self.veredicto}: {self.motivo}"]
        if self.citas_validas:
            lineas.append(f"     sostienen: {', '.join(self.citas_validas)}")
        for eid, motivo in sorted(self.citas_rechazadas.items()):
            lineas.append(f"     {eid}: {motivo}")
        return "\n".join(lineas)


def _t(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def _coincide(e: Evento, a: Afirmacion) -> str | None:
    """None si el evento sostiene la afirmacion; si no, el motivo por el que no.

    La comparacion de sujeto y objeto es por subcadena sin distinguir mayusculas: el
    analista escribe `ecarrizo` y el evento dice `WKS-04\\ecarrizo`. Lo que NO se relaja es
    la accion, que es vocabulario cerrado y tiene que coincidir exacto.
    """
    if a.sujeto.lower() not in e.sujeto.lower():
        return f"el sujeto del evento es '{e.sujeto}'"
    if a.accion != e.accion:
        return f"la accion del evento es '{e.accion}'"
    if a.objeto.lower() not in e.objeto.lower():
        return f"el objeto del evento es '{e.objeto}'"
    if e.instante < _t(a.desde) or e.instante > _t(a.hasta):
        return f"el evento cae fuera de la ventana ({e.instante:%Y-%m-%dT%H:%M:%SZ})"
    return None


def verificar(afirmacion: Afirmacion, cita: list[str],
              eventos: list[Evento]) -> Resultado:
    """Una afirmacion con su cita contra la evidencia."""
    sujeto = afirmacion.sujeto.strip().lower()
    if sujeto in SUJETOS_PROHIBIDOS:
        return Resultado(afirmacion, FUERA_DE_VOCABULARIO,
                         f"'{afirmacion.sujeto}' no es un sujeto observable: "
                         f"{SUJETOS_PROHIBIDOS[sujeto]}")

    accion = afirmacion.accion.strip().lower()
    if accion in ACCIONES_PROHIBIDAS:
        return Resultado(afirmacion, FUERA_DE_VOCABULARIO,
                         f"'{afirmacion.accion}' no es un hecho registrado: "
                         f"{ACCIONES_PROHIBIDAS[accion]}")
    if accion not in ACCIONES:
        return Resultado(afirmacion, FUERA_DE_VOCABULARIO,
                         f"'{afirmacion.accion}' no pertenece al vocabulario. "
                         f"Acciones validas: {', '.join(sorted(ACCIONES))}")

    if not cita:
        return Resultado(afirmacion, SIN_CITA,
                         "un hallazgo sin cita no es verificable")

    indice = {e.id: e for e in eventos}
    validas: list[str] = []
    rechazadas: dict[str, str] = {}

    for eid in cita:
        e = indice.get(eid.upper())
        if e is None:
            rechazadas[eid] = "el evento no existe en la evidencia"
            continue
        motivo = _coincide(e, afirmacion)
        if motivo is None:
            validas.append(eid.upper())
        else:
            rechazadas[eid] = motivo

    if any(m == "el evento no existe en la evidencia" for m in rechazadas.values()):
        return Resultado(afirmacion, CITA_INEXISTENTE,
                         "hay identificadores citados que no existen",
                         validas, rechazadas)
    if not validas:
        return Resultado(afirmacion, CITA_NO_SOSTIENE,
                         "todos los eventos citados existen y ninguno sostiene la "
                         "afirmacion",
                         validas, rechazadas)
    return Resultado(afirmacion, VERIFICADO,
                     f"{len(validas)} de {len(cita)} citas sostienen la afirmacion",
                     validas, rechazadas)


# --------------------------------------------------------------------------------------


def sostiene(afirmacion: Afirmacion, eventos: list[Evento],
             antes_de: str | None = None) -> list[Evento]:
    """Busca en la evidencia los eventos que sostienen una afirmacion.

    Distinto de `verificar`, que comprueba una cita que alguien ya escribio. Aca no hay
    cita: se busca. Es lo que necesita el adjudicador de acciones, que tiene que preguntar
    "¿la evidencia sostiene esto?" sin que nadie le haya senialado donde mirar.

    `antes_de` acota a la evidencia **disponible al momento de decidir**, y no es un detalle:
    adjudicar una decision contra evidencia posterior a ella es juzgar con el diario del
    lunes. Una accion se evalua con lo que se sabia en `t`, no con lo que se supo despues.
    """
    limite = _t(antes_de) if antes_de else None
    out = []
    for e in eventos:
        if limite is not None and e.instante > limite:
            continue
        if _coincide(e, afirmacion) is None:
            out.append(e)
    return out


# --------------------------------------------------------------------------------------
# Afirmaciones negativas
# --------------------------------------------------------------------------------------

AUSENCIA_DEMOSTRADA = "AUSENCIA-DEMOSTRADA"
AUSENCIA_NO_CONCLUYENTE = "AUSENCIA-NO-CONCLUYENTE"
DESMENTIDA = "DESMENTIDA"


def verificar_ausencia(afirmacion: Afirmacion, eventos: list[Evento]) -> Resultado:
    """Verifica una afirmacion NEGATIVA: "esto no ocurrio".

    Es una operacion distinta de la positiva y mucho mas facil de hacer mal. Una afirmacion
    positiva se sostiene con una cita; una negativa se sostiene con **cobertura**, y no
    tener eventos nunca alcanza por si solo.

    Tres resultados:

      DESMENTIDA               Hay eventos que satisfacen la afirmacion: no ocurrio es
                               falso.
      AUSENCIA-DEMOSTRADA      No hay eventos, Y la fuente que los habria registrado cubria
                               la ventana y registra esa clase de hecho. Las tres
                               condiciones juntas.
      AUSENCIA-NO-CONCLUYENTE  No hay eventos y la cobertura no esta demostrada. No se
                               afirma nada.

    La distincion entre los dos ultimos es la que sostiene el modulo entero, y es la
    confusion mas cara del oficio: no haber encontrado GetObject en el trail no prueba que
    no hubo descargas, prueba que el trail no registra data events de S3.
    """
    from cobertura import observable

    sujeto = afirmacion.sujeto.strip().lower()
    if sujeto in SUJETOS_PROHIBIDOS:
        return Resultado(afirmacion, FUERA_DE_VOCABULARIO,
                         f"'{afirmacion.sujeto}' no es un sujeto observable: "
                         f"{SUJETOS_PROHIBIDOS[sujeto]}")
    accion = afirmacion.accion.strip().lower()
    if accion in ACCIONES_PROHIBIDAS:
        return Resultado(afirmacion, FUERA_DE_VOCABULARIO,
                         f"'{afirmacion.accion}' no es un hecho registrado: "
                         f"{ACCIONES_PROHIBIDAS[accion]}")
    if accion not in ACCIONES:
        return Resultado(afirmacion, FUERA_DE_VOCABULARIO,
                         f"'{afirmacion.accion}' no pertenece al vocabulario")

    encontrados = [e.id for e in eventos if _coincide(e, afirmacion) is None]
    if encontrados:
        return Resultado(afirmacion, DESMENTIDA,
                         f"hay {len(encontrados)} evento(s) que satisfacen la afirmacion",
                         encontrados[:10])

    obs = observable(afirmacion.accion, afirmacion.objeto,
                     afirmacion.desde, afirmacion.hasta)
    if obs.informa_la_ausencia:
        return Resultado(afirmacion, AUSENCIA_DEMOSTRADA,
                         f"no hay eventos y la cobertura esta demostrada -- {obs.motivo}")
    return Resultado(afirmacion, AUSENCIA_NO_CONCLUYENTE,
                     f"no hay eventos, pero la ausencia no informa -- {obs.motivo}")


# --------------------------------------------------------------------------------------


def cargar_hallazgos(ruta: Path) -> list[dict]:
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    return datos["hallazgos"] if isinstance(datos, dict) else datos


def verificar_archivo(ruta: Path, eventos: list[Evento]) -> list[Resultado]:
    """Verifica un archivo de hallazgos completo.

    Es el punto por el que entra lo que produce un agente: escribe el archivo, el motor lo
    verifica, y lo que no pasa queda afuera con su motivo escrito.
    """
    out: list[Resultado] = []
    for h in cargar_hallazgos(ruta):
        try:
            afirmacion = Afirmacion.desde_dict(h.get("afirmacion", {}))
        except (ValueError, TypeError) as err:
            out.append(Resultado(
                Afirmacion(str(h.get("resumen", "?"))[:40], "?", "?", "?", "?"),
                FUERA_DE_VOCABULARIO, str(err)))
            continue
        out.append(verificar(afirmacion, h.get("cita", []), eventos))
    return out
