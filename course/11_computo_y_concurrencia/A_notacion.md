---
id: notacion-computo
title: "Notación de la unidad"
nav_title: "A. Notación"
summary: "La hoja única de símbolos de Cómputo y concurrencia: estados de una tarea, secuencial, concurrente y paralelo, asíncrono, GIL, speedup, Amdahl, Little y topes, evaluados con un solo ejemplo de tres tareas."
status: ready
tags: [concurrencia, notacion, gantt, amdahl, little]
prerequisites: [computo-y-concurrencia]
---

# Notación de la unidad

**Anexo · Cómputo y concurrencia** · Pregunta: ¿qué significa exactamente cada símbolo que usan las ocho páginas? · Meta: que cualquier Gantt de la unidad se pueda verificar con estas definiciones y una cuenta.

Las páginas introducen los símbolos poco a poco (la tabla del final dice cuál entra dónde). Esta hoja los junta, y si una página dice otra cosa, **manda esta hoja**.

## En corto

- **Una tarea vive en un intervalo y en cada instante está en uno de cuatro estados**: ejecuta, espera, lista o bloqueada. Los cuatro suman su vida.
- **Secuencial, concurrente y paralelo son propiedades de una traza**, no de una biblioteca. Todo lo paralelo es concurrente; asíncrono no es un cuarto caso, es cómo cede el hilo quien espera.
- **Un solo ejemplo** (3 tareas de 20 ms + 200 ms + 20 ms) se evalúa aquí completo: 720 ms en secuencia, 280 ms con `gather`, 2080 ms si una tarea calcula dentro del loop.

## Convenciones

- **Frontera.** Se observa un sistema concreto, casi siempre el cliente. La CPU del servidor remoto no es CPU del cliente: desde el cliente, el trabajo del servidor es espera.
- **Granularidad.** Se fija un conjunto de tareas y se compara siempre sobre ese mismo conjunto. Cada tarea es **un flujo secuencial**: ocupa a lo más una CPU a la vez. Si por dentro reparte trabajo, sus subtareas son otro conjunto, a otra escala.
- **Intervalos semiabiertos.** $[a,b)$ incluye $a$ y excluye $b$. Por eso $[0,240)$ y $[240,480)$ se tocan en 240 y **no** se solapan: la barra siguiente del Gantt empieza en el mismo punto donde acaba la anterior.
- **Unidades.** Las trazas ilustrativas van en milisegundos; las mediciones reales, en segundos.

## Tiempo y tareas

| Símbolo | Significado | Nota |
|---|---|---|
| $t$ | un instante, $t \ge 0$ | el conjunto de instantes no lleva letra propia; $T$ es otra cosa |
| $\operatorname{dur}(X)$ | duración total de un conjunto de instantes $X$: suma de las longitudes de sus intervalos disjuntos | $\operatorname{dur}([0,20)\cup[220,240)) = 40$ |
| $\mathcal{T}=\{\tau_1,\dots,\tau_n\}$ | las tareas observadas; $n$ es cuántas son | $\tau_i$ nombra una tarea, no una duración ni necesariamente un `asyncio.Task` |
| $\operatorname{arrival}(\tau)$ | instante en que llega la solicitud | puede ser anterior a su inicio: la solicitud espera en una cola de entrada |
| $\operatorname{start}(\tau)$ | instante en que el sistema observado **admite** la tarea | en `asyncio`, al crear la tarea; con hilos, al arrancar el hilo; en un servidor, cuando un hilo toma la conexión |
| $\operatorname{end}(\tau)$ | instante en que termina | $\operatorname{arrival}\le\operatorname{start}<\operatorname{end}$ |
| $\operatorname{vida}(\tau)=[\operatorname{start}(\tau),\operatorname{end}(\tau))$ | ciclo de vida | todo estado de la tarea cae dentro |
| $d(\tau)=\operatorname{end}(\tau)-\operatorname{start}(\tau)$ | duración de la vida | |
| $\operatorname{latencia}(\tau)=\operatorname{end}(\tau)-\operatorname{arrival}(\tau)$ | lo que percibe quien pidió | incluye la cola previa; coincide con $d$ si $\operatorname{arrival}=\operatorname{start}$ |

## Los cuatro estados de una tarea

| Estado | Símbolo | Qué pasa | Ejemplos |
|---|---|---|---|
| ejecuta | $\operatorname{exec}(\tau)$ | una CPU corre instrucciones de $\tau$ | parsear un JSON, `calcula()` |
| espera | $\operatorname{wait}(\tau)$ | $\tau$ espera algo **externo al programa**: red, disco, temporizador | la respuesta HTTP, `asyncio.sleep`, `time.sleep` |
| lista | $\operatorname{ready}(\tau)$ | $\tau$ podría avanzar, pero **no tiene turno**: le falta CPU, el GIL o el hilo del loop | la respuesta llegó y el loop sigue ocupado con otra tarea |
| bloqueada | $\operatorname{blocked}(\tau)$ | $\tau$ espera algo que **otra tarea del mismo programa** tiene que soltar o producir | permiso de un `Semaphore`, un `Lock`, una conexión del pool, el resultado de otra tarea |

Los cuatro conjuntos están contenidos en la vida, son disjuntos dos a dos y la cubren entera (una **partición**; $\sqcup$ es unión de conjuntos disjuntos):

$$\operatorname{vida}(\tau)=\operatorname{exec}(\tau)\sqcup\operatorname{wait}(\tau)\sqcup\operatorname{ready}(\tau)\sqcup\operatorname{blocked}(\tau)$$

Con $e=\operatorname{dur}(\operatorname{exec})$, $w=\operatorname{dur}(\operatorname{wait})$, $r=\operatorname{dur}(\operatorname{ready})$ y $b=\operatorname{dur}(\operatorname{blocked})$:

$$d(\tau)=e+w+r+b$$

Mientras no hay semáforos, locks ni pools, $b=0$ y las páginas omiten `blocked`.

**La prueba operativa** para clasificar un tramo:

1. «Si ahora mismo le doy una CPU libre, y con ella el GIL y el hilo del loop, ¿avanza?» **Sí → `ready`.**
2. Si no avanza, ¿qué tiene que ocurrir? Algo fuera del programa (llega un paquete, termina el disco, vence un temporizador) → **`wait`**. Otra tarea del programa suelta un permiso, un lock o una conexión, o entrega un resultado → **`blocked`**.

Dos consecuencias de esta convención:

- **Esperar el GIL es `ready`**, no `blocked`: el GIL es parte del turno de ejecución, como la CPU. Por eso los hilos de cálculo que no ejecutan se dibujan rayados («lista, sin turno»).
- **`time.sleep` dentro del loop** deja a esa tarea en `wait`, pero sin soltar el hilo del loop: todas las demás pasan a `ready`. Eso es exactamente lo que significa una llamada síncrona.

## Medidas de una tarea y de un lote

| Símbolo | Definición | Cómo se mide o se lee |
|---|---|---|
| $\rho(\tau)=e/d$ | fracción de la vida que ejecuta, **medida con la tarea sola** ($r=b=0$) | CPU-bound: $\rho\approx1$; I/O-bound: $\rho$ pequeño. Nombra el cuello de botella, no la ausencia de E/S |
| $T=\max_i\operatorname{end}(\tau_i)-\min_i\operatorname{start}(\tau_i)$ | tiempo total del lote (*makespan*) | `time.perf_counter()` antes y después del lote |
| $C=\sum_i e_i$ | tiempo de CPU del lote | lo aproxima `time.process_time()`, con las advertencias del final |
| $\operatorname{ExecutingAt}(t)=\{\tau_i : t\in\operatorname{exec}(\tau_i)\}$ | tareas ejecutando en el instante $t$ | un trazo vertical en el Gantt, contando sólo barras de ejecución |
| $P$ | CPU lógicas disponibles | `os.cpu_count()`, u `os.process_cpu_count()` (3.13+) si hay afinidad; $\operatorname{card}(\operatorname{ExecutingAt}(t))\le P$ |
| $U=C/(P\cdot T)$ | utilización de la CPU | área ocupada de las filas de CPU entre su área total |

En la unidad 3, $P$ también se usó para rendimiento; aquí $P$ son siempre **CPU lógicas** (con SMT, dos por núcleo físico). Una cuota como `docker --cpus` no cambia `os.cpu_count()`, pero sí limita cuánta CPU recibes.

## Secuencial, concurrente, paralelo

| Propiedad | Definición sobre $\mathcal{T}$ fijo | En el Gantt |
|---|---|---|
| secuencial | $\forall i\ne j:\ \operatorname{vida}(\tau_i)\cap\operatorname{vida}(\tau_j)=\varnothing$ | ningún par de vidas se traslapa; tocarse en un borde no cuenta |
| concurrente | $\exists i\ne j:\ \operatorname{dur}(\operatorname{vida}(\tau_i)\cap\operatorname{vida}(\tau_j))>0$ | algún trazo vertical corta dos o más vidas |
| solapa esperas | $\exists i\ne j:\ \operatorname{dur}(\operatorname{wait}(\tau_i)\cap\operatorname{exec}(\tau_j))>0$ | un trazo vertical corta una espera de una tarea y una ejecución de otra |
| paralelo | $\exists i\ne j:\ \operatorname{dur}(\operatorname{exec}(\tau_i)\cap\operatorname{exec}(\tau_j))>0$ | dos filas de CPU ocupadas en el mismo instante; exige $P\ge2$ |

Con intervalos semiabiertos, «la intersección no es vacía» y «la intersección dura algo» son lo mismo, así que **concurrente = no secuencial**.

**Teorema.** Paralelo $\Rightarrow$ concurrente, y solapa esperas $\Rightarrow$ concurrente.

**Prueba.** Por definición $\operatorname{exec}(\tau)\subseteq\operatorname{vida}(\tau)$ y $\operatorname{wait}(\tau)\subseteq\operatorname{vida}(\tau)$. Entonces

$$\operatorname{exec}(\tau_i)\cap\operatorname{exec}(\tau_j)\subseteq\operatorname{vida}(\tau_i)\cap\operatorname{vida}(\tau_j)$$

y la duración de un subconjunto no excede la del conjunto. Si la izquierda dura algo positivo, la derecha también: las vidas se solapan. El mismo argumento vale con $\operatorname{wait}(\tau_i)\cap\operatorname{exec}(\tau_j)$. $\square$

El recíproco es falso: con `gather` (abajo) las vidas se solapan y nunca ejecutan dos tareas a la vez.

### La matriz: tres casos, no cuatro

| | No paralelo | Paralelo |
|---|---|---|
| **No concurrente** | secuencial: vidas disjuntas | **imposible** con las mismas tareas (teorema) |
| **Concurrente** | vidas solapadas, ejecución por turnos: hilos con GIL, `asyncio` | ejecución simultánea: procesos |

Quedan tres casos: secuencial; concurrente sin paralelismo; concurrente y paralelo.

**Nota sobre el cambio de escala.** «Paralelo sin concurrente» aparece sólo si cuentas tareas distintas para cada propiedad. Una operación de tu programa (una tarea, ni concurrente ni paralela a tu escala) puede repartir trabajo por dentro: una multiplicación de matrices con BLAS lo reparte en hilos, que a **su** escala son paralelos **y** concurrentes. SIMD es otra cosa: una sola instrucción opera sobre varios datos en un núcleo; es paralelismo de datos, no de tareas, y $\operatorname{card}(\operatorname{ExecutingAt}(t))$ sigue valiendo 1. Una ufunc como `arr * arr` corre en un núcleo; una matmul grande puede dar CPU/reloj mayor que 1.

## Asíncrono: un mecanismo, no una celda

Sea $\operatorname{hilo}(\tau)$ el hilo del sistema operativo que ejecuta $\tau$.

- **Llamada síncrona.** Mientras la operación está pendiente, $\operatorname{hilo}(\tau)$ queda bloqueado: ninguna otra tarea de ese hilo ejecuta.
- **Llamada asíncrona.** La llamada **regresa antes del resultado** con un pendiente (un futuro, una `Task`). Cuando $\tau$ necesita el resultado hace `await`, **se suspende y devuelve su hilo** al planificador (el event loop), que da el turno a otra tarea lista.
- **Consecuencia medible:** $\exists i\ne j$ con $\operatorname{hilo}(\tau_i)=\operatorname{hilo}(\tau_j)$ y $\operatorname{dur}(\operatorname{wait}(\tau_i)\cap\operatorname{exec}(\tau_j))>0$. Solapar esperas **dentro de un mismo hilo** sólo es posible si quien espera cedió el hilo. Con hilos, el solapamiento ocurre entre hilos distintos.
- **Lo que el Gantt solo no dice.** El Gantt de ocupación de hilos y el de `asyncio` son idénticos (ver el ejemplo). Para distinguirlos hace falta la fila de hilo o los eventos de suspensión y reanudación.
- **Asíncrono no implica concurrente.** Una interfaz asíncrona usada con `await` uno tras otro da un Gantt secuencial: el mismo de 720 ms.

Dos precisiones de Python: llamar una función `async def` sólo crea una corrutina, que no corre hasta que se agenda (`create_task`, `gather`) o se espera con `await`; y un `await` sobre un resultado que ya está listo no suspende.

**Cooperativo contra preventivo.**

| Planificación | Quién saca a una tarea de `exec` | Consecuencia |
|---|---|---|
| cooperativa (event loop) | la propia tarea, en un `await` que suspende, o al terminar | un cálculo sin `await` deja en `ready` a todas las demás tareas del loop |
| preventiva (hilos, procesos) | el sistema operativo; en CPython, además, el GIL cada `sys.getswitchinterval()` (5 ms por omisión) | ningún hilo acapara la CPU, pero el turno lo decide el sistema, no tu código |

Una respuesta que llega habilita a su tarea (pasa de `wait` a `ready`); **no interrumpe** a la que está ejecutando.

## El GIL, por intérprete

La ejecución de bytecode de Python es una parte de la ejecución:

$$\operatorname{exec}_{\mathrm{Python}}(\tau)\subseteq\operatorname{exec}(\tau)$$

**Restricción.** Para cada intérprete $I$ con GIL y cada instante $t$:

$$\operatorname{card}\{\tau \text{ de } I : t\in\operatorname{exec}_{\mathrm{Python}}(\tau)\}\le1$$

- En este curso, **un intérprete por proceso**. Los subintérpretes existen, pero no se usan aquí.
- **No impone $P=1$.** El código nativo que suelta el GIL puede ejecutar en otra CPU mientras un hilo ejecuta Python.
- Las demás tareas del mismo intérprete que quieren ejecutar Python están en `ready`.
- **Sueltan el GIL:** las llamadas bloqueantes de E/S y `time.sleep`; las extensiones en C que lo liberan (muchas operaciones de NumPy y BLAS, no todas); y la compilación *free-threaded*, opcional y con soporte oficial desde Python 3.14 (PEP 779, 2025).
- Un event loop ejecuta una tarea a la vez por su planificación cooperativa, **con o sin GIL**.

## El ejemplo único

Tres tareas iguales. Cada una **ejecuta 20 ms, espera 200 ms la red y ejecuta 20 ms**: $e=40$, $w=200$, $d=240$ ms si corre sola. Es una **traza ilustrativa**, no una medición. Las tres llegan en $t=0$ ($\operatorname{arrival}=0$), con un hilo, $P=1$ y sin costos de coordinación.

Con la tarea sola: $\rho=40/240=1/6\approx16.7\%$. Cinco sextos de su vida espera: es I/O-bound.

### Versión secuencial (o `await` uno tras otro): 720 ms

| Tarea | start | end | exec | wait | ready |
|---|---:|---:|---|---|---|
| $\tau_1$ | 0 | 240 | $[0,20)\cup[220,240)$ | $[20,220)$ | $\varnothing$ |
| $\tau_2$ | 240 | 480 | $[240,260)\cup[460,480)$ | $[260,460)$ | $\varnothing$ |
| $\tau_3$ | 480 | 720 | $[480,500)\cup[700,720)$ | $[500,700)$ | $\varnothing$ |

- **Secuencial:** las vidas $[0,240)$, $[240,480)$ y $[480,720)$ son disjuntas (240 pertenece a la segunda, no a la primera).
- $T=720=\sum_i d_i=3\times240$. Sólo en secuencia el total es la suma de las vidas, y sólo si no hay huecos entre ellas.
- $C=3\times40=120$ ms; $\max_t\operatorname{card}(\operatorname{ExecutingAt}(t))=1$; $U=120/(1\times720)=16.7\%$.
- **Latencia contra vida.** $d=240$ para las tres, pero $\operatorname{latencia}=240,\ 480,\ 720$: $\tau_3$ pasa 480 ms en la cola antes de su $\operatorname{start}$. Latencia media: 480 ms.

### Versión con `gather` (o con tres hilos): 280 ms

| Tarea | start | end | exec | wait | ready |
|---|---:|---:|---|---|---|
| $\tau_1$ | 0 | 240 | $[0,20)\cup[220,240)$ | $[20,220)$ | $\varnothing$ |
| $\tau_2$ | 0 | 260 | $[20,40)\cup[240,260)$ | $[40,240)$ | $[0,20)$ |
| $\tau_3$ | 0 | 280 | $[40,60)\cup[260,280)$ | $[60,260)$ | $[0,40)$ |

El mismo Gantt como texto (columnas no a escala; E ejecuta, W espera, R lista, — terminada):

| | 0–20 | 20–40 | 40–60 | 60–220 | 220–240 | 240–260 | 260–280 |
|---|---|---|---|---|---|---|---|
| τ1 | E | W | W | W | E | — | — |
| τ2 | R | E | W | W | W | E | — |
| τ3 | R | R | E | W | W | W | E |
| CPU | τ1 | τ2 | τ3 | ociosa | τ1 | τ2 | τ3 |

Evaluación, paso a paso:

1. **Partición.** $e=(40,40,40)$, $w=(200,200,200)$, $r=(0,20,40)$, $b=0$. Entonces $d_1=40+200+0=240$, $d_2=40+200+20=260$, $d_3=40+200+40=280$. Coincide con $\operatorname{end}-\operatorname{start}$.
2. **Concurrente.** $\operatorname{vida}(\tau_1)\cap\operatorname{vida}(\tau_2)=[0,240)$, que dura 240 ms $>0$.
3. **Solapa esperas.** $\operatorname{exec}(\tau_2)\cap\operatorname{wait}(\tau_1)=[20,40)$, 20 ms $>0$. Con `asyncio` las tres comparten hilo, así que $\tau_1$ **cedió** el hilo: asíncrono. Con hilos, el mismo solapamiento ocurre entre hilos distintos.
4. **No paralelo.** $\operatorname{ExecutingAt}(30)=\{\tau_2\}$, $\operatorname{ExecutingAt}(100)=\varnothing$, $\operatorname{ExecutingAt}(230)=\{\tau_1\}$; nunca hay dos: $\max_t\operatorname{card}(\operatorname{ExecutingAt}(t))=1\le P$.
5. **Tiempo y CPU.** $T=280$; $C=120$; CPU ociosa $280-120=160$ ms, el tramo $[60,220)$; $U=120/280=42.9\%$.
6. **Las esperas no se suman.** $\sum_i w_i=600$ ms y el lote dura 280: las esperas se solapan, así que su suma no es el ocio de nadie.
7. **Speedup sobre la secuencia:** $720/280\approx2.57$. **Latencias:** 240, 260 y 280 ms (media 260, contra 480 en secuencia).
8. **Tareas en vuelo en promedio:** $L=\sum_i d_i/T=(240+260+280)/280=780/280\approx2.79$; en secuencia $720/720=1$.

### Variante: una tarea calcula dentro del loop (2080 ms)

Se cambia $\tau_3$ por un **cálculo de 2000 ms sin ningún `await`**; $\tau_1$ y $\tau_2$ siguen iguales, en el mismo loop.

| Tarea | start | end | exec | wait | ready |
|---|---:|---:|---|---|---|
| $\tau_1$ | 0 | 2060 | $[0,20)\cup[2040,2060)$ | $[20,220)$ | $[220,2040)$ |
| $\tau_2$ | 0 | 2080 | $[20,40)\cup[2060,2080)$ | $[40,240)$ | $[0,20)\cup[240,2060)$ |
| $\tau_3$ | 0 | 2040 | $[40,2040)$ | $\varnothing$ | $[0,40)$ |

- **Partición.** $d_1=40+200+1820=2060$; $d_2=40+200+(20+1820)=2080$; $d_3=2000+0+40=2040$.
- Las respuestas llegan a los 220 y 240 ms; nadie las atiende hasta que el cálculo suelta el loop. $T=2080$.
- $C=40+40+2000=2080=T$, así que $U=100\%$. **La CPU nunca estuvo ociosa y aun así las dos peticiones tardaron 2060 y 2080 ms en vez de 240 y 260.** Utilización alta no significa buen servicio.
- **Regla de arquitectura:** no calcules en el loop; descarga el cálculo a otro proceso (*offload*). Con la frontera puesta en las tareas del loop, el cálculo que corre en otro proceso cuenta como `wait` de $\tau_3$, igual que la red, y $\tau_1$ y $\tau_2$ vuelven a terminar en 240 y 260 ms.

### Variante: tres procesos sobre dos CPU (260 ms)

Las mismas tres tareas del ejemplo, una por proceso, con $P=2$:

| Tarea | exec | wait | ready |
|---|---|---|---|
| $\tau_1$ | $[0,20)\cup[220,240)$ (CPU 1) | $[20,220)$ | $\varnothing$ |
| $\tau_2$ | $[0,20)\cup[220,240)$ (CPU 2) | $[20,220)$ | $\varnothing$ |
| $\tau_3$ | $[20,40)\cup[240,260)$ (CPU 1) | $[40,240)$ | $[0,20)$ |

- **Paralelo:** $\operatorname{ExecutingAt}(10)=\{\tau_1,\tau_2\}$, de cardinal $2\le P=2$; $\operatorname{dur}(\operatorname{exec}(\tau_1)\cap\operatorname{exec}(\tau_2))=40$ ms. Por el teorema, también es concurrente.
- $T=260$; speedup sobre la secuencia $720/260\approx2.77$. Pasar de 2× con 2 CPU no contradice nada: la mejora viene sobre todo de solapar esperas, no de calcular a la vez (contra hilos sólo se ganan 20 ms).
- $U=120/(2\times260)\approx23.1\%$. Las dos CPU están ociosas en $[40,220)$, 180 ms. Con varias CPU, $T-C$ deja de ser el ocio.

## Propiedades que se leen en un Gantt

La clasificación es de **la ejecución dibujada**: una biblioteca no la garantiza por sí sola.

| Ejecución ilustrada | Dónde | Concurrente | Solapa esperas | Máx. ejecutando | Paralela | Interfaz asíncrona |
|---|---|:---:|:---:|:---:|:---:|---|
| llamadas bloqueantes una por una | `cmp-gantt-secuencial` | no | no | 1 | no | no |
| `await` uno tras otro | `cmp-gantt-await-en-serie` | no | no | 1 | no | sí |
| dos hilos que sólo calculan, por turnos del GIL | página 2 | sí | no | 1 | no | no se deduce |
| hilos con E/S bloqueante | `cmp-gantt-hilos` | sí | sí | 1 | no | no, en cada hilo |
| corrutinas con `gather` en un loop | `cmp-gantt-asyncio` | sí | sí | 1 | no | sí |
| trabajos sólo de CPU en dos procesos | página 6 | sí | no | 2 | sí | no se deduce |
| tareas mixtas en tres procesos sobre dos CPU | `cmp-gantt-procesos` | sí | sí | 2 | sí | no se deduce |

Para verificar una figura:

- Cada tarea está en **exactamente un estado** en cada instante de su vida.
- La capacidad de CPU se comprueba contando **sólo** barras de ejecución; el solapamiento de vidas, contando también esperas, listas y bloqueadas.
- Cada fila de CPU dice qué representa (una CPU, el GIL de un proceso, el hilo del loop).
- **Ningún paralelismo se deduce de que el total bajó**: el ejemplo con `gather` baja de 720 a 280 ms con una sola CPU.
- Convención gráfica: ejecuta relleno, espera con contorno, **lista rayada**; la barra siguiente empieza en el mismo $x$ donde termina la anterior.

## Rendimiento: speedup, eficiencia, pools, Amdahl

| Símbolo | Definición | Nota |
|---|---|---|
| $N$ | trabajadores entre los que se reparte (hilos, procesos) | no confundir con $P$ (CPU) ni con $n$ (tareas) |
| $k$ | tope real de lo que corre o está en vuelo: procesos de un pool, permisos de un semáforo, conexiones de un pool | en un pool de procesos, $N=k$ |
| $T(N)$ | tiempo total con $N$ trabajadores | |
| $S=T_{\text{base}}/T_{\text{nueva}}$ | speedup; **siempre se declara la base** | sin unidades; $S<1$ significa que empeoró |
| $S(N)=T(1)/T(N)$ | speedup contra un trabajador | |
| $E(N)=S(N)/N$ | eficiencia | 1 es reparto perfecto |
| $\operatorname{speedup}_{\text{pool}}(k)=T_{\text{pool}}(1)/T_{\text{pool}}(k)$ | el pool contra sí mismo con un trabajador | esconde el costo de tener pool |
| $\operatorname{speedup}_{\text{aplicación}}(k)=T_{\text{secuencial}}/T_{\text{pool}}(k)$ | contra la versión directa, sin pool | lo que gana tu programa |
| $f$ | fracción serial: parte de $T(1)$ que no se reparte | se escribe $f$, no $S$, para no chocar con speedup |
| $h(k)$ | costos que crecen con el número de trabajadores: arrancar procesos, serializar, IPC | un costo fijo cabe en $f$; uno que crece con $k$, no |

**Pool con tareas iguales.** Para $n$ tareas iguales, independientes, indivisibles y sólo de CPU, de duración $c$ cada una, y $k\le P$ procesos:

$$T_{\text{pool}}(k)\approx\left\lceil n/\min(k,P)\right\rceil c+h(k)$$

Con $k\le P$, $\min(k,P)=k$. Con $k>P$ la fórmula deja de ser exacta: el sistema operativo reparte las $P$ CPU entre los $k$ procesos y el resultado depende de cómo los intercale. Lo que no cambia es que $T\ge n\,c/P$: más procesos que CPU no agregan capacidad. La regla práctica es $k=\min(n,P)$.

**Ejemplo (traza ilustrativa).** $n=3$ tareas de cálculo de $c=400$ ms; secuencial, $T=1200$ ms. Con $h=0$:

| $k$ | $P$ | Cuenta | $T$ (ms) | $S$ | $E$ |
|---:|---:|---|---:|---:|---:|
| 1 | 8 | $\lceil3/1\rceil\times400$ | 1200 | 1 | 1 |
| 2 | 8 | $\lceil3/2\rceil\times400$ | 800 | 1.5 | 0.75 |
| 3 | 8 | $\lceil3/3\rceil\times400$ | 400 | 3 | 1 |
| 4 | 8 | $\lceil3/4\rceil\times400$ | 400 | 3 | 0.75 |
| 3 | 2 | $T\ge3\times400/2$ | $\ge600$ | $\le2$ | — |

Con $k=2$ el reparto es perfecto en la primera tanda y la tercera tarea corre sola: la granularidad, no Amdahl, fija el 1.5. Si el pool cuesta $h=20$ ms con cualquier $k$: $T_{\text{pool}}(1)=1220$ y $T_{\text{pool}}(2)=820$, así que $\operatorname{speedup}_{\text{pool}}(2)=1220/820\approx1.49$ y $\operatorname{speedup}_{\text{aplicación}}(2)=1200/820\approx1.46$.

**Ley de Amdahl.** Si una fracción $f$ de $T(1)$ no se reparte y el resto se reparte perfectamente entre $N$ trabajadores:

$$T(N)=T(1)\left(f+\frac{1-f}{N}\right),\qquad S(N)=\frac{1}{f+(1-f)/N},\qquad \lim_{N\to\infty}S(N)=\frac{1}{f}$$

Supone carga fija, $f$ constante, parte repartible divisible tanto como haga falta, trabajadores equivalentes, $N\le P$ y ningún costo que crezca con $N$. Si alguno falla, $T_{\text{real}}(N)=T(1)\,(f+(1-f)/N)+h(N)$. Con tareas indivisibles, además, $S\le\min(N,P,n)$. Amdahl no es un límite entre implementaciones distintas: vectorizar o cambiar de algoritmo cambia $T(1)$.

**Con la medición de referencia** (`calcula`, 4 tareas, pool de 1, 2 y 4 procesos; una corrida en una máquina de 8 CPU lógicas; tus cifras serán otras): $T_{\text{pool}}=1.45$, $0.75$ y $0.54$ s.

- $\operatorname{speedup}_{\text{pool}}(2)=1.45/0.75\approx1.93$, $E\approx0.97$; $\operatorname{speedup}_{\text{pool}}(4)=1.45/0.54\approx2.69$, $E\approx0.67$.
- Ajuste $T(N)=a+b/N$: de $a+b=1.45$ y $a+b/2=0.75$ salen $b=2\times(1.45-0.75)=1.40$ y $a=0.05$. Predice $T(4)=0.05+1.40/4=0.40$ s; medido, 0.54: el modelo no ajusta el punto que queda.
- $f=a/T(1)=0.05/1.45\approx0.034$. Amdahl da $S(2)\approx1.93$, $S(4)\approx3.62$ (medido, 2.69) y techo $1/f\approx29$; con $n=4$ tareas, nunca más de 4.
- Advertencias: son 3 puntos para 2 parámetros (un solo grado de libertad para comprobar) y una sola corrida. Que los 0.14 s de más en $T(4)$ sean arranque de procesos e IPC es una hipótesis, no una medición. Es speedup **del pool**: no hay una versión directa sin pool en esa tabla.

**Vectorizar no es $S(N)$.** Bucle contra NumPy, $0.141/0.0091\approx15.5$: es un speedup contra otra implementación en el mismo núcleo, no un reparto entre trabajadores. No prueba paralelismo ni mide SIMD.

## Ley de Little y topes

| Símbolo | Definición |
|---|---|
| $L$ | tareas en vuelo en promedio, dentro de la frontera que eliges |
| $\lambda$ | tareas que terminan por segundo (rendimiento), en régimen estable |
| $W$ | tiempo medio que una tarea pasa dentro de la frontera |
| $W_{\text{recurso}}$, $W_{\text{conexión}}$ | tiempo medio que una tarea **retiene** un recurso concreto (la conexión, desde que la presta hasta que la devuelve); no es la latencia de toda la petición |

$$L=\lambda\cdot W$$

Con todas las tareas dentro de la ventana medida, $L=\sum_i d_i/T$. Si a lo más $k$ tareas pueden estar en vuelo, $L\le k$ y por tanto

$$\lambda\le\frac{k}{W}$$

**Cota del semáforo.** Con $n$ tareas iguales que retienen un permiso durante toda su duración $e+w$ y un tope de $k$ permisos, algún permiso atiende por lo menos $\lceil n/k\rceil$ tareas una tras otra:

$$T\ge\left\lceil n/k\right\rceil\cdot(e+w)$$

Es una cota inferior: las listas, el arranque y los costos del loop se suman encima.

**Aplicaciones con números.**

| Caso | Cuenta | Resultado |
|---|---|---|
| ejemplo único con `Semaphore(2)` | $\lceil3/2\rceil\times240$ | $T\ge480$ ms (contra 280 sin tope) |
| servidor secuencial, $k=1$, $W=0.202$ s | $\lambda\le1/0.202$ | $\le4.95$ peticiones/s |
| 20 llamadas en serie, $T=4.04$ s | $\lambda=20/4.04$, $W=0.202$ | $L=4.95\times0.202=1.0$ |
| 20 llamadas con 32 hilos, $T=0.23$ s | $\lambda=20/0.23\approx87$/s, $W\approx0.202$ | $L\approx17.6$, igual al speedup $4.04/0.23$: con tareas iguales, speedup = concurrencia media |
| tope 32, $W=0.2$ s | $\lambda\le32/0.2$ | $\le160$/s; 500 llamadas $\ge500/160=3.125$ s |
| 500 llamadas, cota del semáforo | $\lceil500/32\rceil\times0.2=16\times0.2$ | $\ge3.2$ s (medido: 3.32 con hilos, 3.39 con `asyncio`) |
| 100 llamadas, cota del semáforo | $\lceil100/32\rceil\times0.2=4\times0.2$ | $\ge0.8$ s |
| pool de BD, $\lambda=50$/s, $W=0.2$ s (cifras supuestas) | $L=50\times0.2$ | 10 conexiones en uso: un pool de 10 justo alcanza |
| la misma BD con $W=2$ s | $L=50\times2=100>10$ | con tope 10, $\lambda\le10/2=5$/s: las otras 45/s hacen cola; hacen falta timeouts y *backpressure* |

Little dimensiona semáforos, pools y colas con la misma cuenta: **conexiones en uso = $\lambda\cdot W$**. Un tope no es un *rate limit*: $\lambda\le k/W$ depende de $W$, y si la dependencia se vuelve lenta el mismo tope deja pasar menos.

## Advertencias de medición

- **El 99.4 % no es $\sum w$.** En 20 llamadas en serie, $T=4.04$ s y `process_time` da $C\approx0.02$ s: $C/T\approx0.6\%$ y $(T-C)/T\approx99.4\%$. Ese 99.4 % es **tiempo sin CPU del cliente**: en este experimento lo domina la espera de red, pero también incluye turnos y otros efectos. Si sólo eliminaras los 0.02 s de CPU, el speedup máximo sería $4.04/4.01\approx1.0075$: lo que hay que reorganizar son las esperas.
- **`process_time` mide el proceso, no una tarea.** Suma la CPU de todos los hilos del proceso, así que con hilos o con NumPy/BLAS puede dar más segundos de CPU que de reloj (CPU/reloj $>1$: paralelismo). **No cuenta procesos hijos**: con un pool de procesos da casi 0 en el padre. Para los hijos usa `os.times()` (campos `children_user` y `children_system`), que sólo los cuenta cuando ya terminaron y fueron esperados.
- **Una corrida es una corrida.** Las cifras reales de esta hoja son de referencia; el ruido entre corridas puede ser del orden de las diferencias pequeñas (20 ms entre hilos y procesos, 0.07 s entre hilos y `asyncio`).

## Qué símbolo entra en qué página

| Pág. | Página | Entra | Se evalúa con |
|---:|---|---|---|
| 1 | [[donde-pasa-el-tiempo]] | $t$, $[a,b)$, $\operatorname{dur}$, $\tau_i$, $n$, arrival/start/end, vida, $d$, latencia, exec/wait/ready, partición, $e$, $w$, $r$, $\rho$, $T$, $C$; Little con $k=1$: $\lambda=1/W$ | $\tau_1$ sola (240 ms, $\rho=1/6$); 20 llamadas en serie (4.04 s, 99.3 % sin CPU) |
| 2 | [[secuencial-concurrente-paralelo]] | secuencial, concurrente, solapa esperas, paralelo, $\operatorname{ExecutingAt}$, $P$, $U$, teorema, matriz de tres casos, GIL con $\operatorname{exec}_{\mathrm{Python}}$ | secuencial 720 ms, hilos 280 ms, procesos 260 ms |
| 3 | [[asincrono-y-el-event-loop]] | $\operatorname{hilo}(\tau)$, síncrono y asíncrono, cooperativo y preventivo, `ready` dentro del loop | `gather` 280 ms; `await` en serie 720 ms; bloqueo del loop 2080 ms |
| 4 | [[concurrencia-acotada]] | `blocked`, $k$ como permisos, $L=\lambda W$, $\lambda\le k/W$, $\lceil n/k\rceil(e+w)$ | 500 llamadas con tope 32 ($\ge3.2$ s) |
| 5 | [[pools-y-recursos]] | $k$ como conexiones, `blocked` en el pool, conexiones en uso $=\lambda W$ | 20 peticiones de 0.2 s con 5 conexiones: $\lceil20/5\rceil\times0.2=0.8$ s |
| 6 | [[calcular-en-paralelo]] | $N$, $S(N)$, $E(N)$, speedup del pool contra el de la aplicación, $T_{\text{pool}}(k)$, $h(k)$, $f$, Amdahl | `calcula` con 1, 2 y 4 procesos |
| 7 | [[vectorizar]] | cambio de escala: SIMD y BLAS por debajo de la tarea | bucle contra NumPy, 15.8× en un núcleo |
| 8 | [[arquitectura-y-estrategia]] | ninguno nuevo: Little para capacidad, todo junto | los tres casos de diseño |

Vuelve a [[computo-y-concurrencia]].
