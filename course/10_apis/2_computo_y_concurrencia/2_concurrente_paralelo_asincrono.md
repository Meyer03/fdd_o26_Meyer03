---
id: concurrente-paralelo-asincrono
title: "Concurrente, paralelo y asíncrono"
nav_title: "Concurrente, paralelo, asíncrono"
summary: "Tres palabras que se usan como sinónimos y miden cosas distintas: ciclos de vida que se solapan, ejecución en el mismo instante en dos CPU, y llamadas que regresan antes del resultado. Cada una con su medición, y la condición de carrera que aparece cuando varios hilos comparten un dato."
status: ready
estimated_time: 30m
tags: [concurrencia, paralelismo, asincronia, hilos, procesos, gil, condicion-de-carrera, lock, gantt]
prerequisites: [donde-pasa-el-tiempo, el-gil]
---

# Concurrente, paralelo y asíncrono

**Página 2 de 5 · Cómputo y concurrencia**

Meta: saber cuál de las tres palabras describe lo que hace tu programa, y qué se rompe cuando varios hilos tocan el mismo dato.

Veinte llamadas de 0.2 s tardan 4 s en serie. Alguien te dice «hazlo concurrente», otro «paralelo», otro «asíncrono». ¿Son tres nombres de lo mismo? No: **cada palabra afirma algo distinto, y se comprueba con un reloj.**

| Término | Qué es | Lo ves con |
|---|---|---|
| **concurrente** | Dos tareas son concurrentes si sus ciclos de vida (de empezar a terminar) se **solapan** en el tiempo | la celda 2.1 |
| **paralelo** | Dos cosas **se ejecutan en el mismo instante**, en dos CPU lógicas distintas | la celda 2.3 |
| **asíncrono** | La llamada **regresa antes de tener el resultado**, y quien espera **cede el control** de forma explícita | la celda 2.2 |
| **condición de carrera** | El resultado depende del orden en que se intercalan dos hilos que tocan el mismo dato | la celda 2.4 |
| **`Lock`** | Un candado: sólo un hilo a la vez puede estar dentro del bloque que protege | la celda 2.5 |

## En corto

- **Concurrente** habla de *tiempo*: ciclos de vida que se solapan. No dice cuántas CPU hay.
- **Paralelo** habla de *CPU*: ejecución simultánea, así que necesita al menos 2.
- **Asíncrono** es un *modelo de programación* (cómo escribes la espera), no una celda de la matriz.
- **Con GIL, hilos y `asyncio` son concurrentes y no paralelos.** Los procesos son ambas cosas.

## Qué se ejecuta: proceso, hilo, CPU lógica, GIL

La definición larga de estos cuatro está en [[el-gil]]; aquí sólo la tabla que usas para leer el resto de la página.

| | Qué es | Memoria | Lo que obtienes de él |
|---|---|---|---|
| **proceso** | Un programa corriendo | propia: no comparte variables con otro proceso | su propio intérprete y su propio GIL |
| **hilo** | Una línea de ejecución dentro de un proceso | **compartida** con los demás hilos del proceso | solapar esperas; barato de crear |
| **CPU lógica** | Lo que el sistema puede poner a ejecutar algo a la vez | no aplica | el tope de ejecuciones simultáneas |
| **GIL** | El candado que deja a un solo hilo ejecutar Python por intérprete | no aplica | hilos que se turnan para ejecutar |

Lo que cambia todo lo que sigue: **los hilos comparten memoria y los procesos no.** Lo primero abarata la comunicación y abre la condición de carrera; lo segundo la aísla y obliga a mandar los datos de ida y vuelta.

## Concurrente: ciclos de vida que se solapan

**Definición:** dos tareas son concurrentes si una **empieza antes de que la otra termine**. No dice que se ejecuten a la vez, sólo que ninguna espera a que acabe la otra para empezar.

**Haz (celda 2.1):** las mismas 20 llamadas de la página anterior, ahora con 32 hilos.

```python
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from cable import URL

def pide(i):
    return requests.get(f"{URL}/ventas?lento=0.2", timeout=5).status_code

inicio = time.perf_counter()
with ThreadPoolExecutor(max_workers=32) as hilos:
    codigos = list(hilos.map(pide, range(20)))
print(f"{len(codigos)} llamadas, status {set(codigos)}, {time.perf_counter() - inicio:.2f} s")
```

**Qué hace cada línea:**

- `pide(i)` — una llamada `GET` con `?lento=0.2`: el servidor duerme 0.2 s y contesta. Devuelve sólo el status.
- `ThreadPoolExecutor(max_workers=32)` — un grupo de hasta 32 hilos del mismo proceso.
- `hilos.map(pide, range(20))` — lanza las 20 llamadas sin esperar a que termine la anterior y junta los resultados en orden.
- `set(codigos)` — los status distintos que hubo; si todo salió bien, uno solo.

**Deberías ver:** en la máquina del profesor (tu número cambia con tu máquina y su carga),

```text
20 llamadas, status {200}, 0.23 s
```

- **0.23 s contra 4.04 s en serie.** Las 20 llamadas empezaron antes de que terminara la primera: sus ciclos de vida se solaparon. Eso es concurrencia.
- No hubo ejecución simultánea de Python: el tiempo que se ahorró es **tiempo de espera** solapado, no cálculo repartido.

::: figure {#cmp-gantt-hilos title="Las mismas tareas con hilos: esperas solapadas, ejecución turnada"}
![Diagrama de Gantt con tiempo en milisegundos en el eje horizontal y una fila por tarea, más una fila para la CPU. Tres tareas empiezan casi a la vez. Cada una tiene un tramo corto de ejecución y un tramo largo de espera; los tramos de espera se solapan entre sí, pero los tramos de ejecución van uno tras otro y nunca coinciden. La fila de CPU muestra un solo hilo ejecutando en cada instante y largos huecos de inactividad.](../_assets/cmp-gantt-hilos.svg)
:::

En el Gantt de arriba, **las barras de espera se montan unas sobre otras y las de ejecución no.** Eso es lo que hace el GIL: mientras un hilo espera a la red suelta el candado y otro ejecuta; dos hilos nunca ejecutan Python a la vez. La medición que lo prueba para código que calcula (4 hilos ≈ 1 hilo) es la celda 3.2 de [[el-gil]].

## Asíncrono: la llamada regresa antes del resultado

**Definición:** una llamada es asíncrona si **regresa de inmediato con una tarea pendiente (`Task`) del resultado** y, para usarlo, quien espera lo pide con `await`, **cediendo el control** a otra tarea mientras tanto. Es una forma de escribir el programa; no dice cuántas CPU usa.

**Haz (celda 2.2):** una tarea que tarda 0.2 s, creada y consultada antes de que termine.

```python
import asyncio

async def cuenta():
    await asyncio.sleep(0.2)
    return 42

tarea = asyncio.create_task(cuenta())
print("justo después de crearla, terminó:", tarea.done())
resultado = await tarea
print("después de await, terminó:", tarea.done(), "y devolvió", resultado)
```

**Qué hace cada línea:**

- `async def cuenta()` — define una **corrutina**: una función que puede pausarse en un `await`.
- `await asyncio.sleep(0.2)` — espera 0.2 s *cediendo el control* para que otra tarea ejecute.
- `asyncio.create_task(cuenta())` — programa la corrutina y **regresa al instante**, sin esperar el resultado.
- `tarea.done()` — dice si ya terminó.
- `await tarea` — aquí sí cedes el control hasta tener el resultado. En un notebook se usa `await` directo en la celda; `asyncio.run(...)` sólo va en archivos `.py`.

**Deberías ver:**

```text
justo después de crearla, terminó: False
después de await, terminó: True y devolvió 42
```

- La primera línea es `False`: **la llamada regresó antes de tener el resultado.** Esa es la parte asíncrona.
- Lo que hace falta para solapar muchas llamadas (el *event loop*, `gather`) es la siguiente página: [[asyncio-y-el-event-loop]].

## Paralelo: ejecución en el mismo instante

**Definición:** dos cosas son paralelas si **se ejecutan en el mismo instante**. Eso exige al menos 2 CPU lógicas, y en Python con GIL exige **procesos** (o la compilación *free-threaded* de 3.14, que ya vive en [[el-gil]]): cada uno trae su intérprete y su GIL. Hay dos excepciones: extensiones como NumPy liberan el GIL dentro de su código compilado y pueden calcular en paralelo, y CPython *free-threaded* lo desactiva (en 3.14 está soportado y es opcional).

La función que calcula vive en `trabajo_computo.py`, un archivo importable: un proceso nuevo vuelve a importarla, y una celda no vive en ningún archivo (el porqué está en [[el-gil]]).

**Haz (celda 2.3):** el mismo cálculo, 4 veces, con 1, 2 y 4 procesos.

```python
import os
import time
from concurrent.futures import ProcessPoolExecutor
from trabajo_computo import calcula

def mide(n_procesos):
    inicio = time.perf_counter()
    with ProcessPoolExecutor(max_workers=n_procesos) as procesos:
        list(procesos.map(calcula, [5_000_000] * 4))
    return time.perf_counter() - inicio

print("CPU lógicas:", os.cpu_count())
for n in (1, 2, 4):
    print(f"{n} proceso(s): {mide(n):.2f} s")
```

**Qué hace cada línea:**

- `from trabajo_computo import calcula` — la función que suma en Python puro; vive en el archivo, no en la celda.
- `mide(n_procesos)` — corre las 4 llamadas de `calcula` repartidas entre `n_procesos` procesos y devuelve cuánto tardó.
- `[5_000_000] * 4` — cuatro trabajos idénticos.
- `os.cpu_count()` — cuántas CPU lógicas ve el sistema: el tope de la ejecución simultánea.

**Deberías ver:**

```text
CPU lógicas: 8
1 proceso(s): 2.34 s
2 proceso(s): 1.45 s
4 proceso(s): 1.00 s
```

- **2.34 s con 1 proceso, 1.45 s con 2, 1.00 s con 4**, en una máquina con 8 CPU lógicas. Con 2 procesos hay dos ejecuciones en el mismo instante.
- Pasar de 1 a 2 acorta el total porque **hay ejecución simultánea**. Con más procesos que CPU libres se turnan y el total deja de bajar; aquí no se llegó a ese límite (4 procesos sobre 8 CPU). El total de 4 procesos (1.00 s) queda por encima del ideal (2.34 / 4 = 0.58 s) porque **arrancar un proceso y copiarle los datos cuesta tiempo**.

::: figure {#cmp-gantt-procesos title="Con dos CPU, dos tareas ejecutan en el mismo instante"}
![Diagrama de Gantt con tiempo en milisegundos en el eje horizontal y una fila por tarea, más dos filas de CPU. Dos tareas tienen un tramo de ejecución al mismo tiempo, cada una sobre su propia CPU; las filas de CPU muestran ambas ocupadas en el mismo intervalo. La tercera tarea empieza cuando una CPU queda libre. El total es menor que el de ejecutar las tareas una tras otra.](../_assets/cmp-gantt-procesos.svg)
:::

El Gantt de arriba dibuja tareas con espera, para mostrar el mecanismo; la celda 2.3 es puro cálculo. En él, **las barras de ejecución se montan**: eso no pasaba con hilos. Cada barra corre sobre una CPU distinta; las filas de CPU lo muestran. Crear un proceso cuesta más que crear un hilo y los datos viajan copiados, así que para trabajo corto no compensa.

## La matriz: concurrente × paralelo

Las dos primeras palabras forman una matriz de 2 × 2. La tercera no entra: asíncrono dice *cómo escribes* la espera, no *cuándo* ejecuta.

::: figure {#cmp-matriz-2x2 title="Concurrente por paralelo: dónde cae cada estrategia"}
![Matriz de dos por dos. Columnas: no paralelo, una sola CPU ejecuta a la vez; paralelo, varias CPU ejecutan en el mismo instante. Filas: no concurrente, una tarea en curso a la vez; concurrente, varias tareas en curso a la vez. Secuencial cae en no concurrente y no paralelo. Hilos con GIL y asyncio caen en concurrente y no paralelo. Procesos caen en concurrente y paralelo. La celda paralelo y no concurrente la ocupa una sola operación de la aplicación repartida dentro de una librería compilada, como NumPy; sus subtareas internas sí son concurrentes, así que es el caso límite. Asíncrono no es una celda: es cómo se escribe la espera, con await.](../_assets/cmp-matriz-2x2.svg)
:::

| Estrategia | Concurrente | Paralelo | Qué consigue en Python con GIL |
|---|:---:|:---:|---|
| secuencial | no | no | nada: una tarea tras otra |
| hilos | **sí** | no | solapa esperas |
| `asyncio` | **sí** | no | solapa esperas, con un solo hilo |
| procesos | **sí** | **sí** | solapa esperas **y** reparte cálculo |

- **Sí, hilos y `asyncio` son concurrentes y no paralelos**: la celda 2.1 ahorró tiempo sin que dos hilos ejecutaran Python a la vez.
- **Paralelo sin concurrente es el caso límite**: *una* sola operación de tu aplicación repartida entre varias CPU dentro de una librería compilada, como NumPy sobre un arreglo grande (ver [[vectorizar]]). Si cuentas las subtareas internas de la librería, esas sí son concurrentes. No es una estrategia que escribas en este curso.

> [!NOTE]
> «Más rápido» tiene dos causas distintas. Si el trabajo **espera**, basta con solapar (concurrente). Si **calcula**, sólo ayuda ejecutar a la vez (paralelo). Con la pregunta de la página anterior, ¿espera o calcula?, eliges la columna.

## Cuando hilos comparten un dato: la condición de carrera

Los hilos comparten memoria (primera tabla). Eso es lo que los hace baratos y lo que los hace peligrosos: **`contador += 1` no es una operación indivisible.** Son tres pasos: leer el valor, sumar 1, escribir el resultado. Si otro hilo lee entre el primer y el tercer paso, una de las dos sumas se pierde.

**Haz (celda 2.4):** 4 hilos suman 1 al mismo contador, 100 000 veces cada uno, sin candado.

```python
import sys
import threading

sys.setswitchinterval(1e-6)   # fuerza que los hilos se turnen más seguido

contador = 0

def suma_uno(x):
    return x + 1

def suma(veces):
    global contador
    for _ in range(veces):
        actual = contador              # 1. leer
        contador = suma_uno(actual)    # 2-3. sumar y escribir

hilos = [threading.Thread(target=suma, args=(100_000,)) for _ in range(4)]
for h in hilos:
    h.start()
for h in hilos:
    h.join()
print(f"esperado {4 * 100_000:,}, obtenido {contador:,}")
sys.setswitchinterval(0.005)   # lo regresa al valor por defecto
```

**Qué hace cada línea:**

- `sys.setswitchinterval(1e-6)` — baja a 1 µs el intervalo en que Python deja que otro hilo ejecute (por defecto 5 ms). Sin esto la carrera ocurre sólo *a veces*, y eso es lo que la hace difícil de depurar.
- `global contador` — todos los hilos escriben en la misma variable.
- `actual = contador` y `contador = suma_uno(actual)` — la lectura y la escritura separadas por una llamada a función. Desde Python 3.10 el intérprete sólo cambia de hilo al entrar a una función o al volver al inicio de un bucle; la llamada abre el hueco donde otro hilo se cuela. Sin ella, la carrera existe igual pero casi nunca se ve.
- `h.start()` / `h.join()` — arranca cada hilo y espera a que todos terminen.
- `sys.setswitchinterval(0.005)` — devuelve el intervalo a 5 ms para que no afecte a las celdas siguientes.

**Deberías ver:**

```text
esperado 400,000, obtenido 190,207
```

- **Esperado 400,000, obtenido 190,207.** Faltan sumas: dos hilos leyeron el mismo valor y escribieron el mismo resultado.
- El programa **no truena ni avisa**. Da un número equivocado y distinto en cada corrida.
- Obtener 400,000 en una corrida no demuestra que no haya carrera. Y `setswitchinterval` no garantiza la intercalación: el efecto depende de la implementación y la versión de Python.

El arreglo es un **`Lock`**: sólo un hilo a la vez entra al bloque que lo usa, y los otros esperan su turno.

**Haz (celda 2.5):** el mismo conteo, con candado.

```python
import sys
import threading

sys.setswitchinterval(1e-6)   # el mismo forzado de la celda 2.4

contador = 0
candado = threading.Lock()

def suma_uno(x):
    return x + 1

def suma_con_candado(veces):
    global contador
    for _ in range(veces):
        with candado:
            actual = contador
            contador = suma_uno(actual)

hilos = [threading.Thread(target=suma_con_candado, args=(100_000,)) for _ in range(4)]
for h in hilos:
    h.start()
for h in hilos:
    h.join()
print(f"esperado {4 * 100_000:,}, obtenido {contador:,}")
sys.setswitchinterval(0.005)
```

**Qué hace cada línea:**

- `threading.Lock()` — crea el candado.
- `with candado:` — entra al bloque sólo si nadie más lo tiene; al salir lo suelta, incluso si hay un error.
- Dentro del bloque están juntas la lectura y la escritura: ningún otro hilo se cuela en medio.

**Deberías ver:**

```text
esperado 400,000, obtenido 400,000
```

- **Esperado y obtenido coinciden.** El precio: mientras un hilo está dentro del `with`, los otros esperan, así que el trozo protegido se ejecuta en serie. Protege lo mínimo.

> [!WARNING]
> Los procesos no comparten variables ordinarias: cada uno trabaja sobre su copia, no ve los cambios del otro, y el resultado se devuelve y se junta al final. Si comparten memoria explícitamente o un recurso externo (un archivo, una base de datos), también pueden tener carreras.

## Al diseñar / al revisar código de IA, busca…

- **«Concurrente» o «paralelo» sin medir.** Pregunta cuántas CPU usa y qué tarda con 1 y con N; una respuesta con hilos que calculan no puede ser «paralelo».
- **Hilos o `asyncio` para acelerar un cálculo en Python puro.** Son concurrentes, no paralelos: no ejecutan a la vez.
- **Un contador, lista o diccionario compartido entre hilos, escrito sin `Lock`** (`+=`, `append` encadenado con lectura previa). Es una carrera aunque hoy el resultado salga bien.
- **Un `Lock` que envuelve todo el cuerpo de la función.** Convierte los hilos en una ejecución en serie con más pasos.
- **Procesos con una función definida en la celda o un `lambda`.** El proceso nuevo no la encuentra; debe vivir en un archivo importable.

Sigue con [[asyncio-y-el-event-loop]]: cómo espera cientos de llamadas un solo hilo, y qué hace que deje de hacerlo.
