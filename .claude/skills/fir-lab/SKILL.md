---
name: fir-lab
description: Opera el laboratorio FIR del caso INC-2026-0051 - barrido con detector y agentes, consultar los 6.500 eventos, linea base, situacion y cobertura, someter acciones de respuesta al motor, recomendacion con su condicion de falsedad, cronologia de decisiones y los ocho casos. Usar cuando se pida investigar el escenario, consultar la evidencia, buscar el incidente, verificar hallazgos, medir detectores, proponer o evaluar acciones de respuesta, o trabajar con el proyecto FIR.
---

# Lab FIR

Consola de operacion. El proyecto vive en `C:\Users\Ezela\Desktop\FIR` y los comandos se
corren parados ahi.

Dos escenarios. **A** (`INC-2026-0051`, por defecto) es donde se escribieron las reglas.
**B** (`INC-2026-0058`, `--escenario b`) esta retenido para validar metodo, y **no se tunea
contra el**: se mide y punto. Un metodo que solo funciona en A era la respuesta de A
disfrazada de metodo.

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
│  ── * ──   LAB FIR · INC-2026-0051 (BancoXYZ) · escenario A              │
│   / | \    10 dias · 3 fuentes · 6.532 eventos · 0 acciones aplicadas    │
├──────────────────────────────────────────────────────────────────────────┤
│  1) Barrido        detector · agentes sobre los 10 dias · hallazgos      │
│  2) Consultar      filtrar, contar, agrupar · pivotear un indicador      │
│  3) Linea base     que es normal aca · dias 1-7 contra 8-10              │
│  4) Situacion      alcance · hechos, indicios y desconocidos             │
│  5) Accion         someter una accion al motor · veredicto con traza     │
│  6) Recomendacion  que propone el motor ahora · y de que depende         │
│  7) Cronologia     lo que decidiste · su veredicto · su costo            │
│  8) Regresion      la suite del motor · cada prueba con su esperado      │
│  9) Ataque nuevo   generar escenario C con una tecnica · medir a ciegas  │
│                                                                          │
│  0) Salir                                                                │
╰──────────────────────────────────────────────────────────────────────────╯
```

**Copiar el cuadro literal, sin re-dibujarlo.** Todas las lineas miden 76 caracteres; los
unicos campos que cambian son el caso, el escenario, el conteo y las acciones
aplicadas, y hay que
reemplazarlos respetando el ancho. El asterisco va en ASCII a proposito: los glifos tipo
`✳` se renderizan con ancho variable y descuadran el marco.

**Las ocho opciones estan construidas**, con una salvedad: la 4.4 (alcance como hechos,
indicios y desconocidos) existe via `situacion` y necesita un archivo de hallazgos como
entrada, asi que depende de haber corrido antes la 1.2 o el detector.

**Nunca simular una recomendacion ni un veredicto de accion.** Si un comando falla o falta
un dato, decirlo. Producir esas salidas escribiendo prosa convincente es exactamente el modo
de falla que el laboratorio existe para medir.

Aceptar tanto el numero como la intencion en lenguaje natural.

## Navegacion

Todo submenu termina con `0) Volver al menu anterior`. Despues de ejecutar una accion y
presentar el resultado, volver a ofrecer el submenu donde estaba el usuario.

Entre la salida de un comando y el cuadro siguiente va una regla horizontal (`---`) y una
linea en blanco.

## Que devuelve cada opcion

**El usuario NO ve la salida de las tool calls.** Toda salida hay que **pegarla en la
respuesta**, en un bloque de codigo, textual y completa. Correr un comando y no transcribir
el resultado deja al usuario con la pantalla vacia.

**Datos, no prosa.** Una opcion devuelve la salida del comando y despues el submenu.

- **No** interpretar el resultado en parrafos.
- **No** seniala "lo interesante", ni anticipar hallazgos.
- **No** completar con conocimiento propio de seguridad lo que la salida no dice.

La explicacion se da **solo si el usuario la pide**. El que lee la salida es el analista.

Excepcion: los veredictos (`AUSENCIA-DEMOSTRADA`, `CITA-NO-SOSTIENE`, la observabilidad
`SI`/`NO`/`INDETERMINADO`) y sus motivos se citan textuales, porque son el dato.

---

## 1) Barrido

```
╭──────────────────────────────────────────────────────────────────────────╮
│  1) BARRIDO                                                              │
├──────────────────────────────────────────────────────────────────────────┤
│  1.1)  Detector deterministico (las ocho reglas escritas a mano)         │
│  1.2)  Lanzar agentes de investigacion                                   │
│  1.3)  Verificar un archivo de hallazgos                                 │
│  1.4)  Medir contra la verdad · contraste detector / agente              │
│                                                                          │
│  0)   Volver al menu anterior                                            │
╰──────────────────────────────────────────────────────────────────────────╯
```

| Opcion | Comando |
|---|---|
| 1.1 | `python main.py barrido` |
| 1.3 | `python main.py verificar <archivo.json>` |
| 1.4 | `python main.py medir <archivo...> [--union] [--perdidos]` |

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

**El baseline a batir**: el detector deterministico saca 63,8% de recall en A y 4,3% en B.
La union de tres agentes saca 84,1% en A. **Contra B nunca se midio**, y es lo que falta.

### El protocolo que va en el encargo

Es **metodo**, y por eso vale: no nombra ninguna IP, ninguna cuenta, ninguna fecha ni ningun
hallazgo de ningun escenario. Si nombrara alguno, el agente no estaria investigando --
estaria copiando, y el numero no mediria nada.

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
ejemplo: se mide que proporcion de los eventos del incidente lograste citar.

Al terminar, deci que NO miraste.
```

**La ultima linea del entregable no es cortesia.** Sin ella el agente cita un ejemplo por
hallazgo y el recall se desploma sin que nada lo avise: el verificador comprueba lo que se
afirmo, nunca lo que se callo.

### Sobre la medicion (1.4)

**Se corre despues de cerrar el archivo de hallazgos, nunca durante.** Un agente que vea su
propio recall y vuelva a buscar esta optimizando contra el solucionario.

La verdad no existe en disco: se reconstruye desde el seed al medir y desaparece. Si la
evidencia fue editada, la medicion se niega a correr -- regenerar con `python main.py
generar`.

## 2) Consultar

```
╭──────────────────────────────────────────────────────────────────────────╮
│  2) CONSULTAR                                                            │
├──────────────────────────────────────────────────────────────────────────┤
│  2.1)  Timeline con filtros                                              │
│  2.2)  Un evento: normalizado, semantica y crudo                         │
│  2.3)  Una entidad: todo lo que la menciona · primera y ultima vez       │
│  2.4)  Agregar: contar por ip, sujeto, accion, hora, region              │
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

`evento` emite `EVENTO`, `INCERTIDUMBRE`, `ATRIBUTOS`, `SEMANTICA` (solo Windows) y
`REGISTRO CRUDO`. La seccion `SEMANTICA` sale del catalogo de `eventos.py`, que es la capa
contrastable contra documentacion publicada: pegarla textual, sin ampliarla.

## 3) Linea base

```
╭──────────────────────────────────────────────────────────────────────────╮
│  3) LINEA BASE                                                           │
├──────────────────────────────────────────────────────────────────────────┤
│  3.1)  Que hay en una ventana que no habia antes                         │
│  3.2)  Primera y ultima aparicion de un indicador                        │
│                                                                          │
│  0)   Volver al menu anterior                                            │
╰──────────────────────────────────────────────────────────────────────────╯
```

| Opcion | Comando |
|---|---|
| 3.1 | `python main.py base --desde T --hasta T` |
| 3.2 | `python main.py entidad <ind>` (cabecera `primera` / `ultima`) |

**Es la opcion que hace util tener diez dias.** Reporta solo lo categoricamente nuevo:
valores que aparecen en la ventana y no existian antes. La variacion de volumen no se
reporta a proposito -- comparar totales entre una base de siete dias y una ventana de seis
horas declararia "caida" cualquier actividad rutinaria.

## 4) Situacion

```
╭──────────────────────────────────────────────────────────────────────────╮
│  4) SITUACION                                                            │
├──────────────────────────────────────────────────────────────────────────┤
│  4.1)  Estado de la respuesta: que acciones ya se aplicaron              │
│  4.2)  Cobertura: ventanas, motivos y carencias de auditoria             │
│  4.3)  ¿Habriamos visto este hecho, de haber ocurrido?                   │
│  4.4)  Alcance: hechos, indicios, sin mirar y mirado-y-vacio             │
│  4.5)  Consultas registradas: que zonas se tocaron                       │
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
y desaparece de la opcion 6. **Es lo que hace real al lazo** -- ejecutar cambia el mundo, y
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

## 5) Accion

```
╭──────────────────────────────────────────────────────────────────────────╮
│  5) ACCION                                                               │
├──────────────────────────────────────────────────────────────────────────┤
│  5.1)  Ver el catalogo de acciones                                       │
│  5.2)  Someter una accion al motor                                       │
│  5.3)  Someterla y registrarla en la cronologia                          │
│                                                                          │
│  0)   Volver al menu anterior                                            │
╰──────────────────────────────────────────────────────────────────────────╯
```

| Opcion | Comando |
|---|---|
| 5.1 | `python main.py accion` |
| 5.2 | `python main.py accion <accion> <objetivo> [--en T]` |
| 5.3 | idem + `--registrar <actor>` |

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

## 6) Recomendacion

```
╭──────────────────────────────────────────────────────────────────────────╮
│  6) RECOMENDACION                                                        │
├──────────────────────────────────────────────────────────────────────────┤
│  6.1)  Que acciones estan fundadas ahora                                 │
│  6.2)  Situacion: hechos, indicios y lo que quedo sin establecer         │
│                                                                          │
│  0)   Volver al menu anterior                                            │
╰──────────────────────────────────────────────────────────────────────────╯
```

| Opcion | Comando |
|---|---|
| 6.1 | `python main.py recomendacion [--hallazgos ARCHIVO] [--en T]` |
| 6.2 | `python main.py situacion <archivo_hallazgos.json> [--desde T] [--hasta T]` |

**Con `--hallazgos` la recomendacion sale de una investigacion en vez del detector.** Es el
circuito agentico completo: el agente investiga, escribe su archivo, el verificador decide
que entra, y solo lo verificado funda acciones. Los hallazgos rechazados se listan con su
motivo -- pegarlos, porque decir cuantos quedaron afuera y por que es parte del resultado.

**La recomendacion la deriva el motor. Nunca redactarla, ampliarla ni reordenarla.** Si el
motor propone cinco acciones, van las cinco como salieron. Agregarle una sexta "que tiene
sentido" es exactamente el modo de falla que el proyecto existe para no tener: prosa que
afirma mas de lo que el estado respalda.

Cada recomendacion trae los hechos que la fundan con cita, el impacto operativo y **que la
volveria prematura**. Esa ultima linea no es un adorno: una recomendacion sin su condicion
de falsedad es una orden disfrazada de consejo. Pegarla siempre.

El orden lo pone el motor -- primero lo que preserva evidencia, despues por costo -- y **no
se altera**.

En `situacion` (6.2), las tres secciones se presentan completas. `SIN ESTABLECER` es la que
mas cuesta y la que mas vale, y ahora distingue dos cosas que se ven iguales en cualquier
informe: **SIN MIRAR** es un hueco de investigacion, **MIRADO Y VACIO** es una zona
descartada. Sale de cruzar la cobertura con el registro de consultas.

**Es lo que decide si una contencion es prematura**, asi que no se resume: se pega entera.

`situacion` toma `--desde/--hasta` y **por defecto juzga solo la ventana del incidente**
(8 horas). Si no se pasan, el operador esta viendo los huecos de ese tramo y de ningun otro
-- decirlo cuando se presente la salida, o pasar la ventana que corresponda.

## 7) Cronologia

```
╭──────────────────────────────────────────────────────────────────────────╮
│  7) CRONOLOGIA                                                           │
├──────────────────────────────────────────────────────────────────────────┤
│  7.1)  Las decisiones tomadas y con que se sabia                         │
│                                                                          │
│  0)   Volver al menu anterior                                            │
╰──────────────────────────────────────────────────────────────────────────╯
```

| Opcion | Comando |
|---|---|
| 7.1 | `python main.py cronologia` |

Cada asiento guarda **lo que se sabia en el momento de decidir**, con cita. Es cadena de
custodia de decisiones: lo que responde en el post-mortem cuando preguntan por que se apago
el servidor, y lo que permite defender una decision que salio mal y estaba fundada -- que es
distinto de una mal tomada.

Los asientos se agregan con `accion --registrar <actor>` y **no se editan ni se borran**.

## 8) Regresion

```
╭──────────────────────────────────────────────────────────────────────────╮
│  8) REGRESION                                                            │
├──────────────────────────────────────────────────────────────────────────┤
│  8.1)  Correr las nueve pruebas del motor                                │
│  8.2)  Correr una sola, con su concepto                                  │
│  8.3)  Correr la suite completa de verificaciones                        │
│                                                                          │
│  0)   Volver al menu anterior                                            │
╰──────────────────────────────────────────────────────────────────────────╯
```

| Opcion | Comando |
|---|---|
| 8.1 | `python main.py regresion [--detalle]` |
| 8.2 | `python main.py regresion <N>` |
| 8.3 | `python main.py test` |

**No se llama "Casos" a proposito.** En respuesta a incidentes un caso es la unidad de
trabajo -- con duenio, severidad y estado -- y usar la palabra para una suite de tests
garantiza que alguien abra la opcion esperando su cola y encuentre otra cosa.

Las nueve son decisiones donde **el veredicto no coincide con la intuicion**, y cada una
declara su `esperado`. Con la evidencia intacta, una prueba que no coincide es un bug del
motor: parar todo.

Estan escritas contra el escenario A. **Correrlas contra B no tiene sentido** -- son otro
incidente.

## Trampas

- **El escenario B no se tunea.** Se mide.
- **Un recall alto en A no dice nada solo.** El detector saca 63,8% en A y 4,3% en B porque
  sus ocho reglas se apoyan en que haya fallos de autenticacion, y en B el atacante nunca
  falla. Ese par de numeros es el resultado, no el primero.
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
