# Plan de continuación

Estado al 18 de julio de 2026.

**El objetivo es un mini SOAR simulado y agéntico**: que investigue sobre los 6.500 eventos,
barra, lance agentes, y **proponga acciones con su fundamento**. El diseño conceptual está en
`DISENO.md`, que es más grande que esto a propósito — acá está lo que se construye.

El menú es la estructura del plan. Cada opción es una pieza, y las que faltan están en orden
de dependencia.

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

| | Estado |
|---|---|
| 1 | Detector **construido**. Agentes: arnés escrito, nunca corrido |
| 2 | **Construido** |
| 3 | **Construido** |
| 4 | Falta |
| 5 | Falta |
| 6 | Falta — es la pieza central |
| 7 | Falta |
| 8 | Falta |

Fuera del menú y construido: normalización temporal, cobertura de tres valores, verificador
de citas, integridad y custodia, medición contra la verdad, escenario B retenido.

## El orden, y por qué es ese

**P1 → P3 → P4 → P2 → P5 → P6.**

No es el orden del menú y no es accidental. La recomendación (opción 6) es el punto entero
del proyecto, y construirla después del estado de conocimiento completo deja el laboratorio
sin nada demoable durante mucho tiempo.

Con **P1, P3 y P4** el lazo está entero: barrido con agente, hallazgos verificados,
recomendación con fundamento. Feo pero completo, y a partir de ahí ya se puede decir "mini
SOAR agéntico" sin que sea marketing. **P2, P5 y P6 lo mejoran; no lo habilitan.**

---

## P1 — Correr los agentes (opción 1, mitad faltante)

Primero y barato: el arnés ya existe. Protocolo en el skill, formato en
`hallazgos_prueba.json`, verificador y medición andando.

Lanzar agentes contra A, verificar el archivo de hallazgos, medir. Después contra B **sin
tocar nada**.

Por qué va primero: si un agente no supera al detector determinista, todo lo que sigue se
construiría sobre una premisa sin verificar. El baseline a batir es **63,8% de recall en A y
4,3% en B**.

Cuidado: el agente no puede leer `evidencia/generar_evidencia.py`, `modelo.py` ni `tests.py`.
Ahí está el plan del atacante en Python. Está como regla dura en el skill; conviene además
confirmar qué archivos abrió.

## P2 — Estado de conocimiento (opción 4)

Lo que alimenta a la recomendación, así que va antes.

Tres niveles, que son los veredictos del verificador con otro nombre:

- **Hecho** — afirmación verificada, con cita que la sostiene.
- **Indicio** — compatible con la evidencia, sin verificar o con cita parcial.
- **Desconocido** — nadie consultó esa fuente, ese sujeto o esa ventana.

El tercero es el que cuesta y el que más vale: para saber qué no se miró hay que llevar
registro de qué se consultó. Sin eso, "alcance" es una lista de lo que se encontró y no dice
nada sobre lo que falta.

Sale de: los hallazgos verificados (hecho/indicio) más el modelo de cobertura ya construido
(qué era observable y no se consultó).

## P3 — Catálogo de acciones (opción 5)

Seis a ocho, solo las que el motor pueda evaluar de verdad. **Ninguna acción entra si el
adjudicador no la evalúa**: un catálogo con acciones que no cambian nada se lee como que el
modelo las contempla.

Candidatas: `aislar-host`, `apagar-host`, `revocar-credencial`, `deshabilitar-cuenta`,
`rotar-clave-ssh`, `bloquear-ip`, `capturar-memoria`, `declarar-incidente`.

Cada una declara:

- **precondición**, expresada en el DSL de cuatro campos. Es lo que hace que el veredicto no
  sea una tabla de opiniones del autor: la acción está fundada si existe un conjunto de
  hechos sostenidos, con cita, que satisfacen la precondición declarada.
- **costo operativo**, como texto ordinal del escenario. Sin números inventados.
- **si destruye evidencia recuperable** — apagar un host se lleva la memoria.
- **qué la volvería prematura** — la condición que, de cumplirse, la invalida.

### Veredictos, cuatro y de bordes nítidos

- `FUNDADA` — la precondición se satisface con hechos citables.
- `INFUNDADA` — la evidencia disponible demostrablemente no la sostiene.
- `NO-ADJUDICABLE` — no se puede establecer. **Lo desconocido cae acá, nunca en INFUNDADA.**
  Es la regla que a DFIR le costó cinco auditorías.
- `INAPLICABLE` — el objetivo no existe, o ya está en ese estado.

**Un solo eje: si la acción está fundada.** No se evalúa si "resultó acertada" contra el plan
real del atacante — ver descartes.

## P4 — Motor de recomendación (opción 6)

La pieza central. Dado el estado de conocimiento, qué acciones corresponden ahora.

Una recomendación **nunca sale pelada**. Cada una trae:

- la acción
- los **hechos que la fundan**, con cita
- **de qué depende** — "esto vale si el alcance son estos dos hosts"
- **qué la descartaría** — "si aparece un tercero se vuelve prematura; para saberlo,
  consultá tal cosa"
- el **costo**, ordinal

Una recomendación sin su condición de falsedad es una orden disfrazada de consejo. Es la
diferencia entre un SOAR que asiste y uno que manda.

**La recomendación la deriva el motor, no la redacta el modelo.** El agente traduce y
presenta; el motor decide. Si el LLM escribe recomendaciones libres, vuelve la prosa que
afirma más de lo que el estado respalda.

## P5 — Cronología (opción 7)

Registro de lo decidido: qué acción, en qué momento, con qué se sabía, qué veredicto dio y
qué costo tenía. `custodia.py` ya tiene la estructura de asientos; se extiende a decisiones.

Barato, y es lo que responde en el post-mortem cuando preguntan por qué se apagó el servidor.

## P6 — Catálogo de casos (opción 8)

Los casos donde el veredicto contradice la intuición, cada uno con su `esperado`, como suite
de regresión. Marca de la familia junto con IAM y DFIR.

**Test de viabilidad, antes de escribir el adjudicador:** escribir los casos primero. Si no
salen seis u ocho, el eje da para una checklist y no para un motor.

Candidatos: apagar el host destruye la memoria; aislar sin cerrar alcance deja al atacante en
el host que no se miró; rotar la mitad de las credenciales conserva el acceso y encima avisa;
erradicar sin causa raíz reinfecta; bloquear la IP no sirve cuando el acceso ya es con
credencial válida. Y al menos uno donde la acción obvia **es** la correcta.

---

## Descartado, y por qué

Todo esto está en `DISENO.md` y **no se construye**. Queda acá para no reabrirlo cada vez.

- **Corriente viva y plan pendiente del atacante.** Haría que la consecuencia de una
  contención se lea en los logs en vez de declararse. Es la idea más linda del diseño y el
  pedazo más caro de todo, y un SOAR no lo necesita: recomienda antes, no simula después.
- **Eje "acertada" y los cuatro cuadrantes** (fundada-pero-errada, infundada-pero-acertada).
  Descartado **en firme**, y conviene registrar el argumento correcto porque el primero que
  di era malo: no se descarta por caro. De hecho es barato — se computa retrospectivamente
  contra la evidencia histórica (¿qué eventos del ataque no habrían existido si esta acción
  se tomaba en *t*?) y no necesita corriente viva. Se descarta porque **es una función de
  entrenamiento, no de operación**: un SOAR dice si la acción corresponde, no puntúa al
  analista después contra una verdad que en producción nadie tiene. Si alguna vez el
  proyecto tiene que servir para hablar de criterio y no solo de operación, esta es la
  primera pieza a reincorporar.
- **Ejecución real.** No hay integración con nada. Es un simulador y se presenta como tal.
- **Roles y autoridad.** Es una tabla de permisos evaluando peticiones, o sea el simulador de
  IAM. No agrega concepto nuevo acá.
- **Costo operativo cuantificado.** Los números los declararía el autor y no se contrastan
  contra nada: sería una opinión con formato de métrica.
- **Fases de NIST como estado navegable.** Sin corriente viva no hay progresión que modelar.

## Decisiones cerradas

- Los agentes se lanzan **desde el skill, nunca desde el código**: si Python llamara a la
  API, la suite de regresión dejaría de ser reproducible.
- **El escenario B no se tunea.** Se mide.
- **La verdad no se persiste.** Se regenera desde el seed al medir.
- **Cuatro veredictos**, de bordes nítidos.
- **La evidencia histórica es inmutable.**
- **Ninguna acción entra al catálogo si el motor no la evalúa.**

## Decisiones abiertas

- **¿El motor recomienda y el humano decide, o el agente decide solo?** Cambia qué se mide.
- **¿Escenario C escrito por Ezequiel?** Con B alcanza para sobreajuste grosero, pero los dos
  escenarios los escribí yo, así que no soy evaluador ciego.

## Deuda conocida

- **`test_credenciales_usadas_dentro_de_su_ventana` es vacuo**: no puede fallar. Verifica
  3.249 veces una condición verdadera por construcción — la misma forma de error que las
  cinco auditorías de DFIR. Arreglarlo requiere exponer al test las ventanas de validez del
  generador.
- **Volúmenes arriba del objetivo**: 3249/1954/1329 contra 3000/2000/1000.
- **`tiempo.py` no hace trabajo en este proyecto.** El modelo de incertidumbre temporal
  (deriva de reloj, error propio contra sistemático) vino de DFIR, es correcto y no molesta,
  pero un SOAR no lo necesita. Se conserva porque `eventos.py` normaliza con él; **no
  conviene ponerlo al frente al presentar el proyecto**, porque abre una conversación que no
  lleva a la parte que importa.
- **`clase_operacion()` solo distingue management/data en S3.** El resto cae en
  `desconocida`: honesto pero grueso.
