"""ENUT 2024: descriptivos muestrales preliminares de cuidados especiales.

Sin inferencia poblacional, sin microdatos exportados y sin indicadores de
discapacidad intelectual. Los valores de variables derivadas se reportan
como registros numéricos compatibles con horas, condicionados a ficha oficial.
"""
import json, zipfile
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"01_DATOS_RAW/INEGI/ENUT_2024/conjunto_de_datos_enut_2024_csv.zip"
OUT=ROOT/"08_DOCUMENTACION/auditorias/ENUT_2024/comparacion_cuidados_sexo_exploratoria.json"
VARS=["cuid_esp_disc_enf","trab_no_rem_cuid_hog",
      "cuid_esp_int_hog_con_cp","cuid_esp_int_hog_sin_cp"]
KEEP=["sexo","edad","fac_per"]+VARS

def summary(x):
    n=len(x)
    positive=x.gt(0)
    valid=x.notna() & x.ge(0)
    pv=x[positive]
    return {"n_registros":n,"n_validos":int(valid.sum()),
      "n_positivos":int(positive.sum()),"porcentaje_positivo_sin_ponderar":
      round(float(positive.mean()*100),3) if n else None,
      "n_mayores_168":int(x.gt(168).sum()),
      "media_sobre_todos_sin_ponderar":float(x.mean()) if n else None,
      "mediana_sobre_positivos_sin_ponderar":float(pv.median()) if len(pv) else None,
      "media_sobre_positivos_sin_ponderar":float(pv.mean()) if len(pv) else None}
def main():
    with zipfile.ZipFile(SRC) as z:
        names=[n for n in z.namelist() if n.lower().endswith(".csv")
               and Path(n).stem.lower()=="conjunto_de_datos_enut_2024_tvar_crea"
               and "/conjunto_de_datos/" in n.lower()]
        if len(names)!=1:raise ValueError(f"Tabla TVAR_CREA: {len(names)} archivos")
        with z.open(names[0]) as f:
            d=pd.read_csv(f,usecols=KEEP,dtype="string",
                          keep_default_na=False,encoding="utf-8-sig")
    if len(d)!=74053:raise ValueError(f"Conteo inesperado {len(d)}")
    if set(d.sexo.unique())-{"1","2"}:raise ValueError("Codigos sexo inesperados")
    for v in VARS:
        d[v]=pd.to_numeric(d[v],errors="coerce")
        if d[v].isna().any() or d[v].lt(0).any():
            raise ValueError(f"Valor invalido: {v}")
    result={"fecha_utc":datetime.now(timezone.utc).isoformat(),
      "estado":"DESCRIPTIVOS_MUESTRALES_SIN_PONDERAR",
      "universo_analizado":"registros TVAR_CREA (personas entrevistadas, ENUT 2024)",
      "medidas":{},"grupos":{}}
    for v in VARS:result["medidas"][v]=summary(d[v])
    for sex,name in [("1","hombres"),("2","mujeres")]:
        subset=d.loc[d.sexo==sex]
        result["grupos"][name]={"n":len(subset),
          "medidas":{v:summary(subset[v]) for v in VARS}}
        print(f"{name}: n={len(subset):,}, "
              f"cuidados especiales >0={result['grupos'][name]['medidas']['cuid_esp_disc_enf']['n_positivos']:,}")
    result["advertencias"]=[
      "Descriptivos sin ponderar: no equivalen a población nacional ni a indicadores oficiales.",
      "Cuid_esp_disc_enf incluye enfermedad o discapacidad, no diagnostica discapacidad intelectual.",
      "Validar el significado exacto de la variable y universo en el diccionario TVAR_CREA.",
      "No sumar con/sin cuidados pasivos sin confirmar definición y posibles solapamientos.",
      "Valores >168 podrían expresar tiempos superpuestos u otro concepto: no eliminarlos automáticamente.",
      "Las cifras solo se interpretarán como horas semanales tras confirmación documental.",
      "No se exportan llaves ni registros individuales."
    ]
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("REPORTE:",OUT)
if __name__=="__main__":main()
