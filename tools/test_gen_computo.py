"""Guardas del generador de diagramas de la unidad 10, seccion 10.2 (Computo y concurrencia).

Regenera antes de comparar: correr pytest certifica que lo comiteado coincide
con lo que el generador produce hoy. Editar un SVG a mano falla aqui.

Las convenciones de tamano de la raiz <svg> las cubre
tools/test_svg_tamano_intrinseco.py para todo el curso, y los creditos
tools/test_creditos.py; aqui va lo propio de esta seccion, mas una
comprobacion local de width/height para que el fallo apunte al generador.
"""
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
GENERADOR = RAIZ / "tools/gen_computo.py"
ASSETS = RAIZ / "course/10_apis/_assets"
# Las figuras se buscan en todo el arbol de la unidad: viven en sus secciones.
UNIDAD = RAIZ / "course/10_apis"
SKIN = RAIZ / "skins/fdd-eva.yaml"
GANTT = ("cmp-gantt-secuencial", "cmp-gantt-hilos", "cmp-gantt-asyncio",
         "cmp-gantt-await-en-serie", "cmp-gantt-procesos")


def _cargar():
    assert GENERADOR.is_file(), "falta tools/gen_computo.py"
    spec = importlib.util.spec_from_file_location("gen_computo", GENERADOR)
    modulo = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(RAIZ / "tools"))
    try:
        spec.loader.exec_module(modulo)
    finally:
        sys.path.pop(0)
    return modulo


def _svg(nombre):
    return (ASSETS / f"{nombre}.svg").read_text(encoding="utf-8")


def test_cada_diagrama_declarado_existe_y_lleva_prefijo():
    for nombre in _cargar().DIAGRAMAS:
        assert nombre.startswith("cmp-"), (
            f"{nombre}: los ids de objeto numerado son unicos en TODO el curso; "
            "sin el prefijo 'cmp-' pueden chocar con otra unidad"
        )
        assert (ASSETS / f"{nombre}.svg").is_file(), f"falta {nombre}.svg"


def test_no_sobran_svg_sin_generador():
    declarados = {f"{n}.svg" for n in _cargar().DIAGRAMAS}
    huerfanos = {p.name for p in ASSETS.glob("*.svg")} - declarados
    assert not huerfanos, f"SVG sin entrada en DIAGRAMAS: {sorted(huerfanos)}"


def test_cada_svg_en_disco_es_lo_que_produce_el_generador():
    for nombre, funcion in _cargar().DIAGRAMAS.items():
        assert _svg(nombre) == funcion(), (
            f"{nombre}.svg no coincide con gen_computo.py: no lo edites a mano, "
            "cambia la funcion y vuelve a correr el generador"
        )


def test_los_colores_salen_del_skin():
    """Todo color hexadecimal del SVG esta en skins/fdd-eva.yaml."""
    tokens = yaml.safe_load(SKIN.read_text(encoding="utf-8"))["tokens"]
    paleta = {c.lower() for c in
              set(tokens["color"].values()) | set(tokens["graph"].values())
              if isinstance(c, str)}
    for nombre in _cargar().DIAGRAMAS:
        usados = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b", _svg(nombre))}
        fuera = usados - paleta
        assert not fuera, f"{nombre}.svg usa colores fuera del skin: {sorted(fuera)}"


def test_la_raiz_declara_width_y_height():
    for nombre in _cargar().DIAGRAMAS:
        raiz = re.search(r"<svg\b[^>]*>", _svg(nombre)).group(0)
        assert re.search(r'\swidth="\d+"', raiz) and re.search(r'\sheight="\d+"', raiz), (
            f"{nombre}.svg: sin width/height en la raiz se ve como miniatura"
        )


def test_cada_svg_tiene_aria_label_descriptiva():
    for nombre in _cargar().DIAGRAMAS:
        etiqueta = re.search(r'aria-label="([^"]*)"', _svg(nombre)).group(1)
        assert len(etiqueta) >= 80, (
            f"{nombre}.svg: aria-label demasiado corta para describir el diagrama"
        )


def test_el_texto_se_lee():
    """Nada por debajo de 13 px: en el aula se proyecta."""
    for nombre in _cargar().DIAGRAMAS:
        tamanos = [float(t) for t in re.findall(r'font-size="([\d.]+)"', _svg(nombre))]
        assert tamanos and min(tamanos) >= 13, f"{nombre}.svg: texto de {min(tamanos)} px"


def test_sin_letras_griegas_ni_cocina():
    """El material de origen usaba tau, mu y analogias de restaurante."""
    prohibido = re.compile(r"[Ͱ-Ͽ]|cocin|mesero|chef|restaurante", re.I)
    for nombre in _cargar().DIAGRAMAS:
        assert not prohibido.search(_svg(nombre)), nombre


def test_las_gantt_comparten_tareas_eje_y_leyenda():
    """Comparables a simple vista: mismas tareas, mismo eje en ms, misma leyenda."""
    modulo = _cargar()
    assert (modulo.EJECUTA_MS, modulo.ESPERA_MS) == (20, 200)
    for nombre in GANTT:
        svg = _svg(nombre)
        assert "ejecuta 20 ms, espera 200 ms la red, ejecuta 20 ms" in svg, nombre
        assert "tiempo (ms)" in svg and ">800<" in svg, nombre
        for rotulo in ("ejecuta:", "espera:", "lista:", "CPU"):
            assert rotulo in svg, f"{nombre}.svg sin {rotulo!r}"


def test_los_totales_de_las_gantt():
    """Los totales que las paginas citan salen de estos dibujos."""
    esperados = {
        "cmp-gantt-secuencial": 720, "cmp-gantt-hilos": 280,
        "cmp-gantt-asyncio": 280, "cmp-gantt-await-en-serie": 720,
        "cmp-gantt-procesos": 260, "cmp-bloqueo-del-loop": 2080,
    }
    for nombre, total in esperados.items():
        assert f"total {total} ms" in _svg(nombre), nombre


def test_procesos_dibuja_dos_cpu():
    svg = _svg("cmp-gantt-procesos")
    assert "CPU 1" in svg and "CPU 2" in svg


def test_la_matriz_ubica_las_cuatro_estrategias():
    svg = _svg("cmp-matriz-2x2")
    for pedazo in ("secuencial", "hilos", "asyncio", "procesos",
                   "paralelo", "concurrente", "await"):
        assert pedazo in svg, pedazo


def test_amdahl_dibuja_las_tres_fracciones_seriales():
    svg = _svg("cmp-amdahl")
    for s in ("S = 0.1", "S = 0.25", "S = 0.5", ">16<"):
        assert s in svg, s


def test_el_arbol_termina_en_las_cinco_estrategias():
    svg = _svg("cmp-arbol-decision")
    for hoja in ("asyncio", "hilos", "vectoriza", "procesos", "secuencial", "espera"):
        assert hoja in svg, hoja


def test_el_generador_rechaza_un_nombre_desconocido():
    r = subprocess.run([sys.executable, str(GENERADOR), "cmp-no-existe"],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "desconocido" in r.stderr


def test_cada_svg_esta_referenciado_por_alguna_pagina():
    paginas = "".join(
        p.read_text(encoding="utf-8")
        for p in sorted(UNIDAD.rglob("*.md")) if p.name != "CREDITOS.md"
    )
    for nombre in _cargar().DIAGRAMAS:
        assert f"{nombre}.svg" in paginas, f"{nombre}.svg no aparece en ninguna pagina"
