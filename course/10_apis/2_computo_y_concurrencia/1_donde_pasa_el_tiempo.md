---
id: donde-pasa-el-tiempo
title: "Dónde pasa el tiempo"
nav_title: "Dónde pasa el tiempo"
summary: "Una tarea tiene un tramo en que la CPU trabaja y un tramo en que sólo espera. Medir cuánto de cada uno tiene tu trabajo decide si necesitas hacer más cosas a la vez o calcular más rápido."
status: ready
estimated_time: 15m
tags: [cpu-bound, io-bound, latencia, gantt, medicion, secuencial]
prerequisites: [apis-y-http]
---

# Dónde pasa el tiempo

**Página 1 de 5 · Cómputo y concurrencia**

Pregunta de la página: **¿por qué 20 peticiones tardan 20 veces lo que una?** Y la que sigue: si tardan eso, ¿qué parte del tiempo es tu programa trabajando?

Meta: separar el tiempo de una tarea en lo que **ejecuta** y lo que **espera**, medirlo y leer el resultado en un Gantt.

| Término | Qué es | Lo ves con |
|---|---|---|
| **tarea** | Una unidad de trabajo con un inicio y un fin, por ejemplo una llamada a la API | la celda 1.1 |
| **tramo que ejecuta** | El tiempo en que la CPU corre instrucciones de la tarea | la columna `CPU` de la celda 1.1 |
| **tramo que espera** | El tiempo en que la tarea no avanza porque aguarda algo de fuera (la red, un disco, un timer) | la columna `reloj` de la celda 1.1 |
| **CPU-bound** | Tarea cuyo tiempo es casi todo ejecución: más CPU la acelera | el bucle de la celda 1.1 |
| **I/O-bound** | Tarea cuyo tiempo es casi todo espera: más CPU no la acelera | la llamada de la celda 1.1 |
| **secuencial** | Ejecutar las tareas una tras otra: la siguiente empieza cuando la anterior terminó | la celda 1.2 |

## En corto

- **Una tarea = ejecuta + espera.** El tiempo total (el *reloj*) es la suma de los dos tramos.
- **Una llamada a una API casi no ejecuta: espera.** Tu CPU está disponible durante esa espera y no hace nada.
- **En secuencial las esperas se suman**: 20 llamadas de 0.2 s son 4 s, no 0.2 s.

## Arranque de la sección

Todo lo de esta sección corre contra `servidor.py` de 10.1 y se mide en tu máquina. Lo que sigue es **trabajo previo a la clase** (el aula puede no tener internet): hazlo antes.

```bash
cd estudiantes/$GHUSER/10_apis && uv sync
```

- `uv sync` instala en `.venv/` las dependencias de `pyproject.toml`, incluidas `httpx` y `numpy`, que usan las páginas 3 y 4.

En una terminal aparte, deja el servidor corriendo y en modo silencioso, para que no imprima 10 líneas por petición y no distorsione los tiempos:

```bash
FDD_SILENCIO=1 uv run python servidor.py
```

- `FDD_SILENCIO=1` — variable de entorno que apaga la radiografía de cada petición.
- El servidor atiende cada petición en su propio hilo, así que dos llamadas pueden estar en curso a la vez.
- El endpoint `GET /ventas?lento=0.2` duerme 0.2 s antes de contestar. Es una espera controlada: simula una API remota que tarda.

## Ejecuta y espera

**Definición.** Una **tarea** es una unidad de trabajo con inicio y fin. Su duración se parte en dos tramos que no se traslapan: el que **ejecuta** (la CPU corre instrucciones) y el que **espera** (la tarea no puede avanzar hasta que algo de fuera responda). Hay un tercer estado que sólo aparece cuando varias tareas comparten una CPU: **lista**, la tarea ya podría ejecutar pero otra tiene la CPU y le toca esperar su turno. Los Gantt de las páginas siguientes lo dibujan aparte; la diferencia entre el reloj y el tiempo de CPU de abajo incluye también ese turno.

Una llamada a una API tiene los dos: ejecutar es armar la petición y leer el JSON; esperar es el viaje por la red y el tiempo del servidor (la latencia de [[que-es-una-api]]).

**Para qué sirve separarlos.** Cada tramo se acelera de forma distinta. Ejecutar se acelera con más CPU o menos instrucciones; esperar no se acelera con nada de tu lado, sólo se **solapa** con otra cosa. Si no sabes cuál tramo domina, optimizas el equivocado.

**Si lo ignoras.** Es el error más caro de la sección: comprar más núcleos o reescribir en otro lenguaje un programa que pasa el 99 % del tiempo esperando una respuesta.

## CPU-bound e I/O-bound

**Definición.** Una tarea es **CPU-bound** si casi todo su tiempo es ejecución; es **I/O-bound** (entrada/salida: red, disco) si casi todo su tiempo es espera.

La diferencia se ve comparando dos relojes: el **reloj** (`time.perf_counter`, lo que pasó en la pared) y el **tiempo de CPU** (`time.process_time`, lo que la CPU trabajó para tu proceso). Si coinciden, la tarea ejecutó todo el rato; si el reloj es mucho mayor, esperó.

**Haz (celda 1.1):** mide una llamada con `?lento=0.2` y un bucle puro de Python con los dos relojes.

```python
import time

import requests

from cable import URL


def cuenta(n=3_000_000):
    suma = 0
    for i in range(n):
        suma += i * i
    return suma


def mide(nombre, tarea):
    reloj0, cpu0 = time.perf_counter(), time.process_time()
    tarea()
    reloj = time.perf_counter() - reloj0
    cpu = time.process_time() - cpu0
    print(f"{nombre:22} reloj {reloj:5.2f} s   CPU {cpu:5.2f} s   CPU/reloj {cpu / reloj:5.0%}")


mide("llamada ?lento=0.2", lambda: requests.get(f"{URL}/ventas?lento=0.2", timeout=5))
mide("bucle puro de Python", cuenta)
```

**Qué hace cada línea:**

- `from cable import URL` — la dirección del servidor, de 10.1.
- `cuenta(n)` — suma los cuadrados de `0` a `n - 1` con un bucle de Python: no toca la red ni el disco, sólo calcula.
- `mide(nombre, tarea)` — corre `tarea` y lee los dos relojes antes y después.
- `time.perf_counter()` — el reloj de pared: segundos reales transcurridos.
- `time.process_time()` — los segundos que la CPU trabajó para este proceso; no cuenta el tiempo dormido o esperando.
- `cpu / reloj` — la fracción del tiempo en que la tarea ejecutó.

**Deberías ver:**

```text
llamada ?lento=0.2     reloj  0.20 s   CPU  0.00 s   CPU/reloj    1%
bucle puro de Python   reloj  0.35 s   CPU  0.35 s   CPU/reloj  100%
```

- En la llamada, la CPU trabaja una fracción mínima del reloj: el resto la tarea **esperó**. Es I/O-bound.
- En el bucle, el reloj y la CPU son casi iguales: nunca esperó. Es CPU-bound.
- La misma máquina, el mismo Python, dos tareas de naturaleza opuesta. Por eso la herramienta correcta cambia con la tarea (páginas 2 a 5).

> [!NOTE]
> `process_time` cuenta el proceso completo del notebook, no sólo la tarea; con el kernel en reposo la diferencia es de milisegundos. Los números son de la máquina del profesor, y los tuyos serán otros: lo que se conserva es la proporción.

## Veinte llamadas en secuencia

**Definición.** Un programa es **secuencial** cuando ejecuta las tareas una tras otra: la tarea *k + 1* no empieza hasta que la *k* terminó.

Lo que pasa con 20 llamadas a `?lento=0.2` se lee en un Gantt: una barra por tarea sobre el eje del tiempo, con el tramo que ejecuta y el que espera, y debajo una fila con lo que hace la CPU.

::: figure {#cmp-gantt-secuencial title="Tareas en secuencia: las esperas se suman y la CPU queda inactiva"}
![Diagrama de Gantt de tres tareas en secuencia sobre un eje de tiempo en milisegundos: cada tarea tiene un tramo corto que ejecuta y uno largo que espera, una empieza cuando la anterior termina, y la fila de CPU muestra trabajo sólo en los tramos cortos y el resto marcado como inactiva](../_assets/cmp-gantt-secuencial.svg)
:::

En el Gantt de arriba hay tres cosas que leer:

- Cada tarea empieza hasta que termina la anterior: el tiempo total es la **suma** de las duraciones.
- Los tramos que esperan son largos y los que ejecutan son astillas.
- La fila de la CPU está vacía durante toda espera: la máquina **podía** hacer otra cosa y no hizo nada.

**Haz (celda 1.2):** llama 20 veces seguidas y reparte el tiempo entre ejecutar y esperar.

```python
import time

import requests

from cable import URL

N = 20
reloj0, cpu0 = time.perf_counter(), time.process_time()
for _ in range(N):
    requests.get(f"{URL}/ventas?lento=0.2", timeout=5)
reloj = time.perf_counter() - reloj0
cpu = time.process_time() - cpu0

print(f"{N} llamadas en serie: {reloj:.2f} s  ({reloj / N:.3f} s por llamada)")
print(f"ejecuta (CPU):  {cpu:.2f} s  ({cpu / reloj:.1%})")
print(f"espera:         {reloj - cpu:.2f} s  ({(reloj - cpu) / reloj:.1%})")
print(f"sueño pedido al servidor: {N * 0.2:.1f} s")
```

**Qué hace cada línea:**

- `for _ in range(N)` — 20 vueltas; cada `requests.get` bloquea hasta recibir la respuesta, así que la siguiente no sale antes.
- `reloj - cpu` — lo que no fue CPU de tu proceso: espera.
- `N * 0.2` — lo que pidió el programa: 20 pausas de 0.2 s. El reloj no puede ser menor a eso.

**Deberías ver:**

```text
20 llamadas en serie: 4.04 s  (0.202 s por llamada)
ejecuta (CPU):  0.03 s  (0.7%)
espera:         4.01 s  (99.3%)
sueño pedido al servidor: 4.0 s
```

El total fue **4.04 s**. De ese tiempo, **99.3 %** fue espera; la CPU de tu proceso ejecutó el resto.

## Por qué ese porcentaje decide todo

La regla que ordena el resto de la sección: **el tiempo de una tarea I/O-bound es casi todo espera, y la espera se puede solapar con otra espera**. Si 20 llamadas esperan al mismo tiempo en lugar de una tras otra, el total se acerca a lo que tarda **una**, no a la suma.

| Dónde está el tiempo | Qué lo acelera | Qué no lo acelera | Páginas |
|---|---|---|---|
| **Espera** (I/O-bound) | Solapar esperas: hilos o `asyncio` | Más núcleos; un algoritmo más rápido | 2, 3 |
| **Ejecución** en Python (CPU-bound) | Repartir el cálculo en procesos | Hilos (por el GIL, ver [[el-gil]]) | 2 |
| **Ejecución** sobre muchos datos numéricos | Vectorizar: sacar el bucle de Python | Más hilos | 4 |

Los 20 y los 0.2 s son parámetros de esta demostración. Lo que no depende de ellos es la pregunta que haces antes de tocar el código: **¿cuánto de mi tiempo es espera?** Si la respuesta es 95 %, el máximo que puedes ganar ejecutando más rápido es 5 %.

> [!WARNING]
> Con 100 o 500 llamadas la secuencial no se mide en esta clase: 100 llamadas son 20 s y 500 son 100 s. Son N × 0.2 s, **calculado, no medido**. Es suficiente: la suma de esperas es exacta porque no hay nada que se solape.

## Al diseñar / al revisar código de IA, busca…

- **Un `for` que llama a una API, a una base de datos o a un archivo en cada vuelta**: si las llamadas no dependen una de otra, las esperas se están sumando sin necesidad.
- **Optimización de la parte equivocada**: reescrituras de algoritmo, caché de cálculos o más CPU sobre un programa que pasa casi todo su reloj esperando. Pide la medición de `reloj` contra `CPU` antes de aceptar el cambio.
- **Tiempos sin medir**: «esto es rápido» o «esto es lento» sin `perf_counter`, o con un solo número en lugar de la proporción ejecuta/espera.
- **Una llamada de red sin `timeout`**: la espera no tiene tope (ver [[metodos-y-status]]).
- **Mezclar los dos tipos de tarea en el mismo bucle** (llamar y luego calcular con la respuesta): cada tramo necesita su propia herramienta, y se separan antes de elegir una.

Sigue con [[concurrente-paralelo-asincrono]].
