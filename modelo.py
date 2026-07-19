"""Modelo de comportamiento del entorno.

No se generan lineas de log: se generan entidades con estado y transiciones, y las lineas
son la proyeccion de esas transiciones. La diferencia no es estilistica. Si se escriben
lineas directamente, la consistencia hay que verificarla despues y la superficie de
contradiccion crece con el cuadrado del dataset; si las lineas las emite el estado, la
contradiccion se vuelve estructuralmente imposible.

Ejemplos de lo que este modulo hace inexpresable:

  - Un `Failed password` para una cuenta que sshd ya declaro inexistente: el emisor le
    pregunta a la Cuenta si existe, y si no existe emite `Invalid user`. No hay camino que
    produzca las dos.
  - Un 4634 huerfano: el LogonId lo genera la Sesion al abrirse, y solo esa Sesion puede
    cerrarse.
  - Una llamada de CloudTrail con una credencial revocada: la Credencial conoce su ventana
    de validez y rechaza emitir fuera de ella.
  - Un evento de un host aislado: el Host deja de emitir desde el instante del corte.

Todo actor -- usuario, job, bot de internet, admin, atacante -- usa las MISMAS primitivas
de aleatoriedad, los mismos pools de IP y el mismo jitter. Un atacante que sacara sus IPs
de un rango propio o que actuara a intervalos exactos quedaria separable por artefacto del
generador y no por criterio forense: se lo encontraria contando, no investigando. Lo unico
que distingue al atacante es la secuencia de acciones.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

# Etiquetas de verdad. Cada evento emitido lleva exactamente una: es lo que despues permite
# medir a un detector contra la realidad en vez de contra la impresion del autor.
NORMAL = "normal"
RUIDO = "ruido-internet"
ADMIN = "admin-legitimo"
SOSPECHOSO = "sospechoso-no-incidente"
ATAQUE = "ataque"

ETIQUETAS = (NORMAL, RUIDO, ADMIN, SOSPECHOSO, ATAQUE)

# Codigos de NTSTATUS que aparecen en el campo SubStatus de un 4625. La distincion entre
# los dos primeros es lo que separa enumeracion de usuarios de intento de contrasenia.
STATUS_USUARIO_INEXISTENTE = "0xC0000064"
STATUS_PASSWORD_INCORRECTA = "0xC000006A"
STATUS_CUENTA_DESHABILITADA = "0xC0000072"
STATUS_FUERA_DE_HORARIO = "0xC000006F"


# --------------------------------------------------------------------------------------
# Entidades
# --------------------------------------------------------------------------------------


@dataclass
class Cuenta:
    """Una identidad. `dominio` es el espacio de nombres donde es interpretable.

    La homonimia entre dominios es deliberada y no es identidad: `WKS-04\\ecarrizo` y el
    usuario IAM `ecarrizo` son sujetos distintos que se llaman igual.
    """

    nombre: str
    dominio: str  # "WKS-04", "web-03", "aws"
    existe: bool = True
    habilitada: bool = True
    creada_en: datetime | None = None
    password_valida: str | None = None  # cual contrasenia acepta, para modelar rotaciones

    @property
    def calificado(self) -> str:
        return f"{self.dominio}\\{self.nombre}" if self.dominio != "aws" else self.nombre


@dataclass
class Credencial:
    """Una access key de AWS, con su ventana de validez explicita."""

    id: str
    propietario: str
    creada_en: datetime
    revocada_en: datetime | None = None

    def vigente(self, t: datetime) -> bool:
        if t < self.creada_en:
            return False
        return self.revocada_en is None or t < self.revocada_en


@dataclass
class Sesion:
    """Un logon abierto. El LogonId lo genera la sesion y nadie mas puede cerrarla."""

    logon_id: str
    cuenta: Cuenta
    host: str
    tipo: int
    ip: str
    abierta_en: datetime
    cerrada_en: datetime | None = None

    @property
    def abierta(self) -> bool:
        return self.cerrada_en is None


@dataclass
class Host:
    """Una maquina que emite eventos. Deja de emitir cuando se la aisla.

    El aislamiento es la razon por la que este campo existe: la evidencia de que una
    contencion funciono es que los eventos dejan de aparecer, no una tabla que lo declare.
    """

    nombre: str
    aislado_desde: datetime | None = None

    def emite(self, t: datetime) -> bool:
        return self.aislado_desde is None or t < self.aislado_desde


@dataclass
class Emision:
    """Un evento ya proyectado, antes de recibir su identificador definitivo."""

    t: datetime  # instante real (UTC verdadero, sin la deriva del host)
    fuente: str
    etiqueta: str
    crudo: dict | str
    actor: str  # quien lo produjo, para la narrativa de la verdad


# --------------------------------------------------------------------------------------
# Entorno
# --------------------------------------------------------------------------------------


class Entorno:
    """Estado del mundo y unico emisor de eventos.

    Todas las emisiones pasan por aca, y por eso todas quedan etiquetadas y todas respetan
    las invariantes de estado sin que ningun actor tenga que acordarse.
    """

    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)
        self.emisiones: list[Emision] = []
        self.etiqueta_actual = NORMAL
        self.actor_actual = "?"

        self.cuentas: dict[str, Cuenta] = {}
        self.credenciales: dict[str, Credencial] = {}
        self.hosts: dict[str, Host] = {}
        self.sesiones: list[Sesion] = []
        self._siguiente_logon = 0x1A2B00

        # Pool unico de direcciones de internet. Bots, atacante y accesos remotos legitimos
        # salen todos de aca: la IP no es una senial de generador.
        self.pool_internet: list[str] = []
        self.pool_interno: list[str] = []

    # -- contexto ------------------------------------------------------------------

    def como(self, etiqueta: str, actor: str):
        """Marca el actor y la etiqueta de todo lo que se emita adentro del bloque."""
        return _Contexto(self, etiqueta, actor)

    # -- registro de entidades -----------------------------------------------------

    def cuenta(self, nombre: str, dominio: str, **kw) -> Cuenta:
        c = Cuenta(nombre=nombre, dominio=dominio, **kw)
        self.cuentas[f"{dominio}\\{nombre}"] = c
        return c

    def buscar_cuenta(self, nombre: str, dominio: str) -> Cuenta | None:
        return self.cuentas.get(f"{dominio}\\{nombre}")

    def host(self, nombre: str) -> Host:
        h = Host(nombre=nombre)
        self.hosts[nombre] = h
        return h

    def credencial(self, id: str, propietario: str, creada_en: datetime) -> Credencial:
        c = Credencial(id=id, propietario=propietario, creada_en=creada_en)
        self.credenciales[id] = c
        return c

    # -- emision cruda -------------------------------------------------------------

    def _emitir(self, t: datetime, fuente: str, crudo, host: str | None = None) -> bool:
        """Puerta unica de salida. Un host aislado no emite: ese es todo el mecanismo."""
        if host is not None and not self.hosts[host].emite(t):
            return False
        self.emisiones.append(
            Emision(t=t, fuente=fuente, etiqueta=self.etiqueta_actual,
                    crudo=crudo, actor=self.actor_actual)
        )
        return True

    # -- Windows -------------------------------------------------------------------

    def logon_windows(self, t: datetime, nombre: str, ip: str, tipo: int,
                      password: str = "correcta", host: str = "WKS-04") -> Sesion | None:
        """Intento de autenticacion contra un host Windows.

        El resultado lo decide el estado de la cuenta, no el llamador. Por eso no existe
        forma de emitir un 4625 con SubStatus de contrasenia incorrecta contra una cuenta
        que el entorno no tiene: sale 0xC0000064 y no hay alternativa.
        """
        cuenta = self.buscar_cuenta(nombre, host)

        if cuenta is None or not cuenta.existe:
            self._fallo_windows(t, nombre, ip, tipo, STATUS_USUARIO_INEXISTENTE, host)
            return None
        if not cuenta.habilitada:
            self._fallo_windows(t, nombre, ip, tipo, STATUS_CUENTA_DESHABILITADA, host)
            return None
        if password != (cuenta.password_valida or "correcta"):
            self._fallo_windows(t, nombre, ip, tipo, STATUS_PASSWORD_INCORRECTA, host)
            return None

        self._siguiente_logon += self.rng.randint(3, 40)
        sesion = Sesion(logon_id=f"0x{self._siguiente_logon:X}", cuenta=cuenta, host=host,
                        tipo=tipo, ip=ip, abierta_en=t)
        ok = self._emitir(t, "windows", {
            "EventID": 4624,
            "SystemTime": _iso(t),
            "Computer": host,
            "TargetUserName": nombre,
            "TargetDomainName": host,
            "LogonType": tipo,
            "IpAddress": ip,
            "LogonId": sesion.logon_id,
            "AuthenticationPackageName": "NTLM" if tipo == 3 else "Negotiate",
        }, host=host)
        if not ok:
            return None
        self.sesiones.append(sesion)
        return sesion

    def _fallo_windows(self, t, nombre, ip, tipo, substatus, host) -> None:
        self._emitir(t, "windows", {
            "EventID": 4625,
            "SystemTime": _iso(t),
            "Computer": host,
            "TargetUserName": nombre,
            "TargetDomainName": host,
            "LogonType": tipo,
            "IpAddress": ip,
            "Status": "0xC000006D",
            "SubStatus": substatus,
        }, host=host)

    def logoff(self, sesion: Sesion, t: datetime) -> None:
        """Cierre de sesion. Solo una sesion abierta puede cerrarse, y con su propio id."""
        if not sesion.abierta or t < sesion.abierta_en:
            return
        if self._emitir(t, "windows", {
            "EventID": 4634,
            "SystemTime": _iso(t),
            "Computer": sesion.host,
            "TargetUserName": sesion.cuenta.nombre,
            "LogonType": sesion.tipo,
            "LogonId": sesion.logon_id,
        }, host=sesion.host):
            sesion.cerrada_en = t

    def proceso(self, t: datetime, sesion: Sesion, imagen: str,
                padre: str = "C:\\Windows\\explorer.exe") -> None:
        """4688. El LogonId sale de la sesion: un proceso no puede existir sin su logon.

        Sin CommandLine a proposito: la auditoria de linea de comandos no esta habilitada
        en este entorno, que es la configuracion por defecto de Windows. Se sabe QUE se
        ejecuto, no CON QUE argumentos.
        """
        if not sesion.abierta:
            return
        self._emitir(t, "windows", {
            "EventID": 4688,
            "SystemTime": _iso(t),
            "Computer": sesion.host,
            "SubjectUserName": sesion.cuenta.nombre,
            "SubjectLogonId": sesion.logon_id,
            "NewProcessName": imagen,
            "ParentProcessName": padre,
        }, host=sesion.host)

    def cuenta_creada(self, t: datetime, sesion: Sesion, nueva: str) -> Cuenta:
        """4720. La cuenta pasa a existir en el instante del evento y no antes."""
        self._emitir(t, "windows", {
            "EventID": 4720,
            "SystemTime": _iso(t),
            "Computer": sesion.host,
            "SubjectUserName": sesion.cuenta.nombre,
            "SubjectLogonId": sesion.logon_id,
            "TargetUserName": nueva,
        }, host=sesion.host)
        return self.cuenta(nueva, sesion.host, creada_en=t)

    # -- Linux / sshd --------------------------------------------------------------

    def ssh_intento(self, t: datetime, usuario: str, ip: str, exito: bool,
                    metodo: str = "password", clave: str | None = None,
                    host: str = "web-03") -> Sesion | None:
        """Intento de sshd. El mensaje lo decide el estado de la cuenta.

        sshd distingue en el texto entre un usuario que no existe (`Invalid user`) y una
        contrasenia incorrecta para uno que si (`Failed password`). Es el equivalente exacto
        de la distincion 0xC0000064 / 0xC000006A de Windows, y es la razon por la que un
        log de sshd permite separar enumeracion de intento de acceso.
        """
        cuenta = self.buscar_cuenta(usuario, host)
        pid = self.rng.randint(1000, 32000)

        if cuenta is None or not cuenta.existe:
            self._syslog(t, host, pid, f"Invalid user {usuario} from {ip} port "
                                       f"{self.rng.randint(30000, 65000)}")
            self._syslog(t, host, pid, f"Failed none for invalid user {usuario} from {ip} "
                                       f"port {self.rng.randint(30000, 65000)} ssh2")
            return None

        if not exito:
            self._syslog(t, host, pid, f"Failed {metodo} for {usuario} from {ip} port "
                                       f"{self.rng.randint(30000, 65000)} ssh2")
            return None

        self._siguiente_logon += self.rng.randint(3, 40)
        sesion = Sesion(logon_id=f"sshd-{pid}", cuenta=cuenta, host=host, tipo=0, ip=ip,
                        abierta_en=t)
        detalle = f": RSA SHA256:{clave}" if clave else ""
        if self._syslog(t, host, pid, f"Accepted {metodo} for {usuario} from {ip} port "
                                      f"{self.rng.randint(30000, 65000)} ssh2{detalle}"):
            self.sesiones.append(sesion)
            return sesion
        return None

    def ssh_cierre(self, sesion: Sesion, t: datetime) -> None:
        if not sesion.abierta or t < sesion.abierta_en:
            return
        pid = int(sesion.logon_id.split("-")[1])
        if self._syslog(t, sesion.host, pid,
                        f"Disconnected from user {sesion.cuenta.nombre} {sesion.ip}"):
            sesion.cerrada_en = t

    def sudo(self, t: datetime, sesion: Sesion, comando: str) -> None:
        if not sesion.abierta:
            return
        self._syslog(t, sesion.host, self.rng.randint(1000, 32000),
                     f"{sesion.cuenta.nombre} : TTY=pts/0 ; PWD=/home/"
                     f"{sesion.cuenta.nombre} ; USER=root ; COMMAND={comando}",
                     programa="sudo")

    def _syslog(self, t: datetime, host: str, pid: int, mensaje: str,
                programa: str = "sshd") -> bool:
        """RFC 3164: sin anio y sin offset de zona. El host escribe en hora local.

        Que la linea cruda quede fechada en hora local es el punto: un evento de las 02:31
        UTC aparece como `Mar 10 23:31` si el host esta en -03, o sea con fecha del dia
        ANTERIOR. La normalizacion lo resuelve; el crudo no, y por eso hay que mirarlo.
        """
        local = t + timedelta(hours=ZONA_WEB03_H)
        sello = f"{MESES_TXT[local.month]} {local.day:2d} {local:%H:%M:%S}"
        return self._emitir(t, "syslog", f"{sello} {host} {programa}[{pid}]: {mensaje}",
                            host=host)

    # -- AWS / CloudTrail ----------------------------------------------------------

    def llamada_aws(self, t: datetime, credencial_id: str, servicio: str, operacion: str,
                    ip: str, region: str = "sa-east-1", error: str | None = None,
                    recurso: str | None = None) -> bool:
        """Llamada a la API de AWS. La credencial conoce su ventana de validez.

        Una key revocada no emite: eso es lo que hace observable que la revocacion
        funciono. Y una key que todavia no existe tampoco, lo que impide el evento
        imposible de una credencial usada antes de haberse creado.
        """
        cred = self.credenciales.get(credencial_id)
        if cred is None or not cred.vigente(t):
            return False

        registro = {
            "eventTime": _iso(t),
            "eventSource": f"{servicio}.amazonaws.com",
            "eventName": operacion,
            "awsRegion": region,
            "sourceIPAddress": ip,
            "userIdentity": {
                "type": "IAMUser",
                "accessKeyId": credencial_id,
                "userName": cred.propietario,
            },
            "eventID": f"{self.rng.randrange(16**8):08x}-"
                       f"{self.rng.randrange(16**4):04x}-"
                       f"{self.rng.randrange(16**4):04x}",
            "readOnly": operacion.startswith(("List", "Get", "Describe", "Head")),
        }
        if recurso:
            registro["requestParameters"] = {"resource": recurso}
        if error:
            registro["errorCode"] = error
        return self._emitir(t, "cloudtrail", registro)

    def crear_access_key(self, t: datetime, por: str, para: str, ip: str,
                         nueva_id: str) -> Credencial | None:
        """iam:CreateAccessKey. IAM es global: se registra en us-east-1 sin importar desde
        donde se invoco. Un analista que filtre por la region del negocio no lo ve."""
        if not self.llamada_aws(t, por, "iam", "CreateAccessKey", ip,
                                region="us-east-1", recurso=para):
            return None
        return self.credencial(nueva_id, para, t)

    def revocar(self, credencial_id: str, t: datetime) -> None:
        cred = self.credenciales.get(credencial_id)
        if cred and cred.revocada_en is None:
            cred.revocada_en = t

    def aislar(self, host: str, t: datetime) -> None:
        self.hosts[host].aislado_desde = t

    # -- utilidades compartidas por todos los actores ------------------------------

    def jitter(self, base: datetime, seg: int) -> datetime:
        """Dispersion alrededor de un instante. La usan todos por igual."""
        return base + timedelta(seconds=self.rng.randint(-seg, seg))

    def espera(self) -> int:
        """Intervalo entre acciones de un mismo actor, en segundos.

        Cola pesada: la mayoria de las acciones se agrupan y algunas se separan mucho. Es
        como se comporta la actividad real, y la usan TODOS los actores -- si el atacante
        tuviera intervalos uniformes se lo encontraria con un histograma.
        """
        return int(self.rng.paretovariate(1.6) * 20)

    def ip_internet(self) -> str:
        return self.rng.choice(self.pool_internet)

    def ip_interna(self) -> str:
        return self.rng.choice(self.pool_interno)


class _Contexto:
    def __init__(self, env: Entorno, etiqueta: str, actor: str) -> None:
        self.env, self.etiqueta, self.actor = env, etiqueta, actor

    def __enter__(self):
        self._prev = (self.env.etiqueta_actual, self.env.actor_actual)
        self.env.etiqueta_actual, self.env.actor_actual = self.etiqueta, self.actor
        return self.env

    def __exit__(self, *_):
        self.env.etiqueta_actual, self.env.actor_actual = self._prev
        return False


# --------------------------------------------------------------------------------------

ZONA_WEB03_H = -3  # web-03 escribe syslog en hora local de Buenos Aires

MESES_TXT = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


def _iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
