---
id: asyncio-y-el-event-loop
title: "asyncio y el event loop"
nav_title: "asyncio y el event loop"
summary: "Un solo hilo puede esperar cientos de respuestas a la vez si cada espera cede el control con await. El event loop reparte ese hilo entre corrutinas, y un cálculo largo dentro del loop lo detiene todo."
status: ready
estimated_time: 25m
tags: [asyncio, event-loop, corrutinas, await, gather, semaphore, httpx, run-in-executor]
prerequisites: [concurrente-paralelo-asincrono]
---

# asyncio y el event loop

**Página 3 de 5 · Cómputo y concurrencia**

Meta: esperar 100 o 500 respuestas con un solo hilo, y saber qué línea de código rompe esa ganancia.

La pregunta: **¿cómo espera 100 peticiones un solo hilo?** Los hilos ya solapan esperas (ver [[concurrente-paralelo-asincrono]]), pero cada hilo cuesta memoria y el sistema operativo decide cuándo cambiarlo. `asyncio` hace lo mismo con un hilo y con cambios que decide tu código.

| Término | Definición de una línea | Lo ves en |
|---|---|---|
| **corrutina** | Función definida con `async def`; al llamarla no corre, devuelve un objeto que alguien tiene que esperar | celda 3.1 |
| **`await`** | Obtiene el resultado de lo esperado; cede el control al loop sólo si la operación se suspende | celda 3.1 |
| **tarea** (`asyncio.Task`) | Corrutina ya programada en el loop, que avanza sin que la esperes | celda 3.2 |
| **event loop** | El bucle de un hilo que guarda las corrutinas pendientes y, cuando la tarea actual se suspende o termina, corre otra que ya puede avanzar | celda 3.2 |

## Una corrutina no corre al llamarla

**Haz (celda 3.1):** llama una corrutina sin `await` y luego con `await`.

```python
import asyncio

async def saluda():
    await asyncio.sleep(0.1)
    return "listo"

c = saluda()
print(type(c).__name__)
print(await c)
```

**Qué hace cada línea:**

- `async def saluda()` — define una corrutina.
- `await asyncio.sleep(0.1)` — espera 0.1 s cediendo el hilo al loop.
- `c = saluda()` — no ejecuta nada: guarda la llamada en un objeto `coroutine`.
- `await c` — ahora sí corre y devuelve `"listo"`. El `await` de nivel superior funciona porque el notebook ya tiene un loop corriendo.

**Deberías ver:**

```text
coroutine
listo
```

> [!WARNING]
> En un notebook usa `await` suelto, como en esta celda. `asyncio.run(...)` sólo va en un archivo `.py`: dentro de un notebook truena con `RuntimeError: asyncio.run() cannot be called from a running event loop`, porque el loop ya existe.

## El event loop, con una traza de tiempos

**Haz (celda 3.2):** tres tareas que esperan 1 s cada una; la traza imprime cuándo empieza y termina cada una.

```python
import asyncio
import time

t0 = time.perf_counter()

def marca(texto):
    print(f"{time.perf_counter() - t0:4.2f} s  {texto}")

async def trabajo(nombre):
    marca(f"{nombre} empieza")
    await asyncio.sleep(1)
    marca(f"{nombre} termina")

await asyncio.gather(trabajo("A"), trabajo("B"), trabajo("C"))
marca("las tres terminaron")
```

**Qué hace cada línea:**

- `marca(texto)` — imprime los segundos desde `t0` y un texto.
- `await asyncio.sleep(1)` — la corrutina se pausa; el loop pasa a la siguiente.
- `asyncio.gather(...)` — programa las tres corrutinas como tareas y espera a todas.

**Deberías ver:**

```text
0.00 s  A empieza
0.00 s  B empieza
0.00 s  C empieza
1.00 s  A termina
1.00 s  B termina
1.00 s  C termina
1.00 s  las tres terminaron
```

- Las tres empiezan casi en el mismo instante y terminan casi juntas: **3 esperas de 1 s tardaron 1 s, no 3 s.**
- Todo ocurrió en un hilo. El loop corre A hasta su `await`, luego B, luego C, y vuelve a cada una cuando su espera acaba.

::: figure {#cmp-event-loop title="El event loop reparte un hilo entre corrutinas"}
![Un solo hilo con el event loop en el centro. A la izquierda, tres corrutinas A, B y C hacen await y entregan el control al loop; el loop guarda las que esperan y, cuando una espera termina, la devuelve a la cola de corrutinas listas para reanudarse y la corre hasta su siguiente await. Una línea de tiempo muestra que los tramos de ejecución son cortos y las esperas se solapan.](../_assets/cmp-event-loop.svg)
:::

## Cien peticiones con un hilo: `gather` y `Semaphore`

`requests` bloquea el hilo mientras espera, así que no sirve dentro del loop. El cliente para `asyncio` es `httpx.AsyncClient`.

**Haz (celda 3.3):** 20, 100 y 500 llamadas a `/ventas?lento=0.2`, con 32 en vuelo como máximo.

```python
import asyncio
import time
import httpx
from cable import URL

async def pide(cliente, sem):
    async with sem:
        r = await cliente.get(f"{URL}/ventas?lento=0.2")
        return r.status_code

async def lote(n):
    sem = asyncio.Semaphore(32)
    limites = httpx.Limits(max_connections=32)
    async with httpx.AsyncClient(limits=limites, timeout=30) as cliente:
        return await asyncio.gather(*(pide(cliente, sem) for _ in range(n)))

for n in (20, 100, 500):
    inicio = time.perf_counter()
    codigos = await lote(n)
    print(f"{n:>3} llamadas, asyncio con 32: {time.perf_counter() - inicio:5.2f} s  ({set(codigos)})")
```

**Qué hace cada línea:**

- `asyncio.Semaphore(32)` — deja pasar como máximo 32 corrutinas a la vez por el bloque `async with sem`; las demás esperan su turno.
- `httpx.Limits(max_connections=32)` — el mismo tope en el cliente: 32 conexiones abiertas.
- `await cliente.get(...)` — la corrutina cede el hilo mientras el servidor duerme 0.2 s.
- `asyncio.gather(*(...))` — programa las `n` corrutinas y devuelve sus resultados en orden. Si una falla, por omisión propaga la primera excepción y no cancela las demás.

**Deberías ver:**

```text
 20 llamadas, asyncio con 32:  0.24 s  ({200})
100 llamadas, asyncio con 32:  0.92 s  ({200})
500 llamadas, asyncio con 32:  3.41 s  ({200})
```

- El tiempo crece por tandas: cada tanda de 32 llamadas cuesta ~0.2 s, porque ése es el tope y no el hilo.

::: figure {#cmp-gantt-asyncio title="Mismas tareas, un hilo, gather"}
![Diagrama de Gantt de 0 a 800 ms: tres corrutinas en un solo hilo, lanzadas juntas con gather. Cada una ejecuta 20 ms hasta su await y cede el control; las tres esperas de 200 ms se solapan y la fila de CPU muestra tramos cortos intercalados. Total 280 ms, igual que con hilos y sin ningún hilo extra.](../_assets/cmp-gantt-asyncio.svg)
:::

## Hilos y `asyncio` con el mismo límite

Una comparación es honesta si los dos modelos tienen el mismo tope: aquí, 32 llamadas en vuelo. El secuencial sólo se midió con 20 llamadas; 100 y 500 son el cálculo `N × 0.2 s`.

| Llamadas | Secuencial | Hilos (`max_workers=32`) | `asyncio` (`Semaphore(32)`) |
|---:|---:|---:|---:|
| 20 | 4.04 s | 0.23 s | 0.24 s |
| 100 | 20 s (calculado, no medido) | 0.82 s | 0.92 s |
| 500 | 100 s (calculado, no medido) | 3.32 s | 3.41 s |

Tiempos de la máquina del profesor; los tuyos cambian, la forma no. Con el mismo tope, hilos y `asyncio` tardan lo mismo: **el límite lo pone la concurrencia permitida, no el modelo.** También cambian la biblioteca HTTP y la reutilización de conexiones; son datos de una corrida, no una equivalencia general.

Subir el tope es un parámetro. Con 500 llamadas y 100 en vuelo, los hilos tardan 1.52 s; `asyncio` con 100 conexiones de `httpx` tardó 10.91 s, **más lento que con 32** (una sola corrida, no repetida, sin celda en el notebook). El cliente consumió 10.9 s de CPU; sin perfil ni repeticiones no se puede asegurar la causa. La sospecha es el **pool de conexiones** de `httpx` (las conexiones abiertas que el cliente guarda y reutiliza entre peticiones). Por eso se mide antes de subir un límite.

- Para **esperar**, 100 hilos o 1000 corrutinas es válido; la regla "no más workers que CPU" es de trabajo que calcula.
- La diferencia práctica: una corrutina ocupa unos KB y cambia sin el sistema operativo; un hilo ocupa más y lo cambia el sistema. Con miles de esperas, eso decide.
- `asyncio.to_thread(requests.get, ...)` integra una función bloqueante con `asyncio` usando el **executor** de hilos del loop (por omisión, un pool de `min(32, CPUs + 4)` hilos que ejecuta funciones fuera del loop). Mantiene libre el loop, con los costos y límites de ese pool.

## El contraejemplo: `await` uno tras otro

`async` no vuelve concurrente nada por sí mismo. Un `await` dentro de un `for` espera cada llamada antes de lanzar la siguiente.

**Haz (celda 3.4):** las mismas 20 llamadas, cada una con su `await` en serie.

```python
import time
import httpx
from cable import URL

inicio = time.perf_counter()
async with httpx.AsyncClient(timeout=30) as cliente:
    for _ in range(20):
        r = await cliente.get(f"{URL}/ventas?lento=0.2")
print(f"20 llamadas con await en serie: {time.perf_counter() - inicio:.2f} s")
```

**Qué hace cada línea:**

- `for _ in range(20)` — recorre 20 veces.
- `await cliente.get(...)` — el loop podría correr otras corrutinas durante la espera, pero **no hay otras**: la siguiente vuelta no empieza hasta que ésta termina.

**Deberías ver:**

```text
20 llamadas con await en serie: 4.05 s
```

- Es el tiempo del secuencial (20 × 0.2 s), con sintaxis `async`. La corrutina cedió el hilo y nadie lo usó.
- El arreglo es `gather` (celda 3.3): programar todas antes de esperar.

::: figure {#cmp-gantt-await-en-serie title="await en serie: async sin concurrencia"}
![Diagrama de Gantt de 0 a 800 ms: tres corrutinas con await una tras otra, sin gather. Cada await espera su respuesta completa de 200 ms antes de lanzar la siguiente llamada, así que el dibujo es idéntico al secuencial: total 720 ms y la CPU inactiva durante las tres esperas.](../_assets/cmp-gantt-await-en-serie.svg)
:::

## `time.sleep` contra `asyncio.sleep`

`asyncio.sleep` es una espera que cede el hilo; `time.sleep` es una espera que **se queda con él**. El loop no puede correr nada mientras una corrutina llama `time.sleep`.

**Haz (celda 3.5):** la traza de la celda 3.2, con `time.sleep` en lugar de `asyncio.sleep`.

```python
import asyncio
import time

t0 = time.perf_counter()

def marca(texto):
    print(f"{time.perf_counter() - t0:4.2f} s  {texto}")

async def trabajo(nombre):
    marca(f"{nombre} empieza")
    time.sleep(1)
    marca(f"{nombre} termina")

await asyncio.gather(trabajo("A"), trabajo("B"), trabajo("C"))
marca("las tres terminaron")
```

**Qué hace cada línea:**

- `time.sleep(1)` — duerme el hilo entero, y con él el loop. A no cede nada: termina antes de que B empiece.

**Deberías ver:**

```text
0.00 s  A empieza
1.00 s  A termina
1.00 s  B empieza
2.00 s  B termina
2.00 s  C empieza
3.00 s  C termina
3.00 s  las tres terminaron
```

- Tres esperas de 1 s tardan 3 s: la traza es secuencial.
- Cualquier llamada que bloquea (`time.sleep`, `requests.get`, leer un archivo grande, un cálculo) tiene el mismo efecto.

## Un cálculo dentro del loop lo bloquea

Un `await` es el único punto donde el loop recupera el control. Un cálculo largo no tiene `await`: mientras corre, **ninguna otra corrutina avanza**, ni siquiera un temporizador.

**Haz (celda 3.6):** `latido`, una corrutina que imprime cada 0.1 s; en medio, otra corrutina calcula sin `await`.

```python
import asyncio
import time
from trabajo_computo import calcula

async def latido(veces):
    for i in range(veces):
        print(f"{time.perf_counter() - t0:4.2f} s  latido {i}")
        await asyncio.sleep(0.1)

async def calculo():
    await asyncio.sleep(0.15)
    inicio = time.perf_counter()
    calcula()
    print(f"      el cálculo duró {time.perf_counter() - inicio:.2f} s sin ceder el hilo")

t0 = time.perf_counter()
await asyncio.gather(latido(5), calculo())
```

**Qué hace cada línea:**

- `latido(veces)` — corrutina que imprime la hora y espera 0.1 s, `veces` veces.
- `calcula()` — la función de cálculo de `trabajo_computo.py`; es código normal, sin `await`.
- `asyncio.gather(latido(5), calculo())` — las dos corrutinas en el mismo loop.

**Deberías ver:**

```text
0.00 s  latido 0
0.10 s  latido 1
      el cálculo duró 2.28 s sin ceder el hilo
2.43 s  latido 2
2.53 s  latido 3
2.63 s  latido 4
```

- Los latidos que debían salir cada 0.1 s se detienen durante el cálculo: el loop estuvo bloqueado 2.28 s.
- No es lo que pasa con el GIL: el GIL le quita el turno a un hilo cada ~5 ms (`sys.getswitchinterval()`, ver [[el-gil]]). El loop es cooperativo: nadie interrumpe a una corrutina, y sólo recupera el control cuando ella llega a un `await`.

::: figure {#cmp-bloqueo-del-loop title="Un cálculo sin await detiene el loop"}
![Diagrama de Gantt de 0 a 2200 ms: dos corrutinas lanzan una petición y esperan 200 ms; la corrutina 3 hace un cálculo de 2000 ms dentro del loop sin ningún await. Las respuestas llegan a los 220 y 240 ms, pero las corrutinas 1 y 2 quedan listas sin turno hasta los 2040 y 2060 ms, porque el loop no recupera el control hasta que el cálculo termina. Total 2080 ms. Sin la corrutina de cálculo, ambas peticiones terminarían a los 260 ms.](../_assets/cmp-bloqueo-del-loop.svg)
:::

## La salida: sacar el cálculo del loop

Hay dos caminos, según qué calcule el trabajo:

| El trabajo | Dónde correrlo | Con qué |
|---|---|---|
| espera en una librería que bloquea | un hilo | `await asyncio.to_thread(f, ...)` |
| calcula en Python | otro proceso (tiene su propio GIL) | `await loop.run_in_executor(pool, f, ...)` con un `ProcessPoolExecutor` |

`run_in_executor` manda la función a otro hilo o proceso y devuelve un objeto que sí se puede esperar con `await`: el loop sigue corriendo mientras tanto. La función vive en `trabajo_computo.py` porque un proceso nuevo la importa.

**Haz (celda 3.7):** el mismo latido y el mismo cálculo, con el cálculo en un proceso.

```python
import asyncio
import time
from concurrent.futures import ProcessPoolExecutor
from trabajo_computo import calcula

async def latido(veces):
    for i in range(veces):
        print(f"{time.perf_counter() - t0:4.2f} s  latido {i}")
        await asyncio.sleep(0.1)

async def calculo(pool):
    await asyncio.sleep(0.15)
    loop = asyncio.get_running_loop()
    inicio = time.perf_counter()
    await loop.run_in_executor(pool, calcula)
    print(f"      el cálculo duró {time.perf_counter() - inicio:.2f} s en otro proceso")

t0 = time.perf_counter()
with ProcessPoolExecutor(max_workers=1) as pool:
    await asyncio.gather(latido(5), calculo(pool))
```

**Qué hace cada línea:**

- `asyncio.get_running_loop()` — el loop que corre esta celda.
- `loop.run_in_executor(pool, calcula)` — corre `calcula` en el proceso del pool; el `await` cede el hilo mientras tanto.
- `ProcessPoolExecutor(max_workers=1)` — un solo proceso, suficiente para una función.

**Deberías ver:**

```text
0.00 s  latido 0
0.10 s  latido 1
0.20 s  latido 2
0.30 s  latido 3
0.40 s  latido 4
      el cálculo duró 2.39 s en otro proceso
```

- Los latidos siguen saliendo cada 0.1 s mientras el cálculo corre en otro proceso; el loop no se enteró.
- 2.39 s contra 2.28 s de la celda 3.6: los 2.39 s incluyen arrancar el proceso (el pool lo crea en el primer `run_in_executor`), enviarle la tarea y recibir el resultado; una corrida no permite atribuir toda la diferencia al arranque.

**Al diseñar / al revisar código de IA, busca:**

- `async def` con `await` dentro de un `for` sobre llamadas independientes: es secuencial con otra sintaxis; pide `asyncio.gather`.
- `time.sleep(`, `requests.get(` o `open(...).read()` dentro de una `async def`: bloquea el loop y no lo parece.
- `gather` sin `Semaphore` sobre miles de llamadas: lanza miles de corrutinas a la vez. `httpx` limita por omisión a 100 conexiones; un `Semaphore` limita las operaciones simultáneas, pero no las peticiones por segundo ni evita un `429`.
- Un bucle de cálculo dentro de una `async def`: sácalo con `run_in_executor` y un proceso.
- `asyncio.run(` dentro de una celda de notebook, o `asyncio.to_thread(requests.get, ...)` presentado como `asyncio` de un solo hilo: lo segundo corre en el pool de hilos del executor.

Sigue con [[vectorizar]]: qué hacer cuando lo que tarda es el cálculo y no la espera.
