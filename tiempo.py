"""Normalizacion temporal de evidencia heterogenea a UTC.

Cada fuente registra el tiempo en un formato distinto y hay que llevarlas todas a la misma
unidad para poder ordenarlas y compararlas.

  Windows Security   El EVTX guarda SystemTime ya en UTC.

  CloudTrail         eventTime es UTC, generado por el servicio.

  syslog (sshd)      RFC 3164: "Mar 11 02:04:37". Sin anio y sin offset de zona. El anio se
                     infiere de la fecha de recoleccion; la zona (-03 para web-03) se conoce
                     de la adquisicion.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

MESES = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


# --------------------------------------------------------------------------------------
# Parseo por fuente
# --------------------------------------------------------------------------------------


def desde_evtx(ts: str) -> datetime:
    """SystemTime de un registro EVTX. Ya viene en UTC."""
    return _iso(ts)


def desde_cloudtrail(ts: str) -> datetime:
    """eventTime de CloudTrail. Generado por el servicio, ya en UTC."""
    return _iso(ts)


def desde_syslog(ts: str, zona_offset_h: int, recoleccion: datetime) -> datetime:
    """Timestamp RFC 3164 ("Mar 11 02:04:37"): sin anio y sin zona en el propio texto.

    El anio se infiere como el mas reciente que no deje la fecha en el futuro respecto de
    la recoleccion. La zona se conoce fuera de banda, de la adquisicion, y se aplica aca.
    """
    mes_txt, dia_txt, hora_txt = ts.split()
    mes, dia = MESES[mes_txt], int(dia_txt)
    hh, mm, ss = (int(x) for x in hora_txt.split(":"))

    anio = _inferir_anio(mes, dia, hh, mm, ss, recoleccion)
    local = datetime(anio, mes, dia, hh, mm, ss, tzinfo=timezone.utc)
    return local - timedelta(hours=zona_offset_h)


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
