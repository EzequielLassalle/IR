"""Cronologia de decisiones, y el estado de la respuesta derivado de ella.

Reemplaza al modulo de custodia, que mezclaba dos cosas de valor muy distinto en este
proyecto. El sellado SHA-256 contra linea base era **forensia heredada**: en respuesta a
incidentes nadie hashea logs, y ademas era redundante -- la guarda de semilla de
`generar_evidencia.verdad()` ya comprueba que la evidencia en disco corresponda al escenario,
que es una afirmacion mas fuerte que "no cambio desde que alguien la sello". Lo que si valia
era el registro de decisiones, y es lo unico que queda.

**El estado no se guarda aparte: se deriva replayendo la cronologia.** Es una sola fuente de
verdad. Un estado persistido al lado del registro se desincroniza en cuanto alguien edite uno
de los dos, y despues no hay forma de saber cual miente. Aca la pregunta "¿este host esta
aislado?" se contesta recorriendo lo que se decidio, que es exactamente lo que un analista
puede defender: no "el sistema dice que esta aislado", sino "se aislo el dia tal, con esta
evidencia, y lo decidio esta persona".

De ahi sale la propiedad que hace real al lazo de respuesta: una accion ya aplicada vuelve
`INAPLICABLE` a su repeticion, y desaparece de las recomendaciones. Sin esto, ejecutar no
cambia nada y el menu propone aislar el mismo host para siempre.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ARCHIVO = ".decisiones.json"

# Que estado deja cada accion sobre su objetivo. Una accion que no figura aca no cambia el
# mundo, y por lo tanto **no puede entrar al catalogo**: proponer una accion cuyo efecto el
# modelo no representa es proponer una impresion.
EFECTOS = {
    "aislar-host": "host-aislado",
    "apagar-host": "host-apagado",
    "revocar-credencial": "credencial-revocada",
    "deshabilitar-cuenta": "cuenta-deshabilitada",
    "bloquear-ip": "ip-bloqueada",
    "rotar-clave-ssh": "claves-rotadas",
    "capturar-memoria": "memoria-capturada",
}

# Acciones que quedan subsumidas por otra ya aplicada: no tiene sentido aislar un host que ya
# se apago, ni capturar la memoria despues de haberlo apagado -- ya no hay memoria.
SUBSUME = {
    "host-apagado": {"aislar-host", "apagar-host", "capturar-memoria"},
    "host-aislado": {"aislar-host"},
}


def _ahora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _t(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def _ruta(evid: Path) -> Path:
    return Path(evid) / ARCHIVO


def cargar(evid: Path) -> list[dict]:
    ruta = _ruta(evid)
    if not ruta.exists():
        return []
    return json.loads(ruta.read_text(encoding="utf-8"))


def registrar(evid: Path, actor: str, accion: str, objetivo: str, en: str,
              veredicto: str, motivo: str, cita: list[str], costo: str) -> dict:
    """Asienta una decision de respuesta.

    Guarda **lo que se sabia en el momento de decidir**, con cita. Es lo que responde en el
    post-mortem cuando preguntan por que se apago el servidor, y lo que permite defender una
    decision que salio mal estando fundada -- que es distinto de una mal tomada.

    Los asientos no se editan ni se borran. Un registro de decisiones que se puede reescribir
    despues de conocer el resultado no sirve para lo unico que sirve un registro de
    decisiones.

    Registrar una decision es ejecutarla: por eso, ademas de asentarla, se dispara el
    conector simulado que corresponde (`conectores.py`) y su respuesta queda en el mismo
    asiento. El veredicto no decide si se llama al conector -- lo decide el acto, igual que
    decide el estado (ver `estado()` abajo): un override tambien se dispara.
    """
    import conectores
    respuesta = conectores.llamar(accion, objetivo)

    entrada = {
        "registrado": _ahora(),
        "actor": actor,
        "accion": accion,
        "objetivo": objetivo,
        "decidida_en": en,
        "veredicto": veredicto,
        "motivo": motivo,
        "cita": cita,
        "costo": costo,
        "efecto": EFECTOS.get(accion),
        # Ejecutada pese a que el motor no la fundo. No la invalida -- la marca.
        "override": veredicto != "FUNDADA",
        "conector": respuesta.conector,
        "ticket_id": respuesta.ticket_id,
        "status_conector": respuesta.status,
        "detalle_conector": respuesta.detalle,
    }
    registro = cargar(evid)
    registro.append(entrada)
    _ruta(evid).write_text(json.dumps(registro, indent=1, ensure_ascii=False),
                           encoding="utf-8")
    return entrada


def estado(evid: Path, en: str | None = None) -> dict[str, dict[str, str]]:
    """Estado de la respuesta, replayando la cronologia.

    `en` acota a las decisiones anteriores a ese instante: preguntar por el estado en `t`
    tiene que devolver lo que era cierto en `t`, no lo que se hizo despues. Es la misma
    regla que gobierna la adjudicacion.

    Devuelve `{efecto: {objetivo: momento}}`.
    """
    limite = _t(en) if en else None
    out: dict[str, dict[str, str]] = {}
    for d in cargar(evid):
        # **El estado lo define el acto, no el veredicto del motor.** Si el analista ejecuta
        # una accion que el motor declaro INFUNDADA -- contener primero y justificar despues,
        # que es lo que se hace bajo presion -- el mundo cambio igual. Filtrar por FUNDADA
        # aca convertia al adjudicador en dueño de la realidad: el simulador sostenia que la
        # IP no estaba bloqueada porque no le habia gustado el fundamento, y la seguia
        # reofreciendo. Es al reves de lo que un motor de respuesta con humano en el lazo
        # tiene que hacer.
        #
        # El veredicto no se pierde: viaja como atributo del asiento y se marca como
        # override. Eso es lo que hace defendible una decision en el post-mortem.
        if limite is not None and _t(d["decidida_en"]) > limite:
            continue
        efecto = d.get("efecto")
        if efecto:
            out.setdefault(efecto, {}).setdefault(d["objetivo"], d["decidida_en"])
    return out


def ya_aplicada(evid: Path, accion: str, objetivo: str,
                en: str | None = None) -> tuple[bool, str]:
    """¿Esta accion ya se tomo sobre este objetivo, o quedo subsumida por otra?

    Devuelve `(si, motivo)`. El motivo se emite tal cual en el veredicto `INAPLICABLE`: el
    operador tiene que ver **cuando** se hizo, no solo que ya esta hecho.
    """
    actual = estado(evid, en)

    efecto = EFECTOS.get(accion)
    if efecto and objetivo in actual.get(efecto, {}):
        return True, (f"'{accion}' ya se aplico sobre {objetivo} el "
                      f"{actual[efecto][objetivo]}")

    for efecto_previo, subsumidas in SUBSUME.items():
        if accion in subsumidas and objetivo in actual.get(efecto_previo, {}):
            return True, (f"{objetivo} ya figura como {efecto_previo.replace('-', ' ')} "
                          f"desde el {actual[efecto_previo][objetivo]}: "
                          f"'{accion}' no aporta nada sobre ese estado")
    return False, ""


def cronologia(evid: Path) -> list[str]:
    registro = cargar(evid)
    if not registro:
        return ["  (sin decisiones registradas)"]
    lineas = []
    for d in registro:
        muestra = ", ".join(d["cita"][:6]) + (f" (+{len(d['cita']) - 6})"
                                              if len(d["cita"]) > 6 else "")
        lineas.append(f"  {d['decidida_en']}  {d['accion']} {d['objetivo']}")
        marca = "   << OVERRIDE del criterio del motor" if d.get("override") else ""
        lineas.append(f"    veredicto : {d['veredicto']}  [costo {d['costo']}]{marca}")
        lineas.append(f"    efecto    : {d.get('efecto') or '(ninguno)'}")
        lineas.append(f"    se sabia  : {muestra or '(nada citado)'}")
        lineas.append(f"    motivo    : {d['motivo']}")
        lineas.append(f"    decidio   : {d['actor']}  (registrado {d['registrado']})")
        if d.get("conector"):
            lineas.append(f"    conector  : {d['conector']}  ticket {d['ticket_id']}  "
                          f"[{d['status_conector']}]  {d['detalle_conector']}")
        lineas.append("")
    return lineas


def resumen_estado(evid: Path) -> list[str]:
    actual = estado(evid)
    if not actual:
        return ["  (sin acciones aplicadas)"]
    overrides = {d["objetivo"] for d in cargar(evid) if d.get("override")}
    lineas = []
    for efecto, objetivos in sorted(actual.items()):
        lineas.append(f"  {efecto}")
        for objetivo, momento in sorted(objetivos.items()):
            marca = "  (override)" if objetivo in overrides else ""
            lineas.append(f"    {objetivo:<28} desde {momento}{marca}")
    return lineas
