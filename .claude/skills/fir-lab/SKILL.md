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

1. Correr `python main.py custodia` y leer la linea `INTEGRIDAD`.
2. Correr `python main.py estado`.
3. Mostrar el menu con el caso, el conteo y la integridad en la cabecera.

Si la integridad figura **ALTERADA** y no fue el usuario quien la altero en esta sesion,
avisarlo antes de cualquier otra cosa. Sobre evidencia alterada no se concluye.

```
╭──────────────────────────────────────────────────────────────────────────╮
│   \ | /                                                                  │
│  ── * ──   LAB FIR · INC-2026-0051 (BancoXYZ) · escenario A              │
│   / | \    10 dias · 3 fuentes · 6.532 eventos · integridad: OK          │
├──────────────────────────────────────────────────────────────────────────┤
│  1) Barrido        detector · agentes sobre los 10 dias · hallazgos      │
│  2) Consultar      filtrar, contar, agrupar · pivotear un indicador      │
│  3) Linea base     que es normal aca · dias 1-7 contra 8-10              │
│  4) Situacion      alcance · hechos, indicios y desconocidos             │
│  5) Accion         someter una accion al motor · veredicto con traza     │
│  6) Recomendacion  que propone el motor ahora · y de que depende         │
│  7) Cronologia     lo que decidiste · su veredicto · su costo            │
│  8) Casos          el catalogo · suite de regresion                      │
│                                                                          │
│  0) Salir                                                                │
╰──────────────────────────────────────────────────────────────────────────╯
```

**Copiar el cuadro literal, sin re-dibujarlo.** Todas las lineas miden 76 caracteres; los
unicos campos que cambian son el caso, el escenario, el conteo y la integridad, y hay que
reemplazarlos respetando el ancho. El asterisco va en ASCII a proposito: los glifos tipo
`✳` se renderizan con ancho variable y descuadran el marco.

**Las ocho opciones estan construidas.** Lo unico que falta del proyecto es correr los
agentes de investigacion (opcion 1.2): el arnes existe y nunca se uso, asi que la parte
agentica todavia no esta respaldada por ningun numero.

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
| 1.4 | `python main.py barrido --medir` |

### 1.2 — Como se lanzan los agentes

Se lanzan **desde aca**, con la herramienta de subagentes. Nunca desde el codigo del
proyecto: si Python llamara a la API, el catalogo de casos dejaria de ser reproducible y se
perderia la suite de regresion.

**Reglas duras, sin excepcion:**

- El agente trabaja **solo** con `python main.py <consulta>` sobre el escenario indicado.
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
│  4.1)  Integridad y cadena de custodia                                   │
│  4.2)  Cobertura: ventanas, motivos y carencias de auditoria             │
│  4.3)  ¿Habriamos visto este hecho, de haber ocurrido?                   │
│  4.4)  Alcance: hechos, indicios y desconocidos          [no construido] │
│                                                                          │
│  0)   Volver al menu anterior                                            │
╰──────────────────────────────────────────────────────────────────────────╯
```

| Opcion | Comando |
|---|---|
| 4.1 | `python main.py custodia` |
| 4.2 | `python main.py cobertura` |
| 4.3 | `python main.py observable <accion> <objeto> --desde T --hasta T [--sujeto S]` |

`custodia` emite `INTEGRIDAD` y `CADENA DE CUSTODIA`, y son dos cosas distintas: el hash
dice que el material no cambio; la custodia dice quien lo tuvo. Presentar las dos, sin
fundirlas. **Nunca re-sellar con la evidencia alterada**: destruye la unica referencia
contra la cual detectarlo.

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
| 6.1 | `python main.py recomendacion [--en T] [--desde T] [--hasta T]` |
| 6.2 | `python main.py situacion <archivo_hallazgos.json>` |

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
mas cuesta y la que mas vale: dice donde hay cobertura y no hay hechos. Y significa
exactamente eso, **no "nadie miro"**: esa distincion requiere registrar las consultas del
analista y hoy no se instrumenta. Si el usuario pregunta, decirlo asi.

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

## 8) Casos

```
╭──────────────────────────────────────────────────────────────────────────╮
│  8) CASOS                                                                │
├──────────────────────────────────────────────────────────────────────────┤
│  8.1)  Correr los ocho casos                                             │
│  8.2)  Correr uno solo, con su concepto                                  │
│  8.3)  Correr la suite completa de verificaciones                        │
│                                                                          │
│  0)   Volver al menu anterior                                            │
╰──────────────────────────────────────────────────────────────────────────╯
```

| Opcion | Comando |
|---|---|
| 8.1 | `python main.py casos [--detalle]` |
| 8.2 | `python main.py casos <N>` |
| 8.3 | `python main.py test` |

Los ocho son decisiones donde **el veredicto no coincide con la intuicion**, y cada uno
declara su `esperado`. Con la evidencia intacta, un caso que no coincide es un bug del
motor: parar todo.

Estan escritos contra el escenario A. **Correrlos contra B no tiene sentido** -- son otro
incidente -- y el catalogo no los adapta.

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
