"""Genera la vista ENASIC 2022 v2 del Observatorio PP 2026-2.

Usa SOLO cifras agregadas locales de los 8 indicadores exploratorios.
Incluye, si existe, el estatus de verificación numérica R/Python de los
7 estimadores experimentales: NO LOS PUBLICA NI LOS PRESENTA COMO OFICIALES.
No sobrescribe el prototipo HTML original ni otros módulos.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "08_DOCUMENTACION/auditorias/ENASIC_2022"
INPUT = AUDIT / "hallazgos_preliminares_cuidados.csv"
EXTERNAL = AUDIT / "comparacion_externa_R_Python.json"
OUTPUT = ROOT / "06_OBSERVATORIO/enasic_2022_cuidados.html"
SIGNATURE = "<!-- PP2026_ENASIC_V2_GENERADO -->"
INDICATORS = {
    "horas_40_o_mas": ("40 horas semanales o más", "Carga de cuidados"),
    "horas_98_o_mas_codificadas": ("98 horas o más (categoría límite)", "Carga de cuidados"),
    "sin_apoyo_economico_o_especie_familiar": ("Sin apoyo económico o en especie familiar", "Apoyo familiar"),
    "con_apoyo_economico_o_especie_familiar": ("Con apoyo económico o en especie familiar", "Apoyo familiar"),
    "insatisfaccion_tiempo_libre": ("Insatisfacción con el tiempo libre", "Bienestar"),
    "afectacion_laboral_alguna_dos_opciones": ("Alguna de dos afectaciones laborales", "Trabajo y cuidados"),
    "horas_40_o_mas_y_afectacion_laboral": ("40+ horas y afectación laboral", "Cruces exploratorios"),
    "insatisfaccion_tiempo_libre_y_afectacion_laboral": ("Insatisfacción y afectación laboral", "Cruces exploratorios"),
}
VALIDATED_SEVEN = {
    "cansancio_si", "dejar_trabajo_si", "jornada_horario_si",
    "alguna_dos_afectaciones_laborales", "cuidado_40_horas_o_mas",
    "sin_apoyo_familiar", "insatisfaccion_tiempo_libre",
}

def read_rows():
    if not INPUT.exists():
        raise SystemExit("No existe CSV agregado de ENASIC: " + str(INPUT))
    with INPUT.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 8:
        raise ValueError(f"Se esperaban 8 indicadores, recibidos {len(rows)}")
    indexed = {r["indicador_exploratorio"]: r for r in rows}
    if len(indexed) != 8 or set(indexed) != set(INDICATORS):
        raise ValueError("Inventario de indicadores ENASIC inesperado")
    data = []
    for key, (label, group) in INDICATORS.items():
        r = indexed[key]
        if r["validacion"] != "PRELIMINAR_NO_POBLACIONAL":
            raise ValueError(f"Estatus muestral no esperado: {key}")
        n, yes = int(r["universo_observado"]), int(r["casos"])
        value = float(r["porcentaje_muestral_sin_ponderar"])
        if n != 636 or yes < 0 or yes > n or abs(value - yes / n * 100) > .015:
            raise ValueError(f"Conteos/porcentaje inconsistentes: {key}")
        data.append({
            "id": key, "etiqueta": label, "grupo": group,
            "n": n, "casos": yes, "porcentaje": 100 * yes / n,
            "definicion": r["definicion"]
        })
    return data

def read_numeric_validation():
    if not EXTERNAL.exists():
        return {"ok": False, "label": "Comparación R/Python aún no encontrada en esta carpeta"}
    info = json.loads(EXTERNAL.read_text(encoding="utf-8"))
    comparisons = info.get("indicadores", [])
    names = {r.get("indicador") for r in comparisons if isinstance(r, dict)}
    good = (info.get("estado") == "COINCIDENCIA_EXTERNA_NUMERICA"
            and len(comparisons) == 7 and names == VALIDATED_SEVEN
            and all(r.get("estado") == "COINCIDE" for r in comparisons))
    if not good:
        return {"ok": False, "label": "Comparación numérica no confirmada: verificar archivos"}
    return {"ok": True, "label": "7/7 estimadores experimentales coinciden entre R y Python"}

def escape_data(d):
    text = json.dumps(d, ensure_ascii=False, allow_nan=False)
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

TEMPLATE = r'''<!DOCTYPE html>
<!-- PP2026_ENASIC_V2_GENERADO -->
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ENASIC 2022 | Carga de cuidados · Observatorio PP</title>
<style>
:root{--ink:#1c2e45;--navy:#17283f;--muted:#617087;--bg:#f4f6fa;--line:#dce3eb;--blue:#4d76b6;--gold:#d4a45a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);font:15px/1.55 system-ui,"Segoe UI",sans-serif;color:var(--ink)}
a{color:#20589d}.wrap{max-width:1100px;margin:auto;padding:0 23px}
header{background:var(--navy);color:white;padding:29px 0 61px}
nav{display:flex;justify-content:space-between;align-items:center;gap:16px;font-size:.83rem}
nav a{color:#eac786;text-decoration:none}
.eyebrow{color:#e7c28c;font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;font-weight:800;margin-top:43px}
h1{font-size:clamp(2rem,4.5vw,3rem);line-height:1.15;letter-spacing:-.045em;margin:10px 0 13px}
header p{color:#cfdae8;max-width:770px}
section{margin:25px auto}.panel,.tile{background:#fff;border:1px solid var(--line);border-radius:14px;box-shadow:0 5px 18px #14253b0a}
.panel{padding:24px}.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:-33px;position:relative}
.tile{padding:20px}.tile strong{display:block;font-size:1.8rem;letter-spacing:-.03em}.tile small{color:var(--muted);font-size:.79rem}
h2{margin:0 0 10px;font-size:1.3rem}h3{font-size:1rem;margin:0 0 8px}
.lead{color:var(--muted);font-size:.93rem}.warning{background:#fff9ed;border-left:3px solid var(--gold);border-radius:4px;padding:12px 15px;color:#705632;font-size:.89rem;margin:16px 0}
.controls{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin:20px 0}
label{font-size:.84rem;font-weight:750;color:var(--muted)}
select{border:1px solid #cbd6e4;background:#fff;color:var(--ink);border-radius:8px;padding:10px;font:inherit;min-width:220px}
.barlist{display:grid;gap:12px}.bar{border:1px solid var(--line);border-radius:9px;padding:14px 17px}
.bar-head{display:flex;align-items:center;justify-content:space-between;gap:12px;font-weight:700;font-size:.94rem}
.bar-head strong{color:#1f4f95}.track{background:#e7edf5;border-radius:30px;height:13px;overflow:hidden;margin:11px 0 7px}
.fill{background:var(--blue);height:100%;border-radius:30px}.detail{color:var(--muted);font-size:.81rem}
.columns{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.pill{background:#eaf0f8;color:#25548a;font-size:.81rem;padding:5px 11px;border-radius:22px;font-weight:700;display:inline-block}
.pill.wait{background:#fff3df;color:#8b672d}
ul{padding-left:19px;margin-bottom:0}li{margin:5px 0}
.source{font-size:.84rem;color:var(--muted)}footer{font-size:.81rem;color:var(--muted);padding:20px 0 40px}
@media(max-width:780px){.tiles{grid-template-columns:repeat(2,1fr)}.columns{grid-template-columns:1fr}}
@media(max-width:470px){.tiles{grid-template-columns:1fr 1fr}.tile{padding:12px}.bar-head{font-size:.84rem}}
</style></head><body>
<header><div class="wrap">
<nav><span>PP 2026-2 · Observatorio</span><a href="index.html">← Volver al Observatorio</a></nav>
<div class="eyebrow">ENASIC 2022 · Personas cuidadoras</div>
<h1>Carga de cuidados, bienestar y trabajo</h1>
<p>Indicadores exploratorios de una muestra de 636 registros seleccionados en TPOB_CUI. Muestran relaciones que podemos investigar, no prevalencias nacionales ni impactos causales.</p>
</div></header>
<main class="wrap">
<div class="tiles">
<div class="tile"><strong>5,677</strong><small>Registros de TPOB_CUI</small></div>
<div class="tile"><strong>636</strong><small>Registros del grupo P6_1 = 1</small></div>
<div class="tile"><strong id="k40">—</strong><small>Con 40 h o más de cuidado (muestra)</small></div>
<div class="tile"><strong id="klabor">—</strong><small>Con alguna de dos afectaciones laborales</small></div>
</div>
<section class="panel">
<h2>Indicadores muestrales sin ponderar</h2>
<p class="lead">Todos los porcentajes tienen denominador 636. Puedes filtrar por tema y revisar su definición junto al conteo original.</p>
<div class="warning"><strong>No son cifras nacionales:</strong> no utilizar estos porcentajes para describir a todas las personas cuidadoras de México. Las ocho medidas tienen definiciones diferentes; algunos indicadores se superponen y no se suman.</div>
<div class="controls"><label for="theme">Tema</label><select id="theme"><option value="Todos">Todos</option><option>Carga de cuidados</option><option>Trabajo y cuidados</option><option>Apoyo familiar</option><option>Bienestar</option><option>Cruces exploratorios</option></select></div>
<div class="barlist" id="list"></div>
</section>
<section class="columns">
<div class="panel"><h2>Auditoría y validación numérica</h2>
<p><span id="validation" class="pill"></span></p>
<p class="lead">La estructura del diseño y las claves fueron auditadas. Se compararon estimaciones experimentales ponderadas con la herramienta <code>survey</code> de R y una implementación de Python.</p>
<div class="warning"><strong>Límite técnico pendiente:</strong> la coincidencia R/Python no certifica que TPOB_CUI contenga todas las UPM necesarias para el diseño oficial de los dominios. Por eso no se publican todavía esos siete porcentajes ponderados.</div>
<p class="source">Referencia metodológica: <a href="https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/nueva_estruc/889463909798.pdf" target="_blank" rel="noopener noreferrer">INEGI · Diseño muestral ENASIC 2022 ↗</a></p>
</div>
<div class="panel"><h2>Qué significa para el proyecto</h2>
<ul>
<li>La sobrecarga de tiempo y algunas repercusiones laborales se analizan como dimensiones separadas, no como relaciones causales.</li>
<li>«Apoyo familiar» en este módulo se refiere específicamente a <strong>apoyo económico o en especie</strong> del hogar/familia, no a ayuda general para cuidar.</li>
<li>El valor 98 de horas representa la categoría «98 horas o más», no un valor puntual.</li>
<li>La ENASIC no identifica específicamente diagnósticos de discapacidad intelectual o síndrome de Down.</li>
<li>Los datos nacionales orientarán las preguntas para la asociación; no sustituyen el diagnóstico local ni el consentimiento.</li>
</ul>
</div>
</section>
<section class="panel"><h2>Cómo conectamos estos resultados</h2>
<p class="lead">ENASIC permite explorar la situación de las personas cuidadoras. ENUT aporta información sobre horas de cuidado y ENIGH sobre condiciones económicas. Cada encuesta tiene poblaciones y diseños diferentes; no cruzamos sus registros individuales.</p>
<p><a href="index.html">Volver a los tres módulos del Observatorio →</a></p>
</section>
</main>
<footer class="wrap">Fuente: INEGI ENASIC 2022, microdatos públicos; cálculos descriptivos propios del PP 2026-2. Esta vista no presenta estimaciones poblacionales oficiales ni datos individuales.</footer>
<script type="application/json" id="data">__DATA__</script>
<script type="application/json" id="meta">__META__</script>
<script>
(function(){
"use strict";
const data=JSON.parse(document.getElementById("data").textContent);
const meta=JSON.parse(document.getElementById("meta").textContent);
const category=document.getElementById("theme");
function render(){
 const current=category.value;
 const selected=data.filter(d=>current==="Todos"||d.grupo===current);
 const container=document.getElementById("list");
 container.replaceChildren();
 for(const item of selected){
  const outer=document.createElement("article");outer.className="bar";
  const head=document.createElement("div");head.className="bar-head";
  const title=document.createElement("span");title.textContent=item.etiqueta;
  const number=document.createElement("strong");number.textContent=item.porcentaje.toFixed(2)+"%";
  head.append(title,number);
  const track=document.createElement("div");track.className="track";
  const fill=document.createElement("div");fill.className="fill";fill.style.width=item.porcentaje+"%";
  track.append(fill);
  const small=document.createElement("div");small.className="detail";
  small.textContent=item.casos+" de "+item.n+" registros · "+item.definicion;
  outer.append(head,track,small);container.append(outer);
 }
}
category.addEventListener("change",render);
document.getElementById("k40").textContent=data.find(d=>d.id==="horas_40_o_mas").casos.toLocaleString("es-MX");
document.getElementById("klabor").textContent=data.find(d=>d.id==="afectacion_laboral_alguna_dos_opciones").casos.toLocaleString("es-MX");
const status=document.getElementById("validation");
status.textContent=meta.label;
if(!meta.ok)status.classList.add("wait");
render();
})();
</script></body></html>'''

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true",
                        help="Regenera exclusivamente un HTML creado por este script")
    args = parser.parse_args()
    data = read_rows()
    meta = read_numeric_validation()
    if OUTPUT.exists():
        prev = OUTPUT.read_text(encoding="utf-8")[:200]
        if SIGNATURE not in prev:
            raise SystemExit("Archivo HTML ajeno al generador: protegido contra sobrescritura")
        if not args.overwrite:
            raise SystemExit("Ya existe ENASIC v2; usa --overwrite para actualizar")
    page = TEMPLATE.replace("__DATA__", escape_data(data)).replace("__META__", escape_data(meta))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(page, encoding="utf-8")
    print("ENASIC V2 GENERADO:", OUTPUT)
    print("INDICADORES DESCRIPTIVOS SIN PONDERAR:", len(data))
    print("ESTADO COMPARACION NUMERICA:", meta["label"])
    print("SIN PUBLICAR ESTIMACIONES EXPERIMENTALES PONDERADAS.")
    print("PROTOTIPO ENASIC ORIGINAL CONSERVADO INTACTO.")

if __name__ == "__main__":
    main()
