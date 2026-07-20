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
│   7) El motor                 citas, cobertura, adjudicar, recomendar    │
│   8) El estado                ejecutar tiene que cambiar el mundo        │
│                                                                          │
│  EL CODIGO                                                               │
│   9) El codigo                los modulos y como encajan                 │
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

Estos numeros salen de correr `python main.py verdad --si`:

```
ETIQUETAS
------------------------------------------------------------------------------
    4512  (69.1%)  normal
    1271  (19.5%)  ruido-internet
     648  ( 9.9%)  sospechoso-no-incidente
      69  ( 1.1%)  ataque
      32  ( 0.5%)  admin-legitimo
```

`verdad` esta deliberadamente escondido detras de una confirmacion (`--si`) y prohibido para
cualquier agente que este investigando (regla dura en `fir-lab`): imprime la narrativa
completa del incidente, es el solucionario. Ese candado no aplica ahora -- vos escribiste
este codigo, no estas investigando el caso a ciegas -- pero conviene saber que existe y por
que, porque en la parte 6 vuelve a aparecer.

Y por que el comando no lee un archivo con las respuestas guardadas: las etiquetas se
**reconstruyen desde la semilla del generador** cada vez que se corre, no viven en ningun
lado. Si vivieran al lado de la evidencia, quien investiga -- persona o agente -- las tendria
a un `Read` de distancia.

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

El detector automatico se corre asi:

```
python main.py barrido
```
```
BARRIDO DETERMINISTICO  (27 hallazgos)
------------------------------------------------------------------------------

[ALTA] acceso_tras_fallos
  web-03:ubuntu autentico con exito desde 198.51.100.77, direccion que acumulaba 18 fallos en las 6 horas previas.
  cita: L1025, L1001, L1002, L1007, L1008, L1009, L1010, L1011 (+11)
  no prueba: La correlacion es por direccion IP, que no identifica un equipo ni una persona: NAT, proxies y direcciones reasignadas producen la misma coincidencia.
```

`barrido` son **ocho reglas escritas a mano** en `deteccion.py`. Una **regla de deteccion** es
una condicion sobre los eventos que, cuando se cumple, emite un hallazgo con la misma forma
que acabas de ver arriba -- afirmacion mas cita. Es como funciona un SIEM: el software donde
una organizacion centraliza sus logs y corre reglas sobre ellos. Notar tambien el campo
`no prueba`: cada regla declara de antemano que NO demuestra, para no vender una correlacion
como una certeza.

**La frase que resume el motor entero**, y conviene decirla textual porque las partes
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

## 7) El motor

Es una sola parte con cinco piezas, todas la misma operacion de la parte 6 (agarrar una
afirmacion, agarrar lo que cita, decidir si sostiene) aplicada a cinco situaciones distintas:
verificar una cita, respetar un vocabulario cerrado, leer una ausencia, adjudicar una accion
ya tomada, y generar una recomendacion nueva. Van en orden porque cada una necesita la
anterior.

### Verificar

Correr `python main.py verificar hallazgos_prueba.json`. Son 11 hallazgos, 2 admitidos. Ese
archivo **no son hallazgos del caso**: es un banco de prueba escrito a mano donde casi todo
esta mal a proposito, uno por cada forma de estar mal (su `_nota` lo dice).

Tres familias de rechazo. Dos triviales: **cita inexistente** (`C8888`, `W9999` no existen en
la evidencia) y **sin cita** (un hallazgo sin respaldo no es verificable).

La que importa es **`CITA-NO-SOSTIENE`**: cita eventos **reales** y afirma algo que esos
eventos no dicen. Tres variantes, las tres con `W1497` de por medio:

```
mlopez autentico-remoto WKS-04       -> W1497: el sujeto del evento es 'WKS-04\ecarrizo'
ecarrizo ejecuto-proceso powershell  -> W1497: la accion del evento es 'autentico-remoto'
ecarrizo autentico-remoto (dia 5)    -> W1497: el evento cae fuera de la ventana
```

Sujeto, accion, ventana: los tres campos que se pueden falsear manteniendo un ID valido al
lado. **Las tres se ven impecables a simple vista**, y ese es el punto: es el modo de falla
real de un modelo de lenguaje. Inventar identificadores casi no lo hace. Citar bien y concluir
mal, todo el tiempo. Si el verificador no atrapa esas, no sirve para nada.

El hallazgo que sale `VERIFICADO: 1 de 2 citas sostienen` muestra que alcanza con una cita
buena: la verificacion no es binaria por hallazgo, es por cita.

### Vocabulario cerrado

Misma salida de arriba, los tres hallazgos con `FUERA-DE-VOCABULARIO`:

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

Tres razones distintas: `el atacante` no es observable (un log registra que `ecarrizo`
autentico, no **quien** la uso -- el salto de cuenta a persona es atribucion, y ninguna cita
podria respaldarla). `movimiento-lateral` no es un evento (es una lectura de varios eventos
juntos, valida como conclusion, no como afirmacion verificable). `descargo-archivos`
simplemente no esta en las diez acciones validas -- error de tipos, no de epistemologia.

**La regla de diseno:** el vocabulario es cerrado, entonces lo que no se puede verificar no se
puede ni siquiera escribir. La restriccion esta en la entrada, no en la salida.

### Cobertura

Correr `python main.py cobertura`. Esta pieza contesta lo que quedo colgando desde la parte 1:
**que significa no haber encontrado algo.** Dos cosas incompatibles: *no paso* o *no lo puedo
saber*, segun si la fuente que lo habria registrado cubria la ventana.

Las `CARENCIAS DE AUDITORIA` son agujeros **declarados de antemano** -- por ejemplo, CloudTrail
registra que alguien listo un bucket de S3 pero no si descargo un archivo de adentro (los data
events se activan aparte, son carisimos en volumen). El agujero esta exactamente donde mas
duele, y eso es realista.

```
python main.py observable llamo-api s3:GetObject --desde 2026-03-10T00:00:00Z --hasta 2026-03-10T06:00:00Z --sujeto AKIA6WNPXQ4TZBVMH8KR
python main.py observable llamo-api cloudtrail:StopLogging --desde 2026-03-10T00:00:00Z --hasta 2026-03-10T06:00:00Z --sujeto AKIA6WNPXQ4TZBVMH8KR
```

Misma forma -- "X **no** hizo Y" -- veredictos opuestos: `NO llamo-api s3:GetObject` sale
`AUSENCIA-NO-CONCLUYENTE` (no hay eventos, pero no los habria habido igual, por la carencia de
arriba); `NO llamo-api cloudtrail:StopLogging` sale `DESMENTIDA` (hay 1 evento que la
contradice -- apagar el propio log de auditoria, y que aparezca es en si mismo el dato). El
tercer valor, `INDETERMINADO`, es para cuando no se puede afirmar cobertura: lo desconocido
nunca cae del lado de "si, lo habriamos visto".

La otra mitad de la misma idea, con `python main.py situacion hallazgos_agente_windows.json`:
un caso donde nadie miro CloudTrail y uno donde se miro y no habia nada producen la misma
lista de hallazgos. La salida los separa cruzando cobertura con la bitacora de consultas:

```
[?] cloudtrail: 'llamo-api'    SIN MIRAR
    la fuente cubre la ventana y registra esta accion, y ninguna consulta la alcanzo
```

`SIN MIRAR` es un hueco de investigacion; si la fuente hubiera sido consultada y no hubiera
dado nada, seria `MIRADO Y VACIO` -- una zona descartada, no un hueco. Este modulo tiene dos
versiones falladas en su historia (registraba lo pedido en vez de lo obtenido, y despues daba
por mirado el producto cartesiano de fuentes por accion) -- contadas en el docstring de
`bitacora.py`.

### Adjudicar

Aca arranca la segunda mitad del proyecto: dejar de preguntar *que paso* y empezar a preguntar
*que hago*. Vocabulario de respuesta nuevo: **contener** es cortarle al atacante la capacidad
de seguir; **aislar un host** es cortarle la red dejandolo prendido; **deshabilitar una
cuenta** es que deje de autenticar; **revocar una credencial** es invalidar una access key;
**capturar memoria** es volcar la RAM, y es **perecedero** -- si la maquina se apaga, se
pierde. Todas tienen costo real.

**Adjudicar** somete una accion ya elegida y contesta si la evidencia la respaldaba:

```
python main.py accion deshabilitar-cuenta "WKS-04\\soporte_it" --en 2026-03-09T22:00:00Z
python main.py accion deshabilitar-cuenta "WKS-04\\soporte_it" --en 2026-03-10T04:00:00Z
```

`INFUNDADA` y `FUNDADA`. Lo unico que cambia es `--en`, el instante en que se toma la
decision -- el motor solo mira evidencia **anterior** a ese instante. Adjudicar contra
evidencia posterior es juzgar con el diario del lunes.

El `INFUNDADA` no dice solo "no hay evidencia", dice *"...y la fuente que lo habria
registrado cubria la ventana"* -- la cobertura de arriba, enganchada aca: el motor distingue
"no hay" de "no podria saberlo". Y al pie aparece `QUE LA VOLVERIA PREMATURA`: `FUNDADA` no
quiere decir recomendable -- `apagar-host` sale fundada con los mismos requisitos que aislar,
y apagar destruye la memoria volatil que capturar-memoria necesitaba.

### Recomendar

**El bug central del proyecto**, y se cuenta como historia. Adjudicar es retrospectivo y **un
humano ya eligio el objetivo** -- al elegirlo aporto la sospecha, y al motor le alcanza con
comprobar una precondicion de capacidad. Recomendar es generativo: **nadie aporta sospecha**,
entonces la precondicion tendria que cargarla entera. La primera version no lo distinguia:
recorria el inventario entero y proponia contener nueve cosas en una ventana **anterior al
ataque**, cuando no habia pasado nada.

La correccion: los objetivos salen de **entidades senaladas por un hallazgo**, ademas de
cumplir la precondicion.

```
python main.py recomendacion --en 2026-03-06T00:00:00Z --desde 2026-03-02T00:00:00Z --hasta 2026-03-06T00:00:00Z
python main.py recomendacion
```

**Cero contra once.** Sin hallazgos previos al ataque, no hay candidatos -- lista vacia, la
respuesta correcta. En la salida completa, el campo que no existia antes de la correccion:

```
bloquear-ip 198.51.100.77
  senialado  : acceso_tras_fallos, rociado_contrasenias
  funda      : intentos fallidos desde la direccion; autenticacion exitosa desde la misma
  la descarta: Si el acceso ya es con credencial valida. Bloquear el origen no detiene a
               quien puede autenticarse desde cualquier otro.
```

`senialado` es la trazabilidad al hallazgo que puso a esa entidad en la lista. Lo encontro una
auditoria externa corriendo la recomendacion sobre una ventana previa al ataque -- antes de eso
el comportamiento estaba racionalizado como leccion en un caso de test, en vez de corregido.

**Comprobacion:** por que la misma precondicion de capacidad alcanza para adjudicar y no para
recomendar, si es la misma condicion. La respuesta esta en quien aporta la sospecha: en
adjudicar la aporta el humano al elegir el objetivo; en recomendar no la aporta nadie, y por
eso el hallazgo tiene que hacer ese trabajo.

## 8) El estado

```
python main.py accion aislar-host WKS-04 --registrar prueba
python main.py accion aislar-host WKS-04
python main.py respuesta
```

La primera sale `FUNDADA` y agrega `Registrada en la cronologia por 'prueba'` -- y despues un
bloque `CONECTOR` con un ticket (`edr  ticket EDR-395472  [ok]`). Nada de eso llama a un
sistema real: es un conector simulado (`conectores.py`) que devuelve una respuesta con la
forma de una real, para que quede registrado que la decision no solo se adjudico, se disparo.
La segunda sale `INAPLICABLE: 'aislar-host' ya se aplico sobre WKS-04`. La tercera muestra el
estado del mundo: `host-aislado: WKS-04 desde 2026-03-10T04:00:00Z`.

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

# EL CODIGO

## 9) El codigo

Recien aca, y a proposito: con las ocho partes anteriores cada modulo se explica en una
linea porque ya se sabe que problema resuelve. Son ~4.000 lineas de Python puro, sin
dependencias.

**Generar la evidencia.**

`modelo.py` define entidades con estado -- cuentas que existen o no, sesiones con su
`LogonId`, credenciales con ventana de validez, hosts que dejan de emitir si se los aisla --
y **cada transicion emite sus lineas de log**. No se escriben logs: se escribe comportamiento,
y los logs caen como efecto.

Eso hace la contradiccion **estructuralmente imposible**: no se puede emitir un `Failed
password` para un usuario que sshd ya declaro inexistente, porque el emisor le pregunta al
objeto cuenta. Y regala gratis la etiqueta de verdad por evento (parte 3).

`evidencia/generar_evidencia.py` tiene los actores y el plan del atacante.

**Entender la evidencia.**

| modulo | que resuelve | parte |
|---|---|---|
| `tiempo.py` | normalizacion de cada fuente a un instante UTC | 5 |
| `eventos.py` | normalizacion y semantica publicada | 4 |
| `consulta.py` | filtrar, contar, pivotear, linea base | 2 |
| `cobertura.py` | que se recolecto y que no | 7 |

**Decidir.**

| modulo | que resuelve | parte |
|---|---|---|
| `deteccion.py` | las ocho reglas escritas a mano (`barrido`) | 6 |
| `verificador.py` | citas y vocabulario | 7 |
| `acciones.py` | catalogo, adjudicacion, recomendacion | 7 |
| `decisiones.py` | cronologia y estado derivado | 8 |
| `conectores.py` | conectores simulados que dispara una decision registrada | 8 |
| `situacion.py`, `bitacora.py` | alcance: mirado vs sin mirar | 7 |

`main.py` es la CLI y `tests.py` son 34.886 verificaciones.

### Las dos decisiones de arquitectura que conviene poder defender

**La precondicion de cada accion se declara en un DSL de cuatro campos**, no en prosa ni en una
tabla aparte. Asi el veredicto no mide si el analista adivino lo que pensaba el autor: mide si
la evidencia lo respaldaba. Se ve abriendo `CATALOGO` en `acciones.py`.

**Los tests barren el producto completo derivado de las declaraciones del codigo, nunca casos
elegidos a mano.** Una tabla escrita al lado del test elige justo los casos que no rompen, y
pasa en verde mientras el defecto sigue ahi -- que es exactamente como sobrevivio el bug de
Recomendar (parte 7). Es la leccion que el proyecto anterior pago con cinco auditorias.

**Comprobacion final:** pedirle que recorra el lazo completo sin mirar el skill:

```
barrido o agentes -> hallazgos con cita -> verificacion -> recomendacion
       -> elige una -> se ejecuta y se registra -> el estado cambia
       -> la recomendacion siguiente es distinta
```

Si puede contar esas seis flechas y decir que modulo hace cada una, el proyecto esta
entendido. **La ultima flecha es la que costo y la que lo separa de una lista de sugerencias.**
