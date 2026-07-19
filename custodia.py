"""Integridad y cadena de custodia.

Dos cosas distintas, y llamarlas por el mismo nombre es el error clasico -- esta en el
nombre de la mitad de las herramientas del rubro.

  **Integridad** es una propiedad del material: SHA-256 contra una linea base. Responde si
  los bytes cambiaron desde que se sellaron. Es una funcion matematica y no sabe nada del
  mundo.

  **Custodia** es un registro documental: quien tuvo el material, cuando y con que
  proposito. Responde por la trazabilidad de la tenencia.

La distincion no es academica. Un adversario con acceso de escritura al sellado reemplaza el
archivo y vuelve a sellar: el hash valida perfecto y lo que falla es la custodia. El hash
por si solo nunca prueba que la evidencia sea autentica, solo que no cambio desde un momento
que alguien eligio.

En este proyecto la custodia cubre ademas las **decisiones**, no solo el material. Cada
accion de respuesta deja un asiento con que se sabia en ese momento y quien decidio, que es
lo que responde en el post-mortem cuando alguien pregunta por que se apago el servidor.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent

OK = "OK"
ALTERADA = "ALTERADA"
SIN_SELLAR = "SIN SELLAR"

FUENTES = ("windows.json", "cloudtrail.json", "syslog.json")


def _ahora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


@dataclass
class Asiento:
    """Una entrada de la cadena. `detalle` es prosa; el resto es estructura."""

    momento: str
    actor: str
    accion: str
    detalle: str
    hashes: dict = field(default_factory=dict)


def _archivo(evid: Path) -> Path:
    return evid / ".custodia.json"


def cargar(evid: Path) -> dict:
    ruta = _archivo(evid)
    if not ruta.exists():
        return {"linea_base": {}, "asientos": []}
    return json.loads(ruta.read_text(encoding="utf-8"))


def guardar(evid: Path, datos: dict) -> None:
    _archivo(evid).write_text(json.dumps(datos, indent=1, ensure_ascii=False),
                              encoding="utf-8")


def sellar(evid: Path, actor: str = "generador") -> dict:
    """Establece la linea base de hashes.

    **Solo se sella evidencia recien generada.** Sellar sobre material alterado destruye la
    unica referencia contra la cual detectar la alteracion: despues de eso el verificador
    dice OK para siempre y no hay forma de saber que paso.
    """
    datos = cargar(evid)
    hashes = {n: sha256(evid / n) for n in FUENTES if (evid / n).exists()}
    datos["linea_base"] = hashes
    datos["asientos"].append(asdict(Asiento(
        momento=_ahora(), actor=actor, accion="sellado",
        detalle=f"Linea base establecida sobre {len(hashes)} fuentes.",
        hashes=hashes)))
    guardar(evid, datos)
    return datos


def verificar(evid: Path) -> tuple[str, dict]:
    """Estado de integridad y detalle por fuente."""
    datos = cargar(evid)
    base = datos.get("linea_base") or {}
    if not base:
        return SIN_SELLAR, {}

    detalle = {}
    estado = OK
    for nombre, esperado in base.items():
        ruta = evid / nombre
        if not ruta.exists():
            detalle[nombre] = ("FALTA", esperado, None)
            estado = ALTERADA
            continue
        actual = sha256(ruta)
        if actual != esperado:
            detalle[nombre] = ("ALTERADA", esperado, actual)
            estado = ALTERADA
        else:
            detalle[nombre] = (OK, esperado, actual)
    return estado, detalle


def registrar(evid: Path, actor: str, accion: str, detalle: str) -> None:
    """Aniade un asiento. No toca la linea base: registrar no es re-sellar."""
    datos = cargar(evid)
    datos["asientos"].append(asdict(Asiento(
        momento=_ahora(), actor=actor, accion=accion, detalle=detalle)))
    guardar(evid, datos)


def asientos(evid: Path) -> list[dict]:
    return cargar(evid).get("asientos", [])


def registrar_decision(evid: Path, actor: str, accion: str, objetivo: str, en: str,
                       veredicto: str, motivo: str, cita: list[str], costo: str) -> None:
    """Asiento de una decision de respuesta: cadena de custodia de lo decidido.

    Guarda **lo que se sabia en el momento de decidir**, con cita. Es lo que responde en el
    post-mortem cuando alguien pregunta por que se apago el servidor -- y lo que permite
    defender una decision que salio mal pero estaba fundada, que es distinto de una que
    estaba mal tomada.
    """
    datos = cargar(evid)
    datos.setdefault("decisiones", []).append({
        "registrado": _ahora(),
        "actor": actor,
        "accion": accion,
        "objetivo": objetivo,
        "decidida_en": en,
        "veredicto": veredicto,
        "motivo": motivo,
        "cita": cita,
        "costo": costo,
    })
    guardar(evid, datos)


def decisiones(evid: Path) -> list[dict]:
    return cargar(evid).get("decisiones", [])


def cronologia(evid: Path) -> list[str]:
    regs = decisiones(evid)
    if not regs:
        return ["  (sin decisiones registradas)"]
    lineas = []
    for d in regs:
        muestra = ", ".join(d["cita"][:6]) + (f" (+{len(d['cita']) - 6})"
                                              if len(d["cita"]) > 6 else "")
        lineas.append(f"  {d['decidida_en']}  {d['accion']} {d['objetivo']}")
        lineas.append(f"    veredicto : {d['veredicto']}  [costo {d['costo']}]")
        lineas.append(f"    se sabia  : {muestra or '(nada citado)'}")
        lineas.append(f"    motivo    : {d['motivo']}")
        lineas.append(f"    decidio   : {d['actor']}  (registrado {d['registrado']})")
        lineas.append("")
    return lineas


def resumen(evid: Path) -> list[str]:
    estado, detalle = verificar(evid)
    lineas = [f"INTEGRIDAD: {estado}"]
    for nombre, (est, esperado, actual) in sorted(detalle.items()):
        lineas.append(f"  {nombre:<18} {est}")
        lineas.append(f"  {'':<18} sellado : {esperado[:32]}...")
        if est == "ALTERADA":
            lineas.append(f"  {'':<18} actual  : {actual[:32]}...")

    lineas.append("")
    lineas.append("CADENA DE CUSTODIA")
    for a in asientos(evid):
        lineas.append(f"  {a['momento']}  {a['actor']:<14} {a['accion']}")
        lineas.append(f"  {'':<22} {a['detalle']}")
    if not asientos(evid):
        lineas.append("  (sin asientos)")
    return lineas
