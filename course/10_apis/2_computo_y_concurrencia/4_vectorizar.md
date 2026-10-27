---
id: vectorizar
title: "Vectorizar: cuando el trabajo calcula sobre muchos datos"
nav_title: "Vectorizar"
summary: "Hilos y asyncio reparten esperas; si el trabajo calcula sobre millones de números, la ganancia está en sacar el bucle del intérprete con una operación sobre el arreglo completo. Medido contra un bucle de Python, con sus límites y con la ley de Amdahl."
status: ready
estimated_time: 20m
tags: [vectorizacion, numpy, simd, amdahl, speedup, cpu-bound]
prerequisites: [asyncio-y-el-event-loop]
---

# Vectorizar: cuando el trabajo calcula sobre muchos datos

**Página 4 de 5 · Cómputo y concurrencia**

Meta: saber qué hacer cuando el tiempo no se va en esperar sino en calcular sobre muchos datos, medir cuánto gana una operación sobre un arreglo y calcular el techo de cualquier mejora que reparta trabajo.

Las páginas anteriores repartían **esperas**: hilos y `asyncio` ganan porque mientras una petición espera, otra avanza. Un cálculo sobre cinco millones de números no espera nada. Un bucle de Python lo recorre uno por uno, y repartirlo en hilos no lo acelera por el GIL ([[el-gil]]). ¿Qué cambia si en lugar de repartir el bucle lo eliminas?

| Término | Qué es | Lo ves con |
|---|---|---|
| **vectorización** | Aplicar una operación a un arreglo completo en una sola llamada, en vez de un elemento por vez desde un bucle de Python | la celda 4.2 |
| **arreglo contiguo** | Una secuencia de valores del mismo tipo guardados uno junto a otro en memoria | la celda 4.1 |
| **SIMD** | Instrucción de CPU que opera sobre varios valores a la vez en un solo paso | la figura de abajo |
| **speedup** | Tiempo de la versión base entre tiempo de la versión mejorada | la celda 4.2 |
| **ley de Amdahl** | El techo del speedup cuando sólo una parte del trabajo se puede repartir | la celda 4.4 |

## En corto

- **Vectorizar** no exige repartir el trabajo entre CPU: lo mueve de un bucle del intérprete a un bucle en C que recorre los valores crudos.
- **La ganancia combina sacar el bucle de Python, tipos homogéneos y acceso a memoria**; la medición de abajo no separa cuánto es SIMD.
- **Sólo sirve si la operación es la misma para todos los elementos**. Lógica distinta por elemento, objetos arbitrarios o datos que no caben en memoria quedan fuera.

## Qué guarda cada uno

Una lista de Python guarda **referencias a objetos**: cada `float` es un objeto aparte con su cabecera, y para sumarlos el intérprete sigue cada referencia, revisa el tipo y despacha la operación. Un arreglo de NumPy guarda **los valores crudos, todos del mismo `dtype`**; el que crea `np.arange` está en un bloque contiguo. Sus vistas (p. ej. `a[::2]`) pueden no ser contiguas y siguen admitiendo operaciones vectorizadas.

**Haz (celda 4.1):** crea un arreglo de cinco millones de `float64` y mira qué ocupa; mide aparte lo que cuesta crearlo.

```python
import time
import numpy as np

n = 5_000_000

t0 = time.perf_counter()
a = np.arange(n, dtype=np.float64)
crear_s = time.perf_counter() - t0

print("dtype:", a.dtype, "| bytes por elemento:", a.itemsize)
print("bytes totales:", a.nbytes)
print("contiguo:", a.flags["C_CONTIGUOUS"])
print(f"crear el arreglo: {crear_s:.4f} s")
```

**Qué hace cada línea:**

- `np.arange(n, dtype=np.float64)` crea los números de 0 a `n - 1` ya como decimales de 64 bits.
- `itemsize` y `nbytes` muestran que cada elemento ocupa 8 bytes, sin cabecera de objeto.
- `C_CONTIGUOUS` confirma que los valores están uno junto a otro.
- La creación se mide **aparte**: no se cuenta dentro de la comparación de la siguiente celda.

**Deberías ver:**

```text
dtype: float64 | bytes por elemento: 8
bytes totales: 40000000
contiguo: True
crear el arreglo: 0.0065 s
```

## Bucle de Python contra una sola llamada

La tarea: la suma de cuadrados de los `n` números. Las dos versiones calculan lo mismo; cambia quién recorre los datos.

**Haz (celda 4.2):** mide el bucle de Python sobre una lista y la operación vectorizada sobre el arreglo, y verifica que coinciden.

```python
import time
import numpy as np

n = 5_000_000
a = np.arange(n, dtype=np.float64)
lista = a.tolist()  # la conversión queda fuera de la medición

def suma_cuadrados_bucle(xs):
    total = 0.0
    for x in xs:
        total += x * x
    return total

def suma_cuadrados_numpy(arr):
    return float(np.sum(arr * arr))

suma_cuadrados_numpy(a)  # corrida de calentamiento, se descarta

t0 = time.perf_counter()
r_bucle = suma_cuadrados_bucle(lista)
bucle_s = time.perf_counter() - t0

t0 = time.perf_counter()
r_numpy = suma_cuadrados_numpy(a)
numpy_s = time.perf_counter() - t0

print(f"bucle de Python: {bucle_s:.3f} s")
print(f"NumPy:           {numpy_s:.4f} s")
print(f"speedup:         {bucle_s / numpy_s:.0f}x")
print("coinciden:", np.isclose(r_bucle, r_numpy, rtol=1e-9))
```

**Qué hace cada línea:**

- `lista = a.tolist()` prepara la entrada del bucle fuera del cronómetro, para no cobrarle la conversión.
- `suma_cuadrados_bucle` es el bucle que ya conoces: una multiplicación y una suma por elemento, ejecutadas por el intérprete.
- `arr * arr` y `np.sum` son **dos operaciones sobre el arreglo completo**; el recorrido ocurre en C.
- La llamada sin guardar el resultado es el calentamiento: la primera corrida se descarta.
- `np.isclose` compara con tolerancia relativa porque las dos versiones suman en distinto orden y los decimales no son asociativos.

**Deberías ver:**

```text
bucle de Python: 0.188 s
NumPy:           0.0119 s
speedup:         16x
coinciden: True
```

Son tiempos de la máquina del profesor; los tuyos cambian, y la proporción también puede cambiar.

::: figure {#cmp-vectorizar title="Un bucle elemento a elemento contra una operación sobre el arreglo completo"}
![Dos carriles comparados. Arriba, un bucle de Python que toma un elemento por vez de una lista de referencias, revisa su tipo, multiplica y suma, y repite cinco millones de veces dentro del intérprete. Abajo, un arreglo contiguo de float64 que una sola llamada recorre en un bucle de C, procesando varios valores por instrucción en carriles SIMD.](../_assets/cmp-vectorizar.svg)
:::

## Qué cambió, y cuánto le toca a cada cosa

| Qué cambió | Efecto |
|---|---|
| **Tipos homogéneos** | No se revisa el tipo de cada elemento: se sabe una vez para todo el arreglo |
| **Memoria contigua** | La CPU lee los datos en orden y la caché los tiene a mano |
| **El bucle sale del intérprete** | Desaparecen el despacho por elemento, la referencia a objetos y el conteo de referencias |
| **SIMD** | Una instrucción procesa varios valores a la vez; esta medición no separa cuánto aporta |

**Los 16x combinan sacar el bucle del intérprete, tipos homogéneos y acceso a memoria; esta medición no separa cuánto es SIMD.** Para atribuir una parte a cada cosa harían falta mediciones que cambien una sola a la vez.

## `float64`, no `int64`

Un `np.int64` tiene 64 bits con signo y **no crece**: si el resultado no cabe, da la vuelta sin avisar. Un `int` de Python no tiene tope. La suma de cuadrados de 0 a 5 millones pasa de `9.2e18`, el máximo de `int64`.

**Haz (celda 4.3):** suma los mismos cuadrados con `int64` y compara con el valor exacto.

```python
import numpy as np

n = 5_000_000
enteros = np.arange(n, dtype=np.int64)

con_int64 = int(np.sum(enteros * enteros))
exacto = (n - 1) * n * (2 * n - 1) // 6  # fórmula cerrada, enteros de Python
con_float64 = float(np.sum(np.arange(n, dtype=np.float64) ** 2))

print("máximo de int64:", np.iinfo(np.int64).max)
print("exacto (Python):", exacto)
print("int64 (NumPy):  ", con_int64)
print("float64 (NumPy):", f"{con_float64:.6e}")
```

**Qué hace cada línea:**

- `np.iinfo(np.int64).max` es el mayor entero que cabe en 64 bits con signo.
- `exacto` usa la fórmula de la suma de cuadrados con enteros de Python, que no se desbordan.
- `con_int64` suma en `int64`: el resultado pasa el máximo y sale **otro número, sin error**.
- `con_float64` pierde precisión en los últimos dígitos, pero conserva la magnitud.

**Deberías ver:**

```text
máximo de int64: 9223372036854775807
exacto (Python): 41666654166667500000
int64 (NumPy):   4773166019248396768
float64 (NumPy): 4.166665e+19
```

## Cuándo vectorizar no sirve

| Caso | Por qué | Qué hacer |
|---|---|---|
| **Lógica distinta por elemento** (ramas, estado que cambia al avanzar) | No hay una sola operación que aplicar al arreglo | Procesos, o reescribir con máscaras (`np.where`) si la lógica lo permite |
| **Objetos de Python** (cadenas, diccionarios, instancias) | El arreglo de objetos guarda referencias otra vez: sin tipos crudos, sin ganancia | Procesos, o convertir los datos a un `dtype` numérico si lo admiten |
| **Datos que no caben en memoria** | `arr * arr` crea otro arreglo del mismo tamaño | Procesar por bloques, o una herramienta lazy como Polars (9.3) |
| **Pocos elementos** | El costo fijo de cada llamada pesa más que el bucle | Un bucle normal |
| **Cada elemento depende del anterior** | No se pueden calcular a la vez | Reformular, o aceptar el bucle |

**NumPy libera el GIL** durante las operaciones grandes sobre arreglos: mientras C recorre los datos, otro hilo de Python puede correr. Es un dato útil, no un sustituto de medir; el mecanismo del GIL está en [[el-gil]].

## Amdahl: el techo de repartir el trabajo

> [!NOTE]
> Si falta tiempo, la sección de Amdahl se omite.

Si repartes un trabajo entre `P` unidades de cómputo, sólo la parte repartible se acelera. **La ley de Amdahl** dice cuánto: con `S` la fracción del tiempo que **no** se puede repartir, el speedup con `P` unidades es:

`speedup(P) = 1 / (S + (1 - S) / P)`

Con `P` tendiendo a infinito el techo es `1 / S`. Si la mitad del trabajo es serial, nunca pasas de 2x, tengas las unidades que tengas.

| `S` (fracción serial) | `P` = 2 | `P` = 4 | `P` = 8 | Techo (`P` infinito) |
|---|---:|---:|---:|---:|
| 0.10 | 1.82 | 3.08 | 4.71 | 10.0 |
| 0.25 | 1.60 | 2.29 | 2.91 | 4.0 |
| 0.50 | 1.33 | 1.60 | 1.78 | 2.0 |

**Haz (celda 4.4):** calcula la tabla y mira cuánto rinde duplicar `P` cuando `S = 0.25`.

```python
def amdahl(S, P):
    return 1 / (S + (1 - S) / P)

for S in (0.10, 0.25, 0.50):
    fila = [f"{amdahl(S, P):.2f}" for P in (2, 4, 8)]
    print(f"S={S:.2f}", fila, "techo:", round(1 / S, 1))

print("S=0.25, de 4 a 8 unidades:", round(amdahl(0.25, 8) / amdahl(0.25, 4), 2), "veces más")
```

**Qué hace cada línea:**

- `amdahl(S, P)` es la fórmula tal cual.
- El bucle imprime una fila por cada `S` con `P` = 2, 4 y 8, más el techo `1 / S`.
- La última línea compara 8 unidades contra 4: duplicar `P` no duplica el speedup.

**Deberías ver:**

```text
S=0.10 ['1.82', '3.08', '4.71'] techo: 10.0
S=0.25 ['1.60', '2.29', '2.91'] techo: 4.0
S=0.50 ['1.33', '1.60', '1.78'] techo: 2.0
S=0.25, de 4 a 8 unidades: 1.27 veces más
```

::: figure {#cmp-amdahl title="Speedup teórico de Amdahl según la fracción serial"}
![Tres curvas del speedup teórico contra el número de unidades de cómputo, para fracciones seriales de 0.1, 0.25 y 0.5. Cada curva sube rápido con pocas unidades y se aplana hacia su techo, que es uno entre S: 10, 4 y 2 respectivamente. Una recta de referencia muestra el speedup ideal sin parte serial. Modelo ideal: carga fija, fracción serial constante y sin costos adicionales.](../_assets/cmp-amdahl.svg)
:::

**Amdahl supone una carga fija y un reparto ideal.** `S` es la fracción del tiempo original que no mejora al repartir, incluida la E/S que no se puede solapar. El 0.7 % de CPU de la celda 1.2 no determina `S`. Arrancar procesos, transferir datos y recolectar resultados añaden costos que la fórmula no cuenta; por eso el speedup medido queda por debajo de la curva.

## Al diseñar / al revisar código de IA, busca…

- **Un `for` de Python sobre un arreglo o una columna** para sumar, multiplicar o filtrar: casi siempre es una operación vectorizable.
- **Hilos para acelerar un cálculo numérico**: el GIL impide acelerar bucles de Python con hilos. Muchas operaciones de NumPy lo liberan y BLAS puede usar hilos internos: controla los hilos por proceso para no sobreasignar las CPU.
- **Acumuladores en `int64` o `int32` sobre sumas grandes**: desbordan sin aviso. Revisa el `dtype`.
- **Una medición que incluye crear el arreglo o convertir la lista**, o que no descarta la primera corrida: infla o desinfla el speedup.
- **Una promesa de «N veces más rápido con N procesos»** sin hablar de la fracción serial ni del costo de serializar.

Sigue con [[elegir-la-estrategia]].
