"""Genera codigo/10_apis/computo.ipynb a partir de las paginas de la seccion 10.2.

Mismo contrato que tools/gen_notebook_apis.py: por cada **Haz (celda N.M)**
de las paginas trae, en markdown, la explicacion de la pagina («Qué hace cada
línea», «Deberías ver»), y debajo la celda de codigo. Las paginas son la unica
fuente: si cambia una, se vuelve a correr este script y el notebook la sigue
(tools/test_computo_curriculum.py compara byte a byte).

Las celdas usan `await` de nivel superior (el kernel de Jupyter ya tiene un
event loop corriendo); `asyncio.run(...)` truena ahi y no aparece.

El notebook nunca se edita a mano.
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SECCION = RAIZ / "course/10_apis/2_computo_y_concurrencia"
DESTINO = RAIZ / "codigo/10_apis/computo.ipynb"

PAGINAS = [
    "1_donde_pasa_el_tiempo.md",
    "2_concurrente_paralelo_asincrono.md",
    "3_asyncio_y_el_event_loop.md",
    "4_vectorizar.md",
    "5_elegir_la_estrategia.md",
]

# Titulo de cada celda en el notebook (y la lista que la guarda usa para
# comprobar que toda «celda N.M» citada en una pagina existe y va en orden).
CELDAS = [
    ("1.1", "Dos relojes: una llamada y un bucle"),
    ("1.2", "Veinte llamadas en secuencia"),
    ("2.1", "Las mismas 20 llamadas con 32 hilos"),
    ("2.2", "Una tarea que todavía no termina"),
    ("2.3", "El mismo cálculo con 1, 2 y 4 procesos"),
    ("2.4", "Condición de carrera: contador sin candado"),
    ("2.5", "El mismo conteo con candado"),
    ("3.1", "Una corrutina sin await y con await"),
    ("3.2", "Tres esperas que se solapan"),
    ("3.3", "20, 100 y 500 llamadas con asyncio"),
    ("3.4", "await en serie"),
    ("3.5", "time.sleep dentro de una corrutina"),
    ("3.6", "Un cálculo que no cede el event loop"),
    ("3.7", "El cálculo en un proceso"),
    ("4.1", "Un arreglo de float64"),
    ("4.2", "Bucle contra operación vectorizada"),
    ("4.3", "int64 se desborda"),
    ("4.4", "Ley de Amdahl"),
    ("5.1", "Una lambda a un proceso"),
    ("5.2", "Un pool por llamada contra un pool para todas"),
]
TITULOS = dict(CELDAS)

_HAZ = re.compile(r"^\*\*Haz \(celda (\d+\.\d+)[^)]*\):\*\*\s*(.*)$")


def _plano(texto):
    """Wikilinks de Raya a texto: [[id|rotulo]] -> rotulo, [[id]] -> id."""
    texto = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", texto)
    return re.sub(r"\[\[([^\]]+)\]\]", r"\1", texto)


def _bloque(lineas, i):
    """Si en i empieza un bloque ```, regresa (lenguaje, contenido, fin)."""
    m = re.match(r"^```(\w*)\s*$", lineas[i])
    if not m:
        return None
    j = i + 1
    while j < len(lineas) and not lineas[j].startswith("```"):
        j += 1
    return m.group(1), "\n".join(lineas[i + 1:j]), j + 1


# El arranque (uv sync, el servidor) va en la celda de presentacion del
# notebook y en la terminal; la seccion de la pagina 1 que lo explica se queda
# en la pagina.
SECCIONES_FUERA = ("## Arranque de la sección",)
_FUERA = ("Sigue con", "Regresa al índice", "> [!NOTE]", "> [!WARNING]",
          "> [!TIP]", "> [!CAUTION]", "> **Si sólo recuerdas")


def _partes(pagina):
    """La pagina como lista de ("md", texto) y ("code", codigo, celda)."""
    lineas = pagina.read_text(encoding="utf-8").split("---", 2)[2].splitlines()
    partes, md, dentro, celda, i = [], [], True, None, 0
    while i < len(lineas):
        linea = lineas[i]
        if linea.startswith("## "):
            dentro = not linea.startswith(SECCIONES_FUERA)
            if dentro:
                md.append("#" + linea)
            i += 1
            continue
        if not dentro or linea.startswith("# ") or linea.startswith("**Página "):
            i += 1
            continue
        if linea.startswith("::: "):
            titulo = re.search(r'title="([^"]+)"', linea)
            if linea.startswith("::: figure") and titulo:
                md.append(f"*Figura en la página del curso: «{titulo.group(1)}».*")
            while i + 1 < len(lineas) and lineas[i + 1].strip() != ":::":
                i += 1
            i += 2
            continue
        if linea.startswith(_FUERA):
            i += 1
            continue
        m = _HAZ.match(linea)
        if m:
            celda = m.group(1)
        bloque = _bloque(lineas, i) if linea.startswith("```") else None
        if bloque and bloque[0] == "python" and celda:
            partes.append(("md", "\n".join(md).strip()))
            partes.append(("code", bloque[1], celda))
            md, celda, i = [], None, bloque[2]
            continue
        if bloque:
            md.append(f"```{bloque[0]}\n{bloque[1]}\n```")
            i = bloque[2]
            continue
        md.append(linea)
        i += 1
    if "\n".join(md).strip():
        partes.append(("md", "\n".join(md).strip()))
    return partes


def _encabezado(pagina):
    """Titulo y Meta: de la pagina."""
    cuerpo = pagina.read_text(encoding="utf-8").split("---", 2)[2]
    titulo = re.search(r"^# (.+)$", cuerpo, re.M).group(1)
    meta = re.search(r"^Meta: (.+)$", cuerpo, re.M)
    return titulo, (meta.group(1) if meta else "")


def _md(texto):
    lineas = texto.split("\n")
    return {"cell_type": "markdown", "metadata": {},
            "source": [l + "\n" for l in lineas[:-1]] + [lineas[-1]]}


def _codigo(texto):
    lineas = texto.split("\n")
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": [l + "\n" for l in lineas[:-1]] + [lineas[-1]]}


def notebook():
    celdas = [_md(
        "# Cómputo y concurrencia\n\n"
        "Este notebook es la clase de la sección 10.2 completa: cada celda trae su "
        "explicación arriba y el código listo.\n\n"
        "**Antes de empezar:**\n\n"
        "1. Con internet, antes de la clase: `uv sync` dentro de esta carpeta "
        "(instala `httpx` y `numpy`).\n"
        "2. En una terminal aparte, dentro de esta carpeta, arranca el servidor en "
        "modo silencioso para que no imprima cada petición y no distorsione los "
        "tiempos: `FDD_SILENCIO=1 uv run python servidor.py`. Déjala abierta.\n"
        "3. Elige como kernel el `.venv` de `10_apis`.\n\n"
        "Córrelas **en orden**, una por una (Shift+Enter), y compara con «Deberías ver»: "
        "algunas celdas usan lo que definió la anterior. Las celdas con `await` "
        "funcionan tal cual porque el notebook ya tiene un event loop corriendo; "
        "`asyncio.run(...)` es para archivos `.py`, aquí truena. "
        "La página del curso tiene lo mismo, más las tablas y los diagramas: "
        "https://rayalucaria.org/fdd_o26/apis/computo-y-concurrencia/")]
    vistas = set()
    for nombre in PAGINAS:
        pagina = SECCION / nombre
        titulo, meta = _encabezado(pagina)
        partes = _partes(pagina)
        if not any(p[0] == "code" for p in partes):
            continue
        celdas.append(_md(f"# {titulo}" + (f"\n\nMeta: {_plano(meta)}" if meta else "")))
        for parte in partes:
            if parte[0] == "md" and parte[1]:
                celdas.append(_md(_plano(parte[1])))
            elif parte[0] == "code":
                if parte[2] not in vistas:
                    celdas.append(_md(f"## {parte[2]} · {TITULOS[parte[2]]}"))
                    vistas.add(parte[2])
                celdas.append(_codigo(parte[1]))
    nb = {"cells": celdas, "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 4}
    return json.dumps(nb, ensure_ascii=False, indent=1) + "\n"


if __name__ == "__main__":
    DESTINO.write_text(notebook(), encoding="utf-8")
    print(f"escrito {DESTINO.relative_to(RAIZ)}")
    sys.exit(0)
