"""Motor de consulta y linea base.

Seis mil eventos no entran en la cabeza de nadie ni en el contexto de ningun modelo. Esa es
la premisa que justifica este modulo: la unica forma de trabajar el escenario es preguntarle
cosas, igual que en un SIEM. Filtrar, contar, agrupar, pivotear.

La linea base es lo que hace util tener diez dias en vez de una noche. Comparar la ventana
del incidente contra los dias previos convierte "esto pasó" en "esto no pasaba antes", que
es una afirmacion distinta y mucho mas fuerte. Un logon a las 3 de la maniana no dice nada;
un logon a las 3 de la maniana de una cuenta que nunca en diez dias entro fuera de horario
de oficina, si.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from eventos import Evento


def _t(v: str | datetime | None) -> datetime | None:
    if v is None or isinstance(v, datetime):
        return v
    return datetime.fromisoformat(v.replace("Z", "+00:00")).astimezone(timezone.utc)


def filtrar(eventos: list[Evento], desde=None, hasta=None, fuente=None, sujeto=None,
            accion=None, objeto=None, ip=None, texto=None,
            etiqueta=None, verdad=None) -> list[Evento]:
    """Filtro por campos normalizados. Todos los criterios se combinan con AND.

    `sujeto`, `objeto` y `texto` son subcadenas sin distincion de mayusculas: en un timeline
    real uno no se acuerda del nombre exacto, se acuerda de un pedazo.

    `etiqueta` filtra por la verdad del escenario y **no es una herramienta de analisis**:
    es para medir detectores. Usarla para investigar es hacer trampa.
    """
    desde, hasta = _t(desde), _t(hasta)
    out = []
    for e in eventos:
        if desde and e.instante < desde:
            continue
        if hasta and e.instante > hasta:
            continue
        if fuente and e.fuente != fuente:
            continue
        if accion and e.accion != accion:
            continue
        if sujeto and sujeto.lower() not in e.sujeto.lower():
            continue
        if objeto and objeto.lower() not in e.objeto.lower():
            continue
        if ip and e.ip != ip:
            continue
        if texto and texto.lower() not in str(e.crudo).lower():
            continue
        if etiqueta and verdad and verdad["eventos"][e.id]["etiqueta"] != etiqueta:
            continue
        out.append(e)
    return out


def contar(eventos: list[Evento], por: str, tope: int = 20) -> list[tuple[str, int]]:
    """Agregacion por campo. El equivalente de un `stats count by`."""
    extractor = {
        "fuente": lambda e: e.fuente,
        "accion": lambda e: e.accion,
        "sujeto": lambda e: e.sujeto,
        "objeto": lambda e: e.objeto,
        "ip": lambda e: e.ip or "(sin ip)",
        "hora": lambda e: e.instante.strftime("%H"),
        "dia": lambda e: e.instante.strftime("%Y-%m-%d"),
        "region": lambda e: e.atributos.get("region", "-"),
        "error": lambda e: e.atributos.get("error") or "(ninguno)",
        "logon_type": lambda e: str(e.atributos.get("logon_type", "-")),
        "substatus": lambda e: e.atributos.get("substatus", "-"),
    }
    if por not in extractor:
        raise ValueError(f"campo desconocido: {por}. Disponibles: {sorted(extractor)}")
    c = Counter(extractor[por](e) for e in eventos)
    return c.most_common(tope)


def pivotear(eventos: list[Evento], indicador: str) -> dict[str, list[Evento]]:
    """Todo lo que menciona un indicador, agrupado por fuente.

    Un indicador puede ser una IP, un nombre de cuenta, una access key o un binario. No se
    pregunta de que tipo es: se lo busca en todos los campos, que es como se pivotea de
    verdad cuando uno tiene un dato suelto y no sabe todavia que significa.
    """
    ind = indicador.lower()
    out: dict[str, list[Evento]] = defaultdict(list)
    for e in eventos:
        if (ind in e.sujeto.lower() or ind in e.objeto.lower()
                or ind == (e.ip or "").lower() or ind in str(e.crudo).lower()):
            out[e.fuente].append(e)
    return dict(out)


# --------------------------------------------------------------------------------------
# Linea base
# --------------------------------------------------------------------------------------


@dataclass
class Diferencia:
    campo: str
    valor: str
    en_base: int
    en_ventana: int
    primera: datetime | None = None  # primera aparicion en la ventana (solo los nuevos)

    @property
    def nuevo(self) -> bool:
        return self.en_base == 0

    @property
    def desaparecido(self) -> bool:
        return self.en_ventana == 0


# Silencio: solo tiene sentido para quien se supone que emite (un sujeto, un tipo de accion).
# Que una IP o un objeto puntual no reaparezca es ruido, no una senial.
CAMPOS_SILENCIO = ("sujeto", "accion")
# Un valor "se apago" si por su ritmo en la base esperabamos verlo >= esto y hubo cero. La
# expectativa (no un umbral crudo) es lo que hace que ande igual en una ventana de 1 hora que
# de 7 dias: en una hora casi nada tiene expectativa alta, asi que no marca falsos apagados.
EXPECTATIVA_SILENCIO = 3.0


def linea_base(eventos: list[Evento], desde_ventana, hasta_ventana,
               campos=("sujeto", "ip", "accion", "objeto")) -> list[Diferencia]:
    """Que hay en la ventana que no habia antes, y que habia y dejo de haber.

    La comparacion se normaliza por duracion: si la base son siete dias y la ventana son
    seis horas, comparar totales crudos declararia "caida" cualquier actividad rutinaria.
    Lo que interesa es lo categorico -- apareció algo que nunca existio -- no la variacion
    de volumen.
    """
    desde_ventana, hasta_ventana = _t(desde_ventana), _t(hasta_ventana)
    base = [e for e in eventos if e.instante < desde_ventana]
    ventana = sorted((e for e in eventos
                      if desde_ventana <= e.instante <= hasta_ventana),
                     key=lambda e: e.instante)

    extractor = {
        "sujeto": lambda e: e.sujeto,
        "ip": lambda e: e.ip,
        "accion": lambda e: e.accion,
        "objeto": lambda e: e.objeto,
    }

    # Factor de expectativa: que fraccion de un ritmo de base cabe en la ventana. Se usa para
    # decidir si un valor ausente "se apago" o simplemente no tocaba verlo en un tramo corto.
    factor = 0.0
    if base:
        dur_base = (desde_ventana - min(e.instante for e in base)).total_seconds()
        dur_vent = (hasta_ventana - desde_ventana).total_seconds()
        factor = (dur_vent / dur_base) if dur_base > 0 else 0.0

    diffs: list[Diferencia] = []
    for campo in campos:
        f = extractor[campo]
        c_base = Counter(f(e) for e in base if f(e))
        c_vent: Counter = Counter()
        primera: dict = {}
        for e in ventana:
            v = f(e)
            if not v:
                continue
            c_vent[v] += 1
            primera.setdefault(v, e.instante)

        # Aparecio: valor en la ventana que no existia en la base, con su primera aparicion.
        for valor, cnt in c_vent.items():
            if valor not in c_base:
                diffs.append(Diferencia(campo, valor, 0, cnt, primera[valor]))

        # Se apago: valor regular en la base que dejo de emitir, medido por expectativa.
        if campo in CAMPOS_SILENCIO and factor > 0:
            for valor, cnt in c_base.items():
                if valor not in c_vent and cnt * factor >= EXPECTATIVA_SILENCIO:
                    diffs.append(Diferencia(campo, valor, cnt, 0, None))

    return diffs


def perfil_horario(eventos: list[Evento], sujeto: str) -> dict[int, int]:
    """Distribucion horaria de un sujeto. Sirve para decidir si un horario es anomalo
    PARA ESE SUJETO, que no es lo mismo que anomalo en general."""
    return dict(sorted(Counter(
        e.instante.hour for e in eventos if e.sujeto == sujeto).items()))


def primera_y_ultima(eventos: list[Evento], indicador: str) -> tuple[Evento, Evento] | None:
    """Primera y ultima aparicion de un indicador. La primera aparicion de una IP es el
    dato que decide si un origen es nuevo o venia operando hace dias."""
    encontrados = [e for lista in pivotear(eventos, indicador).values() for e in lista]
    if not encontrados:
        return None
    encontrados.sort(key=lambda e: e.instante)
    return encontrados[0], encontrados[-1]
