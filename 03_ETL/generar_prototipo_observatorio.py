"""Genera un prototipo HTML autonomo del Observatorio con DATOS AGREGADOS.

Entrada: hallazgos_preliminares_cuidados.csv (sin identificadores).
Salida: 06_OBSERVATORIO/prototipo_enasic_2022.html.
No incorpora ni publica microdatos; no hace estimaciones ponderadas.
"""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "08_DOCUMENTACION/auditorias/ENASIC_2022/hallazgos_preliminares_cuidados.csv"
OUTPUT = ROOT / "06_OBSERVATORIO/prototipo_enasic_2022.html"

INDICATORS = {
    "horas_40_o_mas": ("40+ horas de cuidado", "Carga de cuidados"),
    "horas_98_o_mas_codificadas": ("98+ horas de cuidado", "Carga de cuidados"),
    "sin_apoyo_economico_o_especie_familiar": ("Sin apoyo familiar declarado", "Apoyo familiar"),
    "con_apoyo_economico_o_especie_familiar": ("Con apoyo familiar declarado", "Apoyo familiar"),
    "insatisfaccion_tiempo_libre": ("Insatisfaccion con tiempo libre", "Bienestar"),
    "afectacion_laboral_alguna_dos_opciones": ("Alguna afectacion laboral", "Trabajo y cuidados"),
    "horas_40_o_mas_y_afectacion_laboral": ("40+ horas y afectacion laboral", "Cruces exploratorios"),
    "insatisfaccion_tiempo_libre_y_afectacion_laboral": ("Insatisfaccion y afectacion laboral", "Cruces exploratorios"),
}


def main():
    if not INPUT.is_file():
        raise SystemExit(f"Falta el CSV agregado: {INPUT}. Ejecuta generar_hallazgos_preliminares.py")
    with INPUT.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    found = {row["indicador_exploratorio"]: row for row in rows}
    if set(found) != set(INDICATORS):
        raise SystemExit(f"Indicadores diferentes a los esperados: {sorted(set(found) ^ set(INDICATORS))}")
    data = []
    for key, (label, category) in INDICATORS.items():
        row = found[key]
        if row["validacion"] != "PRELIMINAR_NO_POBLACIONAL":
            raise SystemExit(f"Estado metodologico inesperado: {key}")
        cases, denominator = int(row["casos"]), int(row["universo_observado"])
        if denominator != 636 or not 0 <= cases <= denominator:
            raise SystemExit(f"Conteos inesperados: {key}, {cases}/{denominator}")
        pct = cases * 100 / denominator
        if abs(pct - float(row["porcentaje_muestral_sin_ponderar"])) > 0.011:
            raise SystemExit(f"Porcentaje inconsistente: {key}")
        data.append({
            "id": key, "nombre": label, "categoria": category,
            "descripcion": row["definicion"], "casos": cases,
            "denominador": denominator, "porcentaje": round(pct, 2)
        })
    # Escape seguro para insertar datos dentro del elemento JSON.
    embedded = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    page = r'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>Observatorio | Cuidados ENASIC 2022</title>
<style>
:root{font-family:Segoe UI,Arial,sans-serif;color:#182235;background:#f4f6fa}
*{box-sizing:border-box}
body{margin:0}
header{background:#13223a;color:#fff;padding:32px max(22px,calc((100% - 1120px)/2))}
header p{color:#c7d6ee;max-width:850px;line-height:1.55}
main{max-width:1120px;margin:auto;padding:26px 20px 60px}
h1{font-size:clamp(1.6rem,4vw,2.5rem);margin:8px 0}
h2{font-size:1.2rem;margin-top:30px}
.kicker{text-transform:uppercase;letter-spacing:.13em;font-size:.75rem;color:#92b9f3}
.note{border-left:4px solid #557ec9;background:#fff;border-radius:9px;padding:15px 18px;line-height:1.55;margin:20px 0}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:14px}
.card{background:white;border:1px solid #dde3eb;padding:19px;border-radius:13px}
.card strong{display:block;font-size:2rem;color:#203e78;margin:8px 0}
.card span{color:#4c5b6f;font-size:.88rem}
.controls{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:18px 0}
select{font:inherit;padding:10px;border:1px solid #cad4e3;border-radius:8px;background:white}
.chart{display:grid;gap:13px}
.baritem{background:#fff;border:1px solid #dde3eb;padding:15px 17px;border-radius:10px}
.barhead{display:flex;justify-content:space-between;gap:10px;align-items:baseline;flex-wrap:wrap}
.barhead strong{font-size:.94rem}
.barhead span{font-weight:700;color:#223f78}
.track{background:#e7edf5;height:13px;border-radius:9px;overflow:hidden;margin:11px 0 6px}
.fill{height:100%;background:#4b73b5;border-radius:9px}
.small{color:#596778;font-size:.82rem}
footer{margin-top:34px;color:#627186;font-size:.86rem;line-height:1.6}
@media print{header{background:white;color:black} .controls{display:none}body{background:white}}
</style>
</head>
<body>
<header>
<div class="kicker">PP 2026-2 · Observatorio de autonomía, cuidados y sostenibilidad económica</div>
<h1>Carga de cuidados e impacto económico</h1>
<p>Primer módulo visual exploratorio — ENASIC 2022. Datos muestrales sin ponderación del subconjunto observado de 636 registros con P6_1 = 1 en TPOB_CUI.</p>
</header>
<main>
<section class="note"><b>Lectura metodológica obligatoria:</b> estos resultados no representan prevalencias nacionales, estatales ni de discapacidad intelectual. Los indicadores pueden superponerse y <b>no deben sumarse</b>. No se ha evaluado todavía el diseño de la muestra ni la precisión estadística.</section>
<div class="cards">
<div class="card"><span>Registros en TPOB_CUI</span><strong>5,677</strong><span>Base de trabajo, distintas condiciones de aplicación</span></div>
<div class="card"><span>Grupo observado P6_1 = 1</span><strong>636</strong><span>Denominador descriptivo de este módulo</span></div>
<div class="card"><span>40+ horas de cuidado</span><strong id="k_hours">—</strong><span>Conteo no ponderado</span></div>
<div class="card"><span>Alguna afectación laboral</span><strong id="k_labor">—</strong><span>Dos opciones específicas de la pregunta 6.12</span></div>
</div>
<h2>Indicadores exploratorios</h2>
<div class="controls">
<label for="category">Tema:</label>
<select id="category"><option value="Todos">Todos</option><option>Carga de cuidados</option><option>Apoyo familiar</option><option>Bienestar</option><option>Trabajo y cuidados</option><option>Cruces exploratorios</option></select>
</div>
<div id="chart" class="chart" aria-live="polite"></div>
<h2>Interpretación para el PP</h2>
<div class="note">Los patrones observados permiten formular hipótesis sobre sobrecarga, continuidad laboral, bienestar y apoyos familiares. La decisión sobre programas sociales requiere después verificar universos y factores de expansión, delimitar territorio y contrastar necesidades con la asociación colaboradora. <b>No hay evidencia causal</b> en estos cruces.</div>
<footer><b>Fuente:</b> INEGI, ENASIC 2022 (microdatos públicos), procesamiento local del proyecto PP 2026-2. Primer prototipo de divulgación con datos agregados; no contiene identificadores individuales. Los valores de 98 horas corresponden a la categoría 98 o más, no a un valor puntual.</footer>
</main>
<script id="dataset" type="application/json">__DATA__</script>
<script>
"use strict";
const data=JSON.parse(document.getElementById("dataset").textContent);
const chart=document.getElementById("chart");
const select=document.getElementById("category");
function render(){
  chart.replaceChildren();
  const selected=select.value;
  const rows=data.filter(d=>selected==="Todos" || d.categoria===selected);
  for(const d of rows){
    const item=document.createElement("article");item.className="baritem";
    const top=document.createElement("div");top.className="barhead";
    const name=document.createElement("strong");name.textContent=d.nombre;
    const pct=document.createElement("span");pct.textContent=d.porcentaje.toFixed(2)+"%";
    top.append(name,pct);
    const track=document.createElement("div");track.className="track";
    const fill=document.createElement("div");fill.className="fill";
    fill.style.width=d.porcentaje+"%";fill.setAttribute("role","img");
    fill.setAttribute("aria-label",d.porcentaje.toFixed(2)+" por ciento");
    track.append(fill);
    const note=document.createElement("div");note.className="small";
    note.textContent=d.casos+" / "+d.denominador+" registros · "+d.descripcion;
    item.append(top,track,note);chart.append(item);
  }
}
select.addEventListener("change",render);
document.getElementById("k_hours").textContent=data.find(d=>d.id==="horas_40_o_mas").casos;
document.getElementById("k_labor").textContent=data.find(d=>d.id==="afectacion_laboral_alguna_dos_opciones").casos;
render();
</script>
</body>
</html>'''
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(page.replace("__DATA__", embedded), encoding="utf-8")
    print(f"PROTOTIPO GENERADO: {OUTPUT}")
    print(f"INDICADORES: {len(data)} | DENOMINADOR: 636")
    print("Abre el archivo HTML desde el Explorador de Windows.")
    print("Prototipo exploratorio no ponderado: no publicarlo como diagnostico poblacional.")


if __name__ == "__main__":
    main()
