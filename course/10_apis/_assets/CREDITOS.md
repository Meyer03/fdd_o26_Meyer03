# Créditos de materiales de la unidad

Procedencia, ruta y condición de uso de cada material del directorio.

Los SVG salen de `tools/gen_computo.py`, que es su única fuente de verdad. No se
editan a mano, se regeneran. La guarda `tools/test_gen_computo.py` falla si un
archivo del disco deja de coincidir con lo que produce el generador. Los
esquemas se reconstruyeron, con tiempos constantes y no medidos, a partir de los
de la clase 16 (cómputo) del curso de primavera 2026.

| Archivo | Descripción y prompt resumido | Autor / origen | Fecha | Licencia |
|---|---|---|---|---|
| cmp-gantt-secuencial.svg | Ruta: `course/10_apis/_assets/cmp-gantt-secuencial.svg`. Gantt de tres tareas en serie (ejecuta 20 ms, espera 200 ms, ejecuta 20 ms), eje en ms, fila de CPU inactiva durante las esperas; total 720 ms. | Generado por `tools/gen_computo.py`; obra propia | 2026-10-27 | Uso docente del curso |
| cmp-gantt-hilos.svg | Ruta: `course/10_apis/_assets/cmp-gantt-hilos.svg`. Las mismas tareas en tres hilos: esperas solapadas, ejecución turnada por el GIL, tramos «lista»; total 280 ms. | Generado por `tools/gen_computo.py`; obra propia | 2026-10-27 | Uso docente del curso |
| cmp-gantt-asyncio.svg | Ruta: `course/10_apis/_assets/cmp-gantt-asyncio.svg`. Las mismas tareas como corrutinas con `gather` en un hilo: cada `await` cede el turno; total 280 ms. | Generado por `tools/gen_computo.py`; obra propia | 2026-10-27 | Uso docente del curso |
| cmp-gantt-await-en-serie.svg | Ruta: `course/10_apis/_assets/cmp-gantt-await-en-serie.svg`. El anti-patrón de `await` uno tras otro: el mismo dibujo que el secuencial, total 720 ms. | Generado por `tools/gen_computo.py`; obra propia | 2026-10-27 | Uso docente del curso |
| cmp-gantt-procesos.svg | Ruta: `course/10_apis/_assets/cmp-gantt-procesos.svg`. Las mismas tareas en tres procesos sobre dos CPU con ejecución simultánea; total 260 ms. | Generado por `tools/gen_computo.py`; obra propia | 2026-10-27 | Uso docente del curso |
| cmp-matriz-2x2.svg | Ruta: `course/10_apis/_assets/cmp-matriz-2x2.svg`. Matriz concurrente × paralelo con secuencial, hilos, `asyncio` y procesos ubicados; asíncrono como forma de escribir la espera, no como celda. | Generado por `tools/gen_computo.py`; obra propia | 2026-10-27 | Uso docente del curso |
| cmp-event-loop.svg | Ruta: `course/10_apis/_assets/cmp-event-loop.svg`. Traza del event loop con tres corrutinas: cuándo cede cada una en su `await`, el loop sin nadie listo y cuándo las reanuda. | Generado por `tools/gen_computo.py`; obra propia | 2026-10-27 | Uso docente del curso |
| cmp-bloqueo-del-loop.svg | Ruta: `course/10_apis/_assets/cmp-bloqueo-del-loop.svg`. Un cálculo de 2000 ms sin `await` dentro del loop deja listas sin turno a dos corrutinas cuyas respuestas ya llegaron; total 2080 ms. | Generado por `tools/gen_computo.py`; obra propia | 2026-10-27 | Uso docente del curso |
| cmp-vectorizar.svg | Ruta: `course/10_apis/_assets/cmp-vectorizar.svg`. Bucle de Python elemento por elemento a través del intérprete contra un arreglo `float64` contiguo recorrido por un bucle compilado; SIMD como factor secundario. | Generado por `tools/gen_computo.py`; obra propia | 2026-10-27 | Uso docente del curso |
| cmp-amdahl.svg | Ruta: `course/10_apis/_assets/cmp-amdahl.svg`. Curvas teóricas de la ley de Amdahl para fracción serial S = 0.1, 0.25 y 0.5 con P de 1 a 16, la diagonal ideal y el techo 1/S de cada una. | Generado por `tools/gen_computo.py`; obra propia | 2026-10-27 | Uso docente del curso |
| cmp-arbol-decision.svg | Ruta: `course/10_apis/_assets/cmp-arbol-decision.svg`. Árbol de decisión: ¿espera o calcula?, ¿hay librería async?, ¿opera sobre arreglos?, ¿pedazos independientes?; termina en `asyncio`, hilos, vectorizar, procesos o secuencial. | Generado por `tools/gen_computo.py`; obra propia | 2026-10-27 | Uso docente del curso |
