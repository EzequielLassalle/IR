---
name: fir-desde-cero
description: Explica FIR desde cero a alguien que programa pero no viene de seguridad - el dominio, el escenario, cada estructura de datos y cada concepto del motor, de a uno por vez y sin dar por sabido nada de seguridad informatica. Usar cuando se pida entender FIR desde cero, desde abajo, sin suponer conocimiento previo, o cuando una explicacion anterior no cerro.
---

# FIR desde cero

Modo de estudio del proyecto en `C:\Users\Ezela\Desktop\FIR`. Los comandos se corren parado
ahi.

Hay otros dos skills y este no los reemplaza: `fir-lab` opera el laboratorio, `fir-conceptos`
explica el proyecto **suponiendo background de seguridad**. Este skill existe porque esa
suposicion fallo. Si el usuario esta en este skill, la premisa de `fir-conceptos` no aplica y
no hay que volver a ella.

## Con quien estas hablando

**Ezequiel escribio este codigo. Sabe programar.** Python, estructuras de datos, JSON,
funciones, tests, CLI, control de versiones: todo eso se da por sabido y explicarlo es
perder el tiempo y tratarlo de tonto.

**Lo que NO se da por sabido es nada de seguridad informatica.** Literalmente nada. Esta es
la lista de cosas que hay que definir la primera vez que aparecen, sin excepcion y sin
preguntar si hace falta:

- que es un log, un evento, una fuente de logs, un timestamp de auditoria
- Windows Security, EventID, 4624, 4625, 4688, logon type, LogonId, SubStatus
- syslog, sshd, `auth.log`, "Accepted password", "Failed password"
- AWS, CloudTrail, access key, `AKIA...`, IAM, S3, bucket, data event, trail
- cuenta, credencial, autenticacion, sesion, host, estacion de trabajo, servidor expuesto
- que es un ataque, un incidente, un atacante, un indicador
- rociado de contrasenias, reconocimiento, persistencia, movimiento lateral, exfiltracion
- SIEM, SOC, analista, deteccion, regla de deteccion, falso positivo, recall, precision
- respuesta a incidentes, contencion, aislar un host, revocar una credencial, cadena de custodia

**La regla operativa:** si una frase contiene un termino de esa lista y el termino no fue
definido antes en la conversacion, la frase no se emite. Se define primero, en una linea, y
recien despues se usa.

**Cuando dice que no entiende, la causa nunca es que la explicacion fue corta.** Es que hubo
un prerequisito que se salteo. La respuesta correcta es **retroceder y buscar cual**, no
reformular lo mismo con mas palabras ni agregar material nuevo. Preguntarle cual fue la
ultima frase que si le cerro y reconstruir desde ahi.

Registro tecnico, no tutorial. Sin felicitaciones de relleno, sin signos de admiracion, sin
"¡excelente pregunta!". Definir un termino no es hablarle como a un principiante: es la misma
precision que se usaria al documentar una API.

## Como se dicta

**Una parte por vez, y no se avanza sola.** Cada parte termina con una pregunta concreta de
comprobacion -- no "¿se entiende?", sino una pregunta que solo se puede contestar bien si la
parte quedo clara. **No se pasa a la siguiente hasta que la contesta.** Si la contesta mal,
no se corrige y se sigue: se vuelve al punto que fallo.

**Cada afirmacion se respalda corriendo el comando y pegando la salida real.** Si una cifra
no salio de un comando en esta conversacion, no se dice. Cuando una cifra sale de leer el
codigo, se cita el archivo y la linea.

**Ningun concepto se explica en abstracto: se explica sobre un artefacto que esta a la
vista.** Cuando la parte introduce una estructura de datos, un formato o un objeto, hay que
abrir el archivo real donde vive, pegar el fragmento, y decir **que archivo es y en que
linea**. "Un log tiene un timestamp y un sujeto" no se dice sin tener al lado la linea de
`evidencia/windows.json` que lo muestra. Esto vale tambien para las partes que no corren la
CLI: no correr un comando no es lo mismo que no mostrar nada -- leer un archivo del repo
siempre esta permitido y casi siempre es lo que falta.

**No se lo deja solo al final de una parte.** Cerrar con la pregunta de comprobacion y nada
mas es abandonarlo: no sabe si puede volver atras, ni que opciones tiene, ni si su respuesta
lo habilita a seguir. Toda parte termina con el mismo pie fijo, en este orden:

1. la pregunta de comprobacion,
2. un renglon con las salidas: seguir a la parte N+1, volver a la parte N-1 o a cualquier
   otra por numero, ver el indice, o pedir mas detalle de un punto de esta misma parte,
3. una invitacion explicita a decir que quedo flojo, incluso a medias -- "esta parte la
   segui hasta X y ahi me perdi" es una respuesta valida y hay que decirlo.

**Cuando contesta la comprobacion, se acusa recibo de la respuesta antes de avanzar.** Decir
que parte de lo que dijo esta bien, y si falto algo, cual es la pieza exacta que falto. Pasar
a la parte siguiente sin evaluar lo que contesto convierte la comprobacion en decorado.

**Si se queda callado, se ofrecen dos o tres tirones de hilo concretos**, no un "¿alguna
duda?". Preguntas de la forma "¿queres que te muestre como se ve ese mismo evento en
`syslog.json`, que es otro formato?" -- opciones nombradas, no un campo vacio.

**El cuadro se muestra una sola vez, al abrir el skill.** El pie de navegacion de cada parte
lo menciona como opcion, pero el cuadro se vuelve a dibujar solo si lo pide.

Las partes estan ordenadas por dependencia. **La 1 no depende de nada; cada una siguiente
depende de todas las anteriores.** Si pide una parte salteada, decirle que prerequisitos le
faltan y ofrecer ir a buscarlos primero -- pero si insiste, dictarla igual e ir definiendo lo
que falte al vuelo.

```
╭──────────────────────────────────────────────────────────────────────────╮
│   \ | /                                                                  │
│  ── * ──   FIR DESDE CERO                                                │
│   / | \                                                                  │
├──────────────────────────────────────────────────────────────────────────┤
│  EL DOMINIO                                                              │
│   1) Que es un log            y por que alguien los junta                │
│   2) Las tres fuentes         Windows, syslog y CloudTrail, una por una  │
│   3) El escenario             que paso en esos diez dias, como historia  │
│                                                                          │
│  LOS DATOS                                                               │
│   4) El evento                crudo, normalizado, y por que dos capas    │
│   5) El tiempo                un timestamp no siempre alcanza solo       │
│   6) La afirmacion            el otro objeto, y la cita                  │
│                                                                          │
│  EL MOTOR                                                                │
│   7) Verificar                cuando una cita no sostiene lo que dice    │
│   8) El vocabulario cerrado   por que 'el atacante' no se puede afirmar  │
│   9) La cobertura             la diferencia entre no paso y no se sabe   │
│  10) Adjudicar                juzgar una decision con lo que se sabia    │
│  11) Recomendar               por que no es lo mismo, y el bug central   │
│  12) El estado                ejecutar tiene que cambiar el mundo        │
│                                                                          │
│  LA PRUEBA                                                               │
│  13) Medir                    recall, precision y la verdad sin archivo  │
│  14) El escenario B           como se sabe si un metodo transfiere       │
│  15) El codigo                los modulos y como encajan                 │
│                                                                          │
│   0) Salir                                                               │
╰──────────────────────────────────────────────────────────────────────────╯
```

Copiar el cuadro literal. Todas las lineas miden 76 caracteres.

---

# EL DOMINIO

## 1) Que es un log

**No usar ningun comando de la CLI todavia**, y es a proposito: si arranca por `main.py`, la
CLI es una cosa mas que entender antes de entender el problema.

**Pero si hay que abrir un archivo.** Terminar la parte sin que haya visto una linea de log
real es el error a no cometer: se queda con una definicion de "log" que no puede contrastar
con nada. Abrir `evidencia/windows.json`, pegar **un evento crudo entero**, decir el archivo
y el indice, y senalar sobre esa linea concreta las tres propiedades (quien la escribio, que
es un hecho y no un diagnostico, que no se edita). Recien despues sigue el texto de abajo.

Arrancar por lo que ya sabe. Un programa que escribe una linea a un archivo cada vez que pasa
algo -- eso es `logging.info()`, lo conoce. Un log de auditoria es lo mismo, con tres
diferencias que hay que decir explicitamente:

- **Lo escribe el sistema operativo o el servicio, no la aplicacion.** El que audita no es el
  mismo que actua.
- **Registra hechos, no diagnostico.** No dice "algo raro paso", dice "la cuenta X autentico
  desde la IP Y a las Z". La interpretacion no viene incluida.
- **Se escribe una sola vez y no se edita.** Es append-only por diseno.

Un **evento** es una de esas lineas. Una **fuente** es el sistema que las produce.

Despues el encuadre del oficio, en dos parrafos y sin jerga:

Cuando alguien entra a un sistema sin permiso, no deja una notificacion. Deja **rastros
laterales**: se autentico, ejecuto programas, llamo APIs. Cada una de esas cosas produjo una
linea en algun log, porque el sistema audita todo lo que pasa, no solo lo malo. Reconstruir
que hizo es leer esas lineas.

El problema es la proporcion. En este caso son **6.532 eventos y el ataque son 69** -- el
1,1%. El resto es gente trabajando. No hay un campo que diga "esto es el ataque": si lo
hubiera, el problema no existiria.

Cerrar con los dos verbos que estructuran todo el proyecto, porque la mitad del diseno
depende de la distincion:

- **Investigar** es contestar *que paso*, mirando evidencia.
- **Responder** es contestar *que hago al respecto*: apagar algo, bloquear algo, deshabilitar
  una cuenta. Son acciones sobre el mundo, tienen costo, y algunas son irreversibles.

FIR hace las dos, y la segunda es la que casi nadie hace bien.

**Comprobacion:** pedirle que diga, con sus palabras, por que un log de auditoria no puede
simplemente marcar los eventos del ataque con un flag. Si contesta "porque no se sabe cual es
el ataque hasta despues", entendio. Si contesta algo sobre performance o formato, falto la
idea de que el sistema audita sin saber que va a importar.

## 2) Las tres fuentes

Ahora si, primer comando: `python main.py estado`. Pegar la salida.

De esa salida solo importan las tres lineas de conteo por fuente. Explicar **una fuente por
vez**, y de cada una tres cosas: que sistema es, que registra, y como se ve una linea suya.

**windows (1.954 eventos).** Windows tiene un log llamado Security donde el sistema operativo
anota quien inicio sesion, quien fallo, y que programas se ejecutaron. Cada tipo de hecho
tiene un numero fijo, el **EventID**. Los tres que aparecen en este caso:

| EventID | que significa |
|---|---|
| 4624 | alguien inicio sesion con exito |
| 4625 | alguien intento iniciar sesion y fallo |
| 4688 | se ejecuto un programa |

Un 4624 trae ademas un **logon type**, que dice *como* inicio sesion: sentado frente a la
maquina, por red, o por escritorio remoto. Es un numero, y cual es cambia por completo la
lectura. `WKS-04` es la estacion de trabajo de una persona.

**syslog (1.329 eventos).** Es el formato de log de Linux: lineas de texto plano en
`/var/log/auth.log`. Las escribe `sshd`, el servicio que atiende conexiones SSH -- es decir,
el que deja entrar por consola remota desde internet. Dos lineas suyas importan: `Accepted
password` (entro) y `Failed password` (no entro). `web-03` es un servidor **expuesto a
internet**: cualquiera del planeta le puede intentar una conexion.

**cloudtrail (3.249 eventos).** AWS es la nube de Amazon. **CloudTrail** es su log de
auditoria: registra cada llamada a la API de AWS -- crear un usuario, listar archivos,
apagar un servicio. Los sujetos no son personas: son **access keys**, credenciales con forma
`AKIA` + 16 caracteres, que identifican a quien hizo la llamada.

**El punto de la parte** y hay que decirlo explicito: las tres fuentes describen mundos
distintos con vocabularios incompatibles. Windows dice `4624`, syslog dice `Accepted
password`, CloudTrail dice `ConsoleLogin`, y **las tres significan "alguien entro"**. La
parte 4 es como se resuelve eso.

**Comprobacion:** darle una fuente y pedirle que diga que clase de hecho *no* podria
aparecer nunca ahi. Por ejemplo: un `Failed password` de `web-03` no puede aparecer en el log
de Windows, porque son sistemas distintos con logs distintos. Si eso sale, la nocion de
fuente quedo.

## 3) El escenario

Contar el incidente **como historia, en orden cronologico**, sin usar todavia ningun comando
de consulta. El objetivo es que despues, cuando vea un ID de evento, sepa a que parte de la
historia pertenece.

Correr `python main.py estado` de nuevo si hace falta la ventana. Diez dias:
`2026-03-02` a `2026-03-12`. El caso se llama `INC-2026-0051`.

La historia, en cinco actos:

1. **Dia 8, de noche.** Desde una direccion de internet alguien prueba pocas contrasenias
   comunes contra muchas cuentas de `WKS-04`. Se llama **rociado de contrasenias**: al reves
   de probar mil contrasenias contra una cuenta -- que traba la cuenta y hace ruido -- se
   prueba una contrasena contra mil cuentas. Casi todo falla. Una funciona: `ecarrizo`.
2. **Entra por escritorio remoto** a `WKS-04` con esa cuenta.
3. **Reconocimiento.** Ejecuta programas que no hacen dano y solo miran: `whoami` (quien soy),
   `net` (que cuentas hay), `tasklist` (que corre). Se llama reconocimiento y es lo primero
   que hace cualquiera que cae en una maquina que no conoce.
4. **Persistencia.** Crea una cuenta nueva, `soporte_it`. El nombre es deliberado: parece de
   soporte tecnico. Sirve para volver a entrar aunque a `ecarrizo` le cambien la contrasena.
5. **Dia 10, madrugada.** Vuelve a entrar como `soporte_it`, y desde ahi pasa a AWS.

Y el dato que define el ejercicio: **el analista toma el caso dos dias despues**. Nadie lo
vio en el momento. Todo se reconstruye para atras.

### Las cinco capas

Aca esta el corazon del diseno del escenario, y **es la parte que hay que asegurarse de que
entienda antes de seguir**. La evidencia tiene cinco clases de actividad conviviendo:

| capa | que es |
|---|---|
| `normal` | Gente laburando con horarios consistentes, y tareas automaticas |
| `ruido-internet` | Bots escaneando `web-03` porque esta expuesto. Cientos de fallos que no son un ataque contra nadie en particular |
| `admin-legitimo` | Un administrador creando una credencial de AWS de madrugada desde una IP nueva. Se ve identico a un ataque. No lo es |
| `sospechoso-no-incidente` | Una aplicacion con la contrasena vencida reintentando sola **648 veces** |
| `ataque` | El incidente: 69 eventos, 1,1% del total |

**Por que existen las capas 3 y 4.** Si el ataque fuera lo unico raro, encontrar lo raro seria
encontrar el ataque, y el ejercicio seria un `WHERE`. Con esas dos capas hay que distinguir
**lo raro de lo peligroso**, que es el trabajo real y no se automatiza con un filtro.

Mostrarlo con la salida de `estado` que ya esta pegada: el sujeto mas activo es una access
key con 3.131 eventos, el segundo es `svc_backup` con 648. **Ninguno de los dos es el
ataque.** El ataque son 69 eventos que no estan ni cerca del top.

### La regla de la tela

Correr `python main.py entidad 198.51.100.77` y pegar la salida.

Esa es la IP desde la que se rocian las contrasenias el dia 8. Aparece **por primera vez el
dia 1**, haciendo escaneo de fondo contra `web-03`, y de sus 140 eventos 127 son ruido.

Todos los actores del escenario usan las mismas primitivas: el atacante saca sus direcciones
del mismo pool que los bots y espacia sus acciones con la misma distribucion. **Lo unico que
lo distingue es que hace.** Filtrar por esa IP no da el ataque: da 140 eventos de los cuales
13 importan.

**Comprobacion:** preguntarle por que no alcanza con buscar la IP del atacante. La respuesta
correcta menciona que la IP tambien hizo ruido irrelevante, y idealmente que uno no sabe cual
es "la IP del atacante" hasta despues de resolver el caso.

---

# LOS DATOS

## 4) El evento

Correr `python main.py evento W1497` y pegar **la salida completa**, sin cortar ningun
bloque. El error a no repetir es pegar solo el encabezado y despues referirse a campos que
quedaron fuera de lo que vio.

La salida tiene cuatro bloques y cada uno es una capa distinta del mismo hecho. Recorrerlos
**de abajo hacia arriba**, porque el de abajo es el unico que existe de verdad:

**`REGISTRO CRUDO`** es el log tal como lo escribio Windows. `EventID: 4624`, `LogonType: 10`,
`TargetUserName: ecarrizo`. Todo lo demas se deriva de aca.

**`SEMANTICA`** es la traduccion documentada de esos numeros: *"4624 logon type 10
(RemoteInteractive) -- Escritorio remoto (RDP o Terminal Services)"*. RDP es el protocolo de
Windows para usar una maquina remota viendo su escritorio. El logon type importa: type 2 seria
sentado frente a la maquina, type 3 por red, type 10 remoto. Mismo EventID, tres hechos
distintos.

**`EVENTO`** es la version normalizada: `sujeto`, `accion`, `objeto`. La correspondencia es
literal y conviene mostrarla como tabla:

| crudo | normalizado |
|---|---|
| `TargetDomainName` + `TargetUserName` | `sujeto: WKS-04\ecarrizo` |
| `EventID 4624` + `LogonType 10` | `accion: autentico-remoto` |
| `Computer` | `objeto: WKS-04` |

**`ATRIBUTOS`** es lo que no entra en la terna pero se conserva: la IP, el logon type, el
`LogonId` (el identificador de esa sesion concreta).

**Por que dos capas.** Es la respuesta a lo que quedo abierto en la parte 2: tres fuentes
dicen "alguien entro" de tres formas distintas. Si el motor razonara sobre el crudo, cada
regla habria que escribirla tres veces. Normalizando, `autentico-remoto` se dice de una sola
forma y las tres fuentes entran a la misma comparacion. Lo hace `eventos.py`.

**El crudo nunca se descarta.** Queda abajo para auditar la traduccion: si alguien duda de que
`4624 + type 10` sea `autentico-remoto`, tiene el original al lado.

**Comprobacion:** preguntarle que pasaria con la afirmacion `ecarrizo autentico-local WKS-04`
citando `W1497`. Tiene que ver que el evento existe y el sujeto coincide, pero la accion no
-- el logon type 10 es remoto, no local. Eso es exactamente la parte 7 y conviene que lo
descubra el antes de que se lo cuenten.

## 5) El tiempo

Correr `python main.py evento L0337` y pegar la salida completa.

```
EVENTO
------------------------------------------------------------------------------
  id        : L0337
  instante  : 2026-03-05T02:40:00Z
  fuente    : syslog
  sujeto    : web-03:ubuntu
  accion    : autentico-remoto
  objeto    : web-03

ATRIBUTOS
------------------------------------------------------------------------------
  ip          : 190.210.8.92
  metodo      : publickey
  clave       : Qw7ZmT1yBnKe5RfPcHdL

REGISTRO CRUDO
------------------------------------------------------------------------------
  Mar  4 23:40:00 web-03 sshd[24402]: Accepted publickey for ubuntu from 190.210.8.92 port 47587 ssh2: RSA SHA256:Qw7ZmT1yBnKe5RfPcHdL

  El sello de syslog esta en hora local del host (-03) y sin anio: la
  fecha del crudo puede ser el dia anterior al instante real en UTC.
```

**El punto de la parte:** el `REGISTRO CRUDO` dice `Mar 4 23:40:00`. El `instante` normalizado
dice `2026-03-05T02:40:00Z`. Mismo evento, **dos fechas distintas** -- el 4 y el 5 de marzo.
No es un error: es lo que pasa cuando un formato de timestamp no trae, en el texto mismo, dos
datos que hacen falta para ubicarlo en el tiempo sin ambiguedad.

Abrir `tiempo.py` y ver `desde_syslog()`:

```python
def desde_syslog(ts: str, zona_offset_h: int, recoleccion: datetime) -> datetime:
    """Timestamp RFC 3164 ("Mar 11 02:04:37"): sin anio y sin zona en el propio texto.

    El anio se infiere como el mas reciente que no deje la fecha en el futuro respecto de
    la recoleccion. La zona se conoce fuera de banda, de la adquisicion, y se aplica aca.
    """
```

RFC 3164 es el formato clasico de syslog: `"Mar 11 02:04:37"`. Notar lo que falta ahi --
**no hay año, y no hay zona horaria**. Son dos datos que hay que conseguir de otro lado:

- **El año** se infiere: `_inferir_anio()` prueba el año de la recoleccion y, si eso deja el
  evento en el futuro, el anterior. Es una heuristica, no un dato -- si el log tuviera mas de
  un año de antiguedad, se fecharia mal y nada en el propio log lo delataria.
- **La zona** (`zona_offset_h=-3` para `web-03`, definido en `eventos.py`) se capturo en la
  adquisicion. Sin ese numero, `Mar 4 23:40:00` no se puede llevar a UTC en absoluto.

`L0337` es exactamente el caso limite: son las 23:40 en hora local, que ya es la madrugada
siguiente en UTC (-3 se resta, el reloj UTC va **adelante** del local). Por eso el crudo queda
fechado un dia antes del instante real -- y por eso el timeline (que ordena por el instante
normalizado) y el registro crudo (que nunca se toca) pueden discrepar en la fecha sin que haya
ningun error de por medio.

**Comprobacion:** si `zona_offset_h` estuviera mal capturado en la adquisicion -- fuera `-4` en
vez de `-3` -- ¿que le pasaria al instante normalizado de `L0337`? ¿Se movio adentro del mismo
dia o cambiaria de dia otra vez?

## 6) La afirmacion

Correr `head -c 1200 hallazgos_prueba.json` -- o abrirlo -- y pegar la primera entrada.

Hasta aca hubo un solo tipo de objeto: el evento, que **existe** en la evidencia. Ahora
aparece el segundo, y es el que hace al proyecto: la **afirmacion**, que es lo que *alguien
dice* sobre la evidencia. Un analista, una regla automatica, o un agente.

```json
"afirmacion": {
  "sujeto": "ecarrizo",
  "accion": "autentico-remoto",
  "objeto": "WKS-04",
  "desde":  "2026-03-10T00:00:00Z",
  "hasta":  "2026-03-10T01:00:00Z"
},
"cita": ["W1497"]
```

Cinco campos: la misma terna del evento (`sujeto`, `accion`, `objeto`) mas una ventana. Y una
**cita**: la lista de IDs de eventos que supuestamente la respaldan.

Un objeto con afirmacion + cita se llama **hallazgo**. Un archivo de hallazgos es la salida de
investigar: lo produce el detector automatico, o un agente, o una persona.

**La frase que resume el motor entero**, y conviene decirla textual porque las nueve partes
que siguen son casos de ella:

> Todo FIR es una sola operacion repetida: agarrar una afirmacion, agarrar los eventos que
> cita, y decidir si esos eventos la sostienen.

La ventana no es decorativa: `W1497` cae en `2026-03-10T00:20:00Z`, y la afirmacion declara
`00:00 .. 01:00` de ese mismo dia. La cita sostiene solo si el instante del evento cae adentro
de la ventana declarada. Por eso el tiempo venia antes que esto -- si `tiempo.py` normalizara
mal una fecha (parte 5), la verificacion entera se apoyaria en un instante equivocado.

**Comprobacion:** pedirle que arme una afirmacion falsa que cite `W1497` y que **igual se vea
creible**. Si arma una cambiando el sujeto o la accion, la parte 7 ya esta ganada.

---

# EL MOTOR

## 7) Verificar

Correr `python main.py verificar hallazgos_prueba.json`. Pegar la salida completa: son 11
hallazgos y 2 admitidos.

Aclarar primero que **ese archivo no son hallazgos del caso**: es un banco de prueba escrito a
mano donde casi todo esta mal a proposito, uno por cada forma de estar mal. Su `_nota` lo dice.

Agrupar los rechazos en tres familias y no perder tiempo en las dos primeras:

**Cita inexistente.** `C8888`, `W9999` no existen en la evidencia. Trivial de detectar.

**Sin cita.** Un hallazgo sin respaldo no es verificable. Tambien trivial.

**`CITA-NO-SOSTIENE`** -- esta es la que importa. Cita eventos **reales** y afirma algo que
esos eventos no dicen. Tres variantes, las tres con el mismo `W1497` de por medio:

```
mlopez autentico-remoto WKS-04       -> W1497: el sujeto del evento es 'WKS-04\ecarrizo'
ecarrizo ejecuto-proceso powershell  -> W1497: la accion del evento es 'autentico-remoto'
ecarrizo autentico-remoto (dia 5)    -> W1497: el evento cae fuera de la ventana
```

Sujeto, accion, ventana: los tres campos que se pueden falsear manteniendo un ID valido al
lado. **Las tres se ven impecables a simple vista.**

Y el punto de por que esto existe: **ese es el modo de falla real de un modelo de lenguaje.**
Inventar identificadores casi no lo hace. Citar bien y concluir mal, todo el tiempo. Si el
verificador no atrapa esas, no sirve para nada.

Notar tambien el hallazgo que sale `VERIFICADO: 1 de 2 citas sostienen`: alcanza con una cita
buena, y las malas se listan igual con el motivo. La verificacion no es binaria por hallazgo,
es por cita.

**Comprobacion:** preguntarle por que `CITA-NO-SOSTIENE` es peor que `CITA-INEXISTENTE`, si
las dos terminan rechazadas. La respuesta es que la primera pasa cualquier revision humana
rapida y la segunda no.

## 8) El vocabulario cerrado

Sale de la misma salida de la parte 7, de los tres hallazgos con `FUERA-DE-VOCABULARIO`:

```
'el atacante'          -> no es un sujeto observable: un log registra credenciales,
                          cuentas y hosts, nunca personas
'movimiento-lateral'   -> no es un hecho registrado: es una inferencia sobre un patron
                          de eventos, no un evento
'descargo-archivos'    -> no pertenece al vocabulario. Acciones validas: autentico-local,
                          autentico-red, autentico-remoto, cerro-sesion, creo-cuenta,
                          ejecuto-comando, ejecuto-proceso, fallo-autenticacion,
                          fallo-usuario-inexistente, llamo-api
```

Tres rechazos por tres razones distintas y conviene separarlas:

**`el atacante` no es observable.** Un log registra que la cuenta `ecarrizo` autentico. No
registra **quien** la uso: pudo ser su duena, pudo ser alguien con su contrasena. El salto de
cuenta a persona es una atribucion, y no hay ningun evento que la sostenga. El motor no la
prohibe por pedante: la prohibe porque **ninguna cita podria respaldarla**.

**`movimiento-lateral` no es un evento.** Movimiento lateral es "el atacante paso de una
maquina a otra". Eso es una lectura de varios eventos juntos, no algo que un log escriba.
Puede ser la conclusion de un caso; no puede ser una afirmacion verificable contra citas.

**`descargo-archivos` simplemente no existe.** El vocabulario de acciones tiene diez entradas
y esa no esta. Es un error de tipos, no de epistemologia.

**La regla de diseno:** el vocabulario es cerrado, entonces **lo que no se puede verificar no
se puede ni siquiera escribir**. La restriccion esta en la entrada, no en la salida. Un agente
que quiera afirmar "hubo movimiento lateral" tiene que descomponerlo en los eventos concretos
que lo harian cierto -- y esos si se verifican.

**Comprobacion:** darle una conclusion en prosa (`"la cuenta soporte_it se creo para
mantener acceso"`) y pedirle que diga que parte es afirmable y que parte no. Afirmable: que
`ecarrizo` creo la cuenta `soporte_it` en tal ventana. No afirmable: el "para", que es
intencion.

## 9) La cobertura

Correr primero `python main.py cobertura` y pegar la salida.

Esta parte contesta la pregunta que quedo colgando desde la 1: **que significa no haber
encontrado algo.** Significa dos cosas incompatibles: *no paso* o *no lo puedo saber*. La
diferencia depende de si la fuente que lo habria registrado cubria la ventana y registra esa
clase de hecho.

De la salida importan las `CARENCIAS DE AUDITORIA`, que son agujeros **declarados de
antemano**:

```
4688_command_line   El campo CommandLine de los eventos 4688.
                    Se sabe QUE binario se ejecuto, no CON QUE argumentos.
s3_data_events      Los eventos de nivel objeto de S3 (GetObject, PutObject...).
                    La ausencia de GetObject NO es evidencia de que no hubo exfiltracion.
```

Explicar el segundo, que hace falta contexto: S3 es el almacenamiento de archivos de AWS, y
un **bucket** es un contenedor de archivos. CloudTrail por defecto registra las operaciones
*sobre* los buckets (crear, listar, borrar el bucket) pero **no las operaciones sobre los
archivos adentro** -- esas son los data events, y se activan aparte porque son carisimas en
volumen. Consecuencia: se ve que alguien listo los buckets, no se ve si bajo algo.
**Exfiltracion** es justamente sacar datos de la organizacion. O sea: el agujero esta
exactamente donde mas duele, y eso es realista.

Ahora los dos comandos:

```
python main.py observable llamo-api s3:GetObject --desde 2026-03-10T00:00:00Z --hasta 2026-03-10T06:00:00Z --sujeto AKIA6WNPXQ4TZBVMH8KR
python main.py observable llamo-api cloudtrail:StopLogging --desde 2026-03-10T00:00:00Z --hasta 2026-03-10T06:00:00Z --sujeto AKIA6WNPXQ4TZBVMH8KR
```

Las dos afirmaciones tienen la misma forma -- "X **no** hizo Y" -- y veredictos opuestos:

| afirmacion | veredicto | por que |
|---|---|---|
| `NO llamo-api s3:GetObject` | `AUSENCIA-NO-CONCLUYENTE` | no hay eventos, pero no los habria habido igual |
| `NO llamo-api cloudtrail:StopLogging` | `DESMENTIDA` | hay 1 evento que la contradice |

`cloudtrail:StopLogging` es apagar el propio log de auditoria, y que aparezca es en si mismo
el dato.

Y el tercer valor, que no es un descuido: `INDETERMINADO`, para cuando **no se puede afirmar
cobertura**. Lo desconocido nunca cae del lado de "si, lo habriamos visto".

### Mirado y vacio no es sin mirar

Es la otra mitad de la misma idea. Correr:

```
python main.py situacion hallazgos_agente_windows.json
```

Un caso donde nadie miro CloudTrail y uno donde se miro y no habia nada producen **la misma
lista de hallazgos**. El primero tiene un hueco de investigacion; el segundo, una zona
descartada. La salida los separa cruzando la cobertura con la bitacora de consultas:

```
[?] cloudtrail: 'llamo-api'    SIN MIRAR
    la fuente cubre la ventana y registra esta accion, y ninguna consulta la alcanzo
```

Ese hallazgo lo produjo el agente que solo miro Windows, por eso las seis zonas dan `SIN
MIRAR`. Si la fuente **no** cubriera, no seria "sin mirar": seria el caso de `observable`.

Mencionar que este modulo tiene **dos versiones falladas en su historia** -- registraba lo
pedido en vez de lo obtenido, y despues daba por mirado el producto cartesiano de fuentes por
acciones. Las dos veces, el modulo cuya razon de ser es distinguir la ausencia fundada de la
no fundada emitia ausencias falsas. Estan contadas en el docstring de `bitacora.py`.

**Comprobacion:** preguntarle por que `AUSENCIA-NO-CONCLUYENTE` no es lo mismo que `SIN
MIRAR`. La primera es "mire y no podria haberlo visto aunque hubiera pasado"; la segunda es
"podria haberlo visto pero no mire".

## 10) Adjudicar

Aca empieza la segunda mitad del proyecto: dejar de preguntar *que paso* y empezar a preguntar
*que hago*.

Definir primero el vocabulario de respuesta, que no aparecio hasta ahora:

- **Contener** es cortarle al atacante la capacidad de seguir, sin necesariamente entender
  todavia todo lo que hizo.
- **Aislar un host** es cortarle la red a una maquina dejandola prendida.
- **Deshabilitar una cuenta** es que deje de poder autenticar.
- **Revocar una credencial** es invalidar una access key.
- **Capturar memoria** es volcar la RAM a un archivo para analizarla despues. Es **perecedero**:
  si la maquina se apaga o se reinicia, se pierde.

Todas tienen costo real: si aislas un servidor que presta servicio, el servicio se cae.

**Adjudicar** es lo que hace el motor: se le somete una accion ya elegida y contesta si la
evidencia la respaldaba. Correr los dos:

```
python main.py accion deshabilitar-cuenta "WKS-04\\soporte_it" --en 2026-03-09T22:00:00Z
python main.py accion deshabilitar-cuenta "WKS-04\\soporte_it" --en 2026-03-10T04:00:00Z
```

`INFUNDADA` y `FUNDADA`. **Lo unico que cambia es `--en`**, el instante en que se toma la
decision. La cuenta `soporte_it` no existia el dia 9 -- se crea a las 00:31 del dia 10 y
autentica a las 03:01 (`W1515`). El motor solo mira evidencia **anterior** a `--en`.

Ese es el concepto: **una decision se juzga con lo que se sabia cuando se tomo.** Adjudicar
contra evidencia posterior es juzgar con el diario del lunes, y castiga al analista por no
haber adivinado.

Notar dos detalles de la salida:

El `INFUNDADA` no dice solo "no hay evidencia", dice *"...y la fuente que lo habria registrado
cubria la ventana"*. Eso es la parte 9 enganchada aca: el motor distingue "no hay" de "no
podria saberlo".

Y al pie de las dos aparece `QUE LA VOLVERIA PREMATURA`. **`FUNDADA` no quiere decir
recomendable**: `apagar-host` sale fundada con los mismos requisitos que aislar, y apagar
destruye la memoria volatil que capturar-memoria necesitaba. Por eso cada accion arrastra su
propia condicion de falsedad en vez de un semaforo verde.

**Comprobacion:** preguntarle que pasaria si el motor mirara toda la evidencia en vez de solo
la anterior a `--en`. La respuesta: toda accion contra el atacante saldria fundada siempre,
incluso decidida antes de que el ataque ocurriera, y el veredicto dejaria de significar nada.

## 11) Recomendar

**Es el bug central del proyecto y se cuenta como historia, no como feature.**

*Adjudicar* (parte 10) es retrospectivo y **un humano ya eligio el objetivo**. Al elegirlo
aporto la sospecha. Al motor le queda comprobar si la evidencia respaldaba la accion, y ahi
una precondicion de capacidad -- "el host tuvo un acceso remoto" -- alcanza.

*Recomendar* es generativo: **nadie aporta sospecha**, entonces la precondicion tiene que
cargarla entera. La primera version no lo distinguia: recorria el inventario y filtraba por la
misma precondicion de capacidad. Resultado: proponia contener nueve cosas en una ventana
**anterior al ataque**, cuando no habia pasado nada.

La correccion es que los objetivos ya no salen del inventario, sino de **entidades senaladas
por un hallazgo**, ademas de cumplir la precondicion. Se demuestra con la falsificacion:

```
python main.py recomendacion --en 2026-03-06T00:00:00Z --desde 2026-03-02T00:00:00Z --hasta 2026-03-06T00:00:00Z
python main.py recomendacion
```

**Cero contra once.** En la ventana previa al ataque no hay hallazgos, entonces no hay
candidatos, entonces la lista es vacia -- que es la respuesta correcta.

En la salida completa senalar el campo que no existia antes de la correccion:

```
bloquear-ip 198.51.100.77
  senialado  : acceso_tras_fallos, rociado_contrasenias
  funda      : intentos fallidos desde la direccion; autenticacion exitosa desde la misma
  la descarta: Si el acceso ya es con credencial valida. Bloquear el origen no detiene a
               quien puede autenticarse desde cualquier otro.
```

`senialado` es la trazabilidad al hallazgo que puso a esa entidad en la lista.

**Como se encontro el bug**, y hay que contarlo porque es la mejor parte: lo encontro una
auditoria externa corriendo la recomendacion sobre una ventana previa al ataque. Antes de eso
el comportamiento estaba **racionalizado como leccion en un caso de test** -- o sea, el test
verificaba la excusa en vez del comportamiento correcto.

**Comprobacion:** preguntarle por que la misma precondicion alcanza para adjudicar y no para
recomendar, si es la misma condicion. La respuesta esta en quien aporta la sospecha.

## 12) El estado

```
python main.py accion aislar-host WKS-04 --registrar prueba
python main.py accion aislar-host WKS-04
python main.py respuesta
```

La primera sale `FUNDADA` y agrega `Registrada en la cronologia por 'prueba'`. La segunda sale
`INAPLICABLE: 'aislar-host' ya se aplico sobre WKS-04`. La tercera muestra el estado del
mundo: `host-aislado: WKS-04 desde 2026-03-10T04:00:00Z`.

**Ejecutar cambia el mundo, y el mundo cambiado cambia lo que se recomienda despues.** Sin
eso, la recomendacion seria una lista estatica de sugerencias que repite lo mismo para siempre.

**El estado no se guarda como estado: se deriva replayando la cronologia de decisiones.** Por
eso "¿este host esta aislado?" nunca se contesta con un booleano suelto -- se contesta con
quien lo decidio y cuando. Es la misma logica de un event log contra un campo mutable, que ya
conoce de programar.

Y la regla que la hace una herramienta y no un arbitro: **el estado lo define el acto, no el
veredicto.** Si el analista ejecuta algo que el motor declaro `INFUNDADA`, el mundo cambia
igual y queda marcado como **override**. Un adjudicador con poder de veto sobre la realidad
seria lo contrario de tener un humano decidiendo.

**Acordarse de borrar `evidencia/.decisiones.json` al terminar la demostracion**, y correr
`python main.py respuesta` de nuevo para mostrar que quedo limpio.

**Comprobacion:** preguntarle que pasaria si el motor pudiera bloquear una accion `INFUNDADA`.
La respuesta apunta a que el analista sabe cosas que no estan en los logs -- una llamada, un
aviso del proveedor -- y una herramienta que no lo deja actuar con eso queda inutilizada
justo cuando mas importa.

---

# LA PRUEBA

## 13) Medir

Definir las dos metricas antes de correr nada, sin suponerlas conocidas:

- **recall**: de todos los eventos del ataque, que fraccion encontro. Mide lo que se te
  escapa.
- **precision**: de todo lo que reporto, que fraccion era realmente del ataque. Mide cuanto
  ruido te hace.

Se pueden mover en direcciones opuestas: reportar todo da recall perfecto y precision
pesima.

Para medir hace falta saber **cual es la respuesta correcta** -- que eventos son del ataque.
Y aca esta la decision de diseno de la parte:

**La verdad no existe en disco.** Cada evento tiene una etiqueta que dice que capa lo produjo
(parte 3), pero no esta guardada en ningun archivo: **se regenera desde el seed** en el momento
de medir, y desaparece. Si viviera al lado de la evidencia, cualquiera que investigue --
persona o agente -- la abre y saca 100% sin investigar nada.

Hay una guarda: si la evidencia en disco no corresponde al seed, la medicion **se niega a
correr** en vez de comparar contra otro escenario.

Correr:

```
python main.py barrido
```

`barrido` es el **detector deterministico**: ocho reglas escritas a mano en `deteccion.py`.
Una **regla de deteccion** es una condicion sobre los eventos que, cuando se cumple, emite un
hallazgo. Es como funciona un SIEM -- el software donde una organizacion centraliza sus logs y
corre reglas sobre ellos.

Y notar la precision baja: cita ~1.260 eventos para encontrar 44. **Eso no es siempre un
defecto**: se ahoga en el escaneo de fondo de la capa `ruido-internet`, que es exactamente lo
que le pasa a una regla basada en volumen en una organizacion real.

**Comprobacion:** preguntarle por que la verdad regenerada desde el seed es mas confiable que
un archivo de respuestas, si al final es el mismo dato. La respuesta: porque un archivo se
puede leer durante la investigacion y el seed solo se usa al medir.

## 14) El escenario B

Definir el problema primero, que es un problema de metodo y no de seguridad: **si escribis las
reglas mirando un caso y despues las medis contra ese mismo caso, la medicion no dice nada.**
Es sobreajuste, y lo conoce de otros contextos.

La solucion del proyecto: hay **dos incidentes**. `A` es donde se escribieron las reglas. `B`
esta retenido -- se corre con `--escenario b` -- y **contra B nunca se tunea nada, solo se
mide**.

Correr los dos:

```
python main.py medir hallazgos_agente_cloudtrail.json hallazgos_agente_syslog.json hallazgos_agente_windows.json --union
python main.py --escenario b medir hallazgos_b_cloudtrail.json hallazgos_b_syslog.json hallazgos_b_windows.json --union
```

| | recall en A | recall en B |
|---|---|---|
| detector deterministico | 63,8% | 4,3% |
| agentes, union | 84,1% | 100% |

**El detector se derrumba y hay que explicar por que exactamente**: sus ocho reglas se apoyan,
directa o indirectamente, en que **haya intentos de autenticacion fallidos**. En B el atacante
entra con una credencial legitima y no falla nunca. Es invisible para las ocho. Encuentra 1
de 23.

Los agentes no se derrumban: sacan 100% en B. Llegaron por un punto del protocolo que dice
**comparar cada sujeto contra su propio historial, no contra el promedio**. El agente de
CloudTrail lo resumio solo: *"el caso no esta en el volumen, esta en el repertorio"* -- no
importa cuanto hizo una credencial, importa si hizo cosas que esa credencial nunca hacia.

**Ese par de numeros es el resultado del proyecto, no el primero solo.** 63,8% contra 4,3% es
la demostracion de que el detector memorizo un caso.

### Como se sabe que el agente no hizo trampa

Un **agente** aca es un modelo de lenguaje investigando el caso por CLI. Tres restricciones:

- Se lanza **desde el skill, nunca desde el codigo**. Si Python llamara a la API, la suite de
  regresion dejaria de ser reproducible y correr los tests necesitaria credencial y
  presupuesto.
- Investiga con una **lista blanca de subcomandos**, y tiene prohibido leer el generador y los
  tests -- ahi esta el plan del atacante escrito en Python.
- Escribe sus hallazgos **al DSL cerrado** de la parte 6. Lo que no entra en el DSL no se
  verifica, y lo que no se verifica no entra al caso.

Ademas la bitacora registra cada consulta: en la corrida contra B fueron 96, todas dentro de
la lista blanca, ninguna al comando que revela el caso.

**Comprobacion:** preguntarle por que no se puede simplemente escribir mas reglas mirando B
para subir el 4,3%. La respuesta: porque en el momento en que lo hacen, B deja de ser
retenido y no queda con que medir.

## 15) El codigo

Recien aca, y a proposito: con las catorce partes anteriores cada modulo se explica en una
linea porque ya se sabe que problema resuelve. Son ~4.000 lineas de Python puro, sin
dependencias.

**Generar la evidencia.**

`modelo.py` define entidades con estado -- cuentas que existen o no, sesiones con su
`LogonId`, credenciales con ventana de validez, hosts que dejan de emitir si se los aisla --
y **cada transicion emite sus lineas de log**. No se escriben logs: se escribe comportamiento,
y los logs caen como efecto.

Eso hace la contradiccion **estructuralmente imposible**: no se puede emitir un `Failed
password` para un usuario que sshd ya declaro inexistente, porque el emisor le pregunta al
objeto cuenta. Y regala gratis la etiqueta de verdad por evento (parte 13).

`evidencia/generar_evidencia.py` tiene los actores y los dos planes de atacante.

**Entender la evidencia.**

| modulo | que resuelve | parte |
|---|---|---|
| `tiempo.py` | normalizacion de cada fuente a un instante UTC | 5 |
| `eventos.py` | normalizacion y semantica publicada | 4 |
| `consulta.py` | filtrar, contar, pivotear, linea base | 2 |
| `cobertura.py` | que se recolecto y que no | 9 |

**Decidir.**

| modulo | que resuelve | parte |
|---|---|---|
| `deteccion.py` | las ocho reglas escritas a mano | 13 |
| `verificador.py` | citas y vocabulario | 7, 8 |
| `acciones.py` | catalogo, adjudicacion, recomendacion | 10, 11 |
| `decisiones.py` | cronologia y estado derivado | 12 |
| `situacion.py`, `bitacora.py` | alcance: mirado vs sin mirar | 9 |

`main.py` es la CLI y `tests.py` son 34.886 verificaciones.

### Las dos decisiones de arquitectura que conviene poder defender

**La precondicion de cada accion se declara en un DSL de cuatro campos**, no en prosa ni en una
tabla aparte. Asi el veredicto no mide si el analista adivino lo que pensaba el autor: mide si
la evidencia lo respaldaba. Se ve abriendo `CATALOGO` en `acciones.py`.

**Los tests barren el producto completo derivado de las declaraciones del codigo, nunca casos
elegidos a mano.** Una tabla escrita al lado del test elige justo los casos que no rompen, y
pasa en verde mientras el defecto sigue ahi -- que es exactamente como sobrevivio el bug de la
parte 11. Es la leccion que el proyecto anterior pago con cinco auditorias.

**Comprobacion final:** pedirle que recorra el lazo completo sin mirar el skill:

```
barrido o agentes -> hallazgos con cita -> verificacion -> recomendacion
       -> elige una -> se ejecuta y se registra -> el estado cambia
       -> la recomendacion siguiente es distinta
```

Si puede contar esas seis flechas y decir que modulo hace cada una, el proyecto esta
entendido. **La ultima flecha es la que costo y la que lo separa de una lista de sugerencias.**
