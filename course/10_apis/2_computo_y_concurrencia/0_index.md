---
id: computo-y-concurrencia
title: "Cómputo y concurrencia"
nav_title: "2. Cómputo y concurrencia"
summary: "Dónde pasa el tiempo en un programa, qué significan concurrente, paralelo y asíncrono, cómo espera 100 peticiones un solo hilo, cuándo conviene vectorizar y cómo elegir la estrategia con una medición."
status: ready
estimated_time: 100m
tags: [concurrencia, asyncio, hilos, procesos, numpy, notebook]
prerequisites: [apis-y-http, el-gil]
---

# Cómputo y concurrencia

**Sección 2** · 5 páginas · unos 100 min · sesión del martes 27 de octubre, 19:00–20:30

Meta: decidir, con una medición y no con una intuición, si un trabajo se hace en secuencia, con hilos, con `asyncio`, con procesos o vectorizado, y leer un Gantt que lo justifique.

## En corto

- **Una tarea tiene dos tramos: el que ejecuta y el que espera.** Qué estrategia sirve depende de en cuál de los dos pasa el tiempo.
- **Concurrente, paralelo y asíncrono son tres cosas distintas.** Las tres páginas centrales las separan con una definición, un comando y una salida cada una.
- **Toda la clase corre contra el servidor de la sección 1**, ahora con `?lento=` para fabricar espera, y con funciones locales para fabricar cálculo.

## Las páginas

| # | Página | Qué contesta | Min |
|---:|---|---|---:|
| 1 | [[donde-pasa-el-tiempo]] | Por qué 20 peticiones tardan 20 veces lo que una, y qué distingue esperar de calcular | 15 |
| 2 | [[concurrente-paralelo-asincrono]] | Qué significa cada palabra, qué hace cada estrategia y qué se rompe cuando comparten memoria | 30 |
| 3 | [[asyncio-y-el-event-loop]] | Cómo espera 100 peticiones un solo hilo, y qué lo detiene | 25 |
| 4 | [[vectorizar]] | Qué hacer cuando el trabajo no espera sino que calcula sobre muchos datos | 20 |
| 5 | [[elegir-la-estrategia]] | Dado un trabajo, qué usar, con qué costo y con qué anti-patrones | 10 |

Si falta tiempo se recorta, en este orden: Amdahl en la página 4 y la combinación de estrategias en la 5. Las páginas 2 y 3 no se recortan.

## Glosario de la sección

Cada término se define en la página que se indica, antes de usarlo.

| Término | Definición en una línea | Página |
|---|---|---:|
| Tarea | Unidad de trabajo que tiene un inicio y un resultado | 1 |
| Ejecutar / esperar | Tramo en que la CPU trabaja para ti / tramo en que algo externo (red, disco) tarda | 1 |
| CPU-bound / I/O-bound | Tarea cuyo tiempo se va en ejecutar / en esperar | 1 |
| Concurrente | Varias tareas con ciclos de vida que se solapan en el tiempo | 2 |
| Paralelo | Dos cosas ejecutándose en el mismo instante, lo que exige al menos 2 CPU | 2 |
| Asíncrono | Modelo en que la llamada regresa antes del resultado y quien espera cede el control explícitamente | 2 |
| Condición de carrera | Resultado que depende del orden en que se intercalan dos hilos | 2 |
| Event loop / corrutina | El ciclo que reparte un solo hilo / función que puede suspenderse con `await` | 3 |
| `gather` | Lanza varias corrutinas a la vez y junta sus resultados | 3 |
| Vectorización | Aplicar una operación a un arreglo entero en código compilado, no elemento a elemento en Python | 4 |
| Ley de Amdahl | Tope de aceleración que impone la parte que no se puede repartir | 4 |
| Pool / speedup | Conjunto fijo de hilos o procesos que reparte trabajo / cociente entre el tiempo de antes y el de después | 5 |

## Antes de la clase

**El aula no tiene internet: haz esto antes, con red.** Esta sección agrega dos paquetes al ambiente de la sección 1: `httpx` (cliente que sí puede esperar sin bloquear) y `numpy` (arreglos). Instalarlos exige descargar.

**Haz 1 · trae lo nuevo del curso y actualiza el ambiente:**

```bash
cd {tu_fork_de_la_clase}
git switch main && git fetch upstream && git merge --ff-only upstream/main
git switch -c clase-10-computo
[ -n "$GHUSER" ] && mkdir -p estudiantes/$GHUSER/10_apis \
  && cp -r codigo/10_apis/. estudiantes/$GHUSER/10_apis/ \
  && cd estudiantes/$GHUSER/10_apis && uv sync
```

**Qué hace cada pieza:**

- `git switch main && … merge --ff-only upstream/main` — el ritual de siempre: trae lo nuevo del curso a tu `main`.
- `git switch -c clase-10-computo` — crea la branch de esta clase. **Esta sección tampoco tiene entrega**: no se abre pull request.
- `cp -r codigo/10_apis/. …` — vuelve a copiar la plantilla; trae `computo.ipynb`, `trabajo_computo.py`, el `servidor.py` actualizado y el `pyproject.toml` con las dos dependencias nuevas.
- `uv sync` — descarga `httpx` y `numpy` al `.venv/` de `10_apis`. Es la única parte que necesita internet.

**Deberías ver** al final una línea `Installed … packages`. Si ya tenías `.venv/`, `uv` sólo agrega lo que falta.

**Haz 2 · comprueba que `numpy` y `httpx` se instalaron**, todavía dentro de `10_apis`:

```bash
uv run python -c "import httpx, numpy; print(httpx.__version__, numpy.__version__)"
```

**Deberías ver** dos números de versión separados por un espacio. Si sale `ModuleNotFoundError`, repite `uv sync` con red antes de la clase.

**Haz 3 · arranca el servidor** en una terminal aparte, dentro de tu carpeta `10_apis`:

```bash
FDD_SILENCIO=1 uv run python servidor.py
```

`FDD_SILENCIO=1` apaga la radiografía de cada petición: en esta sección se hacen cientos de llamadas y imprimirlas estorbaría la medición. Se queda escuchando en el puerto 8026 hasta que lo apagues con Ctrl+C. **Deja esa terminal abierta toda la clase.** Esta sección no necesita internet después de la instalación: todo corre contra tu servidor local.

**Haz 4 · abre `computo.ipynb`** en VS Code y elige como kernel el `.venv` de `10_apis`. Sus celdas son las de estas páginas, numeradas `N.M` por página.

## Qué no cubre esta sección

- **Cómo se comunican dos programas cuando hay que esperar un evento** (polling, SSE, WebSocket, webhooks, gRPC, GraphQL): es la siguiente sección, *Patrones y protocolos*.
- **Cómo se arma un sistema con esas piezas sin que se caiga** (timeouts, reintentos, colas, escalado): es la sección después de esa, *Arquitectura de APIs*.
- **Qué es un hilo, un proceso y el GIL por dentro**: está en [[el-gil]]; aquí sólo se resume en una tabla y se usa.

Sigue con [[donde-pasa-el-tiempo]].
