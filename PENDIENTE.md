# Estado y pendientes

Al 19 de julio de 2026.

**Esto es respuesta agéntica, no un SOAR automatizado.** La distinción es de diseño, no de
tamaño: un SOAR ejecuta playbooks por su cuenta; acá el menú ofrece acciones y **decide una
persona**, o un agente recomienda y la persona ejecuta. Por eso no hay playbooks como objeto
y no es una carencia — es el modelo. Lo que sí tiene que existir, y ahora existe, es que
ejecutar cambie el mundo.

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
│  8) Casos          el catalogo · suite de regresion                      │
│                                                                          │
│  0) Salir                                                                │
╰──────────────────────────────────────────────────────────────────────────╯
```

**Las ocho opciones están construidas.** 35.093 verificaciones, 24 pruebas, en verde.

## El lazo, que es lo que hace al proyecto

```
barrido (detector o agentes) → hallazgos con cita → verificación → recomendación
        → el humano elige → se ejecuta y se registra → el estado cambia
        → la recomendación siguiente es distinta
```

La última flecha es la que costó, y es la que separa esto de una lista de sugerencias. Una
acción aplicada devuelve `INAPLICABLE` en su repetición y desaparece de la opción 6.

El estado **no se guarda aparte: se deriva replayando la cronología**. Una sola fuente de
verdad, y la respuesta a "¿este host está aislado?" siempre viene con quién lo decidió y
cuándo.

## Los números

| | recall | precisión |
|---|---|---|
| detector determinista, escenario A | 63,8% | 3,3% |
| detector determinista, escenario B (retenido) | 4,3% | 0,1% |
| tres agentes, unión, escenario A | 87,0% | 47,6% |

El detector se cae en B porque sus ocho reglas se apoyan en que haya fallos de
autenticación, y en B el atacante usa una credencial legítima y nunca falla. Ese par de
números es el resultado del laboratorio, no el primero solo.

**Los agentes nunca corrieron contra B.** Es lo primero que falta.

## Pendiente

**Correr los agentes contra el escenario B.** Es la prueba de que el método transfiere. Si el
recall aguanta, investigan; si se cae como el detector, el protocolo del skill estaba escrito
para A.

**Enriquecimiento.** No hay reputación, geo, inventario de activos ni contexto de identidad,
ni un lugar declarado donde entrarían. En un SOAR real es la mitad del cuerpo de los
playbooks.

**La alerta como entidad.** Hoy se entra al caso por el barrido. No hay alerta con
severidad, deduplicación ni agrupación, que es por donde arranca un SOAR de verdad.

**Métricas operativas.** MTTD, MTTR, tiempo por fase, tasa de falsos positivos. Sólo existe
la métrica de detector.

**Registro de consultas.** `situacion` no puede distinguir "mirado y vacío" de "sin mirar"
porque nadie instrumenta las consultas del analista. El skill ve todas las invocaciones y no
persiste ninguna: es el dato que el motor de estado necesita y la orquestación ya tiene.

**El detector dispara de más.** `credencial_origen_nuevo` alerta con cualquier cambio de IP,
y como la credencial del pipeline rota entre `10.20.9.x`, mete dos recomendaciones aun en
ventanas sin incidente. Es un falso positivo del detector, no del recomendador — pero ahora
que la recomendación hereda la calidad del detector, se paga dos veces.

**`casos.py` ocupa la palabra "caso".** En un SOAR un caso es la unidad de trabajo, y acá es
una suite de regresión. Renombrar a "Regresión" cuesta nada y evita el peor malentendido.

**Deuda: `test_credenciales_usadas_dentro_de_su_ventana` es vacuo.** Verifica 3.249 veces una
condición verdadera por construcción — la misma forma de error que las cinco auditorías de
DFIR. Arreglarlo requiere exponer al test las ventanas de validez del generador.

**`tiempo.py` no hace trabajo acá.** El modelo de incertidumbre de reloj vino de DFIR, es
correcto y `eventos.py` normaliza con él. No lo pongas al frente al presentar el proyecto:
abre una conversación forense en medio de una demo de respuesta.

## Decisiones cerradas

- **Respuesta agéntica con humano en el lazo**, no SOAR automatizado. Sin playbooks como
  objeto, y es deliberado.
- Los agentes se lanzan **desde el skill, nunca desde el código**: si Python llamara a la
  API, la suite de regresión dejaría de ser reproducible.
- **El escenario B no se tunea.** Se mide.
- **La verdad no se persiste.** Se regenera desde el seed al medir.
- **Cuatro veredictos**, de bordes nítidos. Lo desconocido cae en `NO-ADJUDICABLE`.
- **La evidencia histórica es inmutable.** Sólo cambia el estado de la respuesta.
- **Ninguna acción entra al catálogo si no declara su efecto sobre el estado.**
- **Se eliminó el sellado SHA-256.** Era forensia heredada y además redundante: la guarda de
  semilla ya comprueba que la evidencia corresponda al escenario, que es más fuerte que "no
  cambió desde que alguien la selló".

## Descartado, y por qué

- **Corriente viva y plan pendiente del atacante.** Que la contención se lea en logs futuros.
  Es la idea más linda del diseño y el pedazo más caro; con el estado de respuesta se
  consigue el 80% del efecto por el 5% del costo.
- **Eje "acertada" y los cuatro cuadrantes.** Es barato —se computa retrospectivamente contra
  la evidencia histórica— y aun así queda afuera: es función de entrenamiento, no de
  operación. Un SOAR dice si la acción corresponde; no puntúa al analista contra una verdad
  que en producción nadie tiene. Primera pieza a reincorporar si el proyecto tiene que servir
  para hablar de criterio.
- **Ejecución real.** No hay integración con nada, y se presenta como simulador.
- **Roles y autoridad.** Es una tabla de permisos evaluando peticiones: es el simulador de
  IAM.
- **Costo operativo cuantificado.** Números declarados por el autor, sin nada contra qué
  contrastar. Queda como texto ordinal.
