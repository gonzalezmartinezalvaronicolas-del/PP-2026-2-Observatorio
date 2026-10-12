"""ENUT 2024: comparación exploratoria correcta de cuidados dentro del hogar.

Fuente conceptual: descriptor INEGI ENUT 2024, hoja TVAR_CREA,
filas 45-47 y 58. No se aplican ponderaciones ni se interpretan
como cifras oficiales los promedios obtenidos.
"""
from pathlib import Path
from datetime import datetime,timezone
import json,zipfile
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
ZIP=ROOT/"01_DATOS_RAW/INEGI/ENUT_2024/conjunto_de_datos_enut_2024_csv.zip"
OUT=ROOT/"08_DOCUMENTACION/auditorias/ENUT_2024/cuidados_en_hogar_por_sexo_corregido.json"
VARS={
 "cuid_esp_int_hog_sin_cp":"Cuidados especiales a integrantes del hogar, sin pasivos, con emocionales",
 "cuid_esp_int_hog_con_cp":"Cuidados especiales a integrantes del hogar, con pasivos y emocionales",
 "trab_no_rem_cuid_hog":"Cuidados no remunerados a integrantes del hogar, sin pasivos, con emocionales",
 "cuid_esp_disc_enf":"Ayuda gratuita a otros hogares familiares por enfermedad o discapacidad"
}
def resumir(col):
    pos=col[col>0]
    return {"n_personas":int(len(col)),"n_positivos":int((col>0).sum()),
            "porcentaje_positivo_muestral":round(float((col>0).mean()*100),4),
            "media_todos_unidad_original":float(col.mean()),
            "media_positivos_unidad_original":float(pos.mean()) if len(pos) else None,
            "mediana_positivos_unidad_original":float(pos.median()) if len(pos) else None,
            "n_mayor_168":int((col>168).sum())}
def main():
    with zipfile.ZipFile(ZIP) as z:
        names=[n for n in z.namelist() if "/conjunto_de_datos/" in n.lower()
               and Path(n).stem.lower()=="conjunto_de_datos_enut_2024_tvar_crea"]
        if len(names)!=1:raise ValueError("No se encontro TVAR_CREA unica")
        with z.open(names[0]) as f:
            data=pd.read_csv(f,usecols=["sexo",*VARS],dtype="string",
                         encoding="utf-8-sig",keep_default_na=False)
    if len(data)!=74053:raise ValueError("Filas inesperadas")
    if set(data["sexo"].unique())!={"1","2"}:raise ValueError("Codigos sexo inesperados")
    for col in VARS:
        data[col]=pd.to_numeric(data[col],errors="coerce")
        if data[col].isna().any() or data[col].lt(0).any():
            raise ValueError(f"Variable invalida: {col}")
    output={"fecha_utc":datetime.now(timezone.utc).isoformat(),
       "estado":"DESCRIPTIVOS_CORREGIDOS_SIN_PONDERAR",
       "fuente_definiciones":"INEGI ENUT 2024 descriptor TVAR_CREA filas 45-47,58",
       "variables":VARS,"grupos":{}}
    for key,sub in [("total",data),("hombres",data[data.sexo=="1"]),
                    ("mujeres",data[data.sexo=="2"])]:
        output["grupos"][key]={"personas":len(sub),
            "indicadores":{col:resumir(sub[col]) for col in VARS}}
        print(key,":",len(sub),"personas")
        for col in ("cuid_esp_int_hog_sin_cp","cuid_esp_int_hog_con_cp"):
            val=output["grupos"][key]["indicadores"][col]
            print(" ",col,":",val["n_positivos"],"positivos",
                  "media positivos=",round(val["media_positivos_unidad_original"] or 0,3))
    output["limitaciones"]=[
       "Valores no ponderados: no generalizar a poblacion nacional ni compararlos directamente con boletines INEGI.",
       "El descriptor distingue cuidados a integrantes del propio hogar y ayuda a otros hogares familiares.",
       "CUID_ESP_DISC_ENF NO es cuidados a integrantes del propio hogar.",
       "No sumar indicadores con y sin cuidados pasivos; hay superposiciones.",
       "No atribuir los cuidados a discapacidad intelectual especificamente.",
       "Confirmar periodicidad, universo y tecnica oficial antes de rotular unidades como horas semanales o estimar varianzas."
    ]
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print("REPORTE:",OUT)
if __name__=="__main__":main()
