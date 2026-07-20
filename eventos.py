"""Normalizacion de las tres fuentes a un vocabulario comun, y semantica de los artefactos.

Dos capas distintas conviven aca y conviene no confundirlas.

La **normalizacion** lleva cada registro a la misma forma -- instante, fuente, accion,
sujeto, objeto -- para poder mirarlos juntos. Es una decision de este proyecto.

La **semantica** (logon types, codigos de SubStatus, mensajes de sshd, clases de operacion
de CloudTrail) no es una decision de este proyecto: esta publicada por Microsoft, por OpenSSH
y por AWS. Es la unica parte del laboratorio donde estar equivocado es comprobable desde
afuera, y por eso es la que mas vale mantener honesta. Cuando una tabla de aca discrepa de
la documentacion, la tabla esta mal.

El sujeto lleva siempre su dominio de identidad. `WKS-04\\ecarrizo`, `web-03:ubuntu` y el
usuario IAM `ecarrizo` son tres sujetos distintos que comparten nombre. La homonimia es una
pista, no un hecho.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from tiempo import desde_cloudtrail, desde_evtx, desde_syslog

EVID = Path(__file__).resolve().parent / "evidencia"

# --------------------------------------------------------------------------------------
# Semantica publicada
# --------------------------------------------------------------------------------------

LOGON_TYPES = {
    2: ("Interactive", "Sesion en la consola fisica de la maquina."),
    3: ("Network", "Acceso a un recurso de red (SMB, sesion nula, autenticacion de "
                   "servicio). No implica sesion interactiva."),
    4: ("Batch", "Tarea programada."),
    5: ("Service", "Arranque de un servicio."),
    7: ("Unlock", "Desbloqueo de una estacion ya iniciada."),
    8: ("NetworkCleartext", "Credenciales enviadas en claro. Tipico de IIS con basic auth."),
    9: ("NewCredentials", "RunAs con credenciales alternativas para la red."),
    10: ("RemoteInteractive", "Escritorio remoto (RDP o Terminal Services)."),
    11: ("CachedInteractive", "Inicio con credenciales cacheadas, sin alcanzar al DC."),
}

ESTADOS_4625 = {
    "0xC0000064": ("usuario-inexistente",
                   "El nombre de usuario no existe. Es enumeracion: quien prueba conoce "
                   "una lista, no el entorno."),
    "0xC000006A": ("password-incorrecta",
                   "El nombre existe y la contrasenia no coincide. Confirma que la cuenta "
                   "es valida."),
    "0xC0000072": ("cuenta-deshabilitada", "La cuenta existe pero esta deshabilitada."),
    "0xC000006F": ("fuera-de-horario", "Fuera del horario permitido para esa cuenta."),
    "0xC0000133": ("desfasaje-de-reloj",
                   "Kerberos rechazo por diferencia de reloj. Acota la deriva por abajo: "
                   "el umbral por defecto son 5 minutos."),
    "0xC0000234": ("cuenta-bloqueada", "La cuenta esta bloqueada por intentos fallidos."),
}

# Operaciones de CloudTrail por clase. La distincion decide si una ausencia informa: los
# data events son de nivel objeto y no se registran salvo que se los habilite explicitamente
# por tipo de recurso. Habilitar los de S3 no habilita los de Lambda.
MANAGEMENT_S3 = {"ListBuckets", "ListBucket", "GetBucketLocation", "GetBucketPolicy",
                 "GetBucketAcl", "CreateBucket", "DeleteBucket", "PutBucketPolicy"}
DATA_S3 = {"GetObject", "PutObject", "DeleteObject", "CopyObject", "HeadObject"}

ACCIONES = (
    "autentico-remoto",
    "autentico-local",
    "autentico-red",
    "fallo-autenticacion",
    "fallo-usuario-inexistente",
    "cerro-sesion",
    "ejecuto-proceso",
    "creo-cuenta",
    "ejecuto-comando",
    "llamo-api",
)

# Que fuente puede registrar cada accion. Se usa para decidir si una ausencia informa: si
# ninguna fuente registra esa clase de hecho, no haber encontrado nada no dice nada.
ACCIONES_POR_FUENTE = {
    "windows": {"autentico-remoto", "autentico-local", "autentico-red",
                "fallo-autenticacion", "fallo-usuario-inexistente", "cerro-sesion",
                "ejecuto-proceso", "creo-cuenta"},
    "syslog": {"autentico-remoto", "fallo-autenticacion", "fallo-usuario-inexistente",
               "cerro-sesion", "ejecuto-comando"},
    "cloudtrail": {"llamo-api"},
}


def clase_operacion(servicio: str, operacion: str) -> str:
    """`management`, `data` o `desconocida`.

    El tercer valor no es un descuido: si no se sabe de que clase es la operacion, no se
    puede afirmar que el trail la habria registrado, y la ausencia no informa. Tratar lo
    desconocido como management seria afirmar cobertura que no se tiene.
    """
    if servicio == "s3":
        if operacion in MANAGEMENT_S3:
            return "management"
        if operacion in DATA_S3:
            return "data"
        return "desconocida"
    # Servicios cuyos data events este escenario no modela. De una operacion de Lambda o
    # DynamoDB no se sabe si el interruptor estaba puesto.
    if servicio in {"lambda", "dynamodb", "kms", "secretsmanager"}:
        return "desconocida"
    return "management"


# --------------------------------------------------------------------------------------
# Tiempo
# --------------------------------------------------------------------------------------

RECOLECCION = datetime(2026, 3, 12, 14, 0, 0, tzinfo=timezone.utc)

# web-03 escribe en hora local (-03) y sin anio; la zona se conoce de la adquisicion.
ZONA_SYSLOG_H = -3


# --------------------------------------------------------------------------------------
# Evento normalizado
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Evento:
    id: str
    instante: datetime
    fuente: str
    accion: str
    sujeto: str
    objeto: str
    atributos: dict = field(default_factory=dict)
    crudo: object = None

    @property
    def ip(self) -> str | None:
        return self.atributos.get("ip")

    def __str__(self) -> str:
        return (f"{self.id}  {self.instante:%Y-%m-%dT%H:%M:%SZ}  {self.fuente:<11} "
                f"{self.sujeto:<28} {self.accion:<26} {self.objeto}")


# --------------------------------------------------------------------------------------
# Normalizadores
# --------------------------------------------------------------------------------------


def _windows(r: dict) -> Evento | None:
    inst = desde_evtx(r["SystemTime"])
    host = r["Computer"]
    eid = r["EventID"]

    if eid == 4624:
        tipo = r["LogonType"]
        accion = {10: "autentico-remoto", 2: "autentico-local"}.get(tipo, "autentico-red")
        return Evento(r["_id"], inst, "windows", accion,
                      f"{host}\\{r['TargetUserName']}", host,
                      {"ip": r.get("IpAddress"), "logon_type": tipo,
                       "logon_id": r["LogonId"]}, r)

    if eid == 4625:
        sub = r.get("SubStatus", "")
        accion = ("fallo-usuario-inexistente" if sub == "0xC0000064"
                  else "fallo-autenticacion")
        return Evento(r["_id"], inst, "windows", accion,
                      f"{host}\\{r['TargetUserName']}", host,
                      {"ip": r.get("IpAddress"), "logon_type": r.get("LogonType"),
                       "substatus": sub}, r)

    if eid == 4634:
        return Evento(r["_id"], inst, "windows", "cerro-sesion",
                      f"{host}\\{r['TargetUserName']}", host,
                      {"logon_id": r["LogonId"]}, r)

    if eid == 4688:
        return Evento(r["_id"], inst, "windows", "ejecuto-proceso",
                      f"{host}\\{r['SubjectUserName']}",
                      r["NewProcessName"].rsplit("\\", 1)[-1],
                      {"logon_id": r["SubjectLogonId"], "ruta": r["NewProcessName"],
                       "padre": r.get("ParentProcessName")}, r)

    if eid == 4720:
        return Evento(r["_id"], inst, "windows", "creo-cuenta",
                      f"{host}\\{r['SubjectUserName']}", r["TargetUserName"],
                      {"logon_id": r["SubjectLogonId"]}, r)

    return None


_RE_SSH = re.compile(
    r"^(?P<sello>\w{3} [ \d]\d \d{2}:\d{2}:\d{2}) (?P<host>\S+) "
    r"(?P<prog>\w+)\[(?P<pid>\d+)\]: (?P<msg>.*)$")


def _syslog(r: dict) -> Evento | None:
    m = _RE_SSH.match(r["linea"])
    if not m:
        return None
    inst = desde_syslog(m["sello"], ZONA_SYSLOG_H, RECOLECCION)
    host, msg = m["host"], m["msg"]

    if m["prog"] == "sudo":
        usuario = msg.split(" :")[0]
        comando = msg.split("COMMAND=")[-1]
        return Evento(r["_id"], inst, "syslog", "ejecuto-comando",
                      f"{host}:{usuario}", comando.split()[0].rsplit("/", 1)[-1],
                      {"comando": comando}, r)

    mm = re.match(r"Invalid user (\S+) from (\S+)", msg)
    if mm:
        return Evento(r["_id"], inst, "syslog", "fallo-usuario-inexistente",
                      f"{host}:{mm.group(1)}", host, {"ip": mm.group(2)}, r)

    mm = re.match(r"Failed none for invalid user (\S+) from (\S+)", msg)
    if mm:
        return Evento(r["_id"], inst, "syslog", "fallo-usuario-inexistente",
                      f"{host}:{mm.group(1)}", host, {"ip": mm.group(2)}, r)

    mm = re.match(r"Failed (\S+) for (\S+) from (\S+)", msg)
    if mm:
        return Evento(r["_id"], inst, "syslog", "fallo-autenticacion",
                      f"{host}:{mm.group(2)}", host,
                      {"ip": mm.group(3), "metodo": mm.group(1)}, r)

    mm = re.match(r"Accepted (\S+) for (\S+) from (\S+)", msg)
    if mm:
        clave = None
        if "SHA256:" in msg:
            clave = msg.split("SHA256:")[-1].strip()
        return Evento(r["_id"], inst, "syslog", "autentico-remoto",
                      f"{host}:{mm.group(2)}", host,
                      {"ip": mm.group(3), "metodo": mm.group(1), "clave": clave}, r)

    mm = re.match(r"Disconnected from user (\S+) (\S+)", msg)
    if mm:
        return Evento(r["_id"], inst, "syslog", "cerro-sesion",
                      f"{host}:{mm.group(1)}", host, {"ip": mm.group(2)}, r)

    return None


def _cloudtrail(r: dict) -> Evento:
    inst = desde_cloudtrail(r["eventTime"])
    servicio = r["eventSource"].split(".")[0]
    return Evento(r["_id"], inst, "cloudtrail", "llamo-api",
                  r["userIdentity"]["accessKeyId"],
                  f"{servicio}:{r['eventName']}",
                  {"ip": r["sourceIPAddress"], "region": r["awsRegion"],
                   "usuario": r["userIdentity"].get("userName"),
                   "error": r.get("errorCode"),
                   "clase": clase_operacion(servicio, r["eventName"])}, r)


def cargar(evid: Path = EVID) -> list[Evento]:
    """Las tres fuentes en un solo timeline, ordenado por mejor estimacion."""
    eventos: list[Evento] = []
    for r in json.loads((evid / "windows.json").read_text(encoding="utf-8")):
        if (e := _windows(r)) is not None:
            eventos.append(e)
    for r in json.loads((evid / "syslog.json").read_text(encoding="utf-8")):
        if (e := _syslog(r)) is not None:
            eventos.append(e)
    for r in json.loads((evid / "cloudtrail.json").read_text(encoding="utf-8")):
        eventos.append(_cloudtrail(r))
    return sorted(eventos, key=lambda e: (e.instante, e.fuente, e.id))


def cargar_verdad(evid: Path = EVID) -> dict:
    """La verdad del escenario, reconstruida desde el seed. No hay archivo que leer.

    Deliberado: si las etiquetas viviesen al lado de la evidencia, cualquiera que investigue
    -- persona o agente -- las tiene a un `Read` de distancia, y un recall obtenido leyendo
    el solucionario no mide nada. Se regenera en memoria cuando hace falta medir, y
    desaparece.
    """
    import importlib.util

    # El generador vive en un solo lugar; `evid` solo indica contra que escenario medir.
    spec = importlib.util.spec_from_file_location(
        "generar_evidencia", EVID / "generar_evidencia.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.verdad(evid)
