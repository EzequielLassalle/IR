"""Catalogo de acciones de respuesta y su adjudicacion.

Una accion se somete al motor y el motor dice si esta **fundada en lo que la evidencia
sostiene**. Un solo eje. No se evalua si "resulto acertada" contra lo que el atacante
realmente hizo: eso exige una verdad que en produccion nadie tiene, y un SOAR dice si la
accion corresponde, no puntua al analista despues.

La decision de disenio que sostiene el modulo: **la precondicion de cada accion se declara
en el DSL de cuatro campos**, no en prosa ni en una tabla de opiniones. Una accion esta
fundada si existe un conjunto de hechos, con cita, **anteriores al momento de decidir**, que
satisfacen su precondicion declarada. Asi el veredicto no mide si el analista adivino lo que
pensaba el autor: mide si la evidencia lo respaldaba.

Cuatro veredictos de bordes nitidos. El tercero es el importante:

  FUNDADA          Todos los requisitos se satisfacen con evidencia anterior a t.
  INFUNDADA        Falta un requisito Y se puede demostrar que se estaba mirando: la
                   fuente que lo habria registrado cubria la ventana. La evidencia
                   disponible efectivamente no lo respaldaba.
  NO-ADJUDICABLE   Falta un requisito y no hay cobertura demostrada. No se puede afirmar
                   que la accion fuera infundada.
  INAPLICABLE      El objetivo no existe en la evidencia, o ya esta en ese estado.

**Lo desconocido cae en NO-ADJUDICABLE, nunca en INFUNDADA.** Es la misma regla que en
DFIR costo cinco auditorias: delegar una pregunta sobre A en una funcion que responde sobre
A-o-B, con lo desconocido tratado como permisivo en vez de indeterminado. Aca, tratar la
falta de cobertura como prueba de que la accion no correspondia seria condenar una decision
por no haber mirado donde no habia nada que mirar.

Ninguna accion entra al catalogo si el adjudicador no la evalua de verdad. Un catalogo con
acciones que no cambian nada se lee como que el modelo las contempla.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

from cobertura import observable
from eventos import Evento
from verificador import Afirmacion, sostiene

FUNDADA = "FUNDADA"
INFUNDADA = "INFUNDADA"
NO_ADJUDICABLE = "NO-ADJUDICABLE"
INAPLICABLE = "INAPLICABLE"

# Costo operativo, ordinal y declarado por el escenario. **Sin numeros.** Un modelo de costo
# con pesos elegidos por el autor es una opinion con formato de metrica: no se contrasta
# contra nada y convertiria cualquier desacuerdo en "no coincidiste con mi tabla". Lo unico
# que se afirma es el orden relativo.
COSTO = {
    "nulo": 0, "bajo": 1, "medio": 2, "alto": 3, "critico": 4,
}


@dataclass(frozen=True)
class Requisito:
    """Un hecho que tiene que estar sostenido para que la accion corresponda.

    `plantilla` es una afirmacion del DSL con `{objetivo}` sin resolver. El sujeto vacio
    significa "cualquier sujeto": lo que importa es que el hecho haya ocurrido sobre ese
    objetivo, no quien lo hizo.
    """

    descripcion: str
    sujeto: str
    accion: str
    objeto: str
    # Para objetivos de tipo `ip`, que no son expresables en el DSL: la direccion es un
    # atributo del evento, no un sujeto ni un objeto. El requisito se satisface si hay
    # eventos desde esa direccion con alguna de estas acciones.
    acciones_desde_ip: tuple[str, ...] = ()
    # Acota el requisito a una fuente. Hace falta cuando la accion solo tiene sentido en
    # una: rotar claves SSH se funda en autenticaciones de sshd, y un logon RDP de Windows
    # contra el mismo host no la funda aunque el DSL lo matchee.
    fuente: str = ""

    def afirmacion(self, objetivo: str, desde: str, hasta: str) -> Afirmacion:
        return Afirmacion(
            sujeto=self.sujeto.format(objetivo=objetivo),
            accion=self.accion,
            objeto=self.objeto.format(objetivo=objetivo),
            desde=desde, hasta=hasta)


@dataclass(frozen=True)
class Accion:
    nombre: str
    tipo_objetivo: str  # host | credencial | cuenta | ip
    descripcion: str
    requisitos: tuple[Requisito, ...]
    costo: str
    impacto: str  # que se rompe operativamente
    destruye_evidencia: bool
    vuelve_prematura: str  # la condicion que la invalidaria, declarada


# --------------------------------------------------------------------------------------
# El catalogo
# --------------------------------------------------------------------------------------

CATALOGO: dict[str, Accion] = {
    "aislar-host": Accion(
        nombre="aislar-host",
        tipo_objetivo="host",
        descripcion="Corta la conectividad de red del host, preservando su estado.",
        requisitos=(
            Requisito("acceso remoto confirmado al host",
                      sujeto="", accion="autentico-remoto", objeto="{objetivo}"),
        ),
        costo="alto",
        impacto="El host queda inalcanzable. Si presta servicio, el servicio cae.",
        destruye_evidencia=False,
        vuelve_prematura="Si el alcance no esta cerrado. Aislar un host mientras el "
                         "atacante opera en otro no lo contiene y le avisa que fue visto.",
    ),
    "apagar-host": Accion(
        nombre="apagar-host",
        tipo_objetivo="host",
        descripcion="Corta la alimentacion del host.",
        requisitos=(
            Requisito("acceso remoto confirmado al host",
                      sujeto="", accion="autentico-remoto", objeto="{objetivo}"),
        ),
        costo="alto",
        impacto="El host queda fuera de servicio.",
        destruye_evidencia=True,
        vuelve_prematura="Casi siempre. Apagar destruye la memoria volatil -- procesos, "
                         "conexiones vivas, material criptografico en RAM -- que no se "
                         "recupera despues. Aislar consigue la contencion sin ese costo.",
    ),
    "revocar-credencial": Accion(
        nombre="revocar-credencial",
        tipo_objetivo="credencial",
        descripcion="Inhabilita una access key.",
        requisitos=(
            Requisito("uso de la credencial registrado",
                      sujeto="{objetivo}", accion="llamo-api", objeto=""),
        ),
        costo="medio",
        impacto="Todo proceso que use esa credencial falla hasta que se le entregue otra.",
        destruye_evidencia=False,
        vuelve_prematura="Si hay credenciales derivadas sin identificar. Revocar la "
                         "original deja intacta cualquier key creada a partir de ella, y "
                         "encima avisa.",
    ),
    "deshabilitar-cuenta": Accion(
        nombre="deshabilitar-cuenta",
        tipo_objetivo="cuenta",
        descripcion="Deshabilita una cuenta local o de dominio.",
        requisitos=(
            Requisito("autenticacion exitosa de la cuenta",
                      sujeto="{objetivo}", accion="autentico-remoto", objeto=""),
        ),
        costo="medio",
        impacto="La persona o el servicio que use esa cuenta pierde acceso.",
        destruye_evidencia=False,
        vuelve_prematura="Si la cuenta es de servicio y no se identifico que depende de "
                         "ella.",
    ),
    "bloquear-ip": Accion(
        nombre="bloquear-ip",
        tipo_objetivo="ip",
        descripcion="Bloquea una direccion en el perimetro.",
        # Dos requisitos, y hacen falta los dos. "Hubo actividad desde esta direccion" lo
        # cumple cualquier IP del entorno, incluida la del servidor de al lado: un catalogo
        # con esa precondicion recomienda bloquear la red interna. El criterio de playbook
        # es la conjuncion -- intentos fallidos Y un acceso que funciono desde el mismo
        # origen -- que es lo que convierte un escaneo de fondo en un acceso conseguido.
        requisitos=(
            Requisito("intentos de autenticacion fallidos desde la direccion",
                      sujeto="", accion="", objeto="",
                      acciones_desde_ip=("fallo-autenticacion",
                                         "fallo-usuario-inexistente")),
            Requisito("autenticacion exitosa desde la misma direccion",
                      sujeto="", accion="", objeto="",
                      acciones_desde_ip=("autentico-remoto", "autentico-local",
                                         "autentico-red")),
        ),
        costo="bajo",
        impacto="Se pierde visibilidad de lo que esa direccion intentaba.",
        destruye_evidencia=False,
        vuelve_prematura="Si el acceso ya es con credencial valida. Bloquear el origen no "
                         "detiene a quien puede autenticarse desde cualquier otro.",
    ),
    "capturar-memoria": Accion(
        nombre="capturar-memoria",
        tipo_objetivo="host",
        descripcion="Vuelca la memoria del host para analisis posterior.",
        requisitos=(
            Requisito("ejecucion de proceso registrada en el host",
                      sujeto="{objetivo}", accion="ejecuto-proceso", objeto=""),
        ),
        costo="bajo",
        impacto="Carga sobre el host durante el volcado.",
        destruye_evidencia=False,
        vuelve_prematura="Nunca es prematura, pero es perecedera: cada minuto que pasa y "
                         "cada reinicio se lleva contenido.",
    ),
    "rotar-clave-ssh": Accion(
        nombre="rotar-clave-ssh",
        tipo_objetivo="host",
        descripcion="Reemplaza las claves autorizadas del host.",
        requisitos=(
            Requisito("autenticacion por clave publica en el host",
                      sujeto="{objetivo}", accion="autentico-remoto", objeto="{objetivo}",
                      fuente="syslog"),
        ),
        costo="medio",
        impacto="Los despliegues automatizados fallan hasta redistribuir claves.",
        destruye_evidencia=False,
        vuelve_prematura="Si no se enumeraron todas las claves autorizadas: dejar una sola "
                         "sin quitar es no haber rotado nada.",
    ),
}


# --------------------------------------------------------------------------------------
# Adjudicacion
# --------------------------------------------------------------------------------------


@dataclass
class Veredicto:
    accion: str
    objetivo: str
    veredicto: str
    motivo: str
    sostienen: dict[str, list[str]] = field(default_factory=dict)
    faltan: list[str] = field(default_factory=list)

    @property
    def fundada(self) -> bool:
        return self.veredicto == FUNDADA

    def __str__(self) -> str:
        lineas = [f"  {self.accion} {self.objetivo}",
                  f"  -> {self.veredicto}: {self.motivo}"]
        for req, citas in self.sostienen.items():
            muestra = ", ".join(citas[:6]) + (f" (+{len(citas) - 6})"
                                              if len(citas) > 6 else "")
            lineas.append(f"     [ok] {req}: {muestra}")
        for req in self.faltan:
            lineas.append(f"     [--] {req}")
        return "\n".join(lineas)


def _menciona_objetivo(eventos: list[Evento], objetivo: str, tipo: str) -> bool:
    obj = objetivo.lower()
    for e in eventos:
        if tipo == "ip" and (e.ip or "").lower() == obj:
            return True
        if obj in e.sujeto.lower() or obj in e.objeto.lower():
            return True
    return False


def adjudicar(accion: str, objetivo: str, eventos: list[Evento],
              en: str, desde: str, hasta: str, evid=None) -> Veredicto:
    """¿Esta accion esta fundada en lo que la evidencia sostenia en el instante `en`?

    La evidencia se acota a lo anterior a `en`. Adjudicar contra evidencia posterior a la
    decision es juzgar con informacion que el que decidio no tenia.
    """
    acc = CATALOGO.get(accion)
    if acc is None:
        return Veredicto(accion, objetivo, INAPLICABLE,
                         f"'{accion}' no esta en el catalogo. Disponibles: "
                         f"{', '.join(sorted(CATALOGO))}")

    if not _menciona_objetivo(eventos, objetivo, acc.tipo_objetivo):
        return Veredicto(accion, objetivo, INAPLICABLE,
                         f"'{objetivo}' no aparece en la evidencia: no hay nada sobre lo "
                         f"que actuar")

    # Estado de la respuesta: una accion ya tomada no se vuelve a tomar. Es la otra mitad
    # de INAPLICABLE, la que su definicion prometia ("o ya esta en ese estado") y que antes
    # nunca podia devolver porque ejecutar no cambiaba nada.
    if evid is not None:
        import decisiones
        aplicada, motivo = decisiones.ya_aplicada(evid, accion, objetivo, en)
        if aplicada:
            return Veredicto(accion, objetivo, INAPLICABLE, motivo)

    sostienen: dict[str, list[str]] = {}
    faltan: list[str] = []
    sin_cobertura: list[str] = []

    for req in acc.requisitos:
        # Los requisitos sobre una direccion se resuelven por atributo: la IP no es sujeto
        # ni objeto en el DSL, es un campo del evento.
        if req.acciones_desde_ip:
            citas = [e.id for e in eventos
                     if (e.ip or "").lower() == objetivo.lower()
                     and e.accion in req.acciones_desde_ip
                     and e.instante <= _iso(en)]
            if citas:
                sostienen[req.descripcion] = citas
            else:
                faltan.append(req.descripcion)
                # La ausencia de actividad desde una direccion siempre es concluyente: si
                # la fuente cubre la ventana, un evento desde esa IP habria quedado.
            continue

        af = req.afirmacion(objetivo, desde, hasta)
        universo = ([e for e in eventos if e.fuente == req.fuente]
                    if req.fuente else eventos)
        encontrados = sostiene(af, universo, antes_de=en)
        if encontrados:
            sostienen[req.descripcion] = [e.id for e in encontrados]
            continue

        faltan.append(req.descripcion)
        obs = observable(af.accion, af.objeto or "-", desde, hasta)
        if not obs.informa_la_ausencia:
            sin_cobertura.append(f"{req.descripcion} ({obs.motivo})")

    if not faltan:
        return Veredicto(accion, objetivo, FUNDADA,
                         f"los {len(acc.requisitos)} requisito(s) se satisfacen con "
                         f"evidencia anterior a {en}",
                         sostienen, faltan)

    if sin_cobertura:
        return Veredicto(accion, objetivo, NO_ADJUDICABLE,
                         "falta evidencia y no hay cobertura demostrada para afirmar que "
                         "no ocurrio -- " + "; ".join(sin_cobertura),
                         sostienen, faltan)

    return Veredicto(accion, objetivo, INFUNDADA,
                     "la evidencia anterior a la decision no sostiene "
                     + "; ".join(faltan) + ", y la fuente que lo habria registrado cubria "
                     "la ventana",
                     sostienen, faltan)


def _iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


# --------------------------------------------------------------------------------------
# Recomendacion
# --------------------------------------------------------------------------------------


@dataclass
class Recomendacion:
    """Una accion propuesta, **nunca pelada**.

    Una recomendacion sin su condicion de falsedad es una orden disfrazada de consejo. Por
    eso cada una arrastra de que depende y que la descartaria: es la diferencia entre un
    SOAR que asiste y uno que manda.
    """

    veredicto: Veredicto
    accion: Accion
    # Que hallazgos senialaron a esta entidad. Es lo que separa una recomendacion de una
    # entrada del inventario, y va en la salida: el operador tiene que poder ver por que
    # esta entidad y no otra.
    senialado_por: list[str] = field(default_factory=list)

    @property
    def orden(self) -> tuple:
        # Primero lo que no destruye evidencia, despues por costo ascendente: entre dos
        # acciones fundadas, la que cuesta menos y preserva mas va antes.
        return (self.accion.destruye_evidencia, COSTO[self.accion.costo],
                self.accion.nombre)

    def __str__(self) -> str:
        a = self.accion
        citas = sorted({c for lista in self.veredicto.sostienen.values() for c in lista})
        muestra = ", ".join(citas[:8]) + (f" (+{len(citas) - 8})" if len(citas) > 8 else "")
        lineas = [
            f"  {a.nombre} {self.veredicto.objetivo}    [costo {a.costo}]",
            f"    {a.descripcion}",
            f"    senialado  : {', '.join(self.senialado_por) or '(sin hallazgo)'}",
            f"    funda      : {'; '.join(self.veredicto.sostienen)}",
            f"    cita       : {muestra}",
            f"    impacto    : {a.impacto}",
            f"    la descarta: {a.vuelve_prematura}",
        ]
        if a.destruye_evidencia:
            lineas.insert(2, "    ATENCION   : destruye evidencia no recuperable")
        return "\n".join(lineas)


def objetivos_candidatos(eventos: list[Evento], tipo: str) -> list[str]:
    """Todas las entidades de ese tipo que aparecen en la evidencia.

    **Esto es el inventario, no una lista de sospechosos**, y por si solo no sirve para
    recomendar: en una red que funciona, todos los hosts tienen accesos, todas las cuentas
    autentican y todas las credenciales se usan. Se usa para adjudicar (donde el humano ya
    eligio el objetivo) y para saber si un objetivo existe.
    """
    vistos: set[str] = set()
    for e in eventos:
        if tipo == "host" and e.fuente in ("windows", "syslog"):
            vistos.add(e.sujeto.split("\\")[0].split(":")[0])
        elif tipo == "credencial" and e.fuente == "cloudtrail":
            vistos.add(e.sujeto)
        elif tipo == "cuenta" and e.fuente in ("windows", "syslog"):
            vistos.add(e.sujeto)
        elif tipo == "ip" and e.ip:
            vistos.add(e.ip)
    return sorted(vistos)


def objetivos_sospechosos(eventos: list[Evento], hallazgos, tipo: str,
                          desde: str, hasta: str,
                          severidades=("ALTA",)) -> dict[str, list[str]]:
    """Entidades sobre las que **algo disparo**, con el hallazgo que las seniala.

    Esta es la diferencia entre adjudicar y recomendar, y es toda la correccion.

    Adjudicar es retrospectivo: un humano ya eligio el objetivo, y con eso aporto la
    sospecha; al motor solo le queda comprobar que la evidencia respaldaba la accion. Ahi
    una precondicion de capacidad ("el host tuvo un acceso remoto") alcanza.

    Recomendar es generativo: **nadie aporto sospecha, asi que la precondicion tiene que
    cargarla entera**. Recorrer el inventario y filtrar por capacidad devuelve la red
    completa cruzada con verbos -- que es exactamente lo que este modulo hacia antes, y por
    eso proponia contener un incidente cinco dias antes de que ocurriera.

    El criterio de sospecha es que la entidad este senialada por un hallazgo, con sus
    eventos dentro de la ventana. No es el unico posible, y tiene una propiedad que
    conviene decir en voz alta: **traslada la calidad de la recomendacion a la del
    detector**. Eso es honesto y es medible, que es mejor que un umbral inventado aca.
    """
    indice = {e.id: e for e in eventos}
    ini, fin = _iso(desde), _iso(hasta)
    out: dict[str, list[str]] = defaultdict(list)

    for h in hallazgos:
        if h.severidad not in severidades:
            continue
        eventos_h = [indice[c] for c in h.cita if c in indice]
        if not any(ini <= e.instante <= fin for e in eventos_h):
            continue  # el hallazgo no cae en la ventana que se esta evaluando

        for e in eventos_h:
            if tipo == "host" and e.fuente in ("windows", "syslog"):
                out[e.sujeto.split("\\")[0].split(":")[0]].append(h.regla)
            elif tipo == "credencial" and e.fuente == "cloudtrail":
                out[e.sujeto].append(h.regla)
            elif tipo == "cuenta" and e.fuente in ("windows", "syslog"):
                out[e.sujeto].append(h.regla)
            elif tipo == "ip" and e.ip:
                out[e.ip].append(h.regla)

    return {k: sorted(set(v)) for k, v in out.items()}


def recomendar(eventos: list[Evento], en: str, desde: str, hasta: str,
               hallazgos=None, severidades=("ALTA",), evid=None) -> list[Recomendacion]:
    """Que acciones corresponden ahora, con su fundamento y su condicion de falsedad.

    **Dos condiciones, y hacen falta las dos.** La entidad tiene que estar senialada por un
    hallazgo (sospecha) y la accion tiene que estar fundada sobre ella (capacidad). Sin la
    primera se recomienda sobre el inventario; sin la segunda se recomienda una accion que
    la evidencia no respalda.

    Si no se pasan hallazgos, se corre el detector deterministico. Un agente que produjo su
    archivo de hallazgos verificado puede pasarlos y la recomendacion sale de su
    investigacion, que es el circuito que el proyecto persigue.
    """
    if hallazgos is None:
        from deteccion import barrer
        hallazgos = barrer(eventos)

    out: list[Recomendacion] = []
    for acc in CATALOGO.values():
        sospechosos = objetivos_sospechosos(eventos, hallazgos, acc.tipo_objetivo,
                                            desde, hasta, severidades)
        for objetivo, reglas in sorted(sospechosos.items()):
            v = adjudicar(acc.nombre, objetivo, eventos, en, desde, hasta, evid)
            if v.fundada:
                out.append(Recomendacion(v, acc, senialado_por=reglas))
    return sorted(out, key=lambda r: r.orden)
