"""Detector deterministico: el grupo de control.

Reglas escritas a mano, estilo SIEM. Encuentra exactamente lo que las reglas fueron escritas
para encontrar, ni mas ni menos, y esa limitacion es el punto: es la referencia contra la
cual se mide cualquier otro analista, humano o modelo.

Cada regla declara su `cita` -- los identificadores de evento que la sostienen -- porque una
deteccion sin cita no es verificable, y porque la cita es lo que despues permite medirla
contra la etiqueta de verdad.

Y cada regla declara tambien `no_prueba`. Es lo que separa un hallazgo de una conclusion:
una rafaga de fallos desde una IP prueba que alguien probo credenciales, no que haya sido
una persona, ni la misma persona que entro despues. Sin ese campo el informe promete de mas.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import timedelta

from eventos import Evento


@dataclass
class Hallazgo:
    regla: str
    severidad: str  # ALTA / MEDIA / BAJA
    resumen: str
    cita: list[str]
    no_prueba: str
    atributos: dict = field(default_factory=dict)

    def __str__(self) -> str:
        cita = ", ".join(self.cita[:8]) + (f" (+{len(self.cita) - 8})"
                                           if len(self.cita) > 8 else "")
        return (f"[{self.severidad}] {self.regla}\n"
                f"  {self.resumen}\n"
                f"  cita: {cita}\n"
                f"  no prueba: {self.no_prueba}")


# --------------------------------------------------------------------------------------
# Reglas
# --------------------------------------------------------------------------------------

VENTANA_RAFAGA = timedelta(hours=1)
MIN_CUENTAS_SPRAY = 5


def regla_enumeracion_de_usuarios(eventos: list[Evento]) -> list[Hallazgo]:
    """Fallos contra cuentas que no existen, agrupados por origen.

    El codigo que lo sostiene es 0xC0000064 en Windows y `Invalid user` en sshd: los dos
    afirman que el nombre no existe. Que alguien pruebe nombres que el entorno no tiene
    sugiere una lista traida de afuera.
    """
    por_ip: dict[str, list[Evento]] = defaultdict(list)
    for e in eventos:
        if e.accion == "fallo-usuario-inexistente" and e.ip:
            por_ip[e.ip].append(e)

    out = []
    for ip, evs in sorted(por_ip.items()):
        cuentas = {e.sujeto.split("\\")[-1].split(":")[-1] for e in evs}
        if len(cuentas) < 3:
            continue
        out.append(Hallazgo(
            regla="enumeracion_usuarios",
            severidad="MEDIA",
            resumen=f"{len(evs)} intentos contra {len(cuentas)} cuentas inexistentes desde "
                    f"{ip} ({', '.join(sorted(cuentas)[:6])}).",
            cita=[e.id for e in evs],
            no_prueba="No prueba que haya un unico operador detras, ni que sea el mismo "
                      "que despues accedio. Prueba que alguien probo nombres que el "
                      "entorno no tiene.",
            atributos={"ip": ip, "cuentas": sorted(cuentas)},
        ))
    return out


def regla_rociado_de_contrasenias(eventos: list[Evento]) -> list[Hallazgo]:
    """Pocas contrasenias contra muchas cuentas VALIDAS, desde un mismo origen y en rafaga.

    La forma importa: muchas cuentas con pocos intentos cada una es rociado; una cuenta con
    muchos intentos es fuerza bruta y casi siempre es una aplicacion mal configurada. La
    regla exige dispersion de cuentas justamente para no ahogarse en eso.
    """
    por_ip: dict[str, list[Evento]] = defaultdict(list)
    for e in eventos:
        if e.accion == "fallo-autenticacion" and e.ip:
            por_ip[e.ip].append(e)

    out = []
    for ip, evs in sorted(por_ip.items()):
        evs.sort(key=lambda e: e.instante.utc)
        for i, ancla in enumerate(evs):
            ventana = [e for e in evs[i:]
                       if e.instante.utc - ancla.instante.utc <= VENTANA_RAFAGA]
            cuentas = {e.sujeto for e in ventana}
            if len(cuentas) < MIN_CUENTAS_SPRAY:
                continue
            intentos_por_cuenta = len(ventana) / len(cuentas)
            if intentos_por_cuenta > 4:
                continue  # concentrado en pocas cuentas: es otra cosa
            out.append(Hallazgo(
                regla="rociado_contrasenias",
                severidad="ALTA",
                resumen=f"{len(ventana)} fallos de contrasenia contra {len(cuentas)} "
                        f"cuentas validas desde {ip} en menos de una hora "
                        f"({intentos_por_cuenta:.1f} intentos por cuenta).",
                cita=[e.id for e in ventana],
                no_prueba="El patron es compatible con rociado, pero 'rociado' es una "
                          "interpretacion sobre el conjunto: ningun evento individual lo "
                          "dice. Una aplicacion mal configurada produce fallos parecidos.",
                atributos={"ip": ip, "cuentas": sorted(cuentas)},
            ))
            break
    return out


def regla_acceso_tras_fallos(eventos: list[Evento]) -> list[Hallazgo]:
    """Autenticacion exitosa desde una direccion que venia acumulando fallos.

    Es la transicion que convierte un intento en un acceso, y es el hallazgo mas fuerte que
    produce este detector.
    """
    fallos: dict[str, list[Evento]] = defaultdict(list)
    out = []
    for e in sorted(eventos, key=lambda x: x.instante.utc):
        if not e.ip:
            continue
        if e.accion in ("fallo-autenticacion", "fallo-usuario-inexistente"):
            fallos[e.ip].append(e)
        elif e.accion.startswith("autentico-"):
            previos = [f for f in fallos[e.ip]
                       if e.instante.utc - f.instante.utc <= timedelta(hours=6)]
            if len(previos) >= 3:
                out.append(Hallazgo(
                    regla="acceso_tras_fallos",
                    severidad="ALTA",
                    resumen=f"{e.sujeto} autentico con exito desde {e.ip}, direccion que "
                            f"acumulaba {len(previos)} fallos en las 6 horas previas.",
                    cita=[e.id] + [f.id for f in previos],
                    no_prueba="La correlacion es por direccion IP, que no identifica un "
                              "equipo ni una persona: NAT, proxies y direcciones "
                              "reasignadas producen la misma coincidencia.",
                    atributos={"ip": e.ip, "sujeto": e.sujeto},
                ))
    return out


def regla_credencial_creada(eventos: list[Evento]) -> list[Hallazgo]:
    """Creacion de una access key. Operacion administrativa legitima y frecuente: lo que la
    vuelve relevante es el contexto, no el evento."""
    out = []
    for e in eventos:
        if e.objeto == "iam:CreateAccessKey" and not e.atributos.get("error"):
            out.append(Hallazgo(
                regla="credencial_creada",
                severidad="MEDIA",
                resumen=f"La credencial {e.sujeto} creo una access key nueva desde "
                        f"{e.ip} (registrado en {e.atributos.get('region')}).",
                cita=[e.id],
                no_prueba="No prueba intencion de persistencia: crear keys es una "
                          "operacion administrativa habitual. Lo relevante es quien, "
                          "desde donde y cuando, no la operacion en si.",
                atributos={"ip": e.ip, "credencial": e.sujeto},
            ))
    return out


def _red(ip: str) -> str:
    """La /24 de una direccion. Es el grano al que se compara el origen."""
    return ".".join(ip.split(".")[:3]) + ".0/24"


def regla_origen_nuevo_de_credencial(eventos: list[Evento]) -> list[Hallazgo]:
    """Una credencial usada desde una **red** que nunca habia usado.

    La primera version comparaba direcciones exactas, y era inservible: cualquier
    automatizacion detras de un pool de IPs cambia de direccion todo el tiempo. La
    credencial del pipeline rota entre `10.20.9.x` y disparaba la regla en cada corrida,
    incluso en ventanas sin incidente. Volumen de alertas sin discriminacion es el modo en
    que un detector deja de leerse.

    Comparar por /24 es el grano correcto para este entorno: distingue "otra maquina de la
    misma oficina" de "otra red". No es universal -- en una nube con rangos amplios habria
    que comparar por ASN o por bloque asignado -- y por eso el criterio va declarado aca y
    no escondido en un umbral.

    Sigue sin probar robo: un cambio de red, una VPN o trabajo remoto legitimo producen lo
    mismo. Prueba que el origen cambio de red.
    """
    vistas: dict[str, set[str]] = defaultdict(set)
    out = []
    for e in sorted(eventos, key=lambda x: x.instante.utc):
        if e.fuente != "cloudtrail" or not e.ip:
            continue
        cred, red = e.sujeto, _red(e.ip)
        if not vistas[cred]:
            vistas[cred].add(red)
            continue
        if red not in vistas[cred]:
            out.append(Hallazgo(
                regla="credencial_origen_nuevo",
                severidad="ALTA",
                resumen=f"La credencial {cred} se uso desde {e.ip} ({red}), una red sin "
                        f"actividad previa registrada para esa credencial. Redes "
                        f"conocidas: {', '.join(sorted(vistas[cred]))}.",
                cita=[e.id],
                no_prueba="No prueba que la credencial haya sido robada: un cambio de red, "
                          "una VPN o trabajo remoto legitimo producen el mismo cambio de "
                          "origen. Prueba que el origen cambio de red.",
                atributos={"credencial": cred, "ip": e.ip, "red": red},
            ))
        vistas[cred].add(red)
    return out


def regla_operaciones_denegadas(eventos: list[Evento]) -> list[Hallazgo]:
    """Rafaga de operaciones rechazadas por permisos. Marcan el limite de lo que una
    credencial podia hacer, y la forma de la rafaga sugiere tanteo."""
    por_cred: dict[str, list[Evento]] = defaultdict(list)
    for e in eventos:
        if e.atributos.get("error") == "AccessDenied":
            por_cred[e.sujeto].append(e)

    out = []
    for cred, evs in sorted(por_cred.items()):
        if len(evs) < 2:
            continue
        out.append(Hallazgo(
            regla="operaciones_denegadas",
            severidad="MEDIA",
            resumen=f"{len(evs)} operaciones rechazadas por permisos con la credencial "
                    f"{cred}: {', '.join(sorted({e.objeto for e in evs}))}.",
            cita=[e.id for e in evs],
            no_prueba="Una operacion denegada demuestra el intento, no el objetivo. Y no "
                      "descarta que lo mismo se haya logrado despues por otra via.",
            atributos={"credencial": cred},
        ))
    return out


def regla_cuenta_creada(eventos: list[Evento]) -> list[Hallazgo]:
    """Creacion de una cuenta local. Persistencia clasica, y tambien tarea de soporte."""
    return [Hallazgo(
        regla="cuenta_local_creada",
        severidad="ALTA",
        resumen=f"{e.sujeto} creo la cuenta local '{e.objeto}'.",
        cita=[e.id],
        no_prueba="Crear cuentas locales es una tarea administrativa normal. Lo que la "
                  "vuelve sospechosa es el contexto de la sesion que la creo.",
        atributos={"cuenta": e.objeto},
    ) for e in eventos if e.accion == "creo-cuenta"]


BINARIOS_RECONOCIMIENTO = {"whoami.exe", "net.exe", "net1.exe", "nltest.exe",
                           "tasklist.exe", "systeminfo.exe", "reg.exe", "quser.exe"}


def regla_reconocimiento_local(eventos: list[Evento]) -> list[Hallazgo]:
    """Varios binarios de reconocimiento ejecutados por la misma sesion en poco tiempo.

    Ninguno es malicioso por si mismo -- `net.exe` lo corre cualquiera. Lo que informa es
    la concentracion: cinco de estos en una sesion y en minutos no es trabajo de oficina.
    """
    por_sesion: dict[str, list[Evento]] = defaultdict(list)
    for e in eventos:
        if e.accion == "ejecuto-proceso" and e.objeto in BINARIOS_RECONOCIMIENTO:
            por_sesion[e.atributos.get("logon_id", "?")].append(e)

    out = []
    for logon_id, evs in sorted(por_sesion.items()):
        if len({e.objeto for e in evs}) < 4:
            continue
        span = max(e.instante.utc for e in evs) - min(e.instante.utc for e in evs)
        if span > timedelta(hours=2):
            continue
        out.append(Hallazgo(
            regla="reconocimiento_local",
            severidad="ALTA",
            resumen=f"La sesion {logon_id} de {evs[0].sujeto} ejecuto "
                    f"{len({e.objeto for e in evs})} binarios de reconocimiento en "
                    f"{int(span.total_seconds() // 60)} minutos.",
            cita=[e.id for e in evs],
            no_prueba="Cada binario por separado es de uso administrativo normal. La "
                      "concentracion sugiere reconocimiento; no lo registra ningun evento.",
            atributos={"logon_id": logon_id, "sujeto": evs[0].sujeto},
        ))
    return out


REGLAS = [
    regla_enumeracion_de_usuarios,
    regla_rociado_de_contrasenias,
    regla_acceso_tras_fallos,
    regla_credencial_creada,
    regla_origen_nuevo_de_credencial,
    regla_operaciones_denegadas,
    regla_cuenta_creada,
    regla_reconocimiento_local,
]


def barrer(eventos: list[Evento]) -> list[Hallazgo]:
    orden = {"ALTA": 0, "MEDIA": 1, "BAJA": 2}
    hallazgos = [h for regla in REGLAS for h in regla(eventos)]
    return sorted(hallazgos, key=lambda h: (orden[h.severidad], h.regla))


# --------------------------------------------------------------------------------------
# Medicion contra la verdad
# --------------------------------------------------------------------------------------


@dataclass
class Medicion:
    """Precision y recall de un conjunto de hallazgos contra la etiqueta de verdad.

    Es el numero que hace falsable al laboratorio. Sin esto, un detector que encuentra 25 de
    80 eventos del ataque y los cita impecablemente parece perfecto: el verificador
    comprueba lo que se afirmo y nunca lo que se callo.
    """

    citados: int
    de_ataque: int
    total_ataque: int
    por_etiqueta: dict[str, int]

    @property
    def precision(self) -> float:
        return self.de_ataque / self.citados if self.citados else 0.0

    @property
    def recall(self) -> float:
        return self.de_ataque / self.total_ataque if self.total_ataque else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


def medir(hallazgos: list[Hallazgo], verdad: dict) -> Medicion:
    citados = {eid for h in hallazgos for eid in h.cita}
    eventos = verdad["eventos"]
    etiquetas = Counter(eventos[eid]["etiqueta"] for eid in citados if eid in eventos)
    total_ataque = sum(1 for v in eventos.values() if v["etiqueta"] == "ataque")
    return Medicion(
        citados=len(citados),
        de_ataque=etiquetas.get("ataque", 0),
        total_ataque=total_ataque,
        por_etiqueta=dict(etiquetas),
    )


def eventos_perdidos(hallazgos: list[Hallazgo], verdad: dict) -> list[str]:
    """Los eventos del ataque que ningun hallazgo cito. Es la mitad silenciosa del error."""
    citados = {eid for h in hallazgos for eid in h.cita}
    return sorted(eid for eid, v in verdad["eventos"].items()
                  if v["etiqueta"] == "ataque" and eid not in citados)
