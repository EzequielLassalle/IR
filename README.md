# Laboratorio FIR

Diez días de evidencia de tres fuentes con un incidente adentro, y las herramientas para
encontrarlo. Sin dependencias externas: solo la librería estándar.

```
python main.py                  comandos disponibles
python main.py estado           el escenario y su forma
python main.py timeline         el timeline, con filtros
python main.py evento <ID>      un evento: normalizado, semántica y crudo
python main.py entidad <ind>    todo lo que menciona un indicador
python main.py contar --por ip  agregación sobre lo filtrado
python main.py base             qué hay en la ventana que no había antes
python main.py barrido --medir  el detector determinista y su medición
python main.py custodia         integridad y cadena de custodia
python main.py cobertura        qué se recolectó y qué no
python main.py observable       si un hecho habría sido visible

python main.py accion <a> <o>   someter una acción al motor · veredicto con traza
python main.py recomendacion    qué acciones están fundadas ahora, y de qué dependen
python main.py situacion <arch> hechos, indicios y lo que quedó sin establecer
python main.py cronologia       las decisiones tomadas y con qué se sabía
python main.py casos            el catálogo · suite de regresión
python main.py test             las 35.085 verificaciones
```

El diseño completo —decisiones, descartes y etapas pendientes— está en `DISENO.md`.

## El escenario

`INC-2026-0051`. Del 2 al 12 de marzo de 2026, **6.532 eventos** entre Windows Security,
CloudTrail y syslog de sshd. El ataque son **69 eventos, el 1,1% del total**, y ocurre el
día 8. El analista toma el caso dos días después: el incidente pasó y nadie lo vio.

Cinco capas conviven en la evidencia, y las tres últimas son las que hacen al ejercicio:

| Etiqueta | Qué es |
|---|---|
| `normal` | Usuarios con horarios consistentes y jobs automatizados |
| `ruido-internet` | Escaneo de fondo contra el host expuesto. Cientos de fallos que no son un ataque |
| `admin-legitimo` | Un administrador creando una access key de madrugada desde una IP nueva |
| `sospechoso-no-incidente` | Una aplicación con la contraseña vencida que reintenta sola |
| `ataque` | El incidente |

Sin la cuarta capa, encontrar algo raro equivaldría a haber encontrado el incidente. Con
ella hay que distinguir entre lo raro y lo peligroso, que es el trabajo.

## Las dos mitades

**El generador no escribe logs, escribe comportamiento.** `modelo.py` define entidades con
estado —cuentas que existen o no, sesiones que se abren y se cierran, credenciales con
ventana de validez, hosts con su reloj— y cada transición emite sus líneas. La consistencia
deja de ser algo que se verifica y pasa a ser algo que no se puede violar: no hay forma de
emitir un `Failed password` para un usuario que sshd ya declaró inexistente, porque el
emisor le pregunta a la cuenta.

De ahí salen gratis dos cosas: la **etiqueta de verdad por evento**, que es lo que permite
medir un detector contra la realidad, y la deriva de reloj aplicada de forma consistente.

**El detector es el grupo de control.** `deteccion.py` son ocho reglas escritas a mano,
estilo SIEM. Encuentra lo que las reglas fueron escritas para encontrar, ni más ni menos, y
`--medir` lo contrasta contra la verdad:

```
precision : 3.3%
recall    : 63.8%
```

Ese número es el punto del laboratorio. El detector se ahoga en el ruido de internet —cita
1.214 eventos de escaneo por cada 44 del ataque— que es exactamente lo que le pasa a una
regla ingenua en un SOC real. Y deja **25 eventos del ataque sin citar**, que es la mitad
silenciosa del error: un verificador comprueba lo que se afirmó, nunca lo que se calló.

## La regla de la tela

Todos los actores usan las mismas primitivas: el atacante saca sus direcciones del mismo
pool que los bots y espacia sus acciones con la misma distribución de cola pesada. Lo único
que lo distingue es **qué hace**.

Es verificable y está testeado. La dirección `198.51.100.77`, desde la que se rocían
contraseñas el día 8, aparece por primera vez el día 1 haciendo escaneo de fondo y acumula
140 eventos de los cuales 127 son ruido:

```
python main.py entidad 198.51.100.77
```

Si el detector encuentra el ataque tiene que ser porque el comportamiento es sospechoso, no
porque el generador dejó una firma.

## Las trampas del escenario

- **La aplicación de facturación** produce 648 fallos de contraseña contra `svc_backup`
  desde una IP interna fija. Es la firma exacta de una fuerza bruta y es una contraseña
  vencida. Cualquier regla que alerte por volumen de 4625 la encuentra primero.
- **`CreateAccessKey` lo hacen dos actores**: el admin el día 4 y el atacante el día 8. La
  operación sola no resuelve nada; el contexto alrededor sí.
- **El syslog fecha en hora local** (`-03`) y sin año. Los eventos del ataque de las 02:31
  UTC aparecen en el crudo como del día **anterior**. El timeline lo normaliza; el registro
  crudo no.
- **La deriva del reloj de WKS-04 es una tasa, no un offset.** La medición se tomó en la
  recolección; la incertidumbre crece con la distancia a ese momento. Un evento del día 8
  arrastra ±200s, no los ±90s de la medición.
- **Rotar la credencial robada no alcanza**: el atacante creó una propia, y vuelve con ella.

## Los invariantes

`tests.py` corre **33.220 verificaciones** sobre la evidencia. La mitad son invariantes del
generador —todo 4634 tiene su 4624, ninguna cuenta actúa antes de su 4720, el sello local de
syslog corresponde al instante real— y la otra mitad verifica que el escenario siga siendo
un ejercicio: que el ataque sea minoría, que las tres fuentes participen, que haya línea base
limpia antes, y que **ninguna dirección del atacante sea exclusiva del ataque**.

El criterio de cada barrido se deriva de las declaraciones que usa el código y recorre el
producto completo. Nunca se enumeran casos a mano: una tabla escrita al lado del test elige
justo los casos que no rompen.

## La mitad de respuesta

Una acción se somete al motor y el motor dice si está **fundada en lo que la evidencia
sostenía en ese momento**. Un solo eje: no se evalúa si "resultó acertada" contra lo que el
atacante realmente hizo, porque eso exige una verdad que en producción nadie tiene.

La precondición de cada acción se declara **en el DSL de cuatro campos**, no en prosa. Así
el veredicto no mide si el analista adivinó lo que pensaba el autor: mide si la evidencia lo
respaldaba.

```
FUNDADA          los requisitos se satisfacen con evidencia anterior a t
INFUNDADA        falta un requisito Y se puede demostrar que se estaba mirando
NO-ADJUDICABLE   falta un requisito y no hay cobertura demostrada
INAPLICABLE      el objetivo no existe, o ya está en ese estado
```

**Lo desconocido cae en `NO-ADJUDICABLE`, nunca en `INFUNDADA`.** Condenar una decisión por
no haber mirado donde no había nada que mirar es el mismo error que en el proyecto anterior
costó cinco auditorías.

La evidencia se acota a lo anterior al instante de la decisión. Adjudicar contra evidencia
posterior es juzgar con el diario del lunes:

```
$ python main.py accion deshabilitar-cuenta 'WKS-04\soporte_it' --en 2026-03-09T22:00:00Z
  -> INFUNDADA
$ python main.py accion deshabilitar-cuenta 'WKS-04\soporte_it' --en 2026-03-10T04:00:00Z
  -> FUNDADA
```

Y ninguna recomendación sale pelada. Cada una trae los hechos que la fundan con cita, el
impacto operativo, y **qué la volvería prematura** — sin esa condición de falsedad, una
recomendación es una orden disfrazada de consejo.

## Los casos

Ocho decisiones donde el veredicto no coincide con la intuición, cada una con su `esperado`.
Suite de regresión del motor:

```
python main.py casos --detalle
```

El más instructivo es el 8: revocar la credencial del pipeline sale **FUNDADA**, y es la
credencial legítima de la automatización con 95 usos en la ventana. El motor dice que la
evidencia respalda la acción, no que sea buena idea. Y el par 4/5 muestra que el volumen no
es compromiso: la IP interna con 648 fallos no se bloquea y la del ataque, con cinco veces
menos eventos, sí.

## Estado

Construido: generador con invariantes, normalización temporal, consulta, línea base,
detector determinista con medición, verificador de citas, cobertura de tres valores,
integridad y custodia, catálogo de acciones con adjudicación, recomendación, situación,
cronología y los ocho casos.

**Pendiente:** correr los agentes de investigación contra el escenario. El arnés está escrito
—protocolo en el skill, formato de hallazgos, verificador, medición— y **ningún agente corrió
todavía**, así que hoy la parte agéntica no está respaldada por ningún número. Es el P1 de
`PENDIENTE.md`.

## Los módulos

| Archivo | Contenido |
|---|---|
| `modelo.py` | Entidades con estado y única puerta de emisión. La consistencia vive acá. |
| `evidencia/generar_evidencia.py` | Los actores y los dos planes de atacante. Seed fijo. |
| `tiempo.py` | Normalización temporal e incertidumbre partida en propia y sistemática. |
| `eventos.py` | Vocabulario común y semántica contrastable contra documentación publicada. |
| `consulta.py` | Filtrar, contar, pivotear, línea base. |
| `deteccion.py` | Las ocho reglas y la medición contra la verdad. |
| `cobertura.py` | Qué se recolectó y qué no. Observabilidad de tres valores. |
| `custodia.py` | Integridad, cadena de custodia y cronología de decisiones. |
| `verificador.py` | Citas, vocabulario cerrado y afirmaciones de ausencia. |
| `acciones.py` | Catálogo, adjudicación y recomendación. |
| `situacion.py` | Hechos, indicios y lo que quedó sin establecer. |
| `casos.py` | Los ocho casos. |
| `tests.py` | 35.085 verificaciones. Runner propio. |
