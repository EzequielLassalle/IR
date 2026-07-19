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

## Y la segunda vuelta de la misma leccion

La correccion anterior guardaba las fuentes y las acciones como **dos conjuntos
independientes**, y eso da por mirado el producto cartesiano de ambos. Un `timeline` sin
filtro de fuente que devolvia un `cerro-sesion` de syslog y algun evento de windows marcaba
`windows/cerro-sesion` como zona descartada, aunque en esa ventana Windows no tuviera ni un
cierre de sesion. Menos grave que el bug original y exactamente el mismo modo de falla, en la
misma funcion, disparado por la consulta mas comun que hace cualquiera.

**La unidad sobre la que se pregunta es el par (fuente, accion), asi que es el par lo que hay
que guardar.** Aplanarlo en dos conjuntos es volver a afirmar cobertura que no se tiene.

Y se guardan **dos tiempos distintos**, que no son lo mismo: el `alcance` es la ventana que la
consulta abarco -- de sus filtros, o toda la evidencia si no los tenia -- y decide si el
tramo pedido estuvo cubierto; el tramo de los resultados solo dice donde cayo lo que hubo.
Usar el segundo para juzgar cobertura declararia sin mirar cualquier ventana donde la
consulta no encontro nada, que es justo al reves.
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


# Ventana completa del escenario. Una consulta sin filtros temporales abarca todo.
ALCANCE_TOTAL = ("2026-03-02T00:00:00Z", "2026-03-12T23:59:59Z")


def registrar(evid: Path, comando: str, filtros: dict, alcanzado=()) -> None:
    """Anota una consulta, **las zonas que devolvio** y **la ventana que abarco**.

    Las zonas se guardan como pares `fuente|accion`, que es la unidad sobre la que despues
    se pregunta. Guardar fuentes y acciones por separado da por mirado el producto cartesiano
    de ambas, que es afirmar cobertura que no se tiene.

    El alcance sale de los filtros temporales de la consulta, no del tramo donde cayeron los
    resultados: una consulta sobre diez dias que devolvio tres eventos de un martes **miro**
    los diez dias, aunque solo hubiera algo el martes.

    Silencioso por disenio: nunca puede romper el comando que la origino.
    """
    if comando not in CONSULTAS:
        return
    try:
        alcanzado = list(alcanzado)
        registro = cargar(evid)
        registro.append({
            "momento": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "comando": comando,
            "filtros": {k: v for k, v in filtros.items() if v},
            "n": len(alcanzado),
            "zonas": sorted({f"{e.fuente}|{e.accion}" for e in alcanzado}),
            "alcance_desde": filtros.get("desde") or ALCANCE_TOTAL[0],
            "alcance_hasta": filtros.get("hasta") or ALCANCE_TOTAL[1],
        })
        _ruta(evid).write_text(json.dumps(registro, indent=1, ensure_ascii=False),
                               encoding="utf-8")
    except (OSError, AttributeError):
        pass


def toco(evid: Path, fuente: str, accion: str, desde=None, hasta=None) -> bool:
    """¿Alguna consulta mostro eventos de ESTE par fuente/accion, cubriendo ESTA ventana?

    Las dos condiciones se exigen juntas y sobre el par, no sobre sus componentes por
    separado. Mirar `syslog/cerro-sesion` y `windows/ejecuto-proceso` en la misma consulta no
    es haber mirado `windows/cerro-sesion`, aunque las cuatro palabras aparezcan en el
    registro. Relajarlo reintroduce el defecto que hacia mentir a este modulo.

    La ventana se exige por **contencion**: la consulta tuvo que abarcar el tramo entero.
    Haber mirado una hora del dia 5 no es haber mirado la ventana del incidente.
    """
    ini, fin = _t(desde), _t(hasta)
    zona = f"{fuente}|{accion}"
    for c in cargar(evid):
        if not c.get("n"):
            continue  # una consulta sin resultados no cubre nada
        if zona not in c.get("zonas", []):
            continue
        if ini is not None and fin is not None:
            a_ini, a_fin = _t(c.get("alcance_desde")), _t(c.get("alcance_hasta"))
            if a_ini is None or a_fin is None or a_ini > ini or a_fin < fin:
                continue  # la consulta no abarco la ventana entera
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
            lineas.append(f"  {'':<33} devolvio {c['n']} eventos en "
                          f"{len(c['zonas'])} zona(s)")
            lineas.append(f"  {'':<33} {', '.join(c['zonas'][:5])}")
            lineas.append(f"  {'':<33} abarco {c['alcance_desde']} .. "
                          f"{c['alcance_hasta']}")
        else:
            lineas.append(f"  {'':<33} sin resultados: no cubre nada")
    if len(registro) > 20:
        lineas.append(f"  ... y {len(registro) - 20} anteriores")
    return lineas
