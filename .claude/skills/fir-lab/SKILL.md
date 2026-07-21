---
name: fir-lab
description: Opera el laboratorio FIR del caso INC-2026-0051 - barrido con detector y agentes, consultar los 6.500 eventos, linea base, situacion y cobertura, someter acciones de respuesta al motor, recomendacion con su condicion de falsedad, cronologia de decisiones y los ocho casos. Usar cuando se pida investigar el escenario, consultar la evidencia, buscar el incidente, verificar hallazgos, proponer o evaluar acciones de respuesta, o trabajar con el proyecto FIR.
---

# Lab FIR

Consola de operacion. El proyecto vive en `C:\Users\Ezela\Desktop\FIR` y los comandos se
corren parados ahi.

Este skill **no razona sobre la evidencia: la consulta**. Cuando haya que saber si algo se
sostiene, correr el comando y leer su salida. Nunca deducir un resultado de cabeza, nunca
afirmarlo sin haberlo corrido, y nunca completar con conocimiento general de seguridad lo
que la evidencia no dijo.

## Al entrar

1. Correr `python main.py estado`.
2. Correr `python main.py respuesta` y ver si ya hay acciones aplicadas.
3. Mostrar el menu con el caso, el conteo y las acciones aplicadas en la cabecera.

Si hay acciones aplicadas y no fue el usuario quien las tomo en esta sesion, decirlo antes
de cualquier otra cosa: el estado de la respuesta condiciona todo lo que el motor va a
recomendar despues.

```
╭──────────────────────────────────────────────────────────────────────────╮
│   \ | /                                                                  │
│  ── * ──   LAB FIR · INC-2026-0051 (BancoXYZ)                            │
│   / | \    10 dias · 3 fuentes · 6.532 eventos · 0 acciones aplicadas    │
├──────────────────────────────────────────────────────────────────────────┤
│  1) Barrido                                                              │
│  2) Consultar                                                            │
│  3) Linea base                                                           │
│  4) Situacion                                                            │
│  5) Respuesta                                                            │
│  6) Cronologia                                                           │
│  7) Regresion                                                            │
│  8) Otro caso                                                            │
│  9) Borrar hallazgos                                                     │
│                                                                          │
│  0) Salir                                                                │
╰──────────────────────────────────────────────────────────────────────────╯
```

**Copiar el cuadro literal, sin re-dibujarlo.** Todas las lineas miden 76 caracteres; los
unicos campos que cambian son el caso, el conteo y las acciones aplicadas, y hay que
reemplazarlos respetando el ancho. El asterisco va en ASCII a proposito: los glifos tipo
`✳` se renderizan con ancho variable y descuadran el marco.

**Las opciones 1 a 8 estan construidas sobre comandos**, con una salvedad: la 4.4 (alcance
como hechos, indicios y desconocidos) existe via `situacion` y necesita un archivo de
hallazgos como entrada, asi que depende de haber corrido antes la 1.2 o el detector. La
opcion **9 (borrar hallazgos)** no es un comando del proyecto: es housekeeping sobre los
`.json` del directorio -- ver su seccion al final.

**Nunca simular una recomendacion ni un veredicto de accion.** Si un comando falla o falta
un dato, decirlo. Producir esas salidas escribiendo prosa convincente es exactamente el modo
de falla que el laboratorio existe para medir.

Aceptar tanto el numero como la intencion en lenguaje natural.

## Navegacion

**Una opcion del menu principal (1 a 9) SIEMPRE abre primero el submenu de esa seccion.
Nunca dispara un comando directo.** El menu principal elige seccion; el comando se corre
recien cuando el usuario elige una opcion del submenu (`1.1`, `4.3`, etc.). Tocar `1` abre
el submenu de Barrido y ahi se espera `1.1`/`1.2`/`1.3` -- no se corre el detector de una.
Saltarse ese paso, aunque la seccion tenga una opcion "obvia", es un error de navegacion:
el usuario perdio la posibilidad de elegir. La unica excepcion es `0) Salir`.

Todo submenu termina con `0) Volver al menu anterior`. Despues de ejecutar una accion y
presentar el resultado, volver a ofrecer el submenu donde estaba el usuario.

Entre la salida de un comando y el cuadro siguiente va una regla horizontal (`---`) y una
linea en blanco.

**Cualquier punto de decision con dos o mas opciones se presenta como una caja numerada**,
igual que los menus fijos, con `0)` para volver o cancelar. Nunca como pregunta en prosa del
tipo "¿queres X o volvemos?" -- si el resto de la navegacion es "numero + caja", una
pregunta suelta en texto rompe el patron.

**Los rotulos de los menus van en lenguaje llano, no en la jerga tecnica.** Se describe que
hace cada opcion en una frase corta y directa; la precision tecnica vive en el cuerpo de
cada seccion y en la salida de los comandos, no en el rotulo del menu.

**El rotulo se explica solo: nada de aclaracion despues de dos puntos, ni columna de
descripcion.** No `Abrir un evento: normalizado, que significa y crudo`, sino `Abrir un
evento`. **El menu principal tampoco lleva descripcion al lado de cada opcion**: es
`1) Barrido`, no `1) Barrido   buscar el incidente...`. Si el nombre de la opcion ya dice que
hace, todo lo que le cuelga al lado es ruido. El detalle de que devuelve cada opcion vive en
el cuerpo de su seccion, no en el rotulo.

## Que devuelve cada opcion

**El usuario NO ve la salida de las tool calls.** Toda salida hay que **pegarla en la
respuesta**, en un bloque de codigo, textual y completa. Correr un comando y no transcribir
el resultado deja al usuario con la pantalla vacia.

**Datos, no prosa.** Una opcion devuelve la salida del comando y despues el submenu.

- **No** interpretar el resultado en parrafos.
- **No** seniala "lo interesante", ni anticipar hallazgos.
- **No** completar con conocimiento propio de seguridad lo que la salida no dice.

**El skill no conoce la verdad del caso y no debe actuar como si la conociera.** Prohibido
mencionar el incidente, su dia, el atacante, "el ataque", o sugerir que una ventana, un
filtro o una accion "lo agarra" / "lo cubre" / "se queda corta". Eso es filtrar el
solucionario disfrazado de ayuda: convierte al operador en alguien a quien le soplan la
respuesta, y arruina la medicion. Si una ventana no devuelve nada, se dice "nada nuevo en la
ventana" y se ofrece el menu de vuelta -- nunca "para agarrar el incidente ampliala". El
analista decide cuanto mirar; el skill le da la herramienta, no la pista. Vale para toda
opcion, no solo para la linea base.

La explicacion se da **solo si el usuario la pide**. El que lee la salida es el analista.

Excepcion: los veredictos (`AUSENCIA-DEMOSTRADA`, `CITA-NO-SOSTIENE`, la observabilidad
`SI`/`NO`/`INDETERMINADO`) y sus motivos se citan textuales, porque son el dato.

---

## 1) Barrido

```
╭──────────────────────────────────────────────────────────────────────────╮
│  1) BARRIDO   ·  buscar el incidente                                     │
├──────────────────────────────────────────────────────────────────────────┤
│  1.1)  Correr el detector automatico (8 reglas escritas a mano)          │
│  1.2)  Mandar agentes a investigar por su cuenta                         │
│  1.3)  Revisar un archivo de hallazgos que ya tengas                     │
│                                                                          │
│  0)   Volver al menu anterior                                            │
╰──────────────────────────────────────────────────────────────────────────╯
```

| Opcion | Comando |
|---|---|
| 1.1 | `python main.py barrido` |
| 1.3 | `python main.py verificar <archivo.json>` |

### 1.1 — El detector: primero que busca, despues que encontro

**Antes de correr `barrido` y pegar sus resultados, listar las ocho reglas que el detector
tiene escritas.** El usuario tiene que entender que esta buscando el detector antes de leer
el ruido que devuelve, si no la salida parece una pila de hallazgos sin criterio. La lista
es fija -- son las ocho de `deteccion.py` (`REGLAS`), en ese orden -- y se muestra tal cual:

```
El detector automatico corre 8 reglas fijas, siempre las mismas:

  1. enumeracion_usuarios     fallos contra cuentas que NO existen (probar una
                              lista de nombres traida de afuera)
  2. rociado_contrasenias     pocas contrasenias contra MUCHAS cuentas validas
                              desde un mismo origen (password spraying)
  3. acceso_tras_fallos       un login exitoso desde una IP que venia sumando
                              fallos (el intento que se convierte en acceso)
  4. credencial_creada        se creo una access key nueva en AWS
  5. credencial_origen_nuevo  una credencial usada desde una red (/24) que nunca
                              habia usado antes
  6. operaciones_denegadas    varias operaciones rechazadas por permisos con la
                              misma credencial (tanteo de lo que se puede hacer)
  7. cuenta_local_creada      se creo una cuenta local nueva (persistencia)
  8. reconocimiento_local     varios binarios de reconocimiento (whoami, net,
                              nltest...) en una misma sesion y en minutos
```

Esa lista es descripcion de la herramienta, no interpretacion de la evidencia: es fija y no
depende del caso, por eso se puede tener escrita. Lo que sale del comando, no.

**Los resultados se presentan agrupados por severidad y numerados corridos.** No el bloque
largo de cada hallazgo con `cita` y `no prueba` completos -- son 27 y no se pueden escanear
asi. Encabezado por nivel (`── ALTA (N) ──`, `── MEDIA (N) ──`), y debajo una linea corta
por hallazgo con numeracion continua entre grupos, para poder referenciarla despues:

```
── ALTA (8) ──────────────────────────────────────────────
 1) web-03:ubuntu entro tras 18 fallos desde 198.51.100.77
 ...
── MEDIA (19) ─────────────────────────────────────────────
 9) esa credencial creo una access key nueva
 ...
```

Cada linea corta sale **solo** de lo que devolvio el comando -- resumir no es inventar, y no
se agrega ni una palabra de contexto de seguridad que la salida no traiga. El detalle
completo de un hallazgo (la `cita` entera y el `no prueba`) se da textual si el usuario pide
profundizar en uno puntual.

**Despues de listar los hallazgos, ofrecer el paso siguiente como menu**, no cerrar en el
submenu de Barrido a secas. El detector da leads, no conclusiones; el movimiento natural es
picar en el que interesa:

```
╭──────────────────────────────────────────────────────────────────────────╮
│  ¿Y ahora?                                                               │
├──────────────────────────────────────────────────────────────────────────┤
│  1) Mandar un agente a investigar a fondo un hallazgo puntual            │
│  0) Volver al menu de Barrido                                            │
╰──────────────────────────────────────────────────────────────────────────╯
```

Si elige 1, se arma un encargo de agente (el de 1.2, con toda su lista blanca y sus vetos)
**enfocado en el indicador del hallazgo elegido** -- la IP, la cuenta o la credencial que el
detector senialo. Apuntar al lead no es copiar la respuesta: el detector no dice si es
ataque, solo dice donde mirar.

### 1.2 — Como se lanzan los agentes

Se lanzan **desde aca**, con la herramienta de subagentes. Nunca desde el codigo del
proyecto: si Python llamara a la API, el catalogo de casos dejaria de ser reproducible y se
perderia la suite de regresion.

**Reglas duras, sin excepcion:**

- El agente trabaja **solo** con los subcomandos de consulta de `python main.py`:
  `estado`, `cobertura`, `timeline`, `contar`, `evento`, `entidad`, `base`, `observable`.
  **Es una lista blanca, no "todo lo que empiece con main.py".**
- **`python main.py verdad` esta prohibido explicitamente.** Imprime la narrativa completa
  del incidente: es el solucionario. Decir "solo main.py" sin esta linea autoriza el
  comando que entrega las respuestas, y cualquier medicion obtenida asi no vale nada.
- **Tiene prohibido leer `evidencia/generar_evidencia.py`, `modelo.py` y `tests.py`.** Ahi
  esta el plan del atacante escrito en Python. Un agente que los lea produce un informe
  perfecto sin haber investigado, y la medicion pasa a no significar nada. Conviene ademas
  confirmar despues que archivos abrio.
- Cada afirmacion va con **cita a identificadores concretos** y expresada en el DSL de
  cuatro campos (`sujeto`, `accion`, `objeto`, `desde`, `hasta`). Lo que no entra en el DSL
  no se puede verificar, y lo que no se puede verificar no entra al caso.
- El agente **escribe sus hallazgos a un archivo JSON** con el formato de
  `hallazgos_prueba.json`. No los reporta en prosa.

Conviene lanzar **varios en paralelo con encargos distintos** -- uno por fuente, o uno por
hilo. Un agente solo se ancla en lo primero que encuentra y despues lo confirma.

### El protocolo que va en el encargo

Es **metodo**, y por eso vale: no nombra ninguna IP, ninguna cuenta, ninguna fecha ni ningun
hallazgo del escenario. Si nombrara alguno, el agente no estaria investigando -- estaria
copiando.

1. **Verificar integridad antes de mirar nada.**
2. **Leer la cobertura antes de interpretar cualquier ausencia.** No haber encontrado algo
   puede significar que no paso o que no se estaba mirando.
3. **Establecer que es normal ACA antes de decidir que es raro.**
4. **Buscar lo categoricamente nuevo, no lo voluminoso.** Lo que mas aparece suele ser ruido
   de fondo o automatizacion.
5. **Comparar cada sujeto contra su propio historial**, no contra el promedio del entorno.
   Un cambio de repertorio importa aunque el volumen y el origen no cambien.
6. **Pivotear sobre el indicador, no sobre la alerta.** Encontrado un dato, buscar todo lo
   que lo menciona en las tres fuentes.
7. **Seguir la identidad cuando cruza de dominio**, y no darla por la misma. La homonimia es
   una pista, no un hecho.
8. **Para cada hallazgo, mirar antes y despues.** Lo previo da el vector de entrada; lo
   posterior da el alcance y la persistencia.
9. **Descartar los falsos positivos con evidencia, no por criterio.** La actividad
   administrativa legitima y los errores de configuracion producen firmas identicas a las de
   un ataque.
10. **Antes de cerrar, decir que NO se miro.** Que fuente, que ventana, que pregunta quedo
    sin responder.

### La plantilla del encargo

**Pasarla completa.** El protocolo de arriba es el metodo; esto es lo que hace que el agente
produzca algo verificable. Un encargo sin la lista de comandos y sin el esquema del DSL
devuelve prosa con citas al pie, que no entra al motor.

```
Sos analista de seguridad. Investiga el caso <CASO> en C:\Users\Ezela\Desktop\FIR,
enfocado en <FUENTE O HILO>. Trabajas parado en ese directorio.

REGLAS DURAS
1. Tu unica herramienta son estos subcomandos: estado, cobertura, timeline, contar,
   evento, entidad, base, observable. No leas los JSON de evidencia/ a mano.
2. PROHIBIDO abrir evidencia/generar_evidencia.py, modelo.py, tests.py, casos.py y
   deteccion.py. PROHIBIDO correr `python main.py verdad`. Ahi esta la respuesta: si los
   abris, tu informe no vale nada.
3. Cada afirmacion va con cita a identificadores concretos de evento.

<pegar aca el protocolo de diez puntos>

ENTREGABLE
Escribi <RUTA>.json:
{"hallazgos": [{"regla": "...", "severidad": "ALTA|MEDIA|BAJA",
  "afirmacion": {"sujeto": "...", "accion": "...", "objeto": "...",
                 "desde": "...Z", "hasta": "...Z"},
  "resumen": "una frase", "cita": ["W1497"], "no_prueba": "que NO prueba"}]}

`accion` solo puede ser: autentico-remoto, autentico-local, autentico-red,
fallo-autenticacion, fallo-usuario-inexistente, cerro-sesion, ejecuto-proceso,
creo-cuenta, ejecuto-comando, llamo-api.

El sujeto lleva su dominio (WKS-04\nombre, web-03:nombre, AKIA...). NO uses "el
atacante" ni acciones como "movimiento-lateral": el motor las rechaza y con razon.

Un hallazgo por hecho concreto, y CITA TODOS los eventos que lo sostienen, no un
ejemplo.

Al terminar, deci que NO miraste.
```

**La ultima linea del entregable no es cortesia.** Sin ella el agente cita un ejemplo por
hallazgo en vez de todos los eventos que lo sostienen, y nadie se entera de cuanto quedo
afuera: el verificador comprueba lo que se afirmo, nunca lo que se callo.

### Al lanzar y al terminar: que se le dice al usuario

**Al lanzar, no recitar la plomeria del encargo.** La lista blanca, los vetos, el protocolo
de diez pasos y el esquema del DSL son instrucciones para el agente, no informacion para el
usuario. Basta con una linea de que se le encargo y sobre que hilo. Enumerar todas las
reglas que lleva el encargo es ruido: el usuario quiere saber que se investiga, no como esta
instrumentado.

**Al terminar, decir SIEMPRE el archivo de hallazgos que genero**, con su ruta y su nombre,
y cuantos hallazgos por severidad. Ese archivo es lo que despues alimenta al verificador
(1.3) y a la recomendacion (5.4 con `--hallazgos`); sin su nombre el usuario no puede seguir
el circuito. Es el dato mas importante del cierre, no un detalle.

## 2) Consultar

```
╭──────────────────────────────────────────────────────────────────────────╮
│  2) CONSULTAR   ·  mirar la evidencia de cerca                           │
├──────────────────────────────────────────────────────────────────────────┤
│  2.1)  Ver el timeline                                                   │
│  2.2)  Abrir un evento                                                   │
│  2.3)  Seguir una entidad                                                │
│  2.4)  Contar y agrupar                                                  │
│                                                                          │
│  0)   Volver al menu anterior                                            │
╰──────────────────────────────────────────────────────────────────────────╯
```

| Opcion | Comando |
|---|---|
| 2.1 | `python main.py timeline [--desde T] [--hasta T] [--fuente F] [--sujeto S] [--accion A] [--ip I] [--texto X]` |
| 2.2 | `python main.py evento <ID>` |
| 2.3 | `python main.py entidad <indicador>` |
| 2.4 | `python main.py contar --por <campo>` (+ los mismos filtros) |

Identificadores: `W####` (windows), `C####` (cloudtrail), `L####` (syslog).

Campos de `contar`: `fuente`, `accion`, `sujeto`, `objeto`, `ip`, `hora`, `dia`, `region`,
`error`, `logon_type`, `substatus`.

`evento` emite `EVENTO`, `ATRIBUTOS`, `SEMANTICA` (solo Windows) y `REGISTRO CRUDO`. La
seccion `SEMANTICA` sale del catalogo de `eventos.py`, que es la capa contrastable contra
documentacion publicada: pegarla textual, sin ampliarla.

### 2.2 y 2.3 arrancan con un menu, no pidiendo el dato en frio

Estas dos opciones necesitan un identificador (un ID de evento, un indicador de entidad).
**No arrancar preguntando "¿que ID?" a secas: ofrecer primero un menu de opciones.** Pedir
el dato pelado obliga al usuario a saberlo de memoria; el menu lo deja elegir.

**2.3 (seguir una entidad) — menu por tipo, despues valores reales.** Primero un menu con
los tipos de indicador (IP, cuenta de Windows, credencial AWS, host). Elegido el tipo,
mostrar los valores que **de verdad aparecen** en la evidencia, sacados con `contar --por`
(`--por ip`, `--por sujeto`), como menu numerado -- y una opcion para escribir uno a mano.
Los valores salen del comando, no de una lista escrita a mano: nunca inventar un indicador
ni adelantar cual es "el del ataque".

```
╭──────────────────────────────────────────────────────────────────────────╮
│  2.3) SEGUIR UNA ENTIDAD   ·  ¿que tipo?                                 │
├──────────────────────────────────────────────────────────────────────────┤
│  1) Una IP                                                               │
│  2) Una cuenta de Windows                                                │
│  3) Una credencial de AWS (AKIA...)                                      │
│  4) Un host                                                              │
│  5) Escribir el indicador a mano                                         │
│                                                                          │
│  0) Volver al menu de Consultar                                          │
╰──────────────────────────────────────────────────────────────────────────╯
```

**2.2 (abrir un evento) — menu por fuente, y ofrecer los IDs ya vistos.** Un evento se pide
por ID (`W####`/`C####`/`L####`), y no se pueden listar los 6.532. El menu elige fuente, y
si en la sesion ya aparecieron IDs (en un barrido, un timeline, una entidad), ofrecer esos
como atajo antes de pedir que escriba uno. Nunca fabricar un ID que no se haya visto.

```
╭──────────────────────────────────────────────────────────────────────────╮
│  2.2) ABRIR UN EVENTO   ·  ¿de que fuente?                               │
├──────────────────────────────────────────────────────────────────────────┤
│  1) Windows      (W####)                                                 │
│  2) CloudTrail   (C####)                                                 │
│  3) Syslog       (L####)                                                 │
│  4) Un ID que ya aparecio en pantalla                                    │
│                                                                          │
│  0) Volver al menu de Consultar                                          │
╰──────────────────────────────────────────────────────────────────────────╯
```

## 3) Linea base

```
╭──────────────────────────────────────────────────────────────────────────╮
│  3) LINEA BASE   ·  que es nuevo respecto de antes                       │
├──────────────────────────────────────────────────────────────────────────┤
│  1) La ultima hora                                                       │
│  2) Las ultimas 12 horas                                                 │
│  3) El ultimo dia                                                        │
│  4) Los ultimos 7 dias                                                   │
│  5) Los ultimos 30 dias                                                  │
│  6) Una ventana a medida                                                 │
│                                                                          │
│  0) Volver al menu anterior                                              │
╰──────────────────────────────────────────────────────────────────────────╯
```

**La opcion 3 no tiene sub-opciones conceptuales: ofrece ventanas de tiempo y corre.** El
usuario elige cuanto para atras mirar (ultima hora, 12 h, 1 dia, 7 dias, 30 dias, o a
medida) y se corre `base` sobre esa ventana. No preguntar `--desde/--hasta` en frio: el menu
de ventanas es la interfaz.

**Las ventanas se anclan al punto de congelamiento del caso, no a la fecha real de hoy.** El
"ahora" del analista es `entrada` de `python main.py estado` (para el caso principal,
`2026-03-12T06:00:00Z`). Entonces `--hasta` es ese instante y `--desde` es ese instante
menos el offset elegido:

| Opcion | Comando (caso principal, entrada = 2026-03-12T06:00:00Z) |
|---|---|
| 1  La ultima hora     | `python main.py base --desde 2026-03-12T05:00:00Z --hasta 2026-03-12T06:00:00Z` |
| 2  Las ultimas 12 h   | `python main.py base --desde 2026-03-11T18:00:00Z --hasta 2026-03-12T06:00:00Z` |
| 3  El ultimo dia      | `python main.py base --desde 2026-03-11T06:00:00Z --hasta 2026-03-12T06:00:00Z` |
| 4  Los ultimos 7 dias | `python main.py base --desde 2026-03-05T06:00:00Z --hasta 2026-03-12T06:00:00Z` |
| 5  Los ultimos 30 dias| `python main.py base --desde 2026-02-10T06:00:00Z --hasta 2026-03-12T06:00:00Z` |
| 6  A medida           | pedir `--desde` y `--hasta` y correr |

El offset se resta del `entrada` que reporte `estado` en cada caso -- si se opera `--caso b`,
tomar su propio `entrada`, no hardcodear el del principal. Los 30 dias exceden la ventana de
datos (10 dias) y el comando la recorta solo; no es un error.

**Reporta solo lo categoricamente nuevo:** valores que aparecen en la ventana y no existian
antes. La variacion de volumen no se reporta a proposito -- comparar totales entre una base
de siete dias y una ventana de seis horas declararia "caida" cualquier actividad rutinaria.
La primera y ultima aparicion de un indicador puntual ya la da `entidad` (2.3), por eso aca
no hay una opcion aparte para eso.

## 4) Situacion

```
╭──────────────────────────────────────────────────────────────────────────╮
│  4) SITUACION   ·  que se sabe y que falta                               │
├──────────────────────────────────────────────────────────────────────────┤
│  4.1)  Que acciones de respuesta ya se aplicaron                         │
│  4.2)  Cobertura                                                         │
│  4.3)  ¿Habriamos visto este hecho, de haber pasado?                     │
│  4.4)  Alcance                                                           │
│  4.5)  Que zonas de la evidencia ya se tocaron                           │
│                                                                          │
│  0)   Volver al menu anterior                                            │
╰──────────────────────────────────────────────────────────────────────────╯
```

| Opcion | Comando |
|---|---|
| 4.1 | `python main.py respuesta` |
| 4.2 | `python main.py cobertura` |
| 4.3 | `python main.py observable <accion> <objeto> --desde T --hasta T [--sujeto S]` |
| 4.4 | `python main.py situacion <archivo_hallazgos.json> [--desde T] [--hasta T]` |
| 4.5 | `python main.py consultas` |

**El estado de la respuesta no se guarda aparte: se deriva replayando la cronologia.** Una
sola fuente de verdad, y la respuesta a "¿este host esta aislado?" siempre viene con quien
lo decidio y cuando.

Ese estado cambia lo que el motor recomienda: una accion ya aplicada devuelve `INAPLICABLE`
y desaparece de la recomendacion (5.4). **Es lo que hace real al lazo** -- ejecutar cambia el mundo, y
la corrida siguiente lo refleja.

La observabilidad (4.3) tiene **tres valores y el tercero no es un descuido**:

- `SI` — la fuente cubre la ventana y registra esa clase de hecho. Solo aca una ausencia
  informa.
- `NO` — ninguna fuente lo registra, o ninguna cubria la ventana, o una carencia de
  configuracion la vuelve ciega.
- `INDETERMINADO` — no se puede afirmar cobertura.

Con `--sujeto` se somete la afirmacion de ausencia completa y devuelve `DESMENTIDA`,
`AUSENCIA-DEMOSTRADA` o `AUSENCIA-NO-CONCLUYENTE`. **La distincion entre las dos ultimas es
la mas cara del oficio**: no haber encontrado `GetObject` no prueba que no hubo descargas,
prueba que el trail no registra data events de S3.

En `situacion` (4.4), las tres secciones se presentan completas. `SIN ESTABLECER` es la que
mas cuesta y la que mas vale, y distingue dos cosas que se ven iguales en cualquier informe:
**SIN MIRAR** es un hueco de investigacion, **MIRADO Y VACIO** es una zona descartada. Sale
de cruzar la cobertura con el registro de consultas. **Es lo que decide si una contencion es
prematura**, asi que no se resume: se pega entera. Toma `--desde/--hasta` y **por defecto
juzga solo la ventana del incidente** (8 horas) -- si no se pasan, el operador ve los huecos
de ese tramo y de ningun otro, y hay que decirlo o pasar la ventana que corresponda.

## 5) Respuesta

Es la mitad de respuesta entera: proponer acciones, ver si la evidencia las respalda,
aplicarlas, y que el motor -- o un agente -- recomiende. Antes vivia partida en dos menus
(Accion y Recomendacion); es un solo dominio.

```
╭──────────────────────────────────────────────────────────────────────────╮
│  5) RESPUESTA   ·  que hacer, y si la evidencia lo respalda              │
├──────────────────────────────────────────────────────────────────────────┤
│  5.1)  Ver el catalogo de acciones                                       │
│  5.2)  Someter una accion al motor                                       │
│  5.3)  Someterla y registrarla en la cronologia                          │
│  5.4)  Recomendacion del motor                                           │
│  5.5)  Un agente propone acciones                                        │
│                                                                          │
│  0)   Volver al menu anterior                                            │
╰──────────────────────────────────────────────────────────────────────────╯
```

| Opcion | Comando |
|---|---|
| 5.1 | `python main.py accion` |
| 5.2 | `python main.py accion <accion> <objetivo> [--en T]` |
| 5.3 | idem + `--registrar <actor>` |
| 5.4 | `python main.py recomendacion [--hallazgos ARCHIVO] [--en T]` |
| 5.5 | un agente propone (ver abajo) + `python main.py accion` por cada propuesta |

**`--en` es el parametro que hace al modulo**, y conviene explicarlo si el usuario no lo
pasa: es el instante de la decision, y la evidencia se acota a lo anterior. Adjudicar contra
evidencia posterior a la decision es juzgar con el diario del lunes. Por defecto toma el
cierre de la ventana del incidente.

Cuatro veredictos:

- `FUNDADA` — los requisitos se satisfacen con evidencia anterior a *t*.
- `INFUNDADA` — falta un requisito **y** se puede demostrar que se estaba mirando.
- `NO-ADJUDICABLE` — falta un requisito y no hay cobertura demostrada.
- `INAPLICABLE` — el objetivo no existe en la evidencia.

**`FUNDADA` no quiere decir recomendable**, y es la confusion que hay que atajar. El motor
dice que la evidencia respalda la accion, no que sea buena idea: `apagar-host` sale FUNDADA
con los mismos requisitos que `aislar-host` y destruye la memoria volatil. Por eso la salida
trae `QUE LA VOLVERIA PREMATURA` y el aviso de destruccion de evidencia -- **presentar esas
secciones siempre**, no solo el veredicto.

**`NO-ADJUDICABLE` no es un error del motor.** Es la negativa a condenar una decision por no
haber mirado donde no habia nada que mirar.

**Registrar (5.3) dispara ademas un conector simulado** (`conectores.py`): ningun sistema real
recibe nada, pero la salida trae un ticket y un `status` con la forma de una respuesta real, y
ese ticket queda en el mismo asiento de la cronologia. Se dispara **con cualquier veredicto**,
incluido un override -- el conector ejecuta el acto, no juzga si estaba fundado.

### 5.4 — Recomendacion del motor

Es el grupo de control de la mitad de respuesta: el motor deriva que acciones estan
fundadas ahora, deterministicamente. El equivalente al detector (1.1) en la mitad de
investigacion.

**Con `--hallazgos` la recomendacion sale de una investigacion en vez del detector.** Es el
circuito agentico completo: el agente investiga (1.2), escribe su archivo, el verificador
decide que entra, y solo lo verificado funda acciones. Los hallazgos rechazados se listan
con su motivo -- pegarlos, porque decir cuantos quedaron afuera y por que es parte del
resultado.

**La recomendacion la deriva el motor. Nunca redactarla, ampliarla ni reordenarla.** Si el
motor propone cinco acciones, van las cinco como salieron. Agregarle una sexta "que tiene
sentido" es exactamente el modo de falla que el proyecto existe para no tener: prosa que
afirma mas de lo que el estado respalda.

Cada recomendacion trae los hechos que la fundan con cita, el impacto operativo y **que la
volveria prematura**. Esa ultima linea no es un adorno: una recomendacion sin su condicion
de falsedad es una orden disfrazada de consejo. Pegarla siempre.

El orden lo pone el motor -- primero lo que preserva evidencia, despues por costo -- y **no
se altera**.

### 5.5 — Un agente propone acciones

Es la contraparte abierta de 5.4, la misma simetria que hay en la mitad de investigacion
entre el detector (1.1) y los agentes (1.2). Un agente lee el estado del caso -- hallazgos,
situacion, cobertura -- y **propone** acciones de respuesta con su fundamento.

**La disciplina es lo que hace que no sea prosa suelta: el agente propone, el motor
adjudica.** Cada accion que el agente sugiere se corre por `python main.py accion <a> <o>
[--en T]` y se presenta **la propuesta del agente junto al veredicto del motor**
(`FUNDADA`/`INFUNDADA`/`NO-ADJUDICABLE`/`INAPLICABLE`). El agente nunca afirma "hace X" como
verdad -- sugiere y da su porque; el motor dice si la evidencia lo respalda. Un agente con
poder de decidir la respuesta sin adjudicacion seria justo la prosa que el proyecto evita.

El encargo del agente usa **la misma lista blanca y los mismos vetos que el de 1.2** (nada de
`verdad`, ni leer el generador/modelo/tests/detector). Cambia el entregable: en vez de
hallazgos, una lista de acciones propuestas del catalogo (5.1) con objetivo y fundamento,
cada una para pasar por el motor. Nunca inventar una accion fuera del catalogo.

## 6) Cronologia

```
╭──────────────────────────────────────────────────────────────────────────╮
│  6) CRONOLOGIA   ·  que se decidio y por que                             │
├──────────────────────────────────────────────────────────────────────────┤
│  6.1)  Las decisiones tomadas y con que se sabia en cada una             │
│                                                                          │
│  0)   Volver al menu anterior                                            │
╰──────────────────────────────────────────────────────────────────────────╯
```

| Opcion | Comando |
|---|---|
| 6.1 | `python main.py cronologia` |

Cada asiento guarda **lo que se sabia en el momento de decidir**, con cita. Es cadena de
custodia de decisiones: lo que responde en el post-mortem cuando preguntan por que se apago
el servidor, y lo que permite defender una decision que salio mal y estaba fundada -- que es
distinto de una mal tomada.

Los asientos se agregan con `accion --registrar <actor>` y **no se editan ni se borran**. Cada
uno trae ademas el ticket del conector simulado que se disparo (linea `conector`).

## 7) Regresion

```
╭──────────────────────────────────────────────────────────────────────────╮
│  7) REGRESION   ·  poner a prueba el motor                               │
├──────────────────────────────────────────────────────────────────────────┤
│  7.1)  Correr las nueve pruebas del motor                                │
│  7.2)  Correr una sola, con su explicacion                               │
│  7.3)  Correr la suite completa de verificaciones                        │
│                                                                          │
│  0)   Volver al menu anterior                                            │
╰──────────────────────────────────────────────────────────────────────────╯
```

| Opcion | Comando |
|---|---|
| 7.1 | `python main.py regresion [--detalle]` |
| 7.2 | `python main.py regresion <N>` |
| 7.3 | `python main.py test` |

**No se llama "Casos" a proposito.** En respuesta a incidentes un caso es la unidad de
trabajo -- con duenio, severidad y estado -- y usar la palabra para una suite de tests
garantiza que alguien abra la opcion esperando su cola y encuentre otra cosa.

Las nueve son decisiones donde **el veredicto no coincide con la intuicion**, y cada una
declara su `esperado`. Con la evidencia intacta, una prueba que no coincide es un bug del
motor: parar todo.

## 8) Otro caso

```
╭──────────────────────────────────────────────────────────────────────────╮
│  8) OTRO CASO   ·  practicar con un incidente nuevo                      │
├──────────────────────────────────────────────────────────────────────────┤
│  8.1)  Generar un caso nuevo (agente autor, aislado)                     │
│  8.2)  Investigarlo y responderlo a ciegas                               │
│                                                                          │
│  0)   Volver al menu anterior                                            │
╰──────────────────────────────────────────────────────────────────────────╯
```

| Opcion | Comando |
|---|---|
| 8.1 | `python main.py --caso b generar` |
| 8.2 | igual que el resto del menu, agregando `--caso b` en cada comando |

**Es otro incidente para practicar, no para medir nada contra el principal.** No hay
comparacion de numeros entre casos -- cada uno se investiga y se responde por su cuenta. Hoy
hay uno solo implementado: `atacante_salto_triple` (`INC-2026-0064`, en `CASOS` dentro de
`evidencia/generar_evidencia.py`), una cadena de tres saltos -- WKS-04, despues web-03, recien
despues AWS -- que el caso principal no pone a prueba. Agregar otro es agregar otra funcion
de plan y otra entrada a `CASOS`, no un mecanismo nuevo.

**Por que 8.1 y 8.2 conviene que no compartan sesion.** Si elegis la tecnica y despues
investigas vos mismo en la misma conversacion, ya sabes la respuesta y no practicaste nada.
Lanzar 8.2 como un agente fresco (misma lista blanca de 1.2, mismo veto sobre `verdad`) que
no tiene memoria de 8.1 es lo que mantiene el ejercicio siendo investigacion real. Igual que
en 1.2, mirar `python main.py --caso b verdad --si` antes de cerrar el archivo de hallazgos
vacia el ejercicio de sentido -- ahi no hay ningun numero que lo delate, asi que la disciplina
es la unica guarda.

## 9) Borrar hallazgos

Housekeeping: descarta los `.json` de hallazgos **de trabajo** del directorio del proyecto,
para arrancar el lab limpio o tirar el resultado de una investigacion que no sirvio.

**Borra solo los archivos de trabajo. Nunca toca dos que estan protegidos:**

- **`hallazgos_prueba.json` — lo usa `tests.py`.** Es el fixture del test del verificador: si
  se borra, `python main.py test` (7.3) falla. No se borra nunca por esta opcion.
- **`hallazgos_agente_windows.json` — es el ejemplo que citan las docs.** Material de
  referencia del repo. Tampoco se borra por esta opcion.

Todo el resto (los `hallazgos_agente_*.json` que se generan al operar, y cualquier `.json`
de hallazgos que no sea uno de esos dos) es de trabajo y entra al borrado.

**Como se hace:**

1. Listar que archivos de trabajo hay y cuales quedan protegidos, para que el usuario vea
   exactamente que se va y que se queda.
2. **Confirmar antes de borrar.** Borrar es dificil de deshacer; no borrar sin un si
   explicito, aunque la opcion se haya elegido a proposito.
3. Recien ahi eliminarlos, y decir cuales se borraron.

Si no hay ningun archivo de trabajo, decirlo y no hacer nada -- no es un error, es que ya
estaba limpio. Los archivos estan versionados en git y un borrado se puede revertir por ahi,
pero git es del usuario y no se toca desde aca (ver el resto del skill).

## Trampas

- **Precision baja no es siempre un defecto.** El detector cita mas de mil eventos de
  escaneo de fondo: es lo que le pasa a una regla de volumen en un entorno con ruido real.
- **`CITA-NO-SOSTIENE` es el veredicto importante del verificador.** Son afirmaciones que
  citan eventos reales y dicen algo que esos eventos no dicen. A simple vista se ven
  impecables, y es el error que un modelo comete de verdad -- inventar identificadores casi
  no lo hace. El verificador **no** valida la inferencia que encadena varias citas correctas
  en una conclusion falsa, ni comprueba lo que el hallazgo se callo.
- **El syslog fecha en hora local (-03) y sin anio.** Un evento de las 02:31 UTC aparece en
  el crudo con fecha del dia ANTERIOR. El timeline lo normaliza; el crudo no.
- **La homonimia no es identidad.** `WKS-04\ecarrizo` y el usuario IAM `ecarrizo` son
  sujetos distintos.
- **Sin CommandLine en los 4688.** Se sabe que binario se ejecuto, no con que argumentos.
  Toda afirmacion sobre argumentos es indeterminada, no falsa.
