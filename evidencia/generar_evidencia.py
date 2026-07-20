"""Generador del escenario INC-2026-0051.

Corre el modelo de comportamiento durante diez dias y proyecta las tres fuentes. Seed fijo:
la misma corrida produce siempre la misma evidencia.

Los primeros siete dias son operacion normal y sirven de linea base. El ataque cae sobre el
final, y esa asimetria es deliberada: una access key creada un martes no dice nada sola,
dice bastante si en siete dias nadie creo ninguna.

Cuatro capas conviven en la evidencia, y la tercera y la cuarta son las que hacen al
ejercicio:

  normal                    Usuarios con horarios consistentes y jobs automatizados.
  ruido-internet            Escaneo constante contra el host expuesto. Es lo que ve
                            cualquier servidor con SSH abierto, y produce cientos de fallos
                            de autenticacion que NO son un ataque dirigido.
  admin-legitimo            Un administrador haciendo cosas que se parecen al ataque: crear
                            una access key, copiar mucho de golpe, entrar de madrugada
                            desde una IP nueva. Indistinguible del ataque en el evento
                            aislado, distinguible en el contexto.
  sospechoso-no-incidente   Una aplicacion con la contrasenia vencida que reintenta cientos
                            de veces contra una cuenta que existe. Genera exactamente la
                            firma de una fuerza bruta y no lo es. Sirve para que encontrar
                            algo raro no equivalga a haber encontrado el incidente.

La etiqueta de cada evento se emite sola: la pone el contexto del actor, no una anotacion
posterior. Es lo que permite verificar con un comando real (`python main.py verdad --si`)
que la historia de las cinco capas es cierta, en vez de tomarla de la palabra del autor.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modelo import (  # noqa: E402
    ADMIN, ATAQUE, NORMAL, RUIDO, SOSPECHOSO, Entorno,
)

AQUI = Path(__file__).resolve().parent

SEED = 20260312
INICIO = datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)
DIAS = 10
FIN = INICIO + timedelta(days=DIAS)
RECOLECCION = datetime(2026, 3, 12, 14, 0, 0, tzinfo=timezone.utc)

# Instante en que el analista toma el caso. Todo lo anterior es historico congelado; la
# corriente viva arranca aca.
#
# Cae dos dias despues del ultimo evento del ataque, y esa distancia es el punto: el
# incidente ocurrio el dia 8 y nadie lo vio hasta que salto una alerta el dia 10. Los dos
# dias intermedios son operacion normal y estan llenos de actividad legitima, de modo que
# la ventana del incidente no se identifica por ser lo ultimo que pasó.
ENTRADA = datetime(2026, 3, 12, 6, 0, 0, tzinfo=timezone.utc)

USUARIOS_OFICINA = ["ecarrizo", "mlopez", "jperez", "rgomez", "avarela", "dsosa"]
CUENTAS_INEXISTENTES = ["admin", "administrador", "backup", "deploy", "test", "oracle",
                        "postgres", "jenkins", "git", "ftp"]

BINARIOS_NORMALES = [
    "C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE",
    "C:\\Program Files\\Microsoft Office\\root\\Office16\\OUTLOOK.EXE",
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Windows\\System32\\notepad.exe",
    "C:\\Program Files\\7-Zip\\7zFM.exe",
    "C:\\Windows\\System32\\mstsc.exe",
]

OPERACIONES_JOB = [
    ("s3", "ListBucket"), ("s3", "HeadObject"), ("logs", "PutLogEvents"),
    ("logs", "DescribeLogStreams"), ("cloudwatch", "PutMetricData"),
    ("ec2", "DescribeInstances"), ("ec2", "DescribeVolumes"),
    ("sts", "AssumeRole"), ("dynamodb", "DescribeTable"), ("ssm", "GetParameters"),
    ("autoscaling", "DescribeAutoScalingGroups"), ("elasticloadbalancing",
                                                   "DescribeTargetHealth"),
]


# --------------------------------------------------------------------------------------
# Poblacion del entorno
# --------------------------------------------------------------------------------------


def poblar(env: Entorno) -> None:
    env.host("WKS-04")
    env.host("web-03")

    for nombre in USUARIOS_OFICINA:
        env.cuenta(nombre, "WKS-04")
    env.cuenta("administrador", "WKS-04", existe=False)
    env.cuenta("svc_backup", "WKS-04", password_valida="rotada-en-febrero")
    env.cuenta("temporal", "WKS-04", existe=True, habilitada=False)

    env.cuenta("ubuntu", "web-03")
    env.cuenta("deploy", "web-03")

    env.cuenta("ecarrizo", "aws")
    env.cuenta("svc-pipeline", "aws")
    env.cuenta("mrivas", "aws")

    env.credencial("AKIA7QYCVN4RBUXWK3PD", "svc-pipeline", INICIO - timedelta(days=200))
    env.credencial("AKIA3TBWMZ8FLQDNRV6H", "ecarrizo", INICIO - timedelta(days=90))
    env.credencial("AKIA9KLMXР2HTVCJWD5N".replace("Р", "P"), "mrivas",
                   INICIO - timedelta(days=45))
    # Embebida en un archivo de configuracion de web-03 para el pipeline de despliegue.
    # Ningun actor normal la usa: solo aparece en el plan de practica "salto-triple".
    env.credencial("AKIA4RXWNPFOZ8GHK6EY", "svc-web03-deploy", INICIO - timedelta(days=120))

    # Un unico pool de internet para bots, atacante y accesos remotos legitimos. Que la IP
    # del atacante sea indistinguible del ruido es el punto: se lo encuentra por lo que
    # hace, no por de donde viene.
    env.pool_internet = [
        f"{a}.{b}.{c}.{d}"
        for a, b, c, d in [
            (203, 0, 113, 44), (198, 51, 100, 77), (203, 0, 113, 91), (192, 0, 2, 15),
            (198, 51, 100, 12), (203, 0, 113, 7), (192, 0, 2, 200), (198, 51, 100, 143),
            (203, 0, 113, 165), (192, 0, 2, 88), (198, 51, 100, 33), (203, 0, 113, 210),
            (200, 45, 10, 18), (190, 210, 8, 92), (181, 47, 22, 6), (177, 54, 130, 71),
        ]
    ]
    env.pool_interno = [f"10.20.4.{n}" for n in range(10, 60)]


# --------------------------------------------------------------------------------------
# Actores
# --------------------------------------------------------------------------------------


def usuarios_oficina(env: Entorno) -> None:
    """Jornada laboral: entra, trabaja, sale. Fines de semana casi sin actividad."""
    for dia in range(DIAS):
        base = INICIO + timedelta(days=dia)
        finde = base.weekday() >= 5

        for usuario in USUARIOS_OFICINA:
            if finde and env.rng.random() > 0.15:
                continue
            if env.rng.random() > 0.93:
                continue  # ausencias

            with env.como(NORMAL, f"usuario:{usuario}") as e:
                entrada = env.jitter(base + timedelta(hours=9, minutes=e.rng.randint(0, 90)),
                                     900)
                sesion = e.logon_windows(entrada, usuario, e.ip_interna(), tipo=2)
                if sesion is None:
                    continue

                t = entrada
                for _ in range(e.rng.randint(16, 34)):
                    t += timedelta(seconds=e.espera() * 8)
                    if t > base + timedelta(hours=19):
                        break
                    e.proceso(t, sesion, e.rng.choice(BINARIOS_NORMALES))

                salida = env.jitter(base + timedelta(hours=18, minutes=e.rng.randint(0, 90)),
                                    900)
                e.logoff(sesion, max(salida, t + timedelta(minutes=1)))


def jobs_aws(env: Entorno) -> None:
    """Automatizacion de la cuenta: el grueso del volumen de CloudTrail.

    Una cuenta real emite muchisimo trafico repetitivo y aburrido. Es lo que hace que un
    puniado de llamadas del atacante no salte a la vista.
    """
    with env.como(NORMAL, "job:pipeline") as e:
        t = INICIO
        while t < FIN:
            t += timedelta(seconds=e.espera() * 5 + 30)
            if t >= FIN:
                break
            servicio, operacion = e.rng.choice(OPERACIONES_JOB)
            e.llamada_aws(t, "AKIA7QYCVN4RBUXWK3PD", servicio, operacion,
                          ip=f"10.20.9.{e.rng.randint(10, 40)}")


def usuarios_aws(env: Entorno) -> None:
    """Personas trabajando contra la consola en horario de oficina."""
    with env.como(NORMAL, "usuario:ecarrizo-aws") as e:
        for dia in range(DIAS):
            base = INICIO + timedelta(days=dia)
            if base.weekday() >= 5:
                continue
            t = base + timedelta(hours=e.rng.randint(10, 17))
            for _ in range(e.rng.randint(4, 14)):
                t += timedelta(seconds=e.espera() * 8)
                servicio, operacion = e.rng.choice([
                    ("s3", "ListBuckets"), ("s3", "GetBucketLocation"),
                    ("ec2", "DescribeInstances"), ("iam", "ListUsers"),
                    ("cloudwatch", "GetMetricData"), ("rds", "DescribeDBInstances"),
                ])
                e.llamada_aws(t, "AKIA3TBWMZ8FLQDNRV6H", servicio, operacion,
                              ip=e.ip_interna(),
                              region="us-east-1" if servicio == "iam" else "sa-east-1")


def bots_internet(env: Entorno) -> None:
    """Escaneo de fondo contra el host expuesto.

    Cientos de fallos de autenticacion que no son un ataque dirigido. Un detector que
    alerte por 'muchos fallos de SSH' se ahoga aca, y ese es el punto.
    """
    with env.como(RUIDO, "bot:internet") as e:
        t = INICIO
        while t < FIN:
            t += timedelta(seconds=e.espera() * 62)
            if t >= FIN:
                break
            ip = e.ip_internet()
            for _ in range(e.rng.randint(1, 4)):
                t += timedelta(seconds=e.rng.randint(1, 25))
                e.ssh_intento(t, e.rng.choice(CUENTAS_INEXISTENTES), ip, exito=False)


def accesos_ssh_legitimos(env: Entorno) -> None:
    """Operacion sobre web-03: despliegues y mantenimiento."""
    with env.como(NORMAL, "usuario:deploy") as e:
        for dia in range(DIAS):
            base = INICIO + timedelta(days=dia)
            if base.weekday() >= 5 or e.rng.random() > 0.8:
                continue
            t = base + timedelta(hours=e.rng.randint(11, 18))
            sesion = e.ssh_intento(t, "deploy", e.ip_interna(), exito=True,
                                   metodo="publickey", clave="8vN2qLpXeR4kTsYbMwGh")
            if sesion is None:
                continue
            for _ in range(e.rng.randint(1, 4)):
                t += timedelta(seconds=e.espera() * 6)
                e.sudo(t, sesion, e.rng.choice([
                    "/usr/bin/systemctl restart api",
                    "/usr/bin/docker compose up -d",
                    "/usr/bin/tail -n 200 /var/log/api/app.log",
                ]))
            e.ssh_cierre(sesion, t + timedelta(minutes=e.rng.randint(2, 40)))


def app_con_password_vencida(env: Entorno) -> None:
    """Una aplicacion que quedo con la contrasenia vieja de svc_backup y reintenta sola.

    Produce cientos de 4625 con SubStatus 0xC000006A -- cuenta que existe, contrasenia
    incorrecta -- desde una IP interna fija. Es exactamente la firma de una fuerza bruta y
    es un error de configuracion. Que exista obliga a distinguir entre lo raro y lo
    peligroso, que es el trabajo.
    """
    with env.como(SOSPECHOSO, "app:facturacion") as e:
        ip = "10.20.4.201"
        t = INICIO + timedelta(hours=6)
        while t < FIN:
            t += timedelta(minutes=e.rng.randint(11, 32))
            if t >= FIN:
                break
            e.logon_windows(t, "svc_backup", ip, tipo=3, password="la-vieja")


def admin_mantenimiento(env: Entorno) -> None:
    """Un administrador haciendo cosas legitimas que se parecen al ataque.

    Crea una access key, entra de madrugada, opera desde una IP de internet. Cada uno de
    esos hechos, aislado, es indistinguible de lo que hace el atacante tres dias despues.
    """
    with env.como(ADMIN, "admin:mrivas") as e:
        # Mantenimiento nocturno del dia 4: entra desde casa, por internet, de madrugada.
        noche = INICIO + timedelta(days=3, hours=2, minutes=40)
        ip_casa = "190.210.8.92"
        sesion = e.ssh_intento(noche, "ubuntu", ip_casa, exito=True, metodo="publickey",
                               clave="Qw7ZmT1yBnKe5RfPcHdL")
        if sesion:
            for i in range(3):
                e.sudo(noche + timedelta(minutes=4 + i * 7), sesion,
                       "/usr/bin/systemctl restart postgres")
            e.ssh_cierre(sesion, noche + timedelta(minutes=38))

        # Rotacion planificada de una credencial de servicio. Mismo evento que usara el
        # atacante el dia 8, con distinto contexto alrededor.
        t = INICIO + timedelta(days=3, hours=3, minutes=10)
        e.llamada_aws(t, "AKIA9KLMXP2HTVCJWD5N", "iam", "ListAccessKeys", ip_casa,
                      region="us-east-1")
        e.crear_access_key(t + timedelta(minutes=2), "AKIA9KLMXP2HTVCJWD5N",
                           "svc-pipeline", ip_casa, nueva_id="AKIA5RDVZHPQWNJ2TKC8")
        e.llamada_aws(t + timedelta(minutes=6), "AKIA9KLMXP2HTVCJWD5N", "iam",
                      "DeleteAccessKey", ip_casa, region="us-east-1")

        # Copia masiva de un bucket a otro: mucho volumen de golpe, con ticket detras.
        t = INICIO + timedelta(days=5, hours=15)
        for _ in range(e.rng.randint(18, 30)):
            t += timedelta(seconds=e.espera() * 2)
            e.llamada_aws(t, "AKIA9KLMXP2HTVCJWD5N", "s3", "ListBucket", e.ip_interna(),
                          recurso="respaldos-bancoxyz")


def atacante(env: Entorno) -> list[str]:
    """El plan. Escrito de antemano y ejecutado sin adaptarse a nada.

    Que el plan sea fijo es lo que mantiene reproducible el escenario. La contencion lo
    intercepta o no lo intercepta, pero el atacante no aprende: si su plan incluia saltar
    al cuarto host, salta -- no porque vio que aislaron los otros tres.

    Ninguna primitiva es propia: las IPs salen del mismo pool que los bots, los intervalos
    de la misma distribucion de cola pesada. Lo unico que lo distingue es la secuencia.
    """
    narrativa: list[str] = []
    ip_a = "198.51.100.77"
    ip_b = "200.45.10.18"

    with env.como(ATAQUE, "atacante") as e:
        # -- Dia 8, 21:40 UTC: reconocimiento contra el host expuesto --------------
        t = INICIO + timedelta(days=7, hours=21, minutes=40)
        for usuario in ["admin", "oracle", "postgres", "deploy", "test", "git",
                        "ubuntu", "jenkins", "ftp", "backup"]:
            t += timedelta(seconds=e.rng.randint(20, 180))
            e.ssh_intento(t, usuario, ip_a, exito=False)
        narrativa.append("Enumeracion de usuarios contra web-03 desde 198.51.100.77.")

        # Acceso con una clave publica que la cuenta no tenia antes.
        t += timedelta(minutes=e.rng.randint(6, 20))
        sesion_ssh = e.ssh_intento(t, "ubuntu", ip_a, exito=True, metodo="publickey",
                                   clave="Xk9pW3vNqZ7mBtRySdFj")
        narrativa.append("Acceso a web-03 como ubuntu con una clave publica nueva.")

        if sesion_ssh:
            for comando in ["/usr/bin/cat /etc/passwd",
                            "/usr/bin/find / -name *.pem",
                            "/usr/bin/cat /home/ubuntu/.aws/credentials",
                            "/usr/bin/curl http://169.254.169.254/latest/meta-data/"]:
                t += timedelta(seconds=e.espera() * 3 + 40)
                e.sudo(t, sesion_ssh, comando)
            narrativa.append("Lectura de credenciales de AWS desde el filesystem de web-03.")

        # -- Dia 8, 23:10 UTC: rociado de contrasenias contra la estacion ----------
        t = INICIO + timedelta(days=7, hours=23, minutes=10)
        for usuario in ["administrador", "backup", "deploy", "test"]:
            t += timedelta(seconds=e.rng.randint(15, 90))
            e.logon_windows(t, usuario, ip_a, tipo=3, password="Verano2026!")
        for usuario in USUARIOS_OFICINA:
            t += timedelta(seconds=e.rng.randint(15, 90))
            e.logon_windows(t, usuario, ip_a, tipo=3, password="Verano2026!")
        t += timedelta(seconds=e.rng.randint(15, 90))
        e.logon_windows(t, "temporal", ip_a, tipo=3, password="Verano2026!")
        narrativa.append("Rociado de contrasenias contra WKS-04: pocas contrasenias contra "
                         "muchas cuentas, incluidas cuentas que no existen.")

        # -- Dia 9, 00:20 UTC: acceso remoto exitoso -------------------------------
        t = INICIO + timedelta(days=8, hours=0, minutes=20)
        sesion_win = e.logon_windows(t, "ecarrizo", ip_a, tipo=10)
        narrativa.append("Acceso remoto (logon type 10) a WKS-04 como ecarrizo desde la "
                         "misma direccion que acumulaba fallos.")

        if sesion_win:
            for imagen in ["C:\\Windows\\System32\\whoami.exe",
                           "C:\\Windows\\System32\\net.exe",
                           "C:\\Windows\\System32\\net1.exe",
                           "C:\\Windows\\System32\\tasklist.exe",
                           "C:\\Windows\\System32\\findstr.exe",
                           "C:\\Windows\\System32\\nltest.exe",
                           "C:\\Windows\\System32\\reg.exe",
                           "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"]:
                t += timedelta(seconds=e.espera() * 2 + 25)
                e.proceso(t, sesion_win, imagen,
                          padre="C:\\Windows\\System32\\cmd.exe")
            narrativa.append("Reconocimiento local en WKS-04: whoami, net, tasklist, "
                             "findstr, nltest, reg.")

            t += timedelta(minutes=e.rng.randint(4, 12))
            e.cuenta_creada(t, sesion_win, "soporte_it")
            narrativa.append("Creacion de la cuenta local soporte_it (persistencia).")

        # -- Dia 9, 01:05 UTC: uso de la credencial en la nube ---------------------
        t = INICIO + timedelta(days=8, hours=1, minutes=5)
        cred = "AKIA3TBWMZ8FLQDNRV6H"
        for servicio, operacion, region in [
            ("sts", "GetCallerIdentity", "sa-east-1"),
            ("iam", "ListUsers", "us-east-1"),
            ("iam", "ListAttachedUserPolicies", "us-east-1"),
            ("s3", "ListBuckets", "sa-east-1"),
            ("ec2", "DescribeInstances", "sa-east-1"),
            ("ec2", "DescribeSecurityGroups", "sa-east-1"),
            ("rds", "DescribeDBInstances", "sa-east-1"),
        ]:
            t += timedelta(seconds=e.espera() * 2 + 20)
            e.llamada_aws(t, cred, servicio, operacion, ip_b, region=region)
        narrativa.append("Enumeracion de la cuenta de AWS con la credencial de ecarrizo, "
                         "desde 200.45.10.18: una direccion sin actividad previa.")

        # Persistencia en la nube.
        t += timedelta(minutes=e.rng.randint(3, 9))
        e.crear_access_key(t, cred, "ecarrizo", ip_b, nueva_id="AKIA6WNPXQ4TZBVMH8KR")
        narrativa.append("Creacion de una access key nueva para ecarrizo (persistencia).")

        nueva = "AKIA6WNPXQ4TZBVMH8KR"
        for servicio, operacion, region, error in [
            ("sts", "GetCallerIdentity", "sa-east-1", None),
            ("s3", "ListBuckets", "sa-east-1", None),
            ("s3", "GetBucketPolicy", "sa-east-1", None),
            ("cloudtrail", "StopLogging", "us-east-1", "AccessDenied"),
            ("iam", "AttachUserPolicy", "us-east-1", "AccessDenied"),
            ("ec2", "RunInstances", "sa-east-1", "AccessDenied"),
        ]:
            t += timedelta(seconds=e.espera() * 2 + 30)
            e.llamada_aws(t, nueva, servicio, operacion, ip_b, region=region, error=error)
        narrativa.append("Intentos de apagar CloudTrail y de escalar privilegios, los tres "
                         "rechazados por permisos.")

        # -- Dia 9, 02:40 UTC: vuelta con la credencial nueva ----------------------
        # La segunda visita es la que demuestra que la persistencia sirve: entra con la
        # key creada, no con la robada. Rotar solo la original la dejaria intacta.
        t = INICIO + timedelta(days=8, hours=2, minutes=40)
        for servicio, operacion, region in [
            ("s3", "ListBucket", "sa-east-1"),
            ("s3", "GetBucketAcl", "sa-east-1"),
            ("s3", "ListBucket", "sa-east-1"),
            ("ec2", "DescribeSnapshots", "sa-east-1"),
            ("ec2", "DescribeImages", "sa-east-1"),
            ("kms", "ListKeys", "sa-east-1"),
            ("secretsmanager", "ListSecrets", "sa-east-1"),
        ]:
            t += timedelta(seconds=e.espera() * 2 + 25)
            e.llamada_aws(t, nueva, servicio, operacion, ip_b, region=region,
                          recurso="respaldos-bancoxyz" if servicio == "s3" else None)
        narrativa.append("Segunda sesion con la access key creada por el propio atacante: "
                         "la persistencia sobrevive a rotar la credencial original.")

        # Y vuelve al endpoint con la sesion remota, ya con cuenta propia.
        t = INICIO + timedelta(days=8, hours=3, minutes=5)
        sesion_2 = e.logon_windows(t, "soporte_it", ip_a, tipo=10)
        if sesion_2:
            for imagen in ["C:\\Windows\\System32\\net.exe",
                           "C:\\Windows\\System32\\schtasks.exe",
                           "C:\\Windows\\System32\\sc.exe"]:
                t += timedelta(seconds=e.espera() * 2 + 20)
                e.proceso(t, sesion_2, imagen, padre="C:\\Windows\\System32\\cmd.exe")
            narrativa.append("Reingreso a WKS-04 con la cuenta soporte_it y creacion de "
                             "persistencia local (schtasks, sc).")

    return narrativa


def atacante_salto_triple(env: Entorno) -> list[str]:
    """Plan de practica: tres saltos en cadena -- WKS-04, despues web-03, recien despues AWS.

    Existe para tener un segundo caso para investigar y responder, distinto del principal:
    ni un solo salto de dominio (como el plan de arriba) sino dos, y la credencial que
    importa no aparece hasta adentro de web-03. Seguirla exige seguir la identidad a traves
    de dos fronteras, no una.

    El acceso a web-03 no deja un solo intento fallido: entra con una clave publica nueva
    directamente, sin `Invalid user` ni `Failed password` antes.
    """
    narrativa: list[str] = []
    ip_a = "203.0.113.91"
    ip_web03 = "10.20.4.53"

    with env.como(ATAQUE, "atacante") as e:
        # -- Pocos fallos, despues acceso remoto a WKS-04 --------------------------
        t = INICIO + timedelta(days=5, hours=22, minutes=50)
        for _ in range(2):
            t += timedelta(seconds=e.rng.randint(20, 90))
            e.logon_windows(t, "mlopez", ip_a, tipo=3, password="Otonio2026!")
        narrativa.append("Dos intentos fallidos contra mlopez en WKS-04 -- muchos menos que "
                         "un rociado de contrasenias.")

        t += timedelta(seconds=e.rng.randint(30, 120))
        sesion_win = e.logon_windows(t, "mlopez", ip_a, tipo=10)
        narrativa.append("Acceso remoto (logon type 10) a WKS-04 como mlopez.")

        if sesion_win:
            for imagen in ["C:\\Windows\\System32\\whoami.exe",
                           "C:\\Windows\\System32\\net.exe",
                           "C:\\Windows\\System32\\findstr.exe"]:
                t += timedelta(seconds=e.espera() * 2 + 20)
                e.proceso(t, sesion_win, imagen, padre="C:\\Windows\\System32\\cmd.exe")
            narrativa.append("Reconocimiento local en WKS-04: whoami, net, findstr.")

        # -- Salto 1 -> 2: de WKS-04 a web-03, sin un solo intento fallido ---------
        t += timedelta(minutes=e.rng.randint(5, 15))
        sesion_ssh = e.ssh_intento(t, "deploy", ip_web03, exito=True, metodo="publickey",
                                   clave="Zt4mKqL8vXpR2wNsHbYc")
        narrativa.append("Acceso directo a web-03 como deploy con una clave publica nueva, "
                         "sin ningun intento fallido previo contra ese host.")

        if sesion_ssh:
            for comando in ["/usr/bin/cat /etc/app/deploy.conf",
                            "/usr/bin/find /etc -name *.conf -newer /etc/hostname"]:
                t += timedelta(seconds=e.espera() * 3 + 40)
                e.sudo(t, sesion_ssh, comando)
            narrativa.append("Lectura de un archivo de configuracion en web-03 que contiene "
                             "una credencial de AWS embebida.")

        # -- Salto 2 -> 3: de web-03 a AWS, con una credencial que nunca se uso ----
        t += timedelta(minutes=e.rng.randint(3, 10))
        cred = "AKIA4RXWNPFOZ8GHK6EY"
        for servicio, operacion in [("sts", "GetCallerIdentity"), ("s3", "ListBuckets"),
                                    ("iam", "ListAccessKeys")]:
            t += timedelta(seconds=e.espera() * 2 + 25)
            e.llamada_aws(t, cred, servicio, operacion, ip_web03)
        narrativa.append("Primera actividad de AKIA4RXWNPFOZ8GHK6EY en toda la ventana: "
                         "estaba embebida en el archivo de configuracion de web-03 y nunca "
                         "se habia usado.")

        t += timedelta(minutes=e.rng.randint(2, 6))
        e.crear_access_key(t, cred, "svc-web03-deploy", ip_web03,
                           nueva_id="AKIA1QDHXPEC6MYFT39V")
        narrativa.append("Creacion de una access key nueva a partir de la embebida "
                         "(persistencia en la nube).")

        if sesion_ssh:
            e.ssh_cierre(sesion_ssh, t + timedelta(minutes=e.rng.randint(4, 15)))

    return narrativa


# Casos disponibles para investigar y responder. "a" es el caso principal. Los demas son
# practica: otro ataque, generado con la misma maquinaria, sin relacion de medicion entre
# ellos -- no se comparan numeros de uno contra otro, cada uno se investiga por su cuenta.
CASOS = {
    "a": {"seed": SEED, "plan": "atacante", "caso": "INC-2026-0051",
          "dir": "evidencia",
          "resumen": "Intrusion desde internet. Empieza con fallos de autenticacion."},
    "b": {"seed": 20260701, "plan": "atacante_salto_triple", "caso": "INC-2026-0064",
          "dir": "evidencia_b",
          "resumen": "Cadena de tres saltos: WKS-04, web-03, AWS. La credencial que "
                     "importa no aparece hasta el segundo salto."},
}


# --------------------------------------------------------------------------------------
# Proyeccion
# --------------------------------------------------------------------------------------


def generar(seed: int = SEED, plan: str = "atacante") -> dict:
    env = Entorno(seed)
    poblar(env)

    usuarios_oficina(env)
    jobs_aws(env)
    usuarios_aws(env)
    bots_internet(env)
    accesos_ssh_legitimos(env)
    app_con_password_vencida(env)
    admin_mantenimiento(env)
    narrativa = globals()[plan](env)

    emisiones = sorted(env.emisiones, key=lambda x: (x.t, x.fuente))

    prefijos = {"windows": "W", "cloudtrail": "C", "syslog": "L"}
    contadores = {"windows": 0, "cloudtrail": 0, "syslog": 0}
    fuentes: dict[str, list] = {"windows": [], "cloudtrail": [], "syslog": []}
    verdad: dict[str, dict] = {}

    for em in emisiones:
        contadores[em.fuente] += 1
        eid = f"{prefijos[em.fuente]}{contadores[em.fuente]:04d}"
        registro = em.crudo
        if isinstance(registro, dict):
            registro = {"_id": eid, **registro}
        else:
            registro = {"_id": eid, "linea": registro}
        fuentes[em.fuente].append(registro)
        verdad[eid] = {"etiqueta": em.etiqueta, "actor": em.actor,
                       "real_utc": em.t.strftime("%Y-%m-%dT%H:%M:%SZ")}

    return {"fuentes": fuentes, "verdad": verdad, "narrativa": narrativa, "entorno": env}


def _config(evid: Path) -> dict:
    """Que caso corresponde a un directorio de evidencia."""
    for cfg in CASOS.values():
        if Path(evid).name == cfg["dir"]:
            return cfg
    return CASOS["a"]


def verdad(evid: Path = AQUI) -> dict:
    """La verdad del caso, reconstruida en memoria.

    **No se persiste a disco, y esa es una decision de disenio, no una omision.** Las
    etiquetas son una funcion del seed: guardarlas al lado de la evidencia duplicaria
    informacion que ya vive en el codigo, y le pondria a cualquiera que investigue -- una
    persona o un agente -- un archivo con todas las respuestas a un `Read` de distancia.

    Regenerar cuesta menos de un segundo y elimina el problema de raiz: mientras se
    investiga no hay nada que espiar, porque la verdad no existe en ningun lado.

    La guarda de coincidencia es lo que hace confiable el atajo. Si la evidencia en disco
    no corresponde exactamente a este seed -- porque se edito, o se genero con otros
    parametros -- las etiquetas reconstruidas estarian describiendo otro caso. Ante esa
    discrepancia se corta.
    """
    cfg = _config(evid)
    datos = generar(cfg["seed"], cfg["plan"])
    conteo = {f: len(r) for f, r in datos["fuentes"].items()}

    for fuente, registros in datos["fuentes"].items():
        ruta = evid / f"{fuente}.json"
        if not ruta.exists():
            raise RuntimeError(f"falta {ruta.name}: correr `python main.py generar`")
        en_disco = [r["_id"] for r in json.loads(ruta.read_text(encoding="utf-8"))]
        if en_disco != [r["_id"] for r in registros]:
            raise RuntimeError(
                f"{ruta.name} no corresponde al seed {cfg['seed']}: la evidencia en disco fue "
                f"editada o generada con otros parametros. Regenerar con "
                f"`python main.py generar`.")

    etiquetas: dict[str, int] = {}
    for v in datos["verdad"].values():
        etiquetas[v["etiqueta"]] = etiquetas.get(v["etiqueta"], 0) + 1

    return {
        "caso": cfg["caso"],
        "seed": cfg["seed"],
        "ventana": {"desde": INICIO.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "hasta": FIN.strftime("%Y-%m-%dT%H:%M:%SZ")},
        "entrada_del_analista": ENTRADA.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "recoleccion": RECOLECCION.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "conteo": conteo,
        "etiquetas": etiquetas,
        "narrativa": datos["narrativa"],
        "eventos": datos["verdad"],
    }


def escribir(caso: str = "a") -> dict:
    """Proyecta las tres fuentes a disco. La verdad NO se escribe: ver `verdad()`."""
    cfg = CASOS[caso]
    destino = AQUI.parent / cfg["dir"]
    destino.mkdir(exist_ok=True)
    datos = generar(cfg["seed"], cfg["plan"])
    for fuente, registros in datos["fuentes"].items():
        (destino / f"{fuente}.json").write_text(
            json.dumps(registros, indent=1, ensure_ascii=False), encoding="utf-8")

    conteo = {f: len(r) for f, r in datos["fuentes"].items()}
    etiquetas: dict[str, int] = {}
    for v in datos["verdad"].values():
        etiquetas[v["etiqueta"]] = etiquetas.get(v["etiqueta"], 0) + 1
    return {"conteo": conteo, "etiquetas": etiquetas}


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--caso", choices=sorted(CASOS), default="a")
    opciones = ap.parse_args()
    print(f"caso       : {opciones.caso} - {CASOS[opciones.caso]['resumen']}")
    resumen = escribir(opciones.caso)
    total = sum(resumen["conteo"].values())
    print(f"eventos    : {total}")
    for fuente, n in sorted(resumen["conteo"].items()):
        print(f"  {fuente:<12}: {n}")
    print("etiquetas  :")
    for etiqueta, n in sorted(resumen["etiquetas"].items(), key=lambda x: -x[1]):
        print(f"  {etiqueta:<24}: {n:>5}  ({n / total * 100:.1f}%)")
