"""Genera los diagramas SVG de la unidad 10, seccion 10.2 (Computo y concurrencia).

Las primitivas y la paleta salen de tools/svg_base.py: un solo lugar declara
los colores de skins/fdd-eva.yaml.

Este archivo es la unica fuente de verdad de esos SVG. Editar un .svg a mano es
un error que tools/test_gen_computo.py detecta.

Los esquemas se reconstruyen desde fdd_p26/clase/16_computo/scripts/
generar_graficas.py con tiempos constantes, no medidos: no dependen de ninguna
maquina. Las cinco Gantt usan las MISMAS tres tareas (ejecuta 20 ms, espera
200 ms, ejecuta 20 ms) y la misma escala de 0 a 800 ms, para que se comparen a
simple vista.

Los ids llevan prefijo "cmp-" a proposito: los ids de objeto numerado de Raya
son unicos en TODO el curso, no por pagina.
"""
import sys
from pathlib import Path

from svg_base import (
    ACENTO, AMBAR, CIAN, FONDO, LINEA, PANEL, ROJO, SUAVE, TEXTO, TINTE,
    VIOLETA, caja, cierre, flecha, marco, teclado, texto,
)

RAIZ = Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "course/10_apis/_assets"

# Las tres tareas de todas las Gantt: ejecuta, espera la red, ejecuta.
EJECUTA_MS = 20
ESPERA_MS = 200

ANCHO = 1080
X0 = 190          # inicio del area de tiempo
X1 = 1040         # fin del area de tiempo


def _rect(x, y, w, h, relleno, borde="none", grosor=0, guiones=None, radio=3):
    extra = f' stroke-dasharray="{guiones}"' if guiones else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 3):.1f}" height="{h}" '
            f'rx="{radio}" fill="{relleno}" stroke="{borde}" '
            f'stroke-width="{grosor}"{extra}/>')


def _linea(x1, y1, x2, y2, color=LINEA, grosor=1.2, guiones=None):
    extra = f' stroke-dasharray="{guiones}"' if guiones else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{grosor}"{extra}/>')


def _segmento(tipo, x, y, w, h):
    """Un tramo de una fila de la Gantt, con su texto si cabe."""
    p = []
    medio = y + h / 2 + 5
    if tipo == "ejecuta":
        p.append(_rect(x, y, w, h, ACENTO))
    elif tipo == "espera":
        p.append(_rect(x, y, w, h, PANEL, CIAN, 1.6, "6 4"))
        if w > 120:
            p.append(texto(x + w / 2, medio, "espera la red", CIAN, 13))
    elif tipo == "lista":
        p.append(_rect(x, y, w, h, "none", AMBAR, 1.6, "4 3"))
        if w > 60:
            p.append(texto(x + w / 2, medio, "lista, sin turno", AMBAR, 13))
    elif tipo == "bloquea":
        p.append(_rect(x, y, w, h, ROJO))
        if w > 200:
            p.append(texto(x + w / 2, medio, "calcula 2000 ms sin await",
                           FONDO, 14, peso="600"))
    return "".join(p)


def _leyenda(y, con_bloqueo=False):
    items = [
        ("ejecuta", "ejecuta: usa la CPU"),
        ("espera", "espera: red o disco, CPU libre"),
        ("lista", "lista: puede seguir, espera turno"),
        ("inactiva", "CPU inactiva"),
    ]
    if con_bloqueo:
        items[3] = ("bloquea", "calcula dentro del loop")
    p, x = [], X0 - 150
    for tipo, rotulo in items:
        if tipo == "inactiva":
            p.append(_rect(x, y - 13, 30, 16, "none", SUAVE, 1.4, "3 3"))
        else:
            p.append(_segmento(tipo, x, y - 13, 30, 16))
        p.append(texto(x + 40, y, rotulo, TEXTO, 13, anclaje="start"))
        x += 48 + len(rotulo) * 7.2
    return "".join(p)


def _ocupado(segmentos):
    """Tramos de CPU ocupada a partir de las filas: (ini, fin, quien)."""
    return sorted(segmentos)


def _gantt(titulo, subtitulo, aria, filas, cpus, total, nota,
           eje_max=800, paso=100, bloqueo=False):
    """Gantt comun: filas de tareas, filas de CPU, eje en ms, leyenda y nota.

    filas: [(etiqueta, [(tipo, ini_ms, fin_ms), ...])]
    cpus:  [(etiqueta, [(ini_ms, fin_ms, rotulo), ...])]
    """
    escala = (X1 - X0) / eje_max

    def xs(ms):
        return X0 + ms * escala

    alto_fila, alto_barra = 42, 26
    arriba = 112
    y_cpu = arriba + len(filas) * alto_fila + 14
    y_eje = y_cpu + len(cpus) * alto_fila + 8
    y_ley = y_eje + 64
    alto = y_ley + (60 if nota else 30)

    p = [marco(ANCHO, alto, aria)]
    p.append(texto(ANCHO / 2, 42, titulo, TEXTO, 20, peso="600"))
    p.append(texto(ANCHO / 2, 70, subtitulo, SUAVE, 14))

    # Rejilla vertical de fondo.
    for ms in range(0, eje_max + 1, paso):
        p.append(_linea(xs(ms), arriba - 6, xs(ms), y_eje, LINEA, 0.6, "2 6"))

    for i, (etiqueta, segmentos) in enumerate(filas):
        y = arriba + i * alto_fila
        p.append(texto(X0 - 16, y + alto_barra / 2 + 5, etiqueta, TEXTO, 14,
                       anclaje="end"))
        for tipo, ini, fin in segmentos:
            p.append(_segmento(tipo, xs(ini), y, (fin - ini) * escala, alto_barra))

    p.append(_linea(X0 - 170, y_cpu - 8, X1, y_cpu - 8, LINEA, 1))
    for j, (etiqueta, ocupados) in enumerate(cpus):
        y = y_cpu + j * alto_fila
        p.append(texto(X0 - 16, y + alto_barra / 2 + 5, etiqueta, ACENTO, 14,
                       anclaje="end", peso="600"))
        cursor = 0
        for ini, fin, rotulo in _ocupado(ocupados) + [(total, total, None)]:
            if ini > cursor:
                w = (ini - cursor) * escala
                p.append(_rect(xs(cursor), y + 3, w, alto_barra - 6, "none",
                               SUAVE, 1.4, "3 3"))
                if w > 90:
                    p.append(texto(xs(cursor) + w / 2, y + alto_barra / 2 + 5,
                                   "inactiva", SUAVE, 13))
            if rotulo is not None:
                color = ROJO if rotulo.startswith("c3") and bloqueo else ACENTO
                w = (fin - ini) * escala
                p.append(_rect(xs(ini), y, w, alto_barra, color))
                if w >= 18:
                    p.append(texto(xs(ini) + w / 2, y + alto_barra / 2 + 5,
                                   rotulo, FONDO, 13, peso="600"))
            cursor = max(cursor, fin)

    # Eje de tiempo en ms.
    p.append(_linea(X0, y_eje, X1, y_eje, SUAVE, 1.4))
    for ms in range(0, eje_max + 1, paso):
        p.append(_linea(xs(ms), y_eje, xs(ms), y_eje + 6, SUAVE, 1.4))
        p.append(texto(xs(ms), y_eje + 24, str(ms), SUAVE, 13))
    p.append(texto(X0 - 16, y_eje + 24, "tiempo (ms)", SUAVE, 13, anclaje="end"))

    # Marca del total.
    xt = xs(total)
    p.append(_linea(xt, arriba - 16, xt, y_eje, AMBAR, 2, "6 4"))
    a_la_derecha = xt + 120 < ANCHO - 16
    p.append(texto(xt + (8 if a_la_derecha else -8), arriba - 6, f"total {total} ms",
                   AMBAR, 14, anclaje="start" if a_la_derecha else "end", peso="600"))

    p.append(_leyenda(y_ley, bloqueo))
    if nota:
        p.append(texto(ANCHO / 2, y_ley + 36, nota, TEXTO, 14))
    p.append(cierre())
    return "".join(p)


def _tarea(inicio_ejecuta, espera_desde=None, lista=None, segunda=None):
    """Tramos de una tarea: ejecuta 20, espera 200, (lista), ejecuta 20."""
    e1 = (inicio_ejecuta, inicio_ejecuta + EJECUTA_MS)
    w0 = e1[1] if espera_desde is None else espera_desde
    w1 = w0 + ESPERA_MS
    s0 = w1 if segunda is None else segunda
    tramos = [("ejecuta", *e1), ("espera", w0, w1)]
    if s0 > w1:
        tramos.append(("lista", w1, s0))
    tramos.append(("ejecuta", s0, s0 + EJECUTA_MS))
    if lista:
        tramos.insert(0, ("lista", *lista))
    return tramos


SUBTITULO = "las mismas 3 tareas: ejecuta 20 ms, espera 200 ms la red, ejecuta 20 ms"


def _secuenciales(prefijo):
    filas, cpu = [], []
    for i in range(3):
        t0 = i * (2 * EJECUTA_MS + ESPERA_MS)
        filas.append((f"{prefijo} {i + 1}", _tarea(t0)))
        cpu += [(t0, t0 + EJECUTA_MS, str(i + 1)),
                (t0 + EJECUTA_MS + ESPERA_MS, t0 + 2 * EJECUTA_MS + ESPERA_MS, str(i + 1))]
    return filas, cpu


def _intercaladas(prefijo):
    """Tres tareas que se turnan una CPU: el patron de hilos y de asyncio."""
    filas, cpu = [], []
    for i in range(3):
        t0 = i * EJECUTA_MS
        lista = (0, t0) if t0 else None
        filas.append((f"{prefijo} {i + 1}", _tarea(t0, lista=lista)))
        s0 = t0 + EJECUTA_MS + ESPERA_MS
        cpu += [(t0, t0 + EJECUTA_MS, str(i + 1)), (s0, s0 + EJECUTA_MS, str(i + 1))]
    return filas, cpu


def cmp_gantt_secuencial():
    filas, cpu = _secuenciales("tarea")
    aria = (
        "Diagrama de Gantt con eje de tiempo en milisegundos de 0 a 800. Tres "
        "tareas en serie: cada una ejecuta 20 ms, espera 200 ms la red y "
        "ejecuta 20 ms; la tarea 2 empieza cuando termina la 1, en 240 ms, y "
        "la 3 en 480 ms. El total es 720 ms. La fila de CPU esta ocupada solo "
        "en seis tramos de 20 ms e inactiva durante las tres esperas, 600 de "
        "los 720 ms."
    )
    return _gantt(
        "Secuencial: una tarea termina antes de que empiece la siguiente",
        SUBTITULO, aria, filas, [("CPU", cpu)], 720,
        "La CPU trabaja 120 ms de 720: el resto del tiempo nadie la usa.",
    )


def cmp_gantt_hilos():
    filas, cpu = _intercaladas("hilo")
    aria = (
        "Diagrama de Gantt con eje de tiempo en milisegundos de 0 a 800. Las "
        "mismas tres tareas, una por hilo. Las tres esperas de 200 ms se "
        "solapan. La ejecucion se turna por el GIL: el hilo 2 queda listo sin "
        "turno de 0 a 20 ms y el hilo 3 de 0 a 40 ms, porque solo un hilo "
        "ejecuta Python a la vez. La fila de CPU nunca tiene dos tramos al "
        "mismo tiempo. Total 280 ms contra 720 del secuencial."
    )
    return _gantt(
        "Hilos: las esperas se solapan, la ejecución se turna por el GIL",
        SUBTITULO, aria, filas, [("CPU (GIL)", cpu)], 280,
        "280 ms contra 720: se gana porque se espera a la vez, no porque se calcule a la vez.",
    )


def cmp_gantt_asyncio():
    filas, cpu = _intercaladas("corrutina")
    aria = (
        "Diagrama de Gantt con eje de tiempo en milisegundos de 0 a 800. Las "
        "mismas tres tareas como corrutinas en un solo hilo, lanzadas juntas "
        "con gather. Cada corrutina ejecuta 20 ms hasta su await, cede el "
        "control y el loop arranca la siguiente; las tres esperas de 200 ms "
        "se solapan. La fila de CPU muestra tramos cortos intercalados. "
        "Total 280 ms, igual que con hilos y sin ningun hilo extra."
    )
    return _gantt(
        "asyncio con gather: un hilo, cada await cede el turno",
        SUBTITULO, aria, filas, [("CPU (1 hilo)", cpu)], 280,
        "Mismo total que con hilos: 280 ms. La diferencia es quién decide el turno: el await, no el sistema.",
    )


def cmp_gantt_await_en_serie():
    filas, cpu = _secuenciales("corrutina")
    aria = (
        "Diagrama de Gantt con eje de tiempo en milisegundos de 0 a 800. El "
        "anti patron: tres corrutinas con await una tras otra, sin gather. "
        "Cada await espera su respuesta completa antes de lanzar la siguiente "
        "llamada, asi que el dibujo es identico al secuencial: total 720 ms y "
        "la CPU inactiva durante las tres esperas de 200 ms."
    )
    return _gantt(
        "await uno tras otro: async en el código, secuencial en el reloj",
        SUBTITULO, aria, filas, [("CPU (1 hilo)", cpu)], 720,
        "Mientras corrutina 1 espera, nadie más está lanzado: el loop no tiene a quién dar el turno.",
    )


def cmp_gantt_procesos():
    # Tres procesos sobre dos CPU: el tercero espera una CPU libre.
    filas = [
        ("proceso 1", _tarea(0)),
        ("proceso 2", _tarea(0)),
        ("proceso 3", _tarea(20, lista=(0, 20), segunda=240)),
    ]
    cpu1 = [(0, 20, "1"), (20, 40, "3"), (220, 240, "1"), (240, 260, "3")]
    cpu2 = [(0, 20, "2"), (220, 240, "2")]
    aria = (
        "Diagrama de Gantt con eje de tiempo en milisegundos de 0 a 800. Las "
        "mismas tres tareas en tres procesos sobre dos CPU. Los procesos 1 y "
        "2 ejecutan al mismo tiempo, uno en la CPU 1 y otro en la CPU 2; el "
        "proceso 3 queda listo sin CPU hasta los 20 ms. Hay dos filas de CPU "
        "con tramos simultaneos. Total 260 ms: con esta carga casi todo es "
        "espera y la ganancia sobre hilos es de solo 20 ms."
    )
    return _gantt(
        "Procesos: dos CPU ejecutan al mismo tiempo",
        SUBTITULO, aria, filas, [("CPU 1", cpu1), ("CPU 2", cpu2)], 260,
        "260 ms contra 280 de hilos: con tareas que esperan, el paralelismo casi no rinde.",
    )


def cmp_matriz_2x2():
    ancho, alto = 1080, 640
    aria = (
        "Matriz de dos por dos. Columnas: no paralelo, una sola CPU ejecuta "
        "a la vez; paralelo, varias CPU ejecutan en el mismo instante. Filas: "
        "no concurrente, una tarea en curso a la vez; concurrente, varias "
        "tareas en curso a la vez. Secuencial cae en no concurrente y no "
        "paralelo. Hilos de Python con GIL y asyncio caen en concurrente y no "
        "paralelo. Procesos caen en concurrente y paralelo. La celda paralelo "
        "sin concurrencia es una sola operacion repartida dentro de una "
        "libreria compilada. Asincrono no es una celda: es como se escribe la "
        "espera, con await."
    )
    p = [marco(ancho, alto, aria)]
    p.append(texto(ancho / 2, 42, "Concurrente y paralelo son dos preguntas distintas",
                   TEXTO, 20, peso="600"))
    x0, y0, w, h = 300, 130, 360, 200
    p.append(texto(x0 + w, 88, "¿varias CPU ejecutan en el mismo instante?", SUAVE, 14))
    p.append(texto(x0 + w / 2, 116, "no: no paralelo", TEXTO, 15, peso="600"))
    p.append(texto(x0 + w * 1.5, 116, "sí: paralelo", TEXTO, 15, peso="600"))
    p.append(texto(150, y0 - 18, "¿varias tareas en curso", SUAVE, 14))
    p.append(texto(150, y0, "a la vez?", SUAVE, 14))
    p.append(texto(280, y0 + h / 2 + 5, "no: no concurrente", TEXTO, 15,
                   anclaje="end", peso="600"))
    p.append(texto(280, y0 + h * 1.5 + 5, "sí: concurrente", TEXTO, 15,
                   anclaje="end", peso="600"))

    celdas = (
        (0, 0, SUAVE, "secuencial", ["un for con una llamada", "tras otra"]),
        (1, 0, VIOLETA, "una operación repartida",
         ["dentro de una librería compilada", "(p. ej. NumPy multiplicando",
          "matrices grandes); rara de escribir"]),
        (0, 1, CIAN, "hilos  ·  asyncio",
         ["varias esperas en curso,", "pero el GIL deja ejecutar", "Python a uno a la vez"]),
        (1, 1, ACENTO, "procesos",
         ["un intérprete y un GIL", "por proceso: cálculo", "simultáneo en varias CPU"]),
    )
    for col, fila, color, nombre, lineas in celdas:
        x, y = x0 + col * w, y0 + fila * h
        p.append(caja(x + 6, y + 6, w - 12, h - 12, PANEL, color))
        p.append(texto(x + w / 2, y + 52, nombre, color, 20, peso="600"))
        for k, linea in enumerate(lineas):
            p.append(texto(x + w / 2, y + 90 + k * 24, linea, TEXTO, 14))

    p.append(caja(x0, y0 + 2 * h + 22, 2 * w, 64, TINTE, AMBAR, radio=8))
    p.append(texto(x0 + w, y0 + 2 * h + 48,
                   "Asíncrono no es una celda: es cómo se escribe la espera (await).",
                   AMBAR, 15, peso="600"))
    p.append(texto(x0 + w, y0 + 2 * h + 72,
                   "asyncio lo usa para ser concurrente en un solo hilo.", TEXTO, 14))
    p.append(cierre())
    return "".join(p)


def cmp_event_loop():
    ancho = ANCHO
    eje_max, paso = 300, 50
    escala = (X1 - X0) / eje_max

    def xs(ms):
        return X0 + ms * escala

    aria = (
        "Traza del event loop con tres corrutinas, eje de 0 a 300 ms. La "
        "corrutina 1 corre de 0 a 20 ms y cede en su await; el loop arranca la "
        "2, que cede en 40 ms, y la 3, que cede en 60 ms. De 60 a 220 ms nadie "
        "esta listo y el loop espera eventos del sistema operativo sin gastar "
        "CPU. En 220 ms llega la respuesta de la 1 y el loop la reanuda; en "
        "240 y 260 ms reanuda la 2 y la 3. Total 280 ms."
    )
    alto = 620
    p = [marco(ancho, alto, aria)]
    p.append(texto(ancho / 2, 42, "El event loop: quién corre, cuándo cede y cuándo vuelve",
                   TEXTO, 20, peso="600"))
    p.append(texto(ancho / 2, 70, SUBTITULO, SUAVE, 14))
    arriba, alto_fila, barra = 120, 60, 26
    for ms in range(0, eje_max + 1, paso):
        p.append(_linea(xs(ms), arriba - 20, xs(ms), 388, LINEA, 0.6, "2 6"))
    for i in range(3):
        y = arriba + i * alto_fila
        t0 = i * EJECUTA_MS
        p.append(texto(X0 - 16, y + barra / 2 + 5, f"corrutina {i + 1}", TEXTO, 14,
                       anclaje="end"))
        for tipo, ini, fin in _tarea(t0, lista=(0, t0) if t0 else None):
            p.append(_segmento(tipo, xs(ini), y, (fin - ini) * escala, barra))
        # cede: bajo el fin del primer tramo; reanuda: sobre el inicio del segundo.
        xc, xr = xs(t0 + EJECUTA_MS), xs(t0 + EJECUTA_MS + ESPERA_MS)
        p.append(flecha(xc, y + barra + 2, xc, y + barra + 20, AMBAR, 2))
        p.append(texto(xc + 6, y + barra + 20, "cede", AMBAR, 13, anclaje="start"))
        p.append(flecha(xr, y + barra + 20, xr, y + barra + 3, ACENTO, 2))
        p.append(texto(xr - 6, y + barra + 20, "reanuda", ACENTO, 13, anclaje="end"))

    # Fila del loop.
    y = arriba + 3 * alto_fila + 10
    p.append(_linea(X0 - 170, y - 12, X1, y - 12, LINEA, 1))
    p.append(texto(X0 - 16, y + barra / 2 + 5, "event loop", ACENTO, 14,
                   anclaje="end", peso="600"))
    for i in range(3):
        for ini in (i * EJECUTA_MS, i * EJECUTA_MS + EJECUTA_MS + ESPERA_MS):
            p.append(_rect(xs(ini), y, EJECUTA_MS * escala, barra, ACENTO))
            p.append(texto(xs(ini) + EJECUTA_MS * escala / 2, y + barra / 2 + 5,
                           f"c{i + 1}", FONDO, 13, peso="600"))
    w = (220 - 60) * escala
    p.append(_rect(xs(60), y + 3, w, barra - 6, "none", SUAVE, 1.4, "3 3"))
    p.append(texto(xs(60) + w / 2, y + barra / 2 + 5,
                   "nadie listo: espera eventos del sistema, sin gastar CPU", SUAVE, 13))

    y_eje = 388
    p.append(_linea(X0, y_eje, X1, y_eje, SUAVE, 1.4))
    for ms in range(0, eje_max + 1, paso):
        p.append(_linea(xs(ms), y_eje, xs(ms), y_eje + 6, SUAVE, 1.4))
        p.append(texto(xs(ms), y_eje + 24, str(ms), SUAVE, 13))
    p.append(texto(X0 - 16, y_eje + 24, "tiempo (ms)", SUAVE, 13, anclaje="end"))

    pasos = (
        "1. 0 ms: el loop corre c1 hasta su await; c1 cede.",
        "2. 20 y 40 ms: corre c2, cede; corre c3, cede.",
        "3. 60 a 220 ms: las tres esperan la red; el loop duerme.",
        "4. 220 ms: llega la respuesta de c1; el loop la reanuda.",
        "5. 240 y 260 ms: reanuda c2 y c3.",
        "6. 280 ms: las tres terminaron; gather regresa.",
    )
    for k, linea in enumerate(pasos):
        col, fila = divmod(k, 3)
        p.append(texto(60 + col * 500, 460 + fila * 30, linea, TEXTO, 14, anclaje="start"))
    p.append(texto(ancho / 2, 572,
                   "Una corrutina solo suelta el turno en un await: entre dos await nadie más corre.",
                   AMBAR, 15, peso="600"))
    p.append(cierre())
    return "".join(p)


def cmp_bloqueo_del_loop():
    filas = [
        ("corrutina 1", [("ejecuta", 0, 20), ("espera", 20, 220),
                         ("lista", 220, 2040), ("ejecuta", 2040, 2060)]),
        ("corrutina 2", [("lista", 0, 20), ("ejecuta", 20, 40), ("espera", 40, 240),
                         ("lista", 240, 2060), ("ejecuta", 2060, 2080)]),
        ("corrutina 3", [("lista", 0, 40), ("bloquea", 40, 2040)]),
    ]
    cpu = [(0, 20, "c1"), (20, 40, "c2"), (40, 2040, "c3 calcula: el loop no atiende a nadie más"),
           (2040, 2060, "c1"), (2060, 2080, "c2")]
    aria = (
        "Diagrama de Gantt con eje de tiempo en milisegundos de 0 a 2200. Dos "
        "corrutinas lanzan una peticion y esperan 200 ms; la corrutina 3 hace "
        "un calculo de 2000 ms dentro del loop sin ningun await. Las "
        "respuestas llegan en 220 y 240 ms, pero las corrutinas 1 y 2 quedan "
        "listas sin turno hasta 2040 y 2060 ms, porque el loop no recupera el "
        "control hasta que el calculo termina. Total 2080 ms en vez de 240."
    )
    return _gantt(
        "Un cálculo de 2 s dentro del loop detiene a todas las demás",
        "dos peticiones de 200 ms y un cálculo de 2000 ms sin await, en el mismo loop",
        aria, filas, [("event loop", cpu)], 2080,
        "Las respuestas llegaron a los 220 y 240 ms; nadie las atendió hasta que el cálculo soltó el loop.",
        eje_max=2200, paso=200, bloqueo=True,
    )


def cmp_vectorizar():
    ancho, alto = 1080, 600
    aria = (
        "Dos paneles. Arriba, un bucle de Python sobre ocho numeros: por cada "
        "elemento el interprete lee el objeto, revisa su tipo, busca la "
        "operacion y crea un objeto nuevo con el resultado; ocho vueltas, "
        "ocho veces ese trabajo. Abajo, NumPy: los ocho numeros float64 "
        "contiguos en un solo bloque de memoria y una sola llamada desde "
        "Python; un bucle compilado recorre el bloque sin pasar por el "
        "interprete, y como factor secundario las instrucciones SIMD procesan "
        "varios elementos por instruccion."
    )
    p = [marco(ancho, alto, aria)]
    p.append(texto(ancho / 2, 42, "Vectorizar: sacar el bucle del intérprete",
                   TEXTO, 20, peso="600"))

    # Panel del bucle.
    p.append(caja(30, 66, ancho - 60, 236, PANEL, AMBAR))
    p.append(teclado(60, 100, "for x in datos: total += x * x", AMBAR, 16, anclaje="start"))
    p.append(texto(ancho - 60, 100, "Python, elemento por elemento", AMBAR, 15,
                   anclaje="end", peso="600"))
    cw, gap = 92, 22
    x0 = (ancho - 8 * cw - 7 * gap) / 2
    for k in range(8):
        x = x0 + k * (cw + gap)
        p.append(caja(x, 124, cw, 40, FONDO, LINEA, radio=6))
        p.append(teclado(x + cw / 2, 150, f"{k + 1}.0", TEXTO, 14))
        p.append(flecha(x + cw / 2, 166, x + cw / 2, 196, AMBAR, 1.6))
        p.append(caja(x, 200, cw, 40, TINTE, AMBAR, radio=6))
        p.append(texto(x + cw / 2, 225, "intérprete", AMBAR, 13))
    p.append(texto(ancho / 2, 270,
                   "en cada vuelta: leer el objeto, revisar su tipo, buscar la operación, crear un objeto nuevo",
                   TEXTO, 14))
    p.append(texto(ancho / 2, 292, "8 elementos = 8 veces ese trabajo de más", SUAVE, 13))

    # Panel de NumPy.
    p.append(caja(30, 322, ancho - 60, 248, PANEL, ACENTO))
    p.append(teclado(60, 356, "total = (datos * datos).sum()", ACENTO, 16, anclaje="start"))
    p.append(texto(ancho - 60, 356, "NumPy, el arreglo en bloque", ACENTO, 15,
                   anclaje="end", peso="600"))
    bw = 100
    xb = (ancho - 8 * bw) / 2
    p.append(caja(xb - 6, 374, 8 * bw + 12, 52, TINTE, ACENTO, radio=8))
    for k in range(8):
        x = xb + k * bw
        if k:
            p.append(_linea(x, 380, x, 420, LINEA, 1))
        p.append(teclado(x + bw / 2, 406, f"{k + 1}.0", TEXTO, 14))
    p.append(texto(ancho / 2, 446, "8 float64 contiguos en memoria: sin objetos de Python por elemento",
                   SUAVE, 13))
    p.append(flecha(ancho / 2, 452, ancho / 2, 478, ACENTO, 2))
    p.append(caja(220, 482, 640, 44, FONDO, ACENTO, radio=8))
    p.append(texto(ancho / 2, 510, "una llamada: un bucle compilado (C) recorre todo el bloque",
                   ACENTO, 15, peso="600"))
    p.append(texto(ancho / 2, 552,
                   "SIMD procesa varios elementos por instrucción: ayuda, pero es factor secundario",
                   SUAVE, 13))
    p.append(cierre())
    return "".join(p)


def cmp_amdahl():
    ancho, alto = 1080, 640
    aria = (
        "Grafica de la ley de Amdahl. Eje horizontal: P, numero de procesos o "
        "CPU, de 1 a 16. Eje vertical: aceleracion, tiempo con 1 entre tiempo "
        "con P, de 0 a 16. Una diagonal punteada marca la aceleracion ideal "
        "igual a P. Tres curvas teoricas 1 entre S mas 1 menos S sobre P: con "
        "S igual a 0.1 llega a 6.4 en P 16 y su techo es 10; con S 0.25 llega "
        "a 3.4 y su techo es 4; con S 0.5 llega a 1.9 y su techo es 2. Solo "
        "aplica a trabajo que calcula."
    )
    p = [marco(ancho, alto, aria)]
    p.append(texto(ancho / 2, 42, "Ley de Amdahl: la parte serial pone el techo",
                   TEXTO, 20, peso="600"))
    p.append(teclado(ancho / 2, 72, "aceleración = 1 / (S + (1 − S) / P)", ACENTO, 16))
    gx0, gx1, gy0, gy1 = 130, 860, 540, 100   # gy0 abajo, gy1 arriba
    pmax, amax = 16, 16

    def gx(pp):
        return gx0 + (pp - 1) / (pmax - 1) * (gx1 - gx0)

    def gy(a):
        return gy0 - a / amax * (gy0 - gy1)

    for a in range(0, amax + 1, 2):
        p.append(_linea(gx0, gy(a), gx1, gy(a), LINEA, 0.6, "2 6"))
        p.append(texto(gx0 - 12, gy(a) + 5, str(a), SUAVE, 13, anclaje="end"))
    for pp in (1, 2, 4, 6, 8, 10, 12, 14, 16):
        p.append(_linea(gx(pp), gy0, gx(pp), gy0 + 6, SUAVE, 1.4))
        p.append(texto(gx(pp), gy0 + 24, str(pp), SUAVE, 13))
    p.append(_linea(gx0, gy0, gx1, gy0, SUAVE, 1.4))
    p.append(_linea(gx0, gy0, gx0, gy1, SUAVE, 1.4))
    p.append(texto((gx0 + gx1) / 2, gy0 + 52, "P: procesos (una CPU cada uno)", TEXTO, 14))
    p.append(f'<text x="58" y="{(gy0 + gy1) / 2}" fill="{TEXTO}" font-family="system-ui, sans-serif" '
             f'font-size="14" text-anchor="middle" transform="rotate(-90 58 {(gy0 + gy1) / 2})">'
             f'aceleración (veces más rápido)</text>')

    # Ideal.
    p.append(f'<line x1="{gx(1):.1f}" y1="{gy(1):.1f}" x2="{gx(16):.1f}" y2="{gy(16):.1f}" '
             f'stroke="{SUAVE}" stroke-width="1.6" stroke-dasharray="6 5"/>')
    p.append(texto(gx(11.6) - 8, gy(12.6), "ideal: P", SUAVE, 13, anclaje="end"))

    for s, color in ((0.1, ACENTO), (0.25, CIAN), (0.5, AMBAR)):
        pts = []
        for k in range(0, 151):
            pp = 1 + k * (pmax - 1) / 150
            pts.append(f"{gx(pp):.1f},{gy(1 / (s + (1 - s) / pp)):.1f}")
        p.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" '
                 f'stroke-width="3"/>')
        techo = 1 / s
        p.append(_linea(gx0, gy(techo), gx1, gy(techo), color, 1, "3 5"))
        fin = 1 / (s + (1 - s) / pmax)
        p.append(f'<circle cx="{gx(16):.1f}" cy="{gy(fin):.1f}" r="5" fill="{color}"/>')
        p.append(texto(gx1 + 16, gy(fin) + 5, f"S = {s}: {fin:.1f}× en P = 16",
                       color, 14, anclaje="start", peso="600"))
        p.append(texto(gx0 + 10, gy(techo) - 6, f"techo {techo:g}×", color, 13,
                       anclaje="start"))

    p.append(texto(ancho / 2, 620,
                   "S = fracción serial del programa. Solo aplica a trabajo que calcula: esperar no se acelera con CPU.",
                   SUAVE, 13))
    p.append(cierre())
    return "".join(p)


def cmp_arbol_decision():
    ancho, alto = 1080, 640
    aria = (
        "Arbol de decision. Primera pregunta: el tiempo se va en esperar red "
        "o disco, o en calcular; se decide midiendo. Si espera: hay "
        "libreria async como httpx, entonces asyncio con gather y un "
        "Semaphore; si no, hilos con ThreadPoolExecutor. Si calcula: opera "
        "sobre arreglos o columnas de numeros, entonces vectoriza con NumPy o "
        "Polars; si no, cada pedazo es independiente y tarda mas que arrancar "
        "un proceso, entonces procesos con ProcessPoolExecutor hasta el numero "
        "de CPU; si no, secuencial y mejora el algoritmo."
    )
    p = [marco(ancho, alto, aria)]
    p.append(texto(ancho / 2, 42, "Elegir la estrategia: primero mide dónde se va el tiempo",
                   TEXTO, 20, peso="600"))

    def pregunta(cx, cy, w, l1, l2=None):
        h = 64 if l2 else 46
        out = [caja(cx - w / 2, cy - h / 2, w, h, PANEL, TEXTO, radio=10)]
        if l2:
            out.append(texto(cx, cy - 4, l1, TEXTO, 15, peso="600"))
            out.append(texto(cx, cy + 18, l2, SUAVE, 13))
        else:
            out.append(texto(cx, cy + 6, l1, TEXTO, 15, peso="600"))
        return "".join(out)

    def hoja(cx, cy, color, nombre, l1, l2):
        w, h = 200, 92
        return "".join([
            caja(cx - w / 2, cy - h / 2, w, h, TINTE, color, radio=10),
            texto(cx, cy - 16, nombre, color, 17, peso="600"),
            teclado(cx, cy + 8, l1, TEXTO, 13, peso="normal"),
            texto(cx, cy + 30, l2, SUAVE, 13),
        ])

    def rama(x1, y1, x2, y2, rotulo, color=SUAVE):
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        return flecha(x1, y1, x2, y2, LINEA, 2) + texto(
            mx + (10 if x2 >= x1 else -10), my - 4, rotulo, color, 14,
            anclaje="start" if x2 >= x1 else "end", peso="600")

    p.append(pregunta(540, 110, 520, "¿El tiempo se va en esperar o en calcular?",
                      "mídelo: tiempo de reloj contra tiempo de CPU"))
    p.append(rama(420, 142, 270, 214, "espera (red, disco)", CIAN))
    p.append(rama(660, 142, 810, 214, "calcula", AMBAR))

    p.append(pregunta(270, 244, 400, "¿La librería tiene versión async?",
                      "httpx, asyncpg, aiofiles…"))
    p.append(rama(200, 276, 150, 400, "sí", CIAN))
    p.append(rama(340, 276, 390, 400, "no", CIAN))
    p.append(hoja(150, 450, CIAN, "asyncio", "gather + Semaphore", "miles de esperas, 1 hilo"))
    p.append(hoja(390, 450, CIAN, "hilos", "ThreadPoolExecutor", "decenas o cientos"))

    p.append(pregunta(810, 244, 400, "¿Opera sobre arreglos de números?",
                      "columnas, vectores, matrices"))
    p.append(rama(890, 276, 940, 400, "sí", AMBAR))
    p.append(rama(730, 276, 680, 334, "no", AMBAR))
    p.append(hoja(940, 450, AMBAR, "vectoriza", "NumPy, Polars", "el bucle sale de Python"))
    p.append(pregunta(660, 366, 300, "¿Pedazos independientes", "y más largos que arrancar un proceso?"))
    p.append(flecha(700, 398, 700, 520, LINEA, 2))
    p.append(texto(712, 470, "sí", AMBAR, 14, anclaje="start", peso="600"))
    p.append(hoja(700, 566, ACENTO, "procesos", "ProcessPoolExecutor", "hasta el número de CPU"))
    p.append(flecha(610, 398, 500, 520, LINEA, 2))
    p.append(texto(530, 470, "no", AMBAR, 14, anclaje="end", peso="600"))
    p.append(hoja(460, 566, SUAVE, "secuencial", "un for", "mejora el algoritmo"))
    p.append(texto(150, 548, "¿esperas y cálculo juntos?", SUAVE, 13))
    p.append(texto(150, 570, "asyncio para la red,", SUAVE, 13))
    p.append(texto(150, 592, "procesos para el cálculo", SUAVE, 13))
    p.append(cierre())
    return "".join(p)


DIAGRAMAS = {
    "cmp-gantt-secuencial": cmp_gantt_secuencial,
    "cmp-gantt-hilos": cmp_gantt_hilos,
    "cmp-gantt-asyncio": cmp_gantt_asyncio,
    "cmp-gantt-await-en-serie": cmp_gantt_await_en_serie,
    "cmp-gantt-procesos": cmp_gantt_procesos,
    "cmp-matriz-2x2": cmp_matriz_2x2,
    "cmp-event-loop": cmp_event_loop,
    "cmp-bloqueo-del-loop": cmp_bloqueo_del_loop,
    "cmp-vectorizar": cmp_vectorizar,
    "cmp-amdahl": cmp_amdahl,
    "cmp-arbol-decision": cmp_arbol_decision,
}


def escribir(nombre):
    ASSETS.mkdir(parents=True, exist_ok=True)
    destino = ASSETS / f"{nombre}.svg"
    destino.write_text(DIAGRAMAS[nombre](), encoding="utf-8")
    return destino


def main(argv):
    for nombre in argv[1:] or list(DIAGRAMAS):
        if nombre not in DIAGRAMAS:
            raise SystemExit(f"diagrama desconocido: {nombre}")
        destino = escribir(nombre)
        print(f"{destino.name}  ({destino.stat().st_size / 1000:.1f} KB)")


if __name__ == "__main__":
    main(sys.argv)
