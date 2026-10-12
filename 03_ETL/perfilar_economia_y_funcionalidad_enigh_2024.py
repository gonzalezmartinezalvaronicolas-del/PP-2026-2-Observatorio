"""ENIGH 2024: perfil de hogares y controles previos a indicadores.

Clasifica respuestas funcionales solo de forma exploratoria con los codigos
1/2/3/4 verificados en descripcion oficial ENIGH 2024. No interpreta como
diagnosticos ni como discapacidad intelectual. Revisa ingresos y gastos.
No genera microdatos nuevos ni cifras poblacionales.
"""
from pathlib import Path
import zipfile
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"05_BASE_ANALITICA/ENIGH_2024/hogares_economica_preliminar.parquet"
ZIP=ROOT/"01_DATOS_RAW/INEGI/ENIGH_2024/conjunto_de_datos_enigh2024_ns_csv.zip"
OUT=ROOT/"08_DOCUMENTACION/auditorias/ENIGH_2024"
KEY=["folioviv","foliohog"]
VARS=["disc_apren","disc_habla","disc_acti"]
ECON=["ing_cor_num","gasto_mon_num","salud_num","cuidados_num","alimentos_num"]

def main():
    h=pd.read_parquet(BASE)
    if len(h)!=91414 or h.duplicated(KEY).any(): raise ValueError("Base hogar inesperada")
    with zipfile.ZipFile(ZIP) as z:
        names=[n for n in z.namelist() if n.lower().endswith("/conjunto_de_datos/conjunto_de_datos_poblacion_enigh2024_ns.csv")]
        if len(names)!=1:
            names=[n for n in z.namelist() if "/conjunto_de_datos/" in n.lower() and n.lower().endswith(".csv") and "poblacion" in Path(n).stem.lower()]
        if len(names)!=1: raise ValueError("No se identificó CSV poblacion único")
        with z.open(names[0]) as f:
            p=pd.read_csv(f, usecols=KEY+["numren","edad"]+VARS, dtype="string",keep_default_na=False)
    if len(p)!=308598: raise ValueError("Conteo de personas inesperado")
    if p.duplicated(KEY+["numren"]).any(): raise ValueError("Clave persona duplicada")
    result={"estado":"PERFIL_EXPLORATORIO_SIN_PONDERAR",
      "hogares_base":len(h), "personas_base":len(p),"variables_economicas":{},
      "codigos_funcionales":{},"resumen_hogares":{},
      "advertencias":[
        "Conteos muestrales, no estimaciones nacionales.",
        "3 y 4 señalan mucha dificultad o imposibilidad funcional, no diagnóstico intelectual.",
        "Se conserva & como no especificado; no inferir ausencia de dificultad.",
        "Cuidados en concentradohogar es gasto en cuidados personales, no cuidados no remunerados.",
        "Pendiente verificar periodo de cada monto y metodología de estimadores por subdominio.",
        "No publicar como indicador oficial ni combinar individuos con otras encuestas."
      ]}
    for var in ECON:
        x=pd.to_numeric(h[var],errors="coerce")
        result["variables_economicas"][var]={
          "validos":int(x.notna().sum()),"nulos":int(x.isna().sum()),
          "negativos":int((x<0).sum()),
          "ceros":int((x==0).sum()),
          "minimo":float(x.min()) if x.notna().any() else None,
          "maximo":float(x.max()) if x.notna().any() else None}
    for var in VARS:
        counts=p[var].value_counts(dropna=False)
        result["codigos_funcionales"][var]={str(k):int(v) for k,v in counts.items()}
        mask=p[var].isin(["3","4"])
        any_home=(p.loc[mask,KEY].drop_duplicates())
        if len(any_home)==0: n=0
        else:
            n=int(any_home.merge(h[KEY],on=KEY,how="inner").shape[0])
        result["resumen_hogares"][var+"_alguna_persona_3_o_4"]={
          "hogares_muestrales":n,
          "proporcion_muestral":n/len(h)}
    OUT.mkdir(parents=True,exist_ok=True)
    f=OUT/"perfil_economico_funcional_preliminar.json"
    f.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"PERFIL ENIGH: {len(h):,} hogares y {len(p):,} personas.")
    for k,v in result["resumen_hogares"].items():
        print(f"{k}: {v['hogares_muestrales']:,} hogares de muestra ({v['proporcion_muestral']:.2%}; SIN PONDERAR)")
    for k,v in result["variables_economicas"].items():
        print(f"{k}: nulos={v['nulos']}; negativos={v['negativos']}; ceros={v['ceros']}")
    print("REPORTE:",f)
    print("NO SON CIFRAS POBLACIONALES NI DIAGNOSTICOS DE DISCAPACIDAD INTELECTUAL.")

if __name__=="__main__":
    main()
