"""Normalizacion temporal de evidencia heterogenea.

Cada fuente registra el tiempo con garantias distintas. Este modulo lleva todo a UTC
arrastrando la incertidumbre en vez de descartarla: un instante no es un punto, es un
intervalo. Dos eventos solo tienen orden si sus intervalos no se solapan.

Las tres fuentes del caso y su comportamiento real:

  Windows Security   El EVTX guarda UTC (SystemTime), pero lo escribe el reloj del host.
                     Si el host derivo respecto de la fuente de tiempo autoritativa, TODOS
                     sus eventos arrastran ese desfasaje. El drift se mide fuera de banda
                     (comparando contra el DC al momento de la adquisicion), no se infiere
                     de los logs.

  CloudTrail         eventTime es UTC generado por el servicio, no por ningun host nuestro:
                     es la referencia mas confiable del caso. La latencia de entrega (hasta
                     ~15 min hasta S3) NO afecta la precision de eventTime -- afecta que el
                     evento este o no en el archivo al momento de recolectar. Eso es un
                     problema de cobertura, no de reloj, y se modela en cobertura.py.
                     Granularidad de 1 segundo: varios eventos pueden compartir timestamp.

  syslog (sshd)      RFC 3164: "Mar 11 02:04:37". Sin anio y sin offset de zona. El anio se
                     infiere de la fecha de recoleccion; la zona hay que conocerla fuera de
                     banda. Si no se conocio, la unica cota honesta es el rango completo de
                     offsets UTC vigentes (-12 a +14), y el evento deja de ser ordenable
                     contra casi todo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

# Rango de offsets UTC en uso. Un timestamp sin zona podria pertenecer a cualquiera.
OFFSET_MIN_H = -12
OFFSET_MAX_H = 14

MESES = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


@dataclass(frozen=True)
class Reloj:
    """Caracterizacion del reloj de una fuente. Se establece en la adquisicion."""

    fuente: str
    # Desfasaje medido del reloj del host respecto de UTC real, en segundos.
    # Positivo = el host adelanta (registra timestamps mayores a los reales).
    deriva_seg: int = 0
    # Incertidumbre de la medicion de la deriva, en el instante en que se midio.
    error_deriva_seg: int = 0
    # Cuando se tomo la medicion. La deriva vale exactamente ahi y se degrada al alejarse.
    medida_en: datetime | None = None
    # Cota de la TASA de deriva, en segundos por hora. Un reloj no se desfasa de golpe: se
    # desfasa progresivamente. Aplicar el offset medido en T a un evento de T-36h asume
    # tasa cero, que es justo lo que la medicion desmiente. La incertidumbre tiene que
    # crecer con la distancia temporal a la medicion.
    error_tasa_seg_h: float = 0.0
    # Granularidad del registro. Dos eventos dentro de la misma unidad no se ordenan.
    precision_seg: int = 1
    # Offset de zona en horas. None = no se capturo (solo posible en syslog).
    zona_offset_h: int | None = 0

    @property
    def zona_conocida(self) -> bool:
        return self.zona_offset_h is not None

    def incertidumbre_en(self, t: datetime) -> int:
        """Incertidumbre sistematica de la deriva para un evento ubicado en `t`.

        Es el error de la medicion mas lo que la tasa pudo acumular entre el momento del
        evento y el momento en que se midio. Un caso reconstruido dias despues del hecho
        arrastra mas incertidumbre que uno medido en caliente, y el modelo tiene que
        decirlo en vez de esconderlo detras de un numero fijo.
        """
        if self.medida_en is None or not self.error_tasa_seg_h:
            return self.error_deriva_seg
        horas = abs((self.medida_en - t).total_seconds()) / 3600.0
        return int(round(self.error_deriva_seg + horas * self.error_tasa_seg_h))


@dataclass(frozen=True)
class Instante:
    """Momento en UTC con su incertidumbre. `utc` es la mejor estimacion puntual.

    La incertidumbre se lleva partida en dos componentes, y la distincion decide el
    resultado de la mitad de las comparaciones del caso:

      propio         Independiente por evento: la granularidad del registro. Dos eventos
                     de la misma fuente separados por menos que esto no se ordenan.

      sistematico    Compartido por todos los eventos de la fuente: la deriva del reloj
                     del host, o el offset de zona desconocido. Si el reloj adelanta 340s,
                     TODOS sus eventos se corren 340s juntos -- el orden relativo entre
                     ellos queda intacto. Es error de modo comun y se cancela al comparar
                     dentro de la misma fuente.

    Tratar la deriva como incertidumbre independiente haria indecidible el orden entre dos
    eventos consecutivos del mismo log, que es falso y ademas vaciaria de sentido al
    veredicto: si todo es indecidible, INDECIDIBLE no informa nada.
    """

    utc: datetime
    propio_menos: int  # incertidumbre independiente, hacia atras
    propio_mas: int  # independiente, hacia adelante
    sistematico: int  # +/- compartido con el resto de la fuente
    crudo: str  # el texto tal como venia en la fuente
    fuente: str

    @property
    def menos_seg(self) -> int:
        return self.propio_menos + self.sistematico

    @property
    def mas_seg(self) -> int:
        return self.propio_mas + self.sistematico

    @property
    def inicio(self) -> datetime:
        return self.utc - timedelta(seconds=self.menos_seg)

    @property
    def fin(self) -> datetime:
        return self.utc + timedelta(seconds=self.mas_seg)

    @property
    def exacto(self) -> bool:
        return self.menos_seg == 0 and self.mas_seg == 0

    @property
    def amplitud_seg(self) -> int:
        return self.menos_seg + self.mas_seg

    def intervalo(self, con_sistematico: bool = True) -> tuple[datetime, datetime]:
        """Intervalo de posibilidad. Sin el componente sistematico cuando la comparacion es
        contra otro evento de la misma fuente."""
        menos = self.menos_seg if con_sistematico else self.propio_menos
        mas = self.mas_seg if con_sistematico else self.propio_mas
        return (self.utc - timedelta(seconds=menos), self.utc + timedelta(seconds=mas))

    def __str__(self) -> str:
        base = self.utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        if self.exacto:
            return base
        if self.menos_seg == self.mas_seg:
            return f"{base} +/-{_dur(self.menos_seg)}"
        return f"{base} -{_dur(self.menos_seg)}/+{_dur(self.mas_seg)}"


def _dur(seg: int) -> str:
    if seg < 60:
        return f"{seg}s"
    if seg < 3600:
        return f"{seg // 60}m"
    return f"{seg / 3600:.0f}h"


# --------------------------------------------------------------------------------------
# Parseo por fuente
# --------------------------------------------------------------------------------------


def desde_evtx(ts: str, reloj: Reloj) -> Instante:
    """SystemTime de un registro EVTX. Ya viene en UTC; se corrige por la deriva del host.

    La correccion va con signo invertido: si el host adelantaba 340s, el hecho real
    ocurrio 340s ANTES de lo que dice el registro. La incertidumbre sistematica no es fija:
    crece con la distancia entre el evento y el momento en que se midio la deriva.
    """
    t = _iso(ts)
    corregido = t - timedelta(seconds=reloj.deriva_seg)
    return Instante(
        corregido, 0, reloj.precision_seg, reloj.incertidumbre_en(corregido),
        ts, reloj.fuente
    )


def desde_cloudtrail(ts: str, reloj: Reloj) -> Instante:
    """eventTime de CloudTrail. Generado por el servicio: sin deriva de host que corregir.

    La unica incertidumbre es la granularidad de 1 segundo del campo, y es propia de cada
    registro: no hay componente sistematico porque no interviene ningun reloj nuestro.
    """
    t = _iso(ts)
    return Instante(t, 0, reloj.precision_seg, 0, ts, reloj.fuente)


def desde_syslog(ts: str, reloj: Reloj, recoleccion: datetime) -> Instante:
    """Timestamp RFC 3164 ("Mar 11 02:04:37"): sin anio y sin zona.

    El anio se infiere como el mas reciente que no deje la fecha en el futuro respecto de
    la recoleccion. Es una heuristica, no un dato: un log de mas de un anio de antiguedad
    se fecha mal y no hay forma de detectarlo desde el propio log.

    Si la zona del host no se capturo en la adquisicion, el instante real puede caer en
    cualquier offset vigente. La incertidumbre resultante (26 horas) no es un defecto del
    parser: es lo que efectivamente se sabe.
    """
    mes_txt, dia_txt, hora_txt = ts.split()
    mes, dia = MESES[mes_txt], int(dia_txt)
    hh, mm, ss = (int(x) for x in hora_txt.split(":"))

    anio = _inferir_anio(mes, dia, hh, mm, ss, recoleccion)
    local = datetime(anio, mes, dia, hh, mm, ss, tzinfo=timezone.utc)

    if not reloj.zona_conocida:
        # Sin zona: el offset real esta en algun punto del rango vigente. Es incertidumbre
        # SISTEMATICA -- todo el archivo comparte el mismo offset, sea cual sea. Por eso el
        # orden interno del log se mantiene resoluble aun sin saber la zona; lo que se
        # vuelve imposible es anclarlo contra las otras fuentes.
        centro = local - timedelta(hours=(OFFSET_MIN_H + OFFSET_MAX_H) / 2)
        span = (OFFSET_MAX_H - OFFSET_MIN_H) * 3600 // 2
        return Instante(centro, 0, reloj.precision_seg, span, ts, reloj.fuente)

    utc = local - timedelta(hours=reloj.zona_offset_h)
    corregido = utc - timedelta(seconds=reloj.deriva_seg)
    return Instante(
        corregido, 0, reloj.precision_seg, reloj.incertidumbre_en(corregido),
        ts, reloj.fuente
    )


def _inferir_anio(mes, dia, hh, mm, ss, recoleccion: datetime) -> int:
    """El anio mas reciente que no deje el evento en el futuro."""
    for anio in (recoleccion.year, recoleccion.year - 1):
        try:
            cand = datetime(anio, mes, dia, hh, mm, ss, tzinfo=timezone.utc)
        except ValueError:
            continue  # 29 de febrero en anio no bisiesto
        # Margen de 1 dia: la recoleccion y el host pueden estar en zonas distintas.
        if cand <= recoleccion + timedelta(days=1):
            return anio
    return recoleccion.year - 1


def _iso(ts: str) -> datetime:
    t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return t.astimezone(timezone.utc)


# --------------------------------------------------------------------------------------
# Orden
# --------------------------------------------------------------------------------------

ANTES = "antes"
DESPUES = "despues"
INDECIDIBLE = "indecidible"


def comparar(a: Instante, b: Instante) -> str:
    """Orden entre dos instantes, o INDECIDIBLE si sus intervalos se solapan.

    Solape significa que existe al menos una asignacion de tiempos reales, consistente con
    lo que sabemos de ambos relojes, en la que el orden se invierte. Afirmar precedencia
    ahi es afirmar mas de lo que la evidencia sostiene.

    Entre eventos de la MISMA fuente el componente sistematico se ignora: los dos se
    desplazan juntos, asi que no puede invertir su orden relativo. Entre fuentes distintas
    pesa completo, y es lo que vuelve indecidible el cruce entre el endpoint y la nube.
    """
    misma = a.fuente == b.fuente
    a_ini, a_fin = a.intervalo(con_sistematico=not misma)
    b_ini, b_fin = b.intervalo(con_sistematico=not misma)
    if a_fin < b_ini:
        return ANTES
    if b_fin < a_ini:
        return DESPUES
    return INDECIDIBLE


def separacion_minima_seg(a: Instante, b: Instante) -> int:
    """Segundos que como minimo separan a de b. 0 si el orden es indecidible."""
    misma = a.fuente == b.fuente
    a_ini, a_fin = a.intervalo(con_sistematico=not misma)
    b_ini, b_fin = b.intervalo(con_sistematico=not misma)
    if a_fin < b_ini:
        return int((b_ini - a_fin).total_seconds())
    if b_fin < a_ini:
        return int((a_ini - b_fin).total_seconds())
    return 0


def ordenar(instantes: list[Instante]) -> list[Instante]:
    """Orden por mejor estimacion puntual.

    Es un orden total sobre estimaciones, no una afirmacion de precedencia: dos elementos
    consecutivos en la lista pueden ser indecidibles entre si. Para afirmar precedencia
    hay que preguntarle a comparar().
    """
    return sorted(instantes, key=lambda i: (i.utc, i.fuente, i.crudo))


def solapados(instantes: list[Instante]) -> list[tuple[Instante, Instante]]:
    """Pares consecutivos cuyo orden no es resoluble. Son los tramos del timeline donde la
    secuencia mostrada es una eleccion de presentacion, no un hecho."""
    orden = ordenar(instantes)
    return [
        (a, b)
        for a, b in zip(orden, orden[1:])
        if comparar(a, b) == INDECIDIBLE
    ]
