"""Consola del laboratorio FIR. Caso INC-2026-0051.

    python main.py                    comandos disponibles
    python main.py estado             el escenario y su forma
    python main.py panorama           tablero de orientacion del caso
    python main.py timeline           el timeline, con filtros
    python main.py evento <ID>        un evento: normalizado y crudo
    python main.py entidad <ind>      todo lo que menciona un indicador
    python main.py contar --por ip    agregacion sobre lo filtrado
    python main.py base               linea base: que hay en la ventana que no habia antes
    python main.py barrido            el detector deterministico, sus hallazgos
    python main.py verdad             la verdad del escenario (revela el caso)
    python main.py respuesta          que acciones ya se aplicaron
    python main.py cobertura          que se recolecto y que no
    python main.py observable <a> <o> si un hecho habria sido visible
    python main.py verificar <arch>   verifica un archivo de hallazgos
    python main.py test               la suite de verificaciones
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

from consulta import (  # noqa: E402
    contar, filtrar, linea_base, perfil_horario, pivotear, primera_y_ultima,
)
from deteccion import barrer  # noqa: E402
from eventos import ESTADOS_4625, LOGON_TYPES, cargar, cargar_verdad  # noqa: E402

DIRS = {"a": "evidencia", "b": "evidencia_b"}


def _evid(args) -> Path:
    return AQUI / DIRS[getattr(args, "caso", "a")]


def _anotar(args, alcanzado=()) -> None:
    """Persiste la consulta **y lo que devolvio**.

    `alcanzado` no es opcional en la practica: la bitacora registra lo que el analista vio,
    no lo que pidio. Una consulta cuyo filtro nombra una fuente pero no devuelve eventos de
    ella no la marca como mirada.
    """
    import bitacora
    campos = ("fuente", "accion", "sujeto", "objeto", "ip", "texto", "desde", "hasta",
              "id", "indicador", "por")
    bitacora.registrar(_evid(args), getattr(args, "comando", ""),
                       {c: getattr(args, c, None) for c in campos}, alcanzado)

REGLA = "-" * 78


def _seccion(titulo: str) -> None:
    print(f"\n{titulo}")
    print(REGLA)


# --------------------------------------------------------------------------------------


def cmd_estado(args) -> int:
    eventos = cargar(_evid(args))
    verdad = cargar_verdad(_evid(args))

    print(f"caso        : {verdad['caso']}")
    print(f"ventana     : {verdad['ventana']['desde']}  ..  {verdad['ventana']['hasta']}")
    print(f"entrada     : {verdad['entrada_del_analista']}  (historico congelado hasta aca)")
    print(f"recoleccion : {verdad['recoleccion']}")
    print(f"eventos     : {sum(verdad['conteo'].values())}")
    for fuente, n in sorted(verdad["conteo"].items()):
        print(f"  {fuente:<12}: {n:>5}")

    _seccion("SUJETOS MAS ACTIVOS")
    for valor, n in contar(eventos, "sujeto", tope=8):
        print(f"  {n:>6}  {valor}")

    _seccion("ACCIONES")
    for valor, n in contar(eventos, "accion", tope=12):
        print(f"  {n:>6}  {valor}")
    return 0


def _mil(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def cmd_panorama(args) -> int:
    """Tablero de orientacion: de que tamanio es el caso y en que punto del trabajo estas.
    Agrega, no interpreta: cada numero sale de un comando que ya existe."""
    import cobertura
    import decisiones

    evid = _evid(args)
    eventos = cargar(evid)
    verdad = cargar_verdad(evid)

    desde, hasta = verdad["ventana"]["desde"], verdad["ventana"]["hasta"]
    dias = (datetime.fromisoformat(hasta.replace("Z", "+00:00"))
            - datetime.fromisoformat(desde.replace("Z", "+00:00"))).days
    total = sum(verdad["conteo"].values())
    fuentes_txt = "  ".join(f"{f} {_mil(n)}"
                             for f, n in sorted(verdad["conteo"].items(), key=lambda x: -x[1]))

    n_acc = len(decisiones.cargar(evid))
    protegidos = {"hallazgos_prueba.json", "hallazgos_agente_windows.json"}
    trabajo = [p for p in AQUI.glob("hallazgos_*.json") if p.name not in protegidos]
    detector = "persistido" if (AQUI / "hallazgos_detector.json").exists() else "sin persistir"
    activas = sum(1 for f in cobertura.FUENTES.values() if f.activa)

    print(f"PANORAMA  {verdad['caso']}")
    print("=" * 70)
    print(f"Ventana        {desde[:10]}  ->  {hasta[:16].replace('T', ' ')} UTC   ({dias} dias)")
    print(f"Eventos        {_mil(total):<9} {fuentes_txt}")

    _seccion("ACTORES MAS ACTIVOS   (por volumen)")
    top = contar(eventos, "sujeto", tope=6)
    for i in range(0, len(top), 2):
        fila = "".join(f"   {_mil(n):>6}  {v:<28}" for v, n in top[i:i + 2])
        print(fila)

    _seccion("TIPOS DE ACTIVIDAD")
    for v, n in contar(eventos, "accion", tope=6):
        print(f"   {_mil(n):>6}  {v}")

    _seccion("DONDE ESTAS PARADO")
    print(f"   Cobertura       {activas} fuentes activas, ventana completa")
    print(f"   Respuesta       {n_acc} acciones aplicadas")
    print(f"   Investigacion   {len(trabajo)} hallazgos de "
          f"trabajo  |  detector {detector}")
    return 0


def _filtrados(args):
    eventos = cargar(_evid(args))
    return filtrar(eventos, desde=args.desde, hasta=args.hasta, fuente=args.fuente,
                   sujeto=args.sujeto, accion=args.accion, objeto=args.objeto,
                   ip=args.ip, texto=args.texto)


def cmd_timeline(args) -> int:
    evs = _filtrados(args)
    _anotar(args, evs)
    _seccion(f"TIMELINE  ({len(evs)} eventos)")
    for e in evs[:args.tope]:
        print(f"  {e}")
    if len(evs) > args.tope:
        print(f"\n  ... {len(evs) - args.tope} eventos mas. Acotar con --desde/--hasta o "
              f"subir --tope.")
    return 0


def cmd_contar(args) -> int:
    evs = _filtrados(args)
    _anotar(args, evs)
    _seccion(f"CONTEO POR {args.por.upper()}  (sobre {len(evs)} eventos)")
    for valor, n in contar(evs, args.por, tope=args.tope):
        print(f"  {n:>6}  {valor}")
    return 0


def cmd_evento(args) -> int:
    eventos = {e.id: e for e in cargar(_evid(args))}
    e = eventos.get(args.id.upper())
    if e is None:
        print(f"No existe el evento {args.id}.")
        return 1

    _anotar(args, [e])
    _seccion("EVENTO")
    print(f"  id        : {e.id}")
    print(f"  instante  : {e.instante:%Y-%m-%dT%H:%M:%SZ}")
    print(f"  fuente    : {e.fuente}")
    print(f"  sujeto    : {e.sujeto}")
    print(f"  accion    : {e.accion}")
    print(f"  objeto    : {e.objeto}")

    if e.atributos:
        _seccion("ATRIBUTOS")
        for k, v in e.atributos.items():
            if v is not None:
                print(f"  {k:<12}: {v}")

    crudo = e.crudo
    if e.fuente == "windows":
        eid = crudo.get("EventID")
        _seccion("SEMANTICA")
        if eid == 4624:
            nombre, desc = LOGON_TYPES.get(crudo["LogonType"], ("?", "?"))
            print(f"  4624 logon type {crudo['LogonType']} ({nombre})")
            print(f"  {desc}")
        elif eid == 4625:
            nombre, desc = ESTADOS_4625.get(crudo.get("SubStatus", ""), ("?", "?"))
            print(f"  4625 SubStatus {crudo.get('SubStatus')} ({nombre})")
            print(f"  {desc}")
        elif eid == 4688:
            print("  4688 creacion de proceso. Sin CommandLine: la auditoria de linea de")
            print("  comandos no esta habilitada. Se sabe QUE se ejecuto, no con que")
            print("  argumentos.")
        elif eid == 4720:
            print("  4720 creacion de cuenta de usuario local.")

    _seccion("REGISTRO CRUDO")
    if isinstance(crudo, dict) and "linea" in crudo:
        print(f"  {crudo['linea']}")
        print("\n  El sello de syslog esta en hora local del host (-03) y sin anio: la")
        print("  fecha del crudo puede ser el dia anterior al instante real en UTC.")
    else:
        for linea in json.dumps(crudo, indent=1, ensure_ascii=False).splitlines():
            print(f"  {linea}")
    return 0


def cmd_entidad(args) -> int:
    eventos = cargar(_evid(args))
    grupos = pivotear(eventos, args.indicador)
    total = sum(len(v) for v in grupos.values())
    _anotar(args, [e for lista in grupos.values() for e in lista])

    _seccion(f"ENTIDAD  '{args.indicador}'  ({total} eventos)")
    if not total:
        print("  Sin apariciones.")
        return 0

    rango = primera_y_ultima(eventos, args.indicador)
    print(f"  primera : {rango[0].instante:%Y-%m-%dT%H:%M:%SZ}  {rango[0].id}")
    print(f"  ultima  : {rango[1].instante:%Y-%m-%dT%H:%M:%SZ}  {rango[1].id}")

    for fuente, evs in sorted(grupos.items()):
        _seccion(f"EN {fuente.upper()}  ({len(evs)})")
        for e in evs[:args.tope]:
            print(f"  {e}")
        if len(evs) > args.tope:
            print(f"  ... {len(evs) - args.tope} mas")
    return 0


def cmd_base(args) -> int:
    eventos = cargar(_evid(args))
    diffs = linea_base(eventos, args.desde, args.hasta)
    _anotar(args, filtrar(eventos, desde=args.desde, hasta=args.hasta))

    nuevos = sorted((d for d in diffs if d.nuevo), key=lambda d: d.primera)
    apagados = sorted((d for d in diffs if d.desaparecido), key=lambda d: -d.en_base)

    _seccion(f"LINEA BASE  (ventana: {args.desde} .. {args.hasta})")
    if not nuevos and not apagados:
        print("  Sin cambios respecto de antes: nada aparecio ni se apago en la ventana.")
        return 0

    if nuevos:
        print(f"  APARECIO  ({len(nuevos)})  --  no existia antes, en orden de aparicion\n")
        for d in nuevos[:args.tope]:
            cuando = d.primera.strftime("%Y-%m-%d %H:%M")
            print(f"    {cuando}  {d.campo:<8} {d.valor:<44} x{d.en_ventana}")
        if len(nuevos) > args.tope:
            print(f"    ... {len(nuevos) - args.tope} mas")

    if apagados:
        print(f"\n  SE APAGO  ({len(apagados)})  --  emitia regularmente antes, cero ahora\n")
        for d in apagados[:args.tope]:
            print(f"    {d.campo:<8} {d.valor:<44} antes x{d.en_base}")

    return 0


def cmd_barrido(args) -> int:
    from dataclasses import asdict

    eventos = cargar(_evid(args))
    hallazgos = barrer(eventos)

    if getattr(args, "salida", None):
        destino = Path(args.salida)
        payload = {"hallazgos": [asdict(h) for h in hallazgos]}
        destino.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                           encoding="utf-8")
        print(f"{len(hallazgos)} hallazgos escritos en {destino} "
              f"(origen: detector)")
        return 0

    _seccion(f"BARRIDO DETERMINISTICO  ({len(hallazgos)} hallazgos)")
    for h in hallazgos[:args.tope]:
        print(f"\n{h}")
    if len(hallazgos) > args.tope:
        print(f"\n  ... {len(hallazgos) - args.tope} hallazgos mas")
    return 0


def cmd_verdad(args) -> int:
    verdad = cargar_verdad(_evid(args))
    if not args.si:
        print("Esto revela el escenario y arruina el ejercicio.")
        print("Si es lo que queres: python main.py verdad --si")
        return 0

    _seccion("NARRATIVA DEL INCIDENTE")
    for i, linea in enumerate(verdad["narrativa"], 1):
        print(f"  {i}. {linea}")

    _seccion("ETIQUETAS")
    total = sum(verdad["conteo"].values())
    for etiqueta, n in sorted(verdad["etiquetas"].items(), key=lambda x: -x[1]):
        print(f"  {n:>6}  ({n / total * 100:>4.1f}%)  {etiqueta}")
    return 0


def cmd_consultas(args) -> int:
    import bitacora
    _seccion("CONSULTAS REGISTRADAS")
    for linea in bitacora.resumen(_evid(args)):
        print(linea)
    return 0


def cmd_respuesta(args) -> int:
    import decisiones
    _seccion("ESTADO DE LA RESPUESTA")
    for linea in decisiones.resumen_estado(_evid(args)):
        print(linea)
    return 0


def cmd_cobertura(args) -> int:
    import cobertura
    for linea in cobertura.resumen():
        print(linea)
    return 0


def cmd_observable(args) -> int:
    """¿Habriamos visto este hecho, de haber ocurrido?"""
    from cobertura import observable
    from verificador import Afirmacion, verificar_ausencia

    obs = observable(args.accion, args.objeto, args.desde, args.hasta)
    _seccion("OBSERVABILIDAD")
    print(f"  accion  : {args.accion}")
    print(f"  objeto  : {args.objeto}")
    print(f"  ventana : {args.desde} .. {args.hasta}")
    print(f"\n  {obs}")

    if args.sujeto:
        r = verificar_ausencia(
            Afirmacion(args.sujeto, args.accion, args.objeto, args.desde, args.hasta),
            cargar(_evid(args)))
        _seccion("AFIRMACION DE AUSENCIA")
        print(f"  '{args.sujeto} NO {args.accion} {args.objeto}'")
        print(f"\n  -> {r.veredicto}")
        print(f"     {r.motivo}")
    return 0


def cmd_verificar(args) -> int:
    from verificador import verificar_archivo
    resultados = verificar_archivo(Path(args.archivo), cargar(_evid(args)))
    admitidos = [r for r in resultados if r.admitido]

    _seccion(f"VERIFICACION  ({len(admitidos)} de {len(resultados)} admitidos)")
    for r in resultados:
        print(f"\n{r}")
    return 0


def cmd_accion(args) -> int:
    import decisiones
    from acciones import CATALOGO, adjudicar

    if args.accion not in CATALOGO:
        _seccion("CATALOGO DE ACCIONES")
        for nombre, a in sorted(CATALOGO.items()):
            marca = "  (destruye evidencia)" if a.destruye_evidencia else ""
            print(f"  {nombre:<22} [{a.costo:<6}] {a.tipo_objetivo:<11}{marca}")
            print(f"  {'':<22} {a.descripcion}")
        return 0

    v = adjudicar(args.accion, args.objetivo, cargar(_evid(args)),
                  args.en, args.desde, args.hasta, _evid(args))
    a = CATALOGO[args.accion]

    _seccion("ACCION")
    print(f"  {a.nombre} {args.objetivo}")
    print(f"  {a.descripcion}")
    print(f"  decidiendo en : {args.en}")
    print(f"  costo         : {a.costo}")
    print(f"  impacto       : {a.impacto}")
    if a.destruye_evidencia:
        print("  ATENCION      : destruye evidencia no recuperable")

    _seccion("VEREDICTO")
    print(str(v))

    _seccion("QUE LA VOLVERIA PREMATURA")
    print(f"  {a.vuelve_prematura}")

    if args.registrar:
        citas = sorted({c for l in v.sostienen.values() for c in l})
        entrada = decisiones.registrar(_evid(args), args.registrar, a.nombre, args.objetivo,
                                       args.en, v.veredicto, v.motivo, citas, a.costo)
        print(f"\n  Registrada en la cronologia por '{args.registrar}'.")
        _seccion("CONECTOR")
        print(f"  {entrada['conector']}  ticket {entrada['ticket_id']}  "
              f"[{entrada['status_conector']}]")
        print(f"  {entrada['detalle_conector']}")
    return 0


def _hallazgos_de(ruta, eventos):
    """Convierte un archivo de hallazgos en insumo del recomendador.

    **Solo entran los que el verificador admite.** Un hallazgo cuya cita no sostiene lo que
    afirma no puede fundar una accion de contencion: seria recomendar sobre prosa. Los
    rechazados se informan con su motivo en vez de descartarse en silencio.
    """
    from deteccion import Hallazgo
    from verificador import Afirmacion, verificar

    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    crudos = datos["hallazgos"] if isinstance(datos, dict) else datos

    admitidos, rechazados = [], []
    for h in crudos:
        try:
            af = Afirmacion.desde_dict(h.get("afirmacion", {}))
        except (ValueError, TypeError) as err:
            rechazados.append((h.get("regla", "?"), str(err)))
            continue
        r = verificar(af, h.get("cita", []), eventos)
        if r.admitido:
            admitidos.append(Hallazgo(
                regla=h.get("regla", "?"), severidad=h.get("severidad", "MEDIA"),
                resumen=h.get("resumen", ""), cita=h.get("cita", []),
                no_prueba=h.get("no_prueba", "")))
        else:
            rechazados.append((h.get("regla", "?"), f"{r.veredicto}: {r.motivo}"))
    return admitidos, rechazados


def cmd_recomendacion(args) -> int:
    from acciones import recomendar

    eventos = cargar(_evid(args))
    hallazgos = None
    if args.hallazgos:
        hallazgos, rechazados = _hallazgos_de(args.hallazgos, eventos)
        _seccion(f"HALLAZGOS ADMITIDOS  ({len(hallazgos)} de "
                 f"{len(hallazgos) + len(rechazados)})")
        print("  Solo los verificados fundan acciones: recomendar sobre una afirmacion que")
        print("  su cita no sostiene es recomendar sobre prosa.")
        print()
        for regla, motivo in rechazados:
            print(f"  [--] {regla}: {motivo}")
        if not rechazados:
            print("  (ninguno rechazado)")

    rs = recomendar(eventos, args.en, args.desde, args.hasta,
                    hallazgos=hallazgos, evid=_evid(args))
    _seccion(f"RECOMENDACION  ({len(rs)} acciones fundadas al {args.en})")
    print("  Ordenadas por lo que preservan y por costo. Solo se proponen las FUNDADAS:")
    print("  una accion sin fundamento no se sugiere 'por las dudas'.\n")
    for r in rs:
        print(str(r))
        print()
    return 0


def cmd_situacion(args) -> int:
    from situacion import desde_hallazgos, resumen

    sit = desde_hallazgos(Path(args.archivo), cargar(_evid(args)))
    for linea in resumen(sit, cargar(_evid(args)), args.desde, args.hasta,
                         evid=_evid(args)):
        print(linea)
    return 0


def cmd_cronologia(args) -> int:
    import decisiones
    _seccion("CRONOLOGIA DE DECISIONES")
    for linea in decisiones.cronologia(_evid(args)):
        print(linea)
    return 0


def cmd_regresion(args) -> int:
    import regresion
    _seccion("SUITE DE REGRESION")
    if args.numero:
        p = next((x for x in regresion.PRUEBAS if x.numero == args.numero), None)
        if p is None:
            print(f"  No existe la prueba {args.numero}.")
            return 1
        regresion.PRUEBAS = [p]
    for linea in regresion.resumen(_evid(args), detalle=args.detalle or bool(args.numero)):
        print(linea)
    return 0


def cmd_test(args) -> int:
    return subprocess.call([sys.executable, str(AQUI / "tests.py")])


def cmd_generar(args) -> int:
    return subprocess.call([sys.executable,
                            str(AQUI / "evidencia" / "generar_evidencia.py"),
                            "--caso", getattr(args, "caso", "a")])


# --------------------------------------------------------------------------------------


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="main.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--caso", choices=["a", "b"], default="a",
                   help="a = INC-2026-0051 (por defecto). b = INC-2026-0064, cadena de "
                        "tres saltos, para practicar con otro incidente.")
    sub = p.add_subparsers(dest="comando")

    def con_filtros(sp):
        sp.add_argument("--desde")
        sp.add_argument("--hasta")
        sp.add_argument("--fuente", choices=["windows", "cloudtrail", "syslog"])
        sp.add_argument("--sujeto")
        sp.add_argument("--accion")
        sp.add_argument("--objeto")
        sp.add_argument("--ip")
        sp.add_argument("--texto")
        sp.add_argument("--tope", type=int, default=60)
        return sp

    sub.add_parser("estado").set_defaults(func=cmd_estado)

    con_filtros(sub.add_parser("timeline")).set_defaults(func=cmd_timeline)

    sp = con_filtros(sub.add_parser("contar"))
    sp.add_argument("--por", required=True)
    sp.set_defaults(func=cmd_contar)

    sp = sub.add_parser("evento")
    sp.add_argument("id")
    sp.set_defaults(func=cmd_evento)

    sp = sub.add_parser("entidad")
    sp.add_argument("indicador")
    sp.add_argument("--tope", type=int, default=25)
    sp.set_defaults(func=cmd_entidad)

    sp = sub.add_parser("panorama")
    sp.set_defaults(func=cmd_panorama)

    sp = sub.add_parser("base")
    sp.add_argument("--desde", default="2026-03-09T20:00:00Z")
    sp.add_argument("--hasta", default="2026-03-10T04:00:00Z")
    sp.add_argument("--tope", type=int, default=100)
    sp.set_defaults(func=cmd_base)

    sp = sub.add_parser("barrido")
    sp.add_argument("--tope", type=int, default=12)
    sp.add_argument("--salida", help="escribir los hallazgos a un JSON en vez de imprimirlos")
    sp.set_defaults(func=cmd_barrido)

    sp = sub.add_parser("verdad")
    sp.add_argument("--si", action="store_true")
    sp.set_defaults(func=cmd_verdad)

    sub.add_parser("respuesta").set_defaults(func=cmd_respuesta)

    sp = sub.add_parser("consultas")
    sp.set_defaults(func=cmd_consultas)
    sub.add_parser("cobertura").set_defaults(func=cmd_cobertura)

    sp = sub.add_parser("observable")
    sp.add_argument("accion")
    sp.add_argument("objeto")
    sp.add_argument("--desde", required=True)
    sp.add_argument("--hasta", required=True)
    sp.add_argument("--sujeto", help="si se da, evalua la afirmacion de ausencia completa")
    sp.set_defaults(func=cmd_observable)

    sp = sub.add_parser("verificar")
    sp.add_argument("archivo")
    sp.set_defaults(func=cmd_verificar)

    sp = sub.add_parser("accion")
    sp.add_argument("accion", nargs="?", default="",
                    help="sin argumentos lista el catalogo")
    sp.add_argument("objetivo", nargs="?", default="")
    sp.add_argument("--en", default="2026-03-10T04:00:00Z",
                    help="instante de la decision: la evidencia se acota a lo anterior")
    sp.add_argument("--desde", default="2026-03-09T20:00:00Z")
    sp.add_argument("--hasta", default="2026-03-10T04:00:00Z")
    sp.add_argument("--registrar", metavar="ACTOR",
                    help="asienta la decision en la cronologia")
    sp.set_defaults(func=cmd_accion)

    sp = sub.add_parser("recomendacion")
    sp.add_argument("--hallazgos", metavar="ARCHIVO",
                    help="recomendar a partir de una investigacion (de un agente, por "
                         "ejemplo) en vez del detector deterministico")
    sp.add_argument("--en", default="2026-03-10T04:00:00Z")
    sp.add_argument("--desde", default="2026-03-09T20:00:00Z")
    sp.add_argument("--hasta", default="2026-03-10T04:00:00Z")
    sp.set_defaults(func=cmd_recomendacion)

    sp = sub.add_parser("situacion")
    sp.add_argument("archivo")
    sp.add_argument("--desde", default="2026-03-09T20:00:00Z")
    sp.add_argument("--hasta", default="2026-03-10T04:00:00Z")
    sp.set_defaults(func=cmd_situacion)

    sub.add_parser("cronologia").set_defaults(func=cmd_cronologia)

    sp = sub.add_parser("regresion")
    sp.add_argument("numero", nargs="?", type=int)
    sp.add_argument("--detalle", action="store_true")
    sp.set_defaults(func=cmd_regresion)

    sub.add_parser("test").set_defaults(func=cmd_test)
    sub.add_parser("generar").set_defaults(func=cmd_generar)
    return p


def main(argv=None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
