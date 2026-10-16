"""Genera modulo HTML autonomo de ENUT 2024 para el Observatorio PP.

Entrada: indicadores agregados ya producidos por R survey.
NO lee ni exporta la base de 74,053 registros; NO publica microdatos.
No sobrescribe un HTML modificado manualmente sin --overwrite.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "08_DOCUMENTACION/auditorias/ENUT_2024"
RESULTS = AUDIT / "indicadores_cuidados_ponderados_preliminares.csv"
VALIDATION = AUDIT / "validacion_independiente_python_R_enut_2024.json"
OUTPUT = ROOT / "06_OBSERVATORIO/enut_2024_cuidados.html"
SIGNATURE = "<!-- PP2026_ENUT_MODULO_GENERADO -->"

VARIABLES = {
    "cuid_esp_int_hog_sin_cp": "Cuidados especiales dentro del hogar, sin pasivos",
    "cuid_esp_int_hog_con_cp": "Cuidados especiales dentro del hogar, con pasivos",
    "trab_no_rem_cuid_hog": "Cuidados no remunerados a integrantes del hogar",
    "cuid_esp_disc_enf": "Ayuda gratuita a otros hogares familiares",
}
GROUPS = ("total", "mujeres", "hombres")
MEASURES = ("participacion_porcentaje", "media_condicional_unidad_original")
NUMERIC = ("estimacion", "error_estandar", "cv", "lim_inf_95",
           "lim_sup_95", "n_muestra", "n_positivos", "grados_libertad")
BENCHMARKS = {
    "cuid_esp_int_hog_sin_cp": {"mujeres": 12.8, "hombres": 7.5},
    "cuid_esp_int_hog_con_cp": {"mujeres": 23.8, "hombres": 13.1},
}


def load_results() -> list[dict]:
    if not RESULTS.is_file():
        raise SystemExit("Falta archivo agregado: " + str(RESULTS))
    with RESULTS.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    expected = {(g, v, m) for g in GROUPS for v in VARIABLES for m in MEASURES}
    keys = [(r.get("grupo"), r.get("variable"), r.get("medida")) for r in rows]
    if len(rows) != 24 or len(set(keys)) != 24 or set(keys) != expected:
        raise ValueError("Se esperaban las 24 combinaciones unicas de grupo, variable y medida")
    for row in rows:
        for key in NUMERIC:
            value = float(row[key])
            if not math.isfinite(value):
                raise ValueError("Valor no finito en " + key)
            row[key] = int(value) if key in ("n_muestra", "n_positivos", "grados_libertad") else value
        if row["n_positivos"] > row["n_muestra"] or row["n_positivos"] < 0:
            raise ValueError("Conteos invalidos")
        if row["error_estandar"] < 0 or row["cv"] < 0:
            raise ValueError("Error estandar o CV negativo")
        if not row["lim_inf_95"] <= row["estimacion"] <= row["lim_sup_95"]:
            raise ValueError("Intervalo no contiene estimador")
        if row["medida"] == "participacion_porcentaje":
            if not 0 <= row["estimacion"] <= 100:
                raise ValueError("Participacion fuera de 0-100")
    return rows


def load_validation() -> dict:
    if not VALIDATION.is_file():
        return {"validado": False, "detalle": "Pendiente archivo de validacion local"}
    try:
        data = json.loads(VALIDATION.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise ValueError("JSON de validacion invalido") from exc
    ok = (data.get("estado") == "COINCIDENCIA_NUMERICA_24_DE_24"
          and data.get("indicadores_recalculados") == 24
          and data.get("n_registros") == 74053)
    if not ok:
        raise ValueError("La validacion disponible no acredita 24/24 estimadores")
    return {"validado": True,
            "detalle": "24 de 24 estimaciones y errores Taylor reproducidos R/Python",
            "max_diff_se": data.get("diferencia_maxima_error_estandar")}


TEMPLATE = r'''<!DOCTYPE html>
<!-- PP2026_ENUT_MODULO_GENERADO -->
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<title>ENUT 2024 | Observatorio PP 2026-2</title>
<style>
:root{--ink:#14253c;--muted:#556377;--line:#dfe5ed;--base:#f4f6fa;--card:#fff;
--blue:#1657a5;--women:#c1793b;--men:#3777b7;--accent:#e5b86a;}
*{box-sizing:border-box}
body{margin:0;background:var(--base);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--blue)}
h1,h2,h3,p{margin-top:0}
h1{font-size:clamp(2rem,4vw,3.15rem);letter-spacing:-.045em;line-height:1.14;margin-bottom:17px}
h2{font-size:1.27rem;letter-spacing:-.02em;margin-bottom:12px}
h3{font-size:1rem;margin-bottom:8px}
.wrap{max-width:1150px;padding:0 24px;margin:auto}
.top{background:#15263c;color:#dce5f3;padding:20px 0 5px}
.nav{display:flex;gap:12px;align-items:center;justify-content:space-between;font-size:.82rem;letter-spacing:.09em;text-transform:uppercase;font-weight:700}
.mark{width:29px;height:29px;border:2px solid #d8b273;display:inline-grid;place-items:center;border-radius:8px;color:#d8b273;margin-right:9px}
.tag{border:1px solid #42546c;padding:6px 12px;border-radius:99px;color:#dbe6f4}
.hero{padding:55px 0 62px;display:grid;grid-template-columns:1fr .44fr;gap:32px;align-items:center}
.hero p{color:#ccd7e5;max-width:650px}
.eyebrow{font-size:.76rem;text-transform:uppercase;letter-spacing:.18em;color:#d3b87a;font-weight:800;margin:0 0 14px}
.highlight{color:#edcb90}
.side-note{border-left:2px solid var(--accent);padding:2px 0 2px 20px;color:#d5deeb;font-size:.91rem}
.side-note strong{display:block;color:#fff;font-size:1.1rem;margin-bottom:8px}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:-31px auto 32px;position:relative}
.metric,.panel{background:var(--card);border:1px solid var(--line);border-radius:13px;box-shadow:0 6px 24px #1b2d4910}
.metric{padding:21px 20px}
.metric .big{font-weight:750;letter-spacing:-.035em;font-size:1.72rem;line-height:1.15}
.metric small{display:block;color:var(--muted);font-size:.79rem;margin-top:7px}
section{margin:30px auto}
.panel{padding:24px 26px}
.lead{color:var(--muted);font-size:.94rem;max-width:840px}
.secttop{display:flex;justify-content:space-between;align-items:flex-start;gap:18px}
.source{font-size:.82rem;color:var(--muted)}
.selectors{display:flex;gap:14px;flex-wrap:wrap;margin:18px 0 21px}
label{display:flex;flex-direction:column;gap:5px;font-size:.8rem;color:var(--muted);font-weight:700;flex:1;min-width:250px}
select{font:inherit;padding:10px 12px;color:var(--ink);border-radius:8px;border:1px solid #cbd4e0;background:#fff;max-width:100%;font-size:.89rem}
.summary{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:16px}
.summary .box{padding:19px;background:#f9fafc;border:1px solid #e2e8f0;border-radius:10px}
.summary .value{font-size:1.7rem;font-weight:760;letter-spacing:-.035em}
.summary .label{font-size:.78rem;color:var(--muted)}
.women{color:var(--women)}.men{color:var(--men)}
.chart{display:grid;gap:22px;margin:26px 0 12px}
.bar-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:5px;gap:20px}
.bar-head strong{font-size:.94rem}.bar-head span{font-size:1.03rem;font-weight:800}
.rail{height:26px;position:relative;background:linear-gradient(90deg,#eef2f7 0%,#e3eaf3 100%);border-radius:6px;overflow:visible}
.fill{height:100%;min-width:2px;border-radius:6px;opacity:.8}
.ci{position:absolute;top:-4px;height:34px;border:2px solid #16283d;border-left-width:2px;border-right-width:2px;border-top:0;border-bottom:0;border-radius:1px;pointer-events:none}
.dot{position:absolute;top:8px;width:10px;height:10px;background:#fff;border:2px solid #14253c;border-radius:50%;transform:translateX(-50%)}
.bar-detail{color:var(--muted);font-size:.79rem;margin:6px 0 0}
.note{border-left:3px solid var(--accent);padding:8px 12px;background:#fffbf4;color:#665332;font-size:.88rem;margin-top:22px}
.split{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.official{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:15px}
.official .cell{background:#f6f8fb;border-radius:8px;padding:12px 15px}
.official b{display:block;font-size:1.37rem}
.official small{font-size:.78rem;color:var(--muted)}
.status{font-size:.81rem;font-weight:700;border-radius:50px;padding:5px 10px;background:#e8f0e8;color:#315b40}
.status.wait{background:#f9efd7;color:#785f21}
.detail-list{margin:0;padding-left:19px;font-size:.9rem}
.detail-list li{margin-bottom:7px}
.table-wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.85rem}
th,td{padding:10px 12px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
th{background:#f6f8fb;color:#59697c;font-size:.75rem}
td.num{text-align:right;font-variant-numeric:tabular-nums}
summary{cursor:pointer;font-weight:700;padding:10px 0}
footer{color:#627185;font-size:.79rem;padding:20px 0 40px}
@media(max-width:850px){.hero{grid-template-columns:1fr}.metrics{grid-template-columns:repeat(2,1fr)}.split{grid-template-columns:1fr}.summary{grid-template-columns:1fr}.hero{padding-bottom:54px}}
@media(max-width:520px){.wrap{padding:0 14px}.metrics{grid-template-columns:1fr 1fr}.metric{padding:13px}.panel{padding:18px}.top{padding-top:12px}.tag{display:none}}
</style>
</head>
<body>
<div class="top">
 <div class="wrap">
  <div class="nav"><span><span class="mark">PP</span> Observatorio de autonomía y cuidados</span><span class="tag">Módulo ENUT · 2024</span></div>
  <div class="hero">
   <div><div class="eyebrow">Datos → Evidencia → Decisión → Programa</div>
   <h1>El <span class="highlight">tiempo de cuidar</span> también es una dimensión económica y social.</h1>
   <p>Indicadores sobre trabajo no remunerado y cuidados en México, desagregados por sexo, a partir de los microdatos de la Encuesta Nacional sobre Uso del Tiempo 2024.</p></div>
   <div class="side-note"><strong>Evidencia con trazabilidad</strong>Estimaciones propias con factores de expansión y varianza del diseño. Contrastadas con resultados oficiales del INEGI donde existe una medida equivalente.</div>
  </div>
 </div>
</div>
<main class="wrap">
 <div class="metrics">
  <div class="metric"><div class="big">74,053</div><small>Registros del módulo analizados</small></div>
  <div class="metric"><div class="big">24/24</div><small>Estimaciones y errores cotejados en R/Python</small></div>
  <div class="metric"><div class="big">342</div><small>Estratos de diseño</small></div>
  <div class="metric"><div class="big">4,200</div><small>Unidades estrato-UPM observadas</small></div>
 </div>
 <section class="panel">
  <div class="secttop">
   <div><h2>Explorador de indicadores ponderados</h2><p class="lead">Elige la actividad y la medida. Se muestran estimación puntual e intervalo de confianza del 95%, bajo el diseño implementado.</p></div>
   <span id="validBadge" class="status"></span>
  </div>
  <div class="selectors">
   <label>Actividad de cuidado
    <select id="indicator"><option value="cuid_esp_int_hog_sin_cp">Cuidados especiales dentro del hogar · sin pasivos</option><option value="cuid_esp_int_hog_con_cp">Cuidados especiales dentro del hogar · con pasivos</option><option value="trab_no_rem_cuid_hog">Cuidados no remunerados dentro del hogar</option><option value="cuid_esp_disc_enf">Ayuda gratuita a otros hogares familiares</option></select>
   </label>
   <label>Medida
    <select id="metricType"><option value="media_condicional_unidad_original">Promedio entre quienes realizaron la actividad</option><option value="participacion_porcentaje">Porcentaje que realizó la actividad</option></select>
   </label>
  </div>
  <div id="summary" class="summary"></div>
  <div id="chart" class="chart"></div>
  <p id="chartNote" class="source"></p>
  <div class="note" id="analysisNote"></div>
 </section>
 <section class="split">
  <div class="panel">
   <h2>Contraste con la publicación oficial</h2>
   <p class="lead">Promedios de horas semanales de cuidados a integrantes del hogar con enfermedad crónica, temporal o discapacidad. Incluye cuidados emocionales; consulta el tratamiento de pasivos.</p>
   <div id="official" class="official"></div>
   <p class="source">INEGI, ENUT 2024, comunicado de prensa 121/25 (28-ago-2025), página 5. <a href="https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/enut/enut2024_CP.pdf" target="_blank" rel="noopener noreferrer">Documento oficial ↗</a></p>
  </div>
  <div class="panel">
   <h2>Lectura responsable</h2>
   <ul class="detail-list">
    <li><strong>Fuente oficial</strong> y <strong>cálculo propio</strong> se presentan separadamente.</li>
    <li>Las medias son <strong>condicionales</strong>: corresponden a quienes realizaron la actividad, no a todas las personas.</li>
    <li><strong>Con</strong> y <strong>sin</strong> cuidados pasivos no son categorías independientes; no se suman ni se restan sus medias.</li>
    <li>Enfermedad o discapacidad <strong>no equivale</strong> a un diagnóstico de discapacidad intelectual o síndrome de Down.</li>
    <li>Una diferencia entre estimadores no implica por sí sola significancia estadística ni causalidad.</li>
   </ul>
  </div>
 </section>
 <section class="panel">
  <h2>Trazabilidad completa: 24 estimaciones</h2>
  <p class="lead">Incluye participación, promedios condicionales, errores estándar, coeficientes de variación e intervalos del 95%. Todos los registros son agregados; no se muestran microdatos.</p>
  <details>
   <summary>Mostrar las 24 filas de resultados</summary>
   <div class="table-wrap"><table><thead><tr><th>Grupo</th><th>Actividad</th><th>Medida</th><th>Estimación</th><th>SE</th><th>CV</th><th>IC95%</th><th>n muestra</th><th>n positivos</th></tr></thead><tbody id="resultRows"></tbody></table></div>
  </details>
 </section>
</main>
<footer class="wrap">Proyecto académico PP 2026-2 · Observatorio de autonomía, cuidados y sostenibilidad económica. No son estadísticas oficialmente publicadas por INEGI, salvo aquellas identificadas expresamente como referencia oficial. Sin datos personales.</footer>
<script id="payload" type="application/json">__DATA_JSON__</script>
<script>
(function(){
"use strict";
const data=JSON.parse(document.getElementById("payload").textContent);
const names=data.labels, official=data.benchmarks;
const groups=["mujeres","hombres","total"];
const colors={"mujeres":"#c1793b","hombres":"#3777b7","total":"#64748b"};
const indicator=document.getElementById("indicator"), metric=document.getElementById("metricType");
const fmt=function(n,d){return new Intl.NumberFormat("es-MX",{minimumFractionDigits:d,maximumFractionDigits:d}).format(n);};
const unit=function(){return metric.value==="participacion_porcentaje"?"%":" h";};
const keyrow=function(group,v,m){return data.rows.find(function(x){return x.grupo===group&&x.variable===v&&x.medida===m;});};
const escapeHtml=function(s){return String(s).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});};
document.getElementById("validBadge").textContent=data.validacion.validado?"R + Python · 24/24":"Verificación local pendiente";
if(!data.validacion.validado)document.getElementById("validBadge").classList.add("wait");
function render(){
 const v=indicator.value,m=metric.value,isPct=m==="participacion_porcentaje";
 const rows=groups.map(function(g){return keyrow(g,v,m);});
 if(rows.some(function(x){return !x;}))throw new Error("Faltan resultados");
 const a=rows[0],b=rows[1],c=rows[2];
 const diff=a.estimacion-b.estimacion;
 document.getElementById("summary").innerHTML=
 '<div class="box"><div class="label">Mujeres</div><div class="value women">'+fmt(a.estimacion,2)+unit()+'</div><div class="label">IC95%: '+fmt(a.lim_inf_95,2)+' a '+fmt(a.lim_sup_95,2)+unit()+'</div></div>'+
 '<div class="box"><div class="label">Hombres</div><div class="value men">'+fmt(b.estimacion,2)+unit()+'</div><div class="label">IC95%: '+fmt(b.lim_inf_95,2)+' a '+fmt(b.lim_sup_95,2)+unit()+'</div></div>'+
 '<div class="box"><div class="label">Diferencia puntual (mujeres − hombres)</div><div class="value">'+(diff>=0?"+":"")+fmt(diff,2)+(isPct?" pp":" unidades")+'</div><div class="label">No representa prueba de significancia</div></div>';
 const max=isPct?100:Math.max(30,Math.ceil(Math.max(...rows.map(function(r){return r.lim_sup_95;}))*1.3));
 document.getElementById("chart").innerHTML=rows.map(function(r){
  const color=colors[r.grupo];
  const width=Math.max(0,Math.min(100,r.estimacion/max*100));
  const lo=Math.max(0,Math.min(100,r.lim_inf_95/max*100));
  const hi=Math.max(0,Math.min(100,r.lim_sup_95/max*100));
  return '<div><div class="bar-head"><strong>'+escapeHtml(r.grupo.charAt(0).toUpperCase()+r.grupo.slice(1))+'</strong><span>'+fmt(r.estimacion,2)+unit()+'</span></div>'+
   '<div class="rail"><div class="fill" style="width:'+width+'%;background:'+color+'"></div>'+
   '<span class="ci" style="left:'+lo+'%;width:'+Math.max(0,hi-lo)+'%"></span>'+
   '<span class="dot" style="left:'+width+'%"></span></div>'+
   '<p class="bar-detail">IC95% '+fmt(r.lim_inf_95,2)+'–'+fmt(r.lim_sup_95,2)+unit()+' · SE '+fmt(r.error_estandar,3)+' · CV '+fmt(r.cv*100,2)+'%</p></div>';
 }).join("");
 document.getElementById("chartNote").textContent=isPct?
  "Porcentaje ponderado sobre todas las personas del grupo en TVAR_CREA; error y estimación bajo el diseño aplicado.":
  "Promedio ponderado exclusivamente entre quienes registran actividad positiva; interpretación temporal contrastada con INEGI para cuidados especiales.";
 const note=v==="cuid_esp_disc_enf"?
  "Atención: esta variable mide ayuda gratuita a personas de OTROS hogares familiares por enfermedad o discapacidad; no representa cuidados al interior del propio hogar.":
  v==="trab_no_rem_cuid_hog"?
  "Este indicador comprende cuidados no remunerados a integrantes del hogar, sin cuidados pasivos y con cuidados emocionales. No equivale al de cuidados especiales.":
  "Este indicador comprende cuidados a integrantes del propio hogar con enfermedad crónica, temporal o discapacidad. La variante seleccionada "+(v.endsWith("sin_cp")?"EXCLUYE":"INCLUYE")+" cuidados pasivos.";
 document.getElementById("analysisNote").textContent=note;
 if(official[v]&&!isPct){
   const x=official[v];
   document.getElementById("official").innerHTML=
   '<div class="cell"><small>Mujeres · INEGI</small><b>'+fmt(x.mujeres,1)+' h</b><small>PP: '+fmt(a.estimacion,3)+' h</small></div>'+
   '<div class="cell"><small>Hombres · INEGI</small><b>'+fmt(x.hombres,1)+' h</b><small>PP: '+fmt(b.estimacion,3)+' h</small></div>';
 }else{
   document.getElementById("official").innerHTML='<div class="cell" style="grid-column:1/-1"><small>No se realiza comparación oficial para esta combinación. La referencia publicada solo cubre medias condicionales de cuidados especiales dentro del hogar.</small></div>';
 }
}
document.getElementById("resultRows").innerHTML=data.rows.map(function(r){
 const m=r.medida==="participacion_porcentaje"?"Participación (%)":"Media entre positivos";
 return "<tr><td>"+escapeHtml(r.grupo)+"</td><td>"+escapeHtml(names[r.variable])+"</td><td>"+m+"</td>"+
 "<td class='num'>"+fmt(r.estimacion,3)+"</td><td class='num'>"+fmt(r.error_estandar,3)+"</td>"+
 "<td class='num'>"+fmt(r.cv*100,2)+"%</td><td class='num'>"+fmt(r.lim_inf_95,3)+"–"+fmt(r.lim_sup_95,3)+"</td>"+
 "<td class='num'>"+r.n_muestra+"</td><td class='num'>"+r.n_positivos+"</td></tr>";
}).join("");
indicator.addEventListener("change",render);
metric.addEventListener("change",render);
render();
}());
</script>
</body></html>'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true",
                        help="Volver a generar un HTML previo del mismo modulo")
    args = parser.parse_args()
    rows = load_results()
    validation = load_validation()
    if OUTPUT.exists():
        beginning = OUTPUT.read_text(encoding="utf-8")[:200]
        if SIGNATURE not in beginning:
            raise SystemExit("El archivo destino no fue generado por este script; no se sobrescribe.")
        if not args.overwrite:
            raise SystemExit("El modulo ya existe. Usa --overwrite para regenerar.")
    payload = {
        "rows": rows, "labels": VARIABLES,
        "benchmarks": BENCHMARKS, "validacion": validation,
        "fecha_generacion_utc": datetime.now(timezone.utc).isoformat(),
        "fuente_datos": "ENUT 2024, indicadores ponderados propios, R survey + Python",
        "fuente_oficial": "INEGI comunicado 121/25 p.5"
    }
    serialized = json.dumps(payload, ensure_ascii=False, allow_nan=False)
    serialized = serialized.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    result = TEMPLATE.replace("__DATA_JSON__", serialized)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(result, encoding="utf-8")
    print("MODULO ENUT GENERADO:", OUTPUT)
    print("RESULTADOS PUBLICADOS EN HTML: 24 indicadores AGREGADOS")
    print("VALIDACION NUMERICA:", validation["detalle"])
    print("SIN MICRODATOS, SIN LIBRERIAS WEB Y SIN MODIFICAR OTROS MODULOS.")


if __name__ == "__main__":
    main()
