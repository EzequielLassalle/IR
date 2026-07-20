"""Conectores simulados contra los que se disparan las acciones ya adjudicadas.

Ninguno llama a un sistema real -- no hay EDR, ni firewall, ni directorio, ni IAM de nube
detras. Cada uno devuelve una respuesta con la forma de la real (un ticket, un status, un
detalle) para que la cronologia registre que la decision no solo se adjudico: se disparo
contra un sistema, aunque ese sistema sea de mentira.

Determinista a proposito: el ticket sale de un hash de `accion:objetivo`, no de un reloj ni
de un contador global, para que dos corridas del mismo caso produzcan la misma respuesta.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

# Que conector atiende cada accion, y bajo que nombre de sistema.
CONECTOR_POR_ACCION = {
    "aislar-host": "edr",
    "apagar-host": "edr",
    "capturar-memoria": "edr",
    "revocar-credencial": "iam-cloud",
    "deshabilitar-cuenta": "directorio",
    "bloquear-ip": "firewall-perimetral",
    "rotar-clave-ssh": "gestor-configuracion",
}

_DETALLE = {
    "aislar-host": "regla de aislamiento de red aplicada a {objetivo}",
    "apagar-host": "apagado remoto enviado a {objetivo}",
    "capturar-memoria": "volcado de memoria solicitado sobre {objetivo}",
    "revocar-credencial": "access key {objetivo} desactivada en IAM",
    "deshabilitar-cuenta": "cuenta {objetivo} deshabilitada en el directorio",
    "bloquear-ip": "regla de bloqueo agregada para {objetivo} en el perimetro",
    "rotar-clave-ssh": "claves autorizadas reemplazadas en {objetivo}",
}


@dataclass(frozen=True)
class RespuestaConector:
    conector: str
    ticket_id: str
    status: str
    detalle: str


def _ticket_id(conector: str, semilla: str) -> str:
    h = hashlib.sha256(semilla.encode("utf-8")).hexdigest()
    return f"{conector.upper()[:3]}-{int(h[:6], 16) % 900000 + 100000}"


def llamar(accion: str, objetivo: str) -> RespuestaConector:
    """Simula la llamada al conector correspondiente. Siempre devuelve `status: ok` --
    este proyecto no modela fallas del conector, solo su existencia como paso separado."""
    conector = CONECTOR_POR_ACCION.get(accion, "manual")
    ticket = _ticket_id(conector, f"{accion}:{objetivo}")
    detalle = _DETALLE.get(accion, "accion '{accion}' ejecutada sobre {objetivo}").format(
        accion=accion, objetivo=objetivo)
    return RespuestaConector(conector=conector, ticket_id=ticket, status="ok",
                             detalle=detalle)
