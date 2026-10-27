---
id: elegir-la-estrategia
title: "Elegir la estrategia"
nav_title: "Elegir la estrategia"
summary: "Dado un trabajo, la estrategia sale de dónde pasa el tiempo: esperar pide hilos o asyncio, calcular en Python pide procesos, calcular sobre arreglos pide vectorizar. Los errores típicos tienen un comando que los delata."
status: ready
estimated_time: 10m
tags: [concurrency, decision, hilos, asyncio, procesos, vectorizar, anti-patrones]
prerequisites: [vectorizar]
---

# Elegir la estrategia

**Página 5 de 5 · Cómputo y concurrencia**

Pregunta: dado un trabajo concreto, ¿qué uso, y cómo me doy cuenta de que elegí mal?

| Término | Qué es | Lo ves con |
|---|---|---|
| **árbol de decisión** | Las preguntas, en orden, que llevan de «dónde pasa el tiempo» a una estrategia | la figura de abajo |
| **anti-patrón** | Código que funciona y aun así anula la ventaja de la estrategia que dice usar | las celdas 5.1 y 5.2 |
| **pool** | Un grupo de hilos o procesos que se crea una vez y se reutiliza | la celda 5.2 |

## En corto

- **Primero mide dónde pasa el tiempo** ([[donde-pasa-el-tiempo]]); la estrategia es consecuencia, no preferencia.
- **Esperar** se resuelve con hilos o `asyncio`; **calcular en Python**, con procesos; **calcular sobre arreglos**, vectorizando.
- **Un anti-patrón no falla: tarda lo mismo que el secuencial** (o más). Por eso se busca con un comando, no con la vista.

## El árbol

::: figure {#cmp-arbol-decision title="Árbol de decisión: de dónde pasa el tiempo a la estrategia"}
![Árbol de decisión. Pregunta inicial: dónde pasa el tiempo. Si espera red, disco o una base de datos, se usan hilos para pocas esperas y código bloqueante, o asyncio para muchas esperas con librerías async. Si calcula en Python con un bucle que no se puede expresar sobre arreglos, se usan procesos. Si calcula sobre arreglos numéricos, se vectoriza con NumPy. Si el trabajo mezcla esperar y calcular, se combina: esperar con asyncio o hilos y mandar el cálculo a procesos.](../_assets/cmp-arbol-decision.svg)
:::

| Si el trabajo... | Estrategia | Por qué | Página |
|---|---|---|---|
| **espera** (red, disco, base de datos) y son pocas esperas, con código bloqueante | hilos | Mientras un hilo espera, el GIL se libera y otro avanza | [[concurrente-paralelo-asincrono]] |
| **espera** y son muchas, con librerías `async` | `asyncio` | Una corrutina que espera cuesta mucho menos que un hilo | [[asyncio-y-el-event-loop]] |
| **calcula en Python** (un bucle que no cabe en un arreglo) | procesos, si las tareas son independientes y compensan el arranque y la comunicación; si no, se queda secuencial | Cada proceso tiene su intérprete y su GIL; compara contra ejecución directa | [[concurrente-paralelo-asincrono]] |
| **calcula sobre arreglos** numéricos | vectorizar | Saca el bucle del intérprete; no hay nada que repartir | [[vectorizar]] |
| **mezcla** las dos cosas | combinar | Espera con `asyncio` o hilos y manda el cálculo a un pool de procesos | esta página |

## Los costos, medidos

Mismo servidor, mismo límite de concurrencia declarado (32), una sola corrida en esta máquina con `8` CPU.

| Trabajo | Estrategia | Tiempo |
|---|---|---:|
| 20 llamadas de 0.2 s | secuencial | `4.04` s |
| 20 llamadas de 0.2 s | 32 hilos | `0.23` s |
| 20 llamadas de 0.2 s | `asyncio`, semáforo de 32 | `0.24` s |
| 500 llamadas de 0.2 s | 32 hilos | `3.32` s |
| 500 llamadas de 0.2 s | `asyncio`, semáforo de 32 | `3.41` s |
| 4 cálculos en Python (`calcula(5_000_000)`) | 1 proceso | `2.34` s |
| 4 cálculos en Python (`calcula(5_000_000)`) | 4 procesos | `1.00` s |
| suma de cuadrados | bucle de Python | `0.188` s |
| suma de cuadrados | NumPy | `0.0119` s (`16` veces más rápido) |

- **Para esperar, hilos y `asyncio` quedan parejos** con el mismo límite de 32: elegir entre ellos es cuestión de librerías y de cuántas esperas, no de velocidad. Con el tope en 100 dejaron de estarlo (1.52 s contra 10.91 s en una sola corrida, ver [[asyncio-y-el-event-loop]]): un límite nuevo se vuelve a medir.
- **Los procesos ganan en cálculo, no en espera**: lanzarlos para llamadas de red añade arranque y copia de datos sin ganar nada.
- **Repartir tiene techo**: 4 procesos dieron 2.3 veces, no 4. El cociente 2.34/1.00 compara 1 y 4 procesos incluyendo su gestión; no identifica `S` (Amdahl, [[vectorizar]]). Los 16x de NumPy son sobre otra carga (5 M `float64`, no los 20 M enteros de `calcula()`), así que esas dos cifras no se comparan entre sí.

## Anti-patrones, con su comando

| Anti-patrón | Qué pasa | Cómo lo delatas |
|---|---|---|
| **`await` en serie**: `for ...: await ...` | Cada espera empieza cuando termina la anterior: es secuencial con otra sintaxis | El tiempo total es `4.05` s, no `0.24` s; revisa el Gantt de [[asyncio-y-el-event-loop]] |
| **Bloquear el loop**: `time.sleep` o `requests.get` dentro de `async def` | Nada más avanza mientras tanto: un cálculo de `2.28` s detuvo el loop en la celda 3.6 | El latido de la celda 3.6 se detiene |
| **Pool por petición**: crear el pool dentro del bucle | Paga el arranque de hilos o procesos cada vez | La celda 5.2 |
| **`lambda` en procesos** | El proceso hijo recibe la función serializada con `pickle`, y una `lambda` no se puede serializar | La celda 5.1 |
| **Más workers que CPU, en trabajo que calcula** | Los procesos extra se turnan por los mismos núcleos y no suman: 16 tareas cortas tardaron `1.31` s con 8 procesos y `1.32` s con 16, en `8` CPU (una corrida, fuera del notebook) | Compara `max_workers` con `os.cpu_count()` |

La última fila **sólo aplica a trabajo que calcula**. Para esperar, 100 hilos o mil corrutinas es válido: no ocupan CPU mientras esperan.

**Haz (celda 5.1):** manda una `lambda` a un proceso.

```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=2) as pool:
    futuro = pool.submit(lambda x: x * 2, 21)
    try:
        print(futuro.result())
    except Exception as e:
        print(type(e).__name__)
```

**Qué hace cada línea:**

- `ProcessPoolExecutor(max_workers=2)` — dos procesos hijo.
- `pool.submit(lambda ...)` — serializa la función con `pickle` para enviarla al hijo.
- `futuro.result()` — devuelve el resultado o relanza el error que ocurrió en el camino.

**Deberías ver:**

```text
PicklingError
```

- El mensaje de `e` cambia entre versiones de Python (3.13 y 3.14 lo redactan distinto); el tipo es el mismo.

- **La función que va a un proceso debe vivir en un módulo importable** (como `trabajo_computo.py`) o ser una función incorporada: así `pickle` la nombra y el hijo la encuentra.

**Haz (celda 5.2):** compara un pool por llamada con un pool para todas.

```python
import time
from concurrent.futures import ProcessPoolExecutor

t = time.perf_counter()
for i in range(10):
    with ProcessPoolExecutor(max_workers=2) as pool:
        pool.submit(abs, -i).result()
print(f"un pool por llamada : {time.perf_counter() - t:.2f} s")

t = time.perf_counter()
with ProcessPoolExecutor(max_workers=2) as pool:
    for i in range(10):
        pool.submit(abs, -i).result()
print(f"un pool para todas  : {time.perf_counter() - t:.2f} s")
```

**Qué hace cada línea:**

- `pool.submit(abs, -i)` — trabajo mínimo, para que el tiempo sea el del pool y no el del cálculo.
- Primer bloque — crea y destruye un pool en cada vuelta.
- Segundo bloque — crea el pool una vez y lo reutiliza.

**Deberías ver:**

```text
un pool por llamada : 0.73 s
un pool para todas  : 0.07 s
```

- La diferencia es el costo de arrancar procesos, y se paga **por petición** si el pool vive dentro del manejador.

## Qué decide una API frente a esto

Un servidor web recibe muchas peticiones a la vez y tiene que escoger la misma estrategia que tú:

- **Un hilo por conexión.** El servidor de la clase (`ThreadingHTTPServer`) lanza un hilo por cada conexión: simple, y válido porque el trabajo de cada petición casi siempre espera.
- **Un event loop.** Servidores `async` atienden miles de conexiones en un hilo; sirven mientras ningún manejador bloquee el loop.
- **Varios procesos.** Los servidores de producción de Python arrancan varios procesos, cada uno con su GIL, para usar todos los núcleos.

Un manejador que **calcula mucho** no se arregla con más hilos: se mueve el cálculo a un pool de procesos, a otro servicio o a una cola (sección 10.4).

## Cierre

> [!NOTE]
> **Si sólo recuerdas una cosa:** primero averigua si el trabajo espera o calcula; la estrategia es la que ataca ese tramo, y el anti-patrón es el código que la nombra sin ejecutarla. Compara cada cambio de estrategia con la versión secuencial usando los mismos datos.

### Al diseñar, y al revisar código de IA, busca...

- **`for ...: await ...` sobre una lista de llamadas.** Si no hay `gather` ni tareas, es secuencial.
- **`requests`, `time.sleep` o lectura de archivos dentro de `async def`.** Bloquea el loop de todos.
- **Un `ThreadPoolExecutor` o `ProcessPoolExecutor` creado dentro de un bucle o de un manejador.** Sácalo y reutilízalo.
- **Una `lambda` o función anidada enviada a procesos.** Defínela en un módulo importable.
- **`max_workers` fijado en un número grande para trabajo que calcula.** Compáralo con `os.cpu_count()`.
- **Hilos para sumar o multiplicar números en un bucle.** El GIL los turna; vectoriza o usa procesos.

La siguiente clase es **patrones y protocolos de comunicación**: qué hacer cuando dos programas no esperan una respuesta inmediata, sino un evento.
