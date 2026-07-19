"""Bitacora: registro de lo que el analista efectivamente miro.

Se llama asi y no `consultas` para no pisarse con `consulta.py`, que es el motor de consulta.
Este modulo no consulta nada: anota que se consulto.

Existe para cerrar una distincion que sin el es imposible: **"mirado y vacio" no es lo mismo
que "sin mirar"**. Un incidente donde nadie reviso CloudTrail y otro donde se reviso y no
habia nada producen la misma lista de hechos; el primero tiene un hueco de investigacion y
el segundo una zona descartada. Decidir una contencion sin saber cual de los dos es, es
exactamente lo que vuelve prematura a una accion.

## La leccion que costo una auditoria

La primera version registraba **lo que se pidio**, no lo que se obtuvo, y trataba a `entidad`
y `evento` como si alcanzaran todo. El resultado medido: un solo `entidad <una-ip>` marcaba
las seis zonas del escenario como "MIRADO Y VACIO", incluida `cloudtrail: llamo-api` --3.249
eventos, la mitad de la evidencia, donde vive la persistencia en la nube-- que nadie habia
tocado. El modulo cuya unica razon de ser es distinguir la ausencia fundada de la no fundada
estaba emitiendo afirmaciones de ausencia sin fundamento.

Y estaba justificado en este mismo docstring como "la lectura generosa a proposito", con el
argumento de que afirmar que algo no se miro cuando si se miro es peor que lo contrario.
**El razonamiento estaba invertido.** El costo es asimetrico en la direccion opuesta: un
hueco reportado como hueco cuesta una consulta de mas; un hueco reportado como zona
descartada cuesta el alcance del incidente.

Por eso ahora se registra **lo que la consulta devolvio** -- que fuentes, que acciones, sobre
que tramo de tiempo -- y no lo que se pidio. Una consulta que no devuelve eventos de una
fuente no la marca como mirada, por mas que el filtro la nombrara.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ARCHIVO = ".consultas.json"

# Subcomandos que constituyen al analista mirando la evidencia. `barrido`, `recomendacion` y
# los de estado no entran: no son el analista mirando, son el motor produciendo.
CONSULTAS = {"timeline", "contar", "evento", "entidad", "base", "observable"}


def _ruta(evid: Path) -> Path:
    return Path(evid) / ARCHIVO


def _t(s):
    if not s:
        return None
    if isinstance(s, datetime):
        return s
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def cargar(evid: Path) -> list[dict]:
    ruta = _ruta(evid)
    if not ruta.exists():
        return []
    return json.loads(ruta.read_text(encoding="utf-8"))


def registrar(evid: Path, comando: str, filtros: dict, alcanzado=()) -> None:
    """Anota una consulta y **lo que devolvio**.

    `alcanzado` son los eventos que la consulta efectivamente mostro. De ahi salen las
    fuentes, las acciones y el tramo temporal realmente cubierto, que es lo unico sobre lo
    que se puede afirmar que el analista miro.

    Silencioso por disenio: nunca puede romper el comando que la origino.
    """
    if comando not in CONSULTAS:
        return
    try:
        alcanzado = list(alcanzado)
        instantes = [e.instante.utc for e in alcanzado]
        registro = cargar(evid)
        registro.append({
            "momento": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "comando": comando,
            "filtros": {k: v for k, v in filtros.items() if v},
            "n": len(alcanzado),
            "fuentes": sorted({e.fuente for e in alcanzado}),
            "acciones": sorted({e.accion for e in alcanzado}),
            "desde": min(instantes).strftime("%Y-%m-%dT%H:%M:%SZ") if instantes else None,
            "hasta": max(instantes).strftime("%Y-%m-%dT%H:%M:%SZ") if instantes else None,
        })
        _ruta(evid).write_text(json.dumps(registro, indent=1, ensure_ascii=False),
                               encoding="utf-8")
    except (OSError, AttributeError):
        pass


def toco(evid: Path, fuente: str, accion: str, desde=None, hasta=None) -> bool:
    """¿Alguna consulta mostro eventos de esta fuente y accion, en este tramo de tiempo?

    Las tres condiciones se exigen **juntas**. Mirar `windows` no es haber mirado
    `cloudtrail`; mirar `creo-cuenta` no es haber mirado `llamo-api`; y haber mirado el dia 3
    no es haber mirado la ventana del incidente. Relajar cualquiera de las tres reintroduce
    el defecto que hacia mentir a este modulo.
    """
    ini, fin = _t(desde), _t(hasta)
    for c in cargar(evid):
        if not c.get("n"):
            continue  # una consulta sin resultados no cubre nada
        if fuente not in c.get("fuentes", []):
            continue
        if accion not in c.get("acciones", []):
            continue
        if ini is not None and fin is not None:
            c_ini, c_fin = _t(c.get("desde")), _t(c.get("hasta"))
            if c_ini is None or c_fin is None or c_fin < ini or c_ini > fin:
                continue  # la consulta cubrio otro tramo del tiempo
        return True
    return False


def resumen(evid: Path) -> list[str]:
    registro = cargar(evid)
    if not registro:
        return ["  (sin consultas registradas)"]
    lineas = [f"  {len(registro)} consultas registradas", ""]
    for c in registro[-20:]:
        filtros = " ".join(f"--{k} {v}" for k, v in c["filtros"].items())
        lineas.append(f"  {c['momento']}  {c['comando']:<11} {filtros}")
        if c.get("n"):
            lineas.append(f"  {'':<33} devolvio {c['n']} eventos de "
                          f"{', '.join(c['fuentes'])}")
            lineas.append(f"  {'':<33} acciones: {', '.join(c['acciones'][:6])}")
        else:
            lineas.append(f"  {'':<33} sin resultados: no cubre nada")
    if len(registro) > 20:
        lineas.append(f"  ... y {len(registro) - 20} anteriores")
    return lineas
