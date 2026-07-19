# FIR — Laboratorio de respuesta a incidentes

Documento de diseño: el razonamiento detrás de las decisiones, incluidas las que después se
descartaron.

> **El alcance vigente está en el README, no acá.** Este documento describe el diseño
> completo tal como se pensó, que es deliberadamente más grande que lo que se construye. La
> sección 8 (Etapas) quedó superada: el orden real de construcción es P1 → P3 → P4 → P2 →
> P5 → P6, y dos piezas de acá abajo están **descartadas en firme**. Los motivos están al
> final de este documento.
>
> Se conservan escritas porque el argumento por el que se descartaron vale más que el hueco
> que dejan, y porque si el proyecto alguna vez tiene que servir para hablar de criterio y no
> solo de operación, el eje "acertada" es la primera pieza a reincorporar.

Hermano de `Desktop/IAM` y `Desktop/DFIR`: Python puro sin dependencias, JSON generado con
seed fijo, catálogo de casos que declara su `esperado` y funciona además como suite de
regresión, y un skill con menú como consola de operación.

---

## 1. Qué es y qué no es

**Es** un *range* de respuesta a incidentes con adjudicador: un escenario simulado sobre el
que se investiga, se toman decisiones de respuesta, y un motor determinista evalúa cada
decisión contra lo que la evidencia sostenía en ese momento.

**No es un SOAR.** Un SOAR orquesta y ejecuta contra sistemas reales — integraciones, hosts
que se aíslan de verdad, tickets que se abren solos. Acá no se ejecuta nada fuera del
simulador. Presentarlo como SOAR genera la expectativa de integraciones que no existen.

**No es forensia digital.** No hay adquisición, imagen de disco, memoria, sistema de
archivos, registro ni artefactos de host. Es análisis de evidencia de log más gestión de
incidente. Ver §9, pendientes.

**No es DFIR.** `Desktop/DFIR` queda como está y no se toca. FIR lo continúa
conceptualmente: en DFIR la evidencia es el producto final, en FIR es el insumo de una
decisión.

---

## 2. El escenario

Caso `INC-2026-00XX` (BancoXYZ). Diez días de actividad, tres fuentes, **6.000 eventos**:

| Fuente | Eventos | Perfil |
|---|---|---|
| AWS CloudTrail | 3.000 | Cuenta con tráfico automático abundante: roles asumidos por servicios, health checks, Config, jobs programados |
| Windows Security | 2.000 | Estación filtrada a autenticación y creación de proceso (~200/día) |
| Linux sshd / auth | 1.000 | Host expuesto: mayoría escaneo de internet, pocos logins reales |

El ataque son **70-80 eventos**, poco más del 1% del total. Hay que buscarlo.

Además del ataque principal, **una o dos actividades sospechosas adicionales** que no son
parte de él — para que encontrar algo raro no equivalga a haber encontrado el incidente.

### Por qué diez días

Para tener **línea base**. Los primeros siete son operación normal; el ataque cae sobre el
final. Eso permite preguntar *¿esto es raro?*, que con una sola noche de evidencia no
existe. Una access key creada un martes no dice nada sola; dice bastante si en siete días
nadie creó ninguna.

### Las capas de ruido

Tres, y la tercera es la que hace al proyecto:

1. **Actividad de negocio** — usuarios con horarios y patrones consistentes.
2. **Ruido de fondo de internet** — escaneo constante contra el host expuesto, bots probando
   `root` y `admin`. Es lo que ve cualquier servidor con SSH abierto.
3. **Actividad administrativa legítima que se parece al ataque** — un admin que crea una
   access key, un backup que copia mucho de golpe, una cuenta de servicio autenticándose
   desde una IP nueva porque cambió el proveedor.

Sin la capa 3 no se enseña a investigar, se enseña a filtrar. Los falsos positivos
plausibles obligan a descartar con evidencia, que es el trabajo real.

---

## 3. El generador: comportamiento, no líneas

**No se generan logs. Se genera comportamiento, y las líneas son su proyección.**

Se modelan entidades con estado — cuenta que existe o no, sesión que se abre y se cierra,
credencial con fecha de creación y revocación, host con su reloj y su deriva — y cada
transición de estado *emite* sus líneas.

La consistencia deja de ser algo que se verifica y pasa a ser algo que no se puede violar:

- No se puede emitir `Failed password` para un usuario inexistente, porque el emisor le
  pregunta al objeto cuenta si existe; si no existe emite `invalid user`.
- No puede haber un `4634` huérfano, porque el `LogonId` sale del objeto sesión que lo
  generó al abrirse.

### Lo que sale gratis

- **Etiqueta de verdad por evento.** Cada emisión sabe qué actor la produjo:
  `normal` / `ruido-internet` / `admin-legitimo` / `ataque`. Sin anotarla a mano.
- **Deriva de reloj consistente.** Es propiedad del host y se aplica en la proyección, no
  espolvoreada evento por evento.

### La regla de la tela

Todo actor usa **las mismas primitivas**: el atacante saca sus IPs del mismo pool que el
ruido de internet, con la misma irregularidad en los tiempos. Lo único que lo distingue es
**qué hace** — la secuencia de acciones, nunca cómo se generó.

Si el detector encuentra el ataque, tiene que ser porque el comportamiento es sospechoso, no
porque el generador dejó una firma estadística.

### Tests de invariantes, desde el día uno

Baratos, porque solo releen la proyección:

- Todo `4634` tiene su `4624` previo con el mismo `LogonId`.
- Ninguna llamada de CloudTrail usa una key fuera de su ventana de validez.
- Ningún evento menciona una cuenta antes de su creación.
- Ningún host emite mientras está aislado.
- Timestamps monótonos por fuente.
- Todo evento tiene exactamente una etiqueta.

**El criterio se deriva de las declaraciones que usa el generador y se barre el producto
completo. Nunca casos elegidos a mano** — es como se colaron los cinco bugs de DFIR.

### Procedimiento

Escribir el modelo de comportamiento, generar **600 eventos** para depurarlo a ojo, y recién
cuando los invariantes pasen limpios subir el dial a 6.000. Es el mismo generador; el
volumen es un parámetro.

El JSON se versiona tal cual, sin comprimir. El peso no es una restricción del proyecto.

---

## 4. Histórico congelado / corriente viva

Los diez días **ya pasaron y son inmutables**. Las acciones no pueden cambiar un solo evento
previo, o se pierde la propiedad de que la evidencia es un artefacto fijo.

El corte es explícito: evidencia histórica sellada hasta el instante de entrada, y desde ahí
una **corriente viva** que sí responde a las acciones.

De ahí sale el mejor mecanismo del diseño: **la evidencia de que la contención funcionó es
que los eventos dejan de aparecer**, y la de que falló es que aparecen en otro host. No lo
declara una tabla — se lee en los logs.

### El atacante no se adapta: sigue un plan

No aprende, no reacciona, no inventa nada al ser tocado. Tiene un **plan escrito de
antemano** y lo sigue hasta donde llegue. Si su plan incluía saltar al cuarto host, salta —
no porque vio la contención, sino porque siempre lo iba a hacer.

La contención lo intercepta o no lo intercepta. Determinista, reproducible, y el alcance mal
cerrado sigue costando caro.

### Fin del incidente

Termina por **tiempo** o por **erradicación lograda**. Nada de simulación abierta.

---

## 5. Los dos analistas

Se construyen las dos mitades porque contestan preguntas distintas y su contraste es el
resultado más valioso del laboratorio.

**Detector determinista** — reglas escritas a mano, estilo SIEM. Es el grupo de control:
encuentra lo que las reglas fueron escritas para encontrar, ni más ni menos. Barato de
escribir.

**Agente investigando abierto** — consulta, pivotea, nota cosas que ninguna regla declaró.

Con la etiqueta de verdad por evento se mide a los dos contra lo mismo: cuánto encuentra
cada uno, y qué encuentra uno que el otro no. **Ese número es lo que hace falsable al
laboratorio** en lugar de dejarlo en demo.

### Dónde viven los agentes

**En el skill, no en el código. Sin llamadas a la API desde Python.**

Razón decisiva: la suite de regresión no puede depender de un modelo. Si el código llama a
la API, los casos dejan de ser reproducibles, hacen falta credenciales y presupuesto para
correr los tests, y se pierde la característica común a los tres proyectos — Python puro,
corre en cualquier lado, da siempre lo mismo.

**Cierre del hueco de reproducibilidad:** el agente escribe sus hallazgos a un archivo, con
citas, en el DSL cerrado. Ese archivo es un artefacto versionado. El motor verifica ese
archivo y los casos corren contra él. La investigación queda reproducible después de hecha
aunque el agente no lo sea, y se pueden comparar corridas distintas del mismo escenario.

---

## 6. El menú

Dos mitades explícitas: investigar arriba, decidir abajo. Las fases de NIST 800-61 no son
opciones — son **estado**, y van en la cabecera.

```
╭──────────────────────────────────────────────────────────────────────────╮
│   \ | /                                                                  │
│  ── * ──   LAB FIR · INC-2026-00XX (BancoXYZ)                            │
│   / | \    10 dias · 6.000 eventos · fase: analisis · T+00:00            │
├──────────────────────────────────────────────────────────────────────────┤
│  1) Barrido        detector deterministico · agente · contraste          │
│  2) Consultar      filtrar, contar, agrupar · pivotear un indicador      │
│  3) Linea base     que es normal aca · dias 1-7 contra 8-10              │
│  4) Situacion      alcance · hechos, indicios y desconocidos             │
├──────────────────────────────────────────────────────────────────────────┤
│  5) Accion         someter una accion al motor · veredicto con traza     │
│  6) Recomendacion  que haria el motor ahora · y de que depende           │
│  7) Asientos       cada accion tomada · que se sabia · que paso despues  │
│  8) Casos          el catalogo · suite de regresion                      │
│                                                                          │
│  0) Salir                                                                │
╰──────────────────────────────────────────────────────────────────────────╯
```

Copiar literal, ancho interno de 74 caracteres, como los menús de IAM y DFIR.

---

## 7. Adjudicación de acciones

### El estado de conocimiento

Tres niveles, que son los veredictos de DFIR con otro nombre:

- **Hecho** — sostenido por evidencia citable.
- **Indicio** — compatible con la evidencia, no demostrado.
- **Desconocido** — nadie miró.

Las acciones de análisis convierten desconocido en hecho, **pero cuestan tiempo**. No
alcanza el reloj para mirar todo: hay que administrar la ignorancia bajo presión.

### El doble eje

Dos preguntas distintas sobre la misma decisión:

1. **¿Estaba fundada?** — dado lo que se sabía en el instante *t*, ¿la evidencia sostenía
   esa acción?
2. **¿Resultó acertada?** — contra la verdad del escenario, ¿funcionó?

|  | Acertada | Equivocada |
|---|---|---|
| **Fundada** | Bien | **No es un error** |
| **Infundada** | **Suerte** | Error real |

Las dos casillas del medio son el proyecto. *Fundada y equivocada* es la decisión que se
tomó bien y salió mal igual — en el post-mortem se cobra como error y no lo es. *Infundada y
acertada* es la peor, porque se premia y nadie la revisa.

Es la misma estructura que `REFUTADA` contra `INSUFICIENTE` en DFIR: **separar lo que pasó
de lo que se podía saber.**

### Veredictos

**Cuatro, no ocho.** Bordes nítidos, como los de DFIR. Ocho etiquetas de bordes difusos son
ocho discusiones sobre la etiqueta en vez de sobre la evidencia.

La regla de oro se traduce directo: *lo desconocido cae del lado de lo indeterminado, nunca
del lado de la condena*. Una acción cuya justificación no se puede establecer es
**no adjudicable**, nunca infundada.

### La precondición vive en el catálogo

"Fundada" significa que existe un conjunto de hechos sostenidos, con cita, **disponibles
antes de _t_**, que satisfacen la precondición declarada de esa acción. No una tabla aparte
escrita a mano: si el veredicto mide si el analista adivinó la tabla del autor, el usuario
aprende a jugar al simulador y no a investigar.

Ninguna acción entra al catálogo si el adjudicador no la evalúa de verdad. Un catálogo con
quince acciones de las cuales ocho no cambian nada se lee como que el modelo las contempla.

### El asiento por acción

Cada acción tomada genera un registro: **qué se sabía en el instante _t_, con qué citas,
quién decidió, qué se esperaba, y qué pasó después.**

Es cadena de custodia de decisiones. Es lo que responde en el post-mortem cuando alguien
pregunta por qué se apagó el servidor. Rigor probatorio aplicado a la respuesta misma — y es
la pieza que hace defendible al proyecto.

---

## 8. Etapas

Cada una utilizable sola.

1. **Generador.** Modelo de comportamiento, tres fuentes, etiqueta de verdad por evento,
   invariantes testeados. A 600 primero, a 6.000 después. La etapa más larga y la que define
   si el resto sirve.
2. **Motor de consulta.** Filtrar, contar, agrupar por hora, pivotear sobre IP o cuenta. Sin
   esto no se investiga nada. Ya es un laboratorio usable.
3. **Línea base.** Ventana contra ventana: qué es nuevo, qué desapareció, qué cambió de
   volumen.
4. **Verificador de citas + detector determinista.** El verificador se construye y se prueba
   **antes** de meter el agente, con hallazgos escritos a mano — incluyendo hallazgos
   deliberadamente falsos con citas reales, que es el caso que muestra si sirve para algo.
5. **Corriente viva y catálogo de acciones.** Estado de infraestructura, plan del atacante,
   consecuencias observables en los logs.
6. **Adjudicación, doble eje y catálogo de casos.** Asientos, cronología, suite de regresión.

**Primer entregable defendible: etapa 4.** Generador, consulta, línea base y verificación ya
se sostienen solos.

### Test de viabilidad barato

**Escribir los casos donde el veredicto de acción contradice la intuición, antes de escribir
el adjudicador.** Si no salen seis u ocho, el eje da para una checklist y no para un motor —
y conviene saberlo antes de las mil líneas.

Candidatos:

- Apagar el host para cortar rápido destruye memoria, conexiones y claves en RAM.
- Aislar el host 1 sin cerrar alcance: el atacante ya estaba en el 4, y ahora sabe que lo
  vieron.
- Rotar la mitad de las credenciales: conserva acceso y encima quedó avisado.
- Restaurar de un backup posterior al compromiso: vuelve la persistencia con los datos.
- Erradicar sin causa raíz: reinfección.
- Esperar a cerrar la investigación para notificar: el reloj corría desde que se supo.
- Aislar es visible; a veces observar rinde más que cortar.
- **Y al menos uno donde la acción obvia es la correcta**, para que no todo sea trampa.

---

## 9. Descartado, y por qué

- **Llamar a la API desde el código.** Rompe la reproducibilidad de la suite de regresión.
  Los agentes van en el skill.
- **Costo operativo cuantificado.** Los números los declararía el autor y no se contrastan
  contra nada: sería una opinión con formato de métrica. Entra como **texto declarado del
  escenario** (aislar el core bancario impacta más que bloquear una IP), ordinal, sin
  números.
- **Ocho veredictos de acción.** No son ortogonales. Cuatro, de bordes nítidos.
- **Roles y autoridad como subsistema.** Es una tabla de permisos evaluando peticiones — o
  sea, es el simulador de IAM. Agrega superficie sin concepto nuevo *acá*.
- **Preparación del entorno como subsistema propio.** "¿Hay EDR?" es "¿hay una fuente?", y
  eso es el modelo de cobertura que DFIR ya tiene.
- **Atacante que se adapta.** Rompe determinismo y reproducibilidad. Plan fijo en su lugar.
- **Generar 3.000 líneas a mano.** Reemplazado por el modelo de comportamiento.

---

## 10. Pendientes abiertos

**Forensia.** No está resuelta por tener un informe. El asiento por acción es cadena de
custodia de decisiones, no forensia digital. Si más adelante se quiere de verdad, el camino
barato es una cuarta fuente que sea **artefacto de host** — Amcache, Prefetch, o volcado de
claves Run exportado a JSON — con su semántica temporal propia: "primera vez visto" contra
"última ejecución" contra "fecha de compilación del binario". Encaja en el modelo de
cobertura sin fricción, porque un artefacto puede existir y estar vacío por configuración.
Y con eso entra el **timestomping**, que es el problema temporal más forense que existe y es
primo directo de lo que `tiempo.py` ya sabe hacer.

**Anclaje externo.** El riesgo mayor del proyecto es terminar con dos motores de veredicto y
ninguna verdad externa contra la cual estar equivocado — todo declarado por el autor, y el
usuario aprendiendo a predecir al autor en vez de a investigar. Mitigaciones: anclar acciones
y precondiciones a documento publicado (NIST 800-61r2, playbooks de CISA, que especifican
secuencias concretas de contención), y medir precisión y recall contra la etiqueta de verdad.

**Inferencia encadenada.** El verificador de citas comprueba que el evento citado exista y
diga lo afirmado, pero no valida la inferencia que encadena varias citas correctas en una
conclusión falsa. Se mitiga exigiendo que el hallazgo se exprese en el DSL cerrado de cuatro
campos; si el agente redacta prosa libre con citas al pie, no hay motor que lo verifique.

**Lo que se calló.** El verificador nunca comprueba lo omitido. Un agente que encuentra 25 de
80 eventos y los cita impecablemente saca informe perfecto. Por eso la etiqueta de verdad por
evento y la métrica de recall no son opcionales.

**Reutilización desde DFIR.** Evaluar qué se trae tal cual (normalización temporal, semántica
de eventos, modelo de cobertura, la máquina de veredictos, integridad y custodia) y qué se
reescribe. Decidir si se copia o se comparte.


---

# Apéndice — Decisiones cerradas y descartes

Absorbido de `PENDIENTE.md`, que se eliminó al terminar el proyecto. Está acá para no
reabrir cada decisión cada vez que alguien lee el diseño.

## Qué es esto, y qué no

**Respuesta agéntica con humano en el lazo, no un SOAR automatizado.** El menú ofrece
acciones y decide una persona, o un agente recomienda y la persona ejecuta. Por eso no hay
playbooks como objeto: es el modelo, no una carencia. Lo que sí tiene que existir, y existe,
es que ejecutar cambie el mundo.

## Decisiones cerradas

- Los agentes se lanzan **desde el skill, nunca desde el código**: si Python llamara a la
  API, la suite de regresión dejaría de ser reproducible.
- **El escenario B no se tunea.** Se mide.
- **La verdad no se persiste.** Se regenera desde el seed al medir, con una guarda que corta
  si la evidencia en disco no corresponde al escenario.
- **Cuatro veredictos**, de bordes nítidos. Lo desconocido cae en `NO-ADJUDICABLE`, nunca en
  `INFUNDADA`.
- **La evidencia histórica es inmutable.** Sólo cambia el estado de la respuesta.
- **Ninguna acción entra al catálogo si no declara su efecto sobre el estado.**
- **El estado lo define el acto, no el veredicto.** Ejecutar algo que el motor declaró
  `INFUNDADA` cambia el mundo igual y queda marcado como *override*. Un adjudicador con poder
  de veto sobre la realidad sería lo contrario de una herramienta con humano en el lazo.
- **Se eliminó el sellado SHA-256.** Era forensia heredada y redundante: la guarda de semilla
  ya comprueba que la evidencia corresponda al escenario, que es más fuerte que "no cambió
  desde que alguien la selló".

## Descartado, y por qué

- **Corriente viva y plan pendiente del atacante.** Que la contención se lea en logs
  futuros. Es la idea más linda del diseño y el pedazo más caro; el estado de respuesta
  consigue el grueso del efecto por una fracción del costo.
- **Eje "acertada" y los cuatro cuadrantes.** Es barato —se computa retrospectivamente contra
  la evidencia histórica— y aun así queda afuera: es función de entrenamiento, no de
  operación. Un SOAR dice si la acción corresponde; no puntúa al analista contra una verdad
  que en producción nadie tiene. **Primera pieza a reincorporar** si el proyecto alguna vez
  tiene que servir para hablar de criterio y no sólo de operación.
- **Ejecución real.** No hay integración con nada, y se presenta como simulador.
- **Roles y autoridad.** Es una tabla de permisos evaluando peticiones: es el simulador de
  IAM, no agrega concepto nuevo acá.
- **Costo operativo cuantificado.** Números declarados por el autor, sin nada contra qué
  contrastar. Queda como texto ordinal.

## Lo que falta, y no se construyó

- **La alerta como entidad.** Hoy se entra al caso por el barrido. No hay alerta con
  severidad, deduplicación ni agrupación en incidente, que es por donde arranca un SOAR.
- **Enriquecimiento** (reputación, inventario, contexto de identidad) y **métricas
  operativas** (MTTD, MTTR, tasa de falsos positivos).
- **Nadie mide el producto final.** `medir` puntúa a cada analista contra la verdad, pero no
  a las acciones que salen de él: un agente con recall alto y precisión baja arrastra la
  recomendación hacia contener de más, y el arnés no lo detecta.
- **`test_credenciales_usadas_dentro_de_su_ventana` es vacuo**: verifica 3.249 veces una
  condición verdadera por construcción. Es la misma forma de error que las cinco auditorías
  del proyecto anterior.
- **`tiempo.py` no hace trabajo acá.** Vino de DFIR, es correcto, y `eventos.py` normaliza
  con él. No conviene ponerlo al frente al presentar el proyecto.
