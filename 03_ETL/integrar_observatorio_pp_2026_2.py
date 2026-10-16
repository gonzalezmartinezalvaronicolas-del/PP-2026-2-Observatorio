"""Crea portada integrada y módulo exploratorio ENIGH del PP 2026-2.

No altera HTML de ENASIC ni ENUT y solo incorpora agregados del JSON ENIGH.
ENIGH sigue sin ponderar: nunca denominar sus medias/medianas estimaciones nacionales.
Uso en Windows CMD:
  .venv\Scripts\python.exe 03_ETL/integrar_observatorio_pp_2026_2.py
  .venv\Scripts\python.exe 03_ETL/integrar_observatorio_pp_2026_2.py --overwrite
"""
from __future__ import annotations

import argparse
import html
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "06_OBSERVATORIO"
SOURCE = ROOT / "08_DOCUMENTACION/auditorias/ENIGH_2024/comparacion_economica_exploratoria.json"
ENIGH = OUT / "enigh_2024_economia.html"
PORTAL = OUT / "index.html"
SIGNATURE = "<!-- PP2026_GENERADO_INTEGRACION -->"

GROUPS = {
    "total_hogares": "Todos los hogares",
    "alguna_dificultad_grave_en_tres_actividades": "Con dificultad funcional grave en alguna de las tres actividades",
    "sin_dificultad_grave_en_tres_actividades": "Hogares restantes",
    "alguna_dificultad_recordar_concentrarse": "Dificultad grave para recordar o concentrarse",
    "alguna_dificultad_hablar_comunicarse": "Dificultad grave para hablar o comunicarse",
    "alguna_dificultad_actividades_cotidianas": "Dificultad grave para realizar actividades cotidianas",
}
VARIABLES = {
    "ingreso_corriente": "Ingreso corriente",
    "gasto_monetario": "Gasto monetario",
    "gasto_salud": "Gasto en salud",
    "gasto_alimentacion": "Gasto en alimentación",
    "gasto_cuidados_personales": "Gasto en cuidados personales (NO cuidado no remunerado)",
}
METRICS = {"mediana_sin_ponderar": "Mediana", "media_sin_ponderar": "Media"}

CSS = r"""
:root{--navy:#17283f;--ink:#203047;--muted:#5b6d83;--line:#dce4ee;--bg:#f4f6fa;--gold:#c99a53;--blue:#4478ab}
*{box-sizing:border-box}body{margin:0;background:var(--bg);font:15px/1.55 system-ui,"Segoe UI",sans-serif;color:var(--ink)}
a{color:#245b9b}.wrap{max-width:1100px;margin:auto;padding:0 24px}header{background:var(--navy);color:#f9fcff;padding:30px 0 42px}
.kicker{color:#edcb92;letter-spacing:.16em;text-transform:uppercase;font-weight:750;font-size:.76rem}
h1{font-size:clamp(1.9rem,4.3vw,3rem);letter-spacing:-.035em;line-height:1.17;margin:11px 0}
h2{font-size:1.27rem;letter-spacing:-.02em;margin:0 0 9px}h3{font-size:1.05rem;margin:0 0 6px}
p{margin-top:0}.lead{color:var(--muted);font-size:.92rem}.intro{max-width:780px;color:#cdd7e7}
nav{display:flex;justify-content:space-between;align-items:center;gap:20px;font-size:.82rem}
nav a{color:#e7c68d;text-decoration:none}.row{display:grid;grid-template-columns:1fr 1fr;gap:18px}
section{margin:25px auto}.panel,.card,.stat{background:white;border:1px solid var(--line);border-radius:13px;box-shadow:0 6px 18px #16284008}
.panel{padding:24px}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.card{padding:23px;display:flex;flex-direction:column;gap:10px}
.card a{margin-top:auto;font-weight:750;text-decoration:none}.tag{font-size:.77rem;color:#596b7e;background:#eef3f8;border-radius:30px;padding:5px 10px;align-self:flex-start}
.gridstats{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:-24px;position:relative}
.stat{padding:18px}.big{font-size:1.63rem;font-weight:750;letter-spacing:-.03em}.label{font-size:.8rem;color:var(--muted)}
.warning{background:#fff9ef;border-left:3px solid #d5a35c;color:#745734;padding:12px 15px;border-radius:4px;font-size:.89rem}
.controls{display:grid;grid-template-columns:1.4fr .7fr;gap:14px;margin:16px 0}
label{font-weight:700;font-size:.84rem;color:var(--muted);display:flex;flex-direction:column;gap:5px}
select{background:white;border:1px solid #c9d5e4;border-radius:8px;padding:11px;font:inherit;color:var(--ink);max-width:100%}
.bars{margin-top:23px}.barrow{margin:17px 0}.barname{display:flex;justify-content:space-between;gap:15px;font-size:.92rem;font-weight:650}
.track{background:#e9eef4;height:26px;border-radius:6px;margin:6px 0;overflow:hidden}
.fill{height:100%;background:var(--blue);border-radius:6px}.fill.gold{background:var(--gold)}
.note{font-size:.79rem;color:var(--muted)}
table{width:100%;border-collapse:collapse}th,td{padding:12px;border-bottom:1px solid var(--line);text-align:left}
th{background:#f4f7fb;color:var(--muted)}td.num{text-align:right;font-variant-numeric:tabular-nums}
footer{padding:32px 0 40px;color:#63748a;font-size:.82rem}
@media(max-width:750px){.cards,.row,.gridstats{grid-template-columns:1fr}.controls{grid-template-columns:1fr}}
"""

def safe_json(payload: object) -> str:
    s = json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    return s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

def source_data() -> dict:
    if not SOURCE.exists():
        raise SystemExit("No se encontro el JSON exploratorio de ENIGH: " + str(SOURCE))
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    if raw.get("estado") != "COMPARACION_DESCRIPTIVA_SIN_PONDERAR":
        raise ValueError("Estado inesperado de los resultados ENIGH")
    if raw.get("hogares_muestra") != 91414 or raw.get("personas_muestra") != 308598:
        raise ValueError("Totales ENIGH distintos del inventario auditado")
    group_data = raw.get("grupos", {})
    if set(group_data) != set(GROUPS):
        raise ValueError("Faltan grupos o hay grupos inesperados")
    clean = {}
    for group in GROUPS:
        item = group_data[group]
        n = int(item["hogares_muestra"])
        if n < 1 or n > 91414:
            raise ValueError("Conteo de hogares incorrecto")
        measures = item.get("variables", {})
        if set(measures) != set(VARIABLES):
            raise ValueError("Variables economicas inesperadas")
        values = {}
        for var in VARIABLES:
            fields = measures[var]
            values[var] = {}
            for metric in METRICS:
                v = float(fields[metric])
                if not math.isfinite(v) or v < 0:
                    raise ValueError(f"Valor economico invalido {group}/{var}/{metric}")
                values[var][metric] = v
        clean[group] = {"n": n, "variables": values}
    if clean["alguna_dificultad_grave_en_tres_actividades"]["n"] + clean["sin_dificultad_grave_en_tres_actividades"]["n"] != 91414:
        raise ValueError("Los dos grupos generales no completan la muestra")
    return {"groups": clean, "labels": GROUPS, "variables": VARIABLES,
            "metrics": METRICS, "total_hogares":91414,"total_personas":308598}

def page(body: str, title: str, payload: dict | None = None) -> str:
    embedded = (f'<script type="application/json" id="evidence">{safe_json(payload)}</script>'
                if payload is not None else "")
    return f"""<!DOCTYPE html>
{SIGNATURE}
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>{CSS}</style></head><body>
{body}{embedded}
</body></html>"""

def enigh_page(payload: dict) -> str:
    body = r"""
<header><div class="wrap"><nav><span>PP 2026-2 · Observatorio</span>
<a href="index.html">← Volver al Observatorio</a></nav>
<div class="kicker" style="margin-top:30px">ENIGH 2024 · Sostenibilidad económica</div>
<h1>Condiciones económicas y dificultades funcionales</h1>
<p class="intro">Comparaciones descriptivas de hogares de la ENIGH 2024 Nueva Serie. Los resultados son exploratorios; aún no incorporan el diseño probabilístico para estimar valores poblacionales.</p>
</div></header>
<main class="wrap">
<div class="gridstats">
<div class="stat"><div class="big">91,414</div><div class="label">Hogares observados en la muestra</div></div>
<div class="stat"><div class="big">8,125</div><div class="label">Hogares con alguna dificultad funcional grave entre tres actividades</div></div>
<div class="stat"><div class="big">Sin ponderar</div><div class="label">Estado estadístico: no representan estimaciones nacionales</div></div>
</div>
<section class="panel"><h2>Comparar indicadores económicos</h2>
<p class="lead">Las diferencias observadas son descriptivas de la muestra y no establecen causalidad. Los montos conservan el periodo del concentrado original, que debemos confirmar con INEGI antes de etiquetarlo.</p>
<div class="warning"><strong>Interpretación obligatoria:</strong> las dificultades para recordar/concentrarse, hablar o realizar actividades cotidianas NO identifican discapacidad intelectual o síndrome de Down. El rubro «cuidados personales» es gasto monetario en cuidado personal, NO cuidado no remunerado.</div>
<div class="controls">
<label>Variable económica<select id="variable">
<option value="ingreso_corriente">Ingreso corriente</option>
<option value="gasto_monetario">Gasto monetario</option>
<option value="gasto_salud">Gasto en salud</option>
<option value="gasto_alimentacion">Gasto en alimentación</option>
<option value="gasto_cuidados_personales">Gasto en cuidados personales</option>
</select></label>
<label>Medida descriptiva<select id="metric"><option value="mediana_sin_ponderar">Mediana muestral</option>
<option value="media_sin_ponderar">Media muestral</option></select></label>
</div>
<div class="bars" id="bars"></div><p class="note" id="explain"></p>
</section>
<section class="row">
<div class="panel"><h2>Grupos comparados</h2><p class="lead">Los grupos generales dividen la muestra de hogares. Las tres categorías por tipo de dificultad se superponen: no se deben sumar entre sí.</p>
<p><b>8,125 hogares</b> con alguna persona que respondió mucha dificultad o imposibilidad en al menos una de las tres actividades.</p>
<p><b>83,289 hogares restantes</b>, que pueden incluir dificultad leve o respuesta no especificada.</p>
</div>
<div class="panel"><h2>¿Qué falta antes de publicar?</h2>
<p class="lead">Confirmar documentalmente el periodo de referencia y definiciones de montos, aplicar factor y diseño muestral, estimar errores y controlar diferencias de composición de hogares.</p>
<p>Fuente primaria: <a href="https://www.inegi.org.mx/programas/enigh/nc/2024/" target="_blank" rel="noopener noreferrer">INEGI, ENIGH 2024 Nueva Serie ↗</a>.</p>
</div></section>
<section class="panel"><h2>Tablero metodológico</h2>
<p>Este módulo utiliza únicamente los agregados de <code>comparacion_economica_exploratoria.json</code>. Es una exploración inicial de la dimensión económica; no usa información de la asociación ni fusiona individuos con ENUT o ENASIC.</p>
<div class="warning">Los resultados nacionales de ENUT que aparecen en otro módulo tienen un nivel de validación diferente. No trasladar las conclusiones de una encuesta a la otra.</div>
</section>
</main><footer class="wrap">PP 2026-2 · Módulo exploratorio ENIGH · No equivale a estimaciones oficiales publicadas por INEGI.</footer>
<script>
(function(){
"use strict";
const data=JSON.parse(document.getElementById("evidence").textContent);
const v=document.getElementById("variable"),m=document.getElementById("metric");
const IDs=["total_hogares","alguna_dificultad_grave_en_tres_actividades","sin_dificultad_grave_en_tres_actividades",
"alguna_dificultad_recordar_concentrarse","alguna_dificultad_hablar_comunicarse","alguna_dificultad_actividades_cotidianas"];
const fmt=new Intl.NumberFormat("es-MX",{maximumFractionDigits:2,minimumFractionDigits:2});
function escapeHTML(s){return String(s).replace(/[&<>"']/g,x=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[x]));}
function render(){
 const values=IDs.map(id=>({id:id,n:data.groups[id].n,value:data.groups[id].variables[v.value][m.value]}));
 const max=Math.max(...values.map(x=>x.value))*1.12||1;
 document.getElementById("bars").innerHTML=values.map((x,i)=>'<div class="barrow"><div class="barname"><span>'+
 escapeHTML(data.labels[x.id])+'</span><span>$'+fmt.format(x.value)+'</span></div><div class="track"><div class="fill '+(i===1?"gold":"")+
 '" style="width:'+Math.max(0,Math.min(100,x.value/max*100))+'%"></div></div><div class="note">'+x.n.toLocaleString("es-MX")+
 ' hogares en la muestra</div></div>').join("");
 document.getElementById("explain").textContent="Medida seleccionada: "+data.metrics[m.value]+
 ". No se utilizó el factor de expansión. Las categorías por tipo de dificultad se superponen. Los montos NO están etiquetados como mensuales o trimestrales.";
}
v.addEventListener("change",render);m.addEventListener("change",render);render();
})();
</script>
"""
    # Place data script ahead of JS so that it can be parsed synchronously.
    script_start = body.find("<script>\n(function(){")
    embedded = f'<script type="application/json" id="evidence">{safe_json(payload)}</script>\n'
    return page(body[:script_start]+embedded+body[script_start:], "ENIGH 2024 | Economía y condiciones funcionales")

def portal_page() -> str:
    modules = [
        ("ENASIC 2022","Personas cuidadoras y carga de cuidados",
         "Prototipo previo; resultados y límites metodológicos por revisar.",
         "prototipo_enasic_2022.html","Prototipo local existente"),
        ("ENIGH 2024","Sostenibilidad económica de los hogares",
         "Comparaciones económicas de la muestra, sin ponderar; sin inferencia poblacional.",
         "enigh_2024_economia.html","Exploratorio"),
        ("ENUT 2024","Tiempo, cuidados y trabajo no remunerado",
         "24 indicadores propios ponderados y cotejados numéricamente en R y Python; contraste puntual con INEGI.",
         "enut_2024_cuidados.html","Ponderado, con validación numérica")
    ]
    cards = ""
    for heading,subtitle,detail,filename,status in modules:
        if (OUT/filename).is_file() or filename == ENIGH.name:
            link=f'<a href="{html.escape(filename)}">Abrir módulo →</a>'
        else:
            link='<span class="note">Pendiente: generar primero el HTML local</span>'
        cards += (f'<article class="card"><span class="tag">{html.escape(status)}</span><h2>{html.escape(heading)}</h2>'
                  f'<h3>{html.escape(subtitle)}</h3><p class="lead">{html.escape(detail)}</p>{link}</article>')
    body = f"""
<header><div class="wrap"><nav><span>PP · 2026-2</span><span>Observatorio de autonomía y cuidados</span></nav>
<div class="kicker" style="margin-top:40px">DATOS → EVIDENCIA → DECISIÓN → PROGRAMA</div>
<h1>Tres fuentes. Tres perspectivas.<br>Una propuesta social basada en evidencia.</h1>
<p class="intro">Punto de entrada a los análisis de ENASIC 2022, ENIGH 2024 y ENUT 2024. Cada encuesta conserva su universo, sus unidades y su nivel de validación. El territorio y el trabajo con la asociación están pendientes de confirmación.</p>
</div></header>
<main class="wrap">
<section><div class="cards">{cards}</div></section>
<section class="panel"><h2>Cómo se conectan las dimensiones</h2>
<div class="row"><div><h3>Preguntas que estamos investigando</h3><p>¿Qué necesidades y consecuencias enfrentan las personas cuidadoras? ¿Cómo se reflejan algunas dificultades funcionales en condiciones económicas? ¿Cómo se distribuye el tiempo dedicado al cuidado?</p></div>
<div><h3>Del análisis a la intervención</h3><p>La evidencia cuantitativa ayuda a orientar preguntas. Para diseñar un programa social necesitamos además validar necesidades con la organización aliada y acordar territorio, consentimiento y protección de datos.</p></div></div>
<div class="warning">Ninguna de estas encuestas identifica de forma exclusiva a personas con discapacidad intelectual o síndrome de Down. Las conclusiones no pueden extrapolarse automáticamente a una asociación específica.</div>
</section>
<section class="panel"><h2>Fuente y transparencia</h2>
<p>Referencia institucional: <a href="https://www.inegi.org.mx/" target="_blank" rel="noopener noreferrer">INEGI</a>. Las estadísticas oficiales que usemos en diapositivas deberán citar el documento, fecha y página; los cálculos del equipo se identifican por separado.</p>
<p>El Observatorio no fusiona registros individuales de encuestas diferentes ni publica los microdatos locales.</p>
</section></main>
<footer class="wrap">Proyecto académico PP 2026-2 · Versión local para revisión y presentación.</footer>
"""
    return page(body, "Observatorio PP 2026-2 | Inicio")

def write_generated(path: Path, content: str, overwrite: bool):
    if path.exists():
        previous = path.read_text(encoding="utf-8")
        if SIGNATURE not in previous[:200]:
            raise SystemExit("Se protege un archivo HTML ajeno al generador: " + str(path))
        if not overwrite:
            raise SystemExit("La página ya existe. Para regenerar usa --overwrite: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print("GENERADO:", path)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true",
                        help="Regenerar solo los HTML creados por este script")
    args=parser.parse_args()
    payload=source_data()
    # Prever conflictos antes de escribir para evitar un estado a medias.
    for path in (ENIGH, PORTAL):
        if path.exists():
            previous=path.read_text(encoding="utf-8")
            if SIGNATURE not in previous[:200] or not args.overwrite:
                raise SystemExit("Archivo destino protegido o ya existente: "+str(path))
    write_generated(ENIGH, enigh_page(payload), args.overwrite)
    write_generated(PORTAL, portal_page(), args.overwrite)
    print("OBSERVATORIO: portada y modulo ENIGH creados.")
    print("ENASIC y ENUT permanecen INTACTOS.")
    print("ENIGH sigue SIN PONDERAR, no equivale a cifras nacionales.")

if __name__ == "__main__":
    main()
