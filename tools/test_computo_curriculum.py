"""Guarda de la seccion 10.2 Cómputo y concurrencia (unidad 10).

Lo que protege: el notebook es el que producen las paginas, las celdas citadas
existen y van en orden, ninguna celda usa `asyncio.run(` (en un notebook
truena: ya hay un event loop), las funciones que viajan a un proceso se
importan de trabajo_computo.py (una funcion de celda vive en `__main__` y el
hijo no la encuentra), las paginas no tienen marcadores ni analogias, y las
celdas baratas de la pagina 1 corren contra el servidor real.

No ejecuta las celdas de 20 a 500 llamadas ni las de procesos: el profesor
pidio que la suite no devore nucleos.
"""
import ast
import builtins
import importlib.util
import json
import re
import sys
import threading
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SECCION = RAIZ / "course/10_apis/2_computo_y_concurrencia"
PLANTILLA = RAIZ / "codigo/10_apis"
NOTEBOOK = PLANTILLA / "computo.ipynb"
TRABAJO = PLANTILLA / "trabajo_computo.py"

PAGINAS = sorted(p.name for p in SECCION.glob("[0-9]_*.md"))
CON_CELDAS = [n for n in PAGINAS if n != "0_index.md"]

# Limites de palabra: «como sinónimos» no es «como si».
ANALOGIAS = re.compile(r"\b(imagina\w*|es como|como si|piensa en|restaurante\w*|"
                       r"cocina\w*|mesero\w*)\b", re.I)

# Celdas que mandan a un proceso algo que NO es de trabajo_computo.py a
# proposito: 5.1 muestra que una lambda no viaja.
FALLAN_A_PROPOSITO = {"5.1"}
BUILTINS = set(dir(builtins))


def _modulo(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _gen():
    return _modulo("gen_notebook_computo", RAIZ / "tools/gen_notebook_computo.py")


def _cuerpo(nombre):
    return (SECCION / nombre).read_text(encoding="utf-8").split("---", 2)[2]


def _celdas_de(nombre):
    """[(celda, codigo)] de una pagina, en orden, sacadas con el generador."""
    return [(p[2], p[1]) for p in _gen()._partes(SECCION / nombre) if p[0] == "code"]


def _todas():
    return [c for n in CON_CELDAS for c in _celdas_de(n)]


# ── el notebook ───────────────────────────────────────────────────────────

def test_el_notebook_es_el_que_produce_su_generador():
    assert NOTEBOOK.read_text(encoding="utf-8") == _gen().notebook(), (
        "computo.ipynb no coincide con tools/gen_notebook_computo.py: no lo edites "
        "a mano, cambia la pagina o CELDAS y vuelve a correr el generador")


def test_el_notebook_no_trae_salidas():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    for c in nb["cells"]:
        if c["cell_type"] == "code":
            assert c["outputs"] == [] and c["execution_count"] is None


def test_cada_haz_de_las_paginas_esta_en_CELDAS_y_en_orden():
    vistas = []
    for nombre in PAGINAS:
        vistas += re.findall(r"^\*\*Haz \(celda (\d+\.\d+)\):\*\*", _cuerpo(nombre), re.M)
    assert vistas == [c for c, _ in _gen().CELDAS]


@pytest.mark.parametrize("nombre", CON_CELDAS)
def test_numeracion_consecutiva_y_de_su_pagina(nombre):
    pagina = nombre[0]
    numeros = [c for c, _ in _celdas_de(nombre)]
    assert numeros == [f"{pagina}.{k}" for k in range(1, len(numeros) + 1)], (
        f"{nombre}: celdas {numeros}; deben ser {pagina}.1, {pagina}.2, … sin huecos")


def test_cada_haz_trae_su_bloque_python():
    haz = [c for n in PAGINAS
           for c in re.findall(r"^\*\*Haz \(celda (\d+\.\d+)\):\*\*", _cuerpo(n), re.M)]
    assert [c for c, _ in _todas()] == haz


def test_ninguna_celda_usa_asyncio_run():
    for celda, codigo in _todas():
        assert "asyncio.run(" not in codigo, (
            f"celda {celda}: asyncio.run truena dentro del notebook; usa await")


def test_las_celdas_compilan_con_await_de_nivel_superior():
    for celda, codigo in _todas():
        compile(codigo, f"<celda {celda}>", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)


# ── lo que viaja a un proceso viene de trabajo_computo.py ─────────────────

def _enviadas_a_procesos(arbol):
    """Nombres que la celda pasa a .map / .submit / run_in_executor."""
    nombres = []
    for nodo in ast.walk(arbol):
        if not (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)):
            continue
        if nodo.func.attr in ("map", "submit") and nodo.args:
            nombres.append(nodo.args[0])
        elif nodo.func.attr == "run_in_executor" and len(nodo.args) > 1:
            nombres.append(nodo.args[1])
    return nombres


def test_lo_que_va_a_un_proceso_se_importa_de_trabajo_computo():
    trabajo = _modulo("trabajo_computo", TRABAJO)
    revisadas = 0
    for celda, codigo in _todas():
        if "ProcessPoolExecutor" not in codigo or celda in FALLAN_A_PROPOSITO:
            continue
        arbol = compile(codigo, celda, "exec",
                        flags=ast.PyCF_ONLY_AST | ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        importadas = {a.asname or a.name for n in ast.walk(arbol)
                      if isinstance(n, ast.ImportFrom) and n.module == "trabajo_computo"
                      for a in n.names}
        definidas = {n.name for n in ast.walk(arbol)
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for arg in _enviadas_a_procesos(arbol):
            assert isinstance(arg, ast.Name), (
                f"celda {celda}: a un proceso sólo viaja una función con nombre de "
                f"trabajo_computo.py, no {ast.unparse(arg)}")
            if arg.id in BUILTINS:
                continue
            assert arg.id not in definidas, (
                f"celda {celda}: {arg.id} se define en la celda; un proceso hijo no la "
                "encuentra. Va en trabajo_computo.py")
            assert arg.id in importadas, (
                f"celda {celda}: {arg.id} debe importarse de trabajo_computo")
            assert callable(getattr(trabajo, arg.id, None)), (
                f"trabajo_computo.py no define {arg.id}")
            revisadas += 1
    assert revisadas >= 2, "ninguna celda manda calcula a un proceso: ¿cambió el parser?"


def test_trabajo_computo_solo_usa_la_libreria_estandar():
    arbol = ast.parse(TRABAJO.read_text(encoding="utf-8"))
    assert not [n for n in ast.walk(arbol) if isinstance(n, (ast.Import, ast.ImportFrom))]
    assert callable(_modulo("trabajo_computo", TRABAJO).calcula)


# ── las paginas ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("nombre", PAGINAS)
def test_sin_marcadores_de_plantilla(nombre):
    assert "{{" not in _cuerpo(nombre), f"{nombre}: quedó un marcador «{{{{»"


@pytest.mark.parametrize("nombre", PAGINAS)
def test_sin_analogias(nombre):
    hallado = ANALOGIAS.search(_cuerpo(nombre))
    assert not hallado, f"{nombre}: «{hallado.group(0)}»"


def test_la_regex_de_analogias_no_dispara_con_como_sinonimos():
    assert not ANALOGIAS.search("se usan como sinónimos")
    assert ANALOGIAS.search("es como si fuera") and ANALOGIAS.search("Imagina un")


def test_el_proyecto_pide_httpx_y_numpy():
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib
    p =tomllib.loads((PLANTILLA / "pyproject.toml").read_text(encoding="utf-8"))
    deps = p["project"]["dependencies"]
    for paquete in ("httpx", "numpy"):
        assert any(re.match(rf"{paquete}\b", d) for d in deps), f"falta {paquete}"
    assert (PLANTILLA / "uv.lock").is_file()


# ── las celdas baratas de la pagina 1, contra el servidor real ────────────

@pytest.fixture
def servidor(monkeypatch):
    monkeypatch.setenv("FDD_SILENCIO", "1")
    mod = _modulo("servidor_computo", PLANTILLA / "servidor.py")
    assert mod.SILENCIO, "FDD_SILENCIO=1 no apaga la radiografía"
    mod.reiniciar()
    srv = mod.Servidor(("127.0.0.1", 0), mod.Ventas)   # la misma clase que __main__
    assert srv.request_queue_size >= 1024
    hilo = threading.Thread(target=srv.serve_forever, daemon=True)
    hilo.start()
    url = f"http://127.0.0.1:{srv.server_address[1]}"
    cable = _modulo("cable", PLANTILLA / "cable.py")
    cable.URL = url
    monkeypatch.setitem(sys.modules, "cable", cable)
    yield url
    srv.shutdown()
    srv.server_close()


def test_celda_1_1_corre_contra_el_servidor(servidor, capsys):
    """1.1: una llamada con ?lento=0.2 y un bucle de 3 M; ~0.6 s, un núcleo."""
    pytest.importorskip("requests", reason="CI instala sólo pytest, pillow y pyyaml")
    codigo = dict(_celdas_de("1_donde_pasa_el_tiempo.md"))["1.1"]
    exec(compile(codigo, "<celda 1.1>", "exec"), {"__name__": "__celda__"})
    salida = capsys.readouterr().out
    assert "llamada ?lento=0.2" in salida and "bucle puro de Python" in salida
    reloj = float(re.search(r"llamada \?lento=0\.2\s+reloj\s+([\d.]+) s", salida).group(1))
    assert reloj >= 0.2, "la llamada debió esperar los 0.2 s que pidió"
