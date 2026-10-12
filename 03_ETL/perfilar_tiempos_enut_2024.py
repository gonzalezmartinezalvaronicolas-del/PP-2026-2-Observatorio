"""Perfil exploratorio de variables derivadas de uso del tiempo, ENUT 2024.

No convierte tiempos ni interpreta valores especiales sin diccionario oficial.
No publica registros individuales ni identificadores.
"""
from __future__ import annotations
import json, zipfile
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"01_DATOS_RAW/INEGI/ENUT_2024/conjunto_de_datos_enut_2024_csv.zip"
OUT=ROOT/"08_DOCUMENTACION/auditorias/ENUT_2024/perfil_tiempos_tvar_crea.json"
FIELDS=["trab_no_rem_cuid_hog","cuid_esp_disc_enf",
 "cuid_esp_int_hog_con_cp","cuid_esp_int_hog_sin_cp",
 "trab_no_rem_hog","trab_merc_pv","activ_cuid_per"]
META=["sexo","edad","cond_disc","est_dis","upm_dis","fac_per"]
def main():
    with zipfile.ZipFile(SRC) as z:
        names=[n for n in z.namelist() if "/conjunto_de_datos/" in n.lower()
          and Path(n).stem.lower()=="conjunto_de_datos_enut_2024_tvar_crea"
          and n.lower().endswith(".csv")]
        if len(names)!=1: raise ValueError(f"No se encuentra TVAR_CREA única: {len(names)}")
        with z.open(names[0]) as f:
            d=pd.read_csv(f, usecols=FIELDS+META,dtype="string",
              keep_default_na=False,encoding="utf-8-sig",low_memory=False)
    if len(d)!=74053:raise ValueError(f"Conteo inesperado: {len(d)}")
    result={"fecha_utc":datetime.now(timezone.utc).isoformat(),
      "estado":"EXPLORACION_CODIGOS_SIN_INTERPRETAR_UNIDADES",
      "registros":len(d),"variables":{},"sexo_codigos":{}}
    result["sexo_codigos"]={str(k):int(v) for k,v in d["sexo"].value_counts().items()}
    for field in FIELDS:
        v=d[field].fillna("")
        numeric=pd.to_numeric(v.where(v.ne(""),pd.NA),errors="coerce")
        high=v.value_counts(dropna=False).head(12)
        result["variables"][field]={
           "blancos":int(v.eq("").sum()),
           "valores_distintos":int(v.nunique()),
           "valores_no_numericos_no_blancos":int((numeric.isna() & v.ne("")).sum()),
           "minimo_numerico":float(numeric.min()) if numeric.notna().any() else None,
           "maximo_numerico":float(numeric.max()) if numeric.notna().any() else None,
           "codigos_mas_frecuentes":{str(k) if str(k) else "(blanco)":int(value)
                                    for k,value in high.items()}}
        print(f"{field}: blancos={result['variables'][field]['blancos']:,}, "
              f"distintos={result['variables'][field]['valores_distintos']:,}, "
              f"rango={result['variables'][field]['minimo_numerico']}.."
              f"{result['variables'][field]['maximo_numerico']}")
    weights=pd.to_numeric(d["fac_per"],errors="coerce")
    if weights.isna().any() or weights.le(0).any():
        raise ValueError("FAC_PER invalido")
    if d["est_dis"].eq("").any() or d["upm_dis"].eq("").any():
        raise ValueError("EST_DIS o UPM_DIS vacio")
    result["advertencias"]=[
      "Verificar documentalmente formato, horas, minutos, valores especiales y tratamiento de cuidados pasivos.",
      "No interpretar cifras como horas ni sumar variables antes de verificar sus definiciones.",
      "No se obtuvieron promedios nacionales, estimadores, CV ni inferencia sobre discapacidad intelectual.",
      "Fac_per existe y es positivo, pero no se uso para estimaciones."
    ]
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("REPORTE:",OUT)
    print("SIN CALCULOS DE HORAS NI ESTIMACIONES POBLACIONALES.")
if __name__=="__main__":main()
