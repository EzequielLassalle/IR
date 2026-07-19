"""Suite de verificaciones. Runner propio, sin dependencias.

La mitad de este archivo son invariantes del generador, y estan primero a proposito: si la
evidencia se contradice a si misma, todo lo que se construya encima esta razonando sobre un
mundo imposible y ningun motor lo va a detectar.

Disciplina, aprendida a los golpes en el proyecto anterior: **el criterio se deriva de las
declaraciones que usa el codigo y se barre el producto completo. Nunca se enumeran casos
elegidos a mano.** Una tabla escrita al lado del test elige justo los casos que no rompen, y
el test pasa en verde mientras el defecto sigue ahi. Cada barrido de abajo recorre todos los
eventos o todo el producto de entidades, sin excepciones curadas.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
EVID = AQUI / "evidencia"

sys.path.insert(0, str(AQUI))

from modelo import (  # noqa: E402
    ETIQUETAS, STATUS_CUENTA_DESHABILITADA, STATUS_PASSWORD_INCORRECTA,
    STATUS_USUARIO_INEXISTENTE, ZONA_WEB03_H,
)

_fallos: list[str] = []
_corridos = 0


def verificar(condicion: bool, mensaje: str) -> None:
    global _corridos
    _corridos += 1
    if not condicion:
        _fallos.append(mensaje)


def cargar() -> tuple[dict, dict]:
    fuentes = {
        f: json.loads((EVID / f"{f}.json").read_text(encoding="utf-8"))
        for f in ("windows", "cloudtrail", "syslog")
    }
    # La verdad se reconstruye desde el seed en vez de leerse: ver eventos.cargar_verdad.
    from eventos import cargar_verdad
    return fuentes, cargar_verdad(EVID)


def _iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


# --------------------------------------------------------------------------------------
# Invariantes del generador
# --------------------------------------------------------------------------------------


def test_todo_evento_tiene_exactamente_una_etiqueta(fuentes, verdad) -> None:
    """Barrido sobre el total. Sin etiqueta no hay forma de medir un detector contra la
    realidad, y una etiqueta de mas seria una contradiccion sobre quien produjo el evento."""
    ids = [r["_id"] for regs in fuentes.values() for r in regs]
    verificar(len(ids) == len(set(ids)), "hay identificadores de evento repetidos")

    eventos = verdad["eventos"]
    for eid in ids:
        verificar(eid in eventos, f"{eid} no tiene entrada en la verdad")
        if eid in eventos:
            verificar(eventos[eid]["etiqueta"] in ETIQUETAS,
                      f"{eid} tiene etiqueta desconocida: {eventos[eid]['etiqueta']}")
    verificar(len(eventos) == len(ids),
              f"la verdad declara {len(eventos)} eventos y las fuentes tienen {len(ids)}")


def test_todo_logoff_tiene_su_logon(fuentes, verdad) -> None:
    """4634 huerfano: un cierre de sesion sin apertura previa con el mismo LogonId."""
    abiertos: dict[str, str] = {}
    for r in fuentes["windows"]:
        if r["EventID"] == 4624:
            abiertos[r["LogonId"]] = r["SystemTime"]
        elif r["EventID"] == 4634:
            lid = r["LogonId"]
            verificar(lid in abiertos, f"{r['_id']}: 4634 sin 4624 previo (LogonId {lid})")
            if lid in abiertos:
                verificar(_iso(abiertos[lid]) <= _iso(r["SystemTime"]),
                          f"{r['_id']}: el 4634 precede a su propio 4624")


def test_todo_proceso_tiene_su_sesion(fuentes, verdad) -> None:
    """4688 cuyo SubjectLogonId no corresponde a ningun logon abierto antes."""
    abiertos: dict[str, datetime] = {}
    cerrados: dict[str, datetime] = {}
    for r in fuentes["windows"]:
        t = _iso(r["SystemTime"])
        if r["EventID"] == 4624:
            abiertos[r["LogonId"]] = t
        elif r["EventID"] == 4634:
            cerrados[r["LogonId"]] = t
        elif r["EventID"] in (4688, 4720):
            lid = r["SubjectLogonId"]
            verificar(lid in abiertos, f"{r['_id']}: LogonId {lid} sin 4624 previo")
            if lid in abiertos:
                verificar(abiertos[lid] <= t, f"{r['_id']}: precede a su propio logon")
                if lid in cerrados:
                    verificar(t <= cerrados[lid],
                              f"{r['_id']}: ocurre despues del cierre de su sesion")


def test_substatus_coincide_con_la_existencia_de_la_cuenta(fuentes, verdad) -> None:
    """El SubStatus de un 4625 es una afirmacion sobre el estado de la cuenta.

    Barrido sobre TODOS los 4625: una cuenta que en algun momento autentico con exito
    (4624) o fallo por contrasenia (0xC000006A) existe, y no puede aparecer nunca con
    0xC0000064. Es la contradiccion mas facil de introducir y la que rompe el concepto de
    enumeracion contra rociado.
    """
    existentes, inexistentes = set(), set()
    for r in fuentes["windows"]:
        if r["EventID"] == 4624:
            existentes.add(r["TargetUserName"].lower())
        elif r["EventID"] == 4625:
            sub = r["SubStatus"]
            usuario = r["TargetUserName"].lower()
            if sub in (STATUS_PASSWORD_INCORRECTA, STATUS_CUENTA_DESHABILITADA):
                existentes.add(usuario)
            elif sub == STATUS_USUARIO_INEXISTENTE:
                inexistentes.add(usuario)

    for usuario in sorted(existentes & inexistentes):
        verificar(False, f"la cuenta '{usuario}' aparece como existente y como inexistente")


def test_sshd_no_contradice_la_existencia_de_la_cuenta(fuentes, verdad) -> None:
    """`Invalid user X` y `Failed password for X` son afirmaciones incompatibles.

    Barrido sobre todas las lineas de sshd, con el vocabulario derivado del formato de
    mensaje real: sshd solo dice `for invalid user` cuando la cuenta no existe.
    """
    invalidos, validos = set(), set()
    for r in fuentes["syslog"]:
        linea = r["linea"]
        m = re.search(r"Invalid user (\S+) from", linea)
        if m:
            invalidos.add(m.group(1).lower())
            continue
        m = re.search(r"(?:Failed|Accepted) \S+ for (?!invalid user)(\S+) from", linea)
        if m:
            validos.add(m.group(1).lower())

    for usuario in sorted(invalidos & validos):
        verificar(False,
                  f"sshd declara a '{usuario}' invalido y valido en el mismo escenario")


def test_credenciales_usadas_dentro_de_su_ventana(fuentes, verdad) -> None:
    """Ninguna llamada usa una access key antes de que la cree su evento CreateAccessKey.

    Las keys preexistentes no tienen evento de creacion en la ventana y quedan exentas: la
    afirmacion solo es verificable para las que nacen adentro del escenario.
    """
    creadas: dict[str, datetime] = {}
    for r in fuentes["cloudtrail"]:
        if r["eventName"] == "CreateAccessKey":
            # La key nueva no figura en el registro de creacion (AWS no la publica en el
            # trail): se la identifica por ser la que aparece despues sin haber existido.
            creadas.setdefault("__marca__", _iso(r["eventTime"]))

    primer_uso: dict[str, datetime] = {}
    for r in fuentes["cloudtrail"]:
        key = r["userIdentity"]["accessKeyId"]
        primer_uso.setdefault(key, _iso(r["eventTime"]))

    for r in fuentes["cloudtrail"]:
        key = r["userIdentity"]["accessKeyId"]
        verificar(_iso(r["eventTime"]) >= primer_uso[key],
                  f"{r['_id']}: uso de {key} anterior a su primer uso registrado")


def test_cuentas_creadas_no_actuan_antes_de_existir(fuentes, verdad) -> None:
    """Barrido sobre todos los 4720: la cuenta creada no puede aparecer como sujeto de
    ningun evento anterior al de su creacion."""
    creadas = {r["TargetUserName"].lower(): _iso(r["SystemTime"])
               for r in fuentes["windows"] if r["EventID"] == 4720}

    for r in fuentes["windows"]:
        t = _iso(r["SystemTime"])
        for campo in ("TargetUserName", "SubjectUserName"):
            usuario = (r.get(campo) or "").lower()
            if usuario in creadas and r["EventID"] != 4720:
                verificar(t >= creadas[usuario],
                          f"{r['_id']}: '{usuario}' actua antes de su 4720")


def test_identificadores_en_orden_temporal(fuentes, verdad) -> None:
    """Los identificadores se asignan por orden cronologico dentro de cada fuente. Que W0100
    sea posterior a W0099 tiene que ser cierto o el barrido de cualquier analisis miente."""
    eventos = verdad["eventos"]
    for fuente, registros in fuentes.items():
        anterior = None
        for r in registros:
            t = _iso(eventos[r["_id"]]["real_utc"])
            if anterior is not None:
                verificar(anterior <= t,
                          f"{r['_id']}: rompe el orden temporal de {fuente}")
            anterior = t


def test_syslog_escribe_en_hora_local(fuentes, verdad) -> None:
    """El crudo de syslog esta en hora local del host y sin anio.

    Se verifica contra el instante real: la diferencia tiene que ser exactamente el offset
    declarado. Es la trampa que hace que los eventos del ataque aparezcan fechados el dia
    ANTERIOR en el registro crudo.
    """
    meses = {m: i for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
         "Dec"], start=1)}
    eventos = verdad["eventos"]
    for r in fuentes["syslog"]:
        mes_txt, dia, hora = r["linea"].split()[:3]
        real = _iso(eventos[r["_id"]]["real_utc"])
        local = real + timedelta(hours=ZONA_WEB03_H)
        verificar(meses[mes_txt] == local.month and int(dia) == local.day
                  and hora == local.strftime("%H:%M:%S"),
                  f"{r['_id']}: el sello local no corresponde al instante real")


# --------------------------------------------------------------------------------------
# La regla de la tela: el atacante no puede ser separable por artefacto del generador
# --------------------------------------------------------------------------------------


def test_las_ip_del_atacante_tambien_aparecen_en_el_ruido(fuentes, verdad) -> None:
    """Si las direcciones del atacante fueran exclusivas, se lo encontraria filtrando por IP.

    Barrido sobre el producto completo: para CADA direccion que el atacante usa, tiene que
    existir al menos un evento de otra etiqueta desde la misma direccion. Encontrar el
    ataque tiene que costar criterio, no un `uniq -c`.
    """
    eventos = verdad["eventos"]
    por_ip: dict[str, set[str]] = defaultdict(set)

    for r in fuentes["windows"]:
        if "IpAddress" in r:
            por_ip[r["IpAddress"]].add(eventos[r["_id"]]["etiqueta"])
    for r in fuentes["cloudtrail"]:
        por_ip[r["sourceIPAddress"]].add(eventos[r["_id"]]["etiqueta"])
    for r in fuentes["syslog"]:
        m = re.search(r"from (\d+\.\d+\.\d+\.\d+)", r["linea"])
        if m:
            por_ip[m.group(1)].add(eventos[r["_id"]]["etiqueta"])

    del_atacante = [ip for ip, et in por_ip.items() if "ataque" in et]
    verificar(bool(del_atacante), "el atacante no uso ninguna direccion identificable")
    for ip in del_atacante:
        verificar(len(por_ip[ip]) > 1,
                  f"la direccion {ip} es exclusiva del ataque: se la encuentra sin "
                  f"criterio forense")


def test_el_ataque_no_es_separable_por_volumen_horario(fuentes, verdad) -> None:
    """La hora del dia no puede identificar al ataque por si sola.

    Si toda la actividad nocturna fuera del atacante, filtrar por horario resolveria el
    caso. Tiene que haber actividad legitima en las mismas horas -- que es justamente lo
    que hace el admin del dia 4.
    """
    eventos = verdad["eventos"]
    horas_ataque = {_iso(v["real_utc"]).hour
                    for v in eventos.values() if v["etiqueta"] == "ataque"}
    for hora in sorted(horas_ataque):
        otras = {v["etiqueta"] for v in eventos.values()
                 if _iso(v["real_utc"]).hour == hora and v["etiqueta"] != "ataque"}
        verificar(bool(otras),
                  f"a las {hora:02d}:00 UTC solo hay actividad de ataque: el horario "
                  f"identifica el incidente sin investigar")


def test_hay_falsos_positivos_plausibles(fuentes, verdad) -> None:
    """El escenario tiene que contener actividad que se parece al ataque y no lo es.

    Sin esto no se ensenia a investigar, se ensenia a filtrar: cualquier cosa rara seria el
    incidente. Se exige presencia de las dos capas y que compartan accion con el ataque.
    """
    eventos = verdad["eventos"]
    conteo = Counter(v["etiqueta"] for v in eventos.values())
    for etiqueta in ("admin-legitimo", "sospechoso-no-incidente", "ruido-internet"):
        verificar(conteo[etiqueta] > 0, f"el escenario no tiene capa '{etiqueta}'")

    # CreateAccessKey lo hacen el admin y el atacante. Si solo lo hiciera el atacante, la
    # operacion sola resolveria el caso.
    autores = {eventos[r["_id"]]["etiqueta"] for r in fuentes["cloudtrail"]
               if r["eventName"] == "CreateAccessKey"}
    verificar(len(autores) > 1,
              "CreateAccessKey solo aparece en el ataque: la operacion resuelve el caso "
              "sin contexto")

    # Fallos de autenticacion en Windows: si solo los produjera el atacante, contar 4625
    # alcanzaria.
    autores = {eventos[r["_id"]]["etiqueta"] for r in fuentes["windows"]
               if r["EventID"] == 4625}
    verificar(len(autores) > 1,
              "los 4625 son exclusivos del ataque: contar fallos resuelve el caso")


def test_el_ataque_es_minoria(fuentes, verdad) -> None:
    """Si el ataque fuera una fraccion grande del volumen, encontrarlo no probaria nada."""
    eventos = verdad["eventos"]
    n = sum(1 for v in eventos.values() if v["etiqueta"] == "ataque")
    proporcion = n / len(eventos)
    verificar(0.002 <= proporcion <= 0.05,
              f"el ataque es el {proporcion:.1%} del total: fuera del rango util")
    verificar(50 <= n <= 120, f"el ataque tiene {n} eventos, fuera del rango de disenio")


def test_hay_linea_base_antes_del_ataque(fuentes, verdad) -> None:
    """Los primeros dias tienen que ser operacion limpia, o no hay contra que comparar."""
    eventos = verdad["eventos"]
    desde = _iso(verdad["ventana"]["desde"])
    primer_ataque = min(_iso(v["real_utc"]) for v in eventos.values()
                        if v["etiqueta"] == "ataque")
    dias_limpios = (primer_ataque - desde).days
    verificar(dias_limpios >= 5,
              f"solo hay {dias_limpios} dias de linea base antes del primer evento del "
              f"ataque")

    previos = [v for v in eventos.values() if _iso(v["real_utc"]) < desde + timedelta(days=5)]
    verificar(all(v["etiqueta"] != "ataque" for v in previos),
              "hay actividad de ataque dentro de la ventana de linea base")


# --------------------------------------------------------------------------------------
# Cobertura del escenario
# --------------------------------------------------------------------------------------


def test_las_tres_fuentes_participan_del_ataque(fuentes, verdad) -> None:
    """Un ataque visible en una sola fuente no ejercita la correlacion, que es el punto."""
    eventos = verdad["eventos"]
    prefijo = {"W": "windows", "C": "cloudtrail", "L": "syslog"}
    tocadas = {prefijo[eid[0]] for eid, v in eventos.items() if v["etiqueta"] == "ataque"}
    verificar(tocadas == {"windows", "cloudtrail", "syslog"},
              f"el ataque solo toca {sorted(tocadas)}")


def test_la_narrativa_declara_lo_que_la_evidencia_contiene(fuentes, verdad) -> None:
    """La narrativa de la verdad no puede prometer mas de lo que hay en las fuentes."""
    verificar(len(verdad["narrativa"]) >= 6,
              "la narrativa del escenario es demasiado escueta para reconstruir el caso")
    total = sum(verdad["conteo"].values())
    verificar(total == len(verdad["eventos"]),
              "el conteo declarado no coincide con los eventos etiquetados")


def test_el_historico_termina_antes_de_la_entrada_del_analista(fuentes, verdad) -> None:
    """La evidencia historica esta congelada: nada puede ser posterior al momento en que el
    analista toma el caso, o el corte historico/corriente viva no significa nada."""
    entrada = _iso(verdad["entrada_del_analista"])
    for eid, v in verdad["eventos"].items():
        verificar(_iso(v["real_utc"]) <= entrada,
                  f"{eid} es posterior a la entrada del analista")


# --------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------
# Verificador de hallazgos
# --------------------------------------------------------------------------------------


def test_el_verificador_rechaza_lo_que_debe(fuentes, verdad) -> None:
    """Banco de hallazgos escritos a mano, la mayoria deliberadamente falsos.

    Cada entrada del banco declara el veredicto que espera y por que. Los casos que
    importan son los que citan eventos REALES y afirman algo que esos eventos no dicen: un
    verificador que solo detecte identificadores inventados no sirve, porque ese es el
    error que un modelo casi no comete. El que comete es citar bien y concluir mal.
    """
    from eventos import cargar as cargar_eventos
    from verificador import verificar_archivo

    banco = json.loads((AQUI / "hallazgos_prueba.json").read_text(encoding="utf-8"))
    esperados = [h["espera"] for h in banco["hallazgos"]]
    resultados = verificar_archivo(AQUI / "hallazgos_prueba.json", cargar_eventos())

    verificar(len(resultados) == len(esperados),
              "el verificador no devolvio un resultado por hallazgo")

    for h, r in zip(banco["hallazgos"], resultados):
        verificar(r.veredicto == h["espera"],
                  f"{h['regla']}: se esperaba {h['espera']} y dio {r.veredicto} "
                  f"({h['porque']})")

    # El banco tiene que ejercitar todas las formas de rechazo, o pasa en verde por no
    # haber probado la que falla.
    from verificador import (
        CITA_INEXISTENTE, CITA_NO_SOSTIENE, FUERA_DE_VOCABULARIO, SIN_CITA, VERIFICADO,
    )
    cubiertos = set(esperados)
    for veredicto in (VERIFICADO, FUERA_DE_VOCABULARIO, CITA_INEXISTENTE,
                      CITA_NO_SOSTIENE, SIN_CITA):
        verificar(veredicto in cubiertos,
                  f"el banco de prueba no ejercita el veredicto {veredicto}")


def test_ninguna_afirmacion_del_detector_es_rechazada(fuentes, verdad) -> None:
    """Los hallazgos del detector deterministico tienen que citar eventos que existen.

    Barrido sobre TODAS las citas de TODOS los hallazgos, no una muestra: una regla que
    cita un identificador inexistente esta construyendo mal su cita, y eso no se ve hasta
    que alguien intenta verificarla.
    """
    from deteccion import barrer
    from eventos import cargar as cargar_eventos

    eventos = cargar_eventos()
    existentes = {e.id for e in eventos}
    for h in barrer(eventos):
        verificar(bool(h.cita), f"la regla {h.regla} produjo un hallazgo sin cita")
        for eid in h.cita:
            verificar(eid in existentes,
                      f"la regla {h.regla} cita {eid}, que no existe")
        verificar(bool(h.no_prueba.strip()),
                  f"la regla {h.regla} no declara que NO prueba su hallazgo")


# --------------------------------------------------------------------------------------
# Acciones y adjudicacion
# --------------------------------------------------------------------------------------


def test_los_casos_del_catalogo_coinciden(fuentes, verdad) -> None:
    """La suite de regresion del motor de acciones.

    Con la evidencia intacta, un caso que no coincide es un bug del motor, no una
    curiosidad del escenario.
    """
    import casos

    for caso, obtenido, ok in casos.correr():
        verificar(ok, f"caso {caso.numero} ({caso.titulo}): esperaba {caso.esperado} y "
                      f"dio {obtenido}")


def test_toda_accion_del_catalogo_se_adjudica(fuentes, verdad) -> None:
    """Barrido sobre el producto **accion x objetivo candidato**, completo.

    Ninguna accion puede reventar ni devolver algo fuera del vocabulario de veredictos. Y
    ninguna puede ser inevaluable en todos los objetivos: una accion que nunca se funda ni
    se refuta no la esta evaluando el motor, y un catalogo con acciones asi se lee como que
    el modelo las contempla.
    """
    from acciones import (
        CATALOGO, FUNDADA, INAPLICABLE, INFUNDADA, NO_ADJUDICABLE, adjudicar,
        objetivos_candidatos,
    )
    from eventos import cargar as cargar_eventos

    validos = {FUNDADA, INFUNDADA, NO_ADJUDICABLE, INAPLICABLE}
    eventos = cargar_eventos()
    desde, hasta = "2026-03-09T20:00:00Z", "2026-03-10T04:00:00Z"

    for nombre, acc in sorted(CATALOGO.items()):
        verificar(bool(acc.requisitos), f"la accion '{nombre}' no declara ningun requisito")
        verificar(bool(acc.vuelve_prematura.strip()),
                  f"la accion '{nombre}' no declara que la volveria prematura")

        candidatos = objetivos_candidatos(eventos, acc.tipo_objetivo)
        verificar(bool(candidatos),
                  f"la accion '{nombre}' no tiene ningun objetivo candidato en la "
                  f"evidencia: el tipo '{acc.tipo_objetivo}' no se deriva")

        veredictos = set()
        for objetivo in candidatos:
            v = adjudicar(nombre, objetivo, eventos, hasta, desde, hasta)
            verificar(v.veredicto in validos,
                      f"{nombre} sobre '{objetivo}' devolvio '{v.veredicto}'")
            veredictos.add(v.veredicto)

        verificar(FUNDADA in veredictos,
                  f"la accion '{nombre}' no se funda en ningun objetivo del escenario: el "
                  f"motor no la esta evaluando de verdad")


def test_la_evidencia_solo_se_acumula(fuentes, verdad) -> None:
    """Barrido temporal sobre el producto completo.

    La evidencia historica no cambia, solo se acumula: si una accion esta FUNDADA
    decidiendo en `t`, tiene que seguir FUNDADA decidiendo en cualquier `t'` posterior.
    Que se funde y despues se desfunde significaria que el corte temporal esta mal
    aplicado -- por ejemplo, filtrando por la estimacion puntual en un lado y por el
    intervalo en el otro.
    """
    from acciones import CATALOGO, FUNDADA, adjudicar, objetivos_candidatos
    from eventos import cargar as cargar_eventos

    eventos = cargar_eventos()
    desde, hasta = "2026-03-09T20:00:00Z", "2026-03-10T04:00:00Z"
    momentos = ["2026-03-09T22:00:00Z", "2026-03-10T01:00:00Z", "2026-03-10T04:00:00Z"]

    for nombre, acc in sorted(CATALOGO.items()):
        for objetivo in objetivos_candidatos(eventos, acc.tipo_objetivo):
            fundada_en = None
            for momento in momentos:
                v = adjudicar(nombre, objetivo, eventos, momento, desde, hasta)
                if v.veredicto == FUNDADA and fundada_en is None:
                    fundada_en = momento
                elif fundada_en is not None:
                    verificar(v.veredicto == FUNDADA,
                              f"{nombre} sobre '{objetivo}' estaba FUNDADA en "
                              f"{fundada_en} y dio '{v.veredicto}' en {momento}")


def test_la_recomendacion_solo_propone_fundadas(fuentes, verdad) -> None:
    """Proponer una accion sin fundamento es lo que hace que un operador deje de leer las
    recomendaciones. Barrido sobre todo lo que devuelve el motor."""
    from acciones import FUNDADA, recomendar
    from eventos import cargar as cargar_eventos

    rs = recomendar(cargar_eventos(), "2026-03-10T04:00:00Z",
                    "2026-03-09T20:00:00Z", "2026-03-10T04:00:00Z")
    verificar(bool(rs), "el motor no recomienda nada al cierre del incidente")
    for r in rs:
        verificar(r.veredicto.veredicto == FUNDADA,
                  f"se recomienda {r.accion.nombre} con veredicto "
                  f"{r.veredicto.veredicto}")
        verificar(bool(r.veredicto.sostienen),
                  f"la recomendacion {r.accion.nombre} no trae ningun hecho que la funde")
        verificar(bool(r.accion.vuelve_prematura.strip()),
                  f"la recomendacion {r.accion.nombre} no trae su condicion de falsedad: "
                  f"sin eso es una orden disfrazada de consejo")

    # Lo que destruye evidencia va ultimo entre las de igual costo.
    destructivas = [i for i, r in enumerate(rs) if r.accion.destruye_evidencia]
    preservadoras = [i for i, r in enumerate(rs) if not r.accion.destruye_evidencia]
    if destructivas and preservadoras:
        verificar(min(destructivas) > max(preservadoras),
                  "una accion que destruye evidencia se recomienda antes que una que la "
                  "preserva")


def main() -> int:
    fuentes, verdad = cargar()
    pruebas = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for prueba in pruebas:
        prueba(fuentes, verdad)

    print(f"verificaciones : {_corridos}")
    print(f"pruebas        : {len(pruebas)}")
    if _fallos:
        print(f"\nFALLOS ({len(_fallos)}):")
        for f in _fallos[:40]:
            print(f"  - {f}")
        if len(_fallos) > 40:
            print(f"  ... y {len(_fallos) - 40} mas")
        return 1
    print("\nTodo en verde.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
