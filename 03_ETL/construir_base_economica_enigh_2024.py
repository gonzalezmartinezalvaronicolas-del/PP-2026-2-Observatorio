"""ENIGH 2024: construir base preliminar por HOGAR sin suponer codigos clinicos.

Carga solo poblacion/concentradohogar del ZIP original, comprueba cardinalidades,
agrega variables de composicion y conserva ingresos/gastos en su unidad original.
NO calcula estimaciones nacionales ni interpreta disc_* como discapacidad
intelectual. El Parquet local contiene microdatos: NO subirlo a GitHub.
"""
from __future__ import annotations
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/"01_DATOS_RAW/INEGI/ENIGH_2024/conjunto_de_datos_enigh2024_ns_csv.zip"
DEST = ROOT/"05_BASE_ANALITICA/ENIGH_2024/hogares_economica_preliminar.parquet"
REPORT = ROOT/"08_DOCUMENTACION/auditorias/ENIGH_2024/base_economica_preliminar.json"
HK = ["folioviv","foliohog"]
PERSON_FIELDS = HK + ["numren","edad","sexo","disc_ver","disc_oir","disc_brazo",
    "disc_camin","disc_apren","disc_vest","disc_habla","disc_acti"]
HOUSE_FIELDS = HK + ["factor","est_dis","upm","entidad" if False else "ubica_geo",
    "tot_integ","ing_cor","gasto_mon","salud","cuidados","alimentos"]
DISC_FIELDS = [x for x in PERSON_FIELDS if x.startswith("disc_")]

def get_name(z, table):
    found = [n for n in z.namelist() if n.lower().endswith(".csv")
       and "/conjunto_de_datos/" in n.lower()
       and Path(n).stem.lower().replace("conjunto_de_datos_","")
           .replace("_enigh2024_ns","")==table]
    if len(found)!=1:
        raise ValueError(f"Esperaba un archivo {table}: {len(found)}")
    return found[0]

def load(z, table, cols):
    with z.open(get_name(z,table)) as f:
        return pd.read_csv(f, usecols=cols, dtype="string",
            keep_default_na=False, encoding="utf-8-sig",low_memory=False)

def main():
    if not SOURCE.exists(): raise SystemExit(f"No se encuentra: {SOURCE}")
    with zipfile.ZipFile(SOURCE) as z:
        h=load(z,"concentradohogar",HOUSE_FIELDS)
        p=load(z,"poblacion",PERSON_FIELDS)
    if len(h)!=91414 or len(p)!=308598:
        raise ValueError("Conteos alterados respecto a auditoria de ENIGH")
    if h.duplicated(HK).any() or p.duplicated(HK+["numren"]).any():
        raise ValueError("Claves no unicas")
    for k in HK:
        if h[k].eq("").any() or p[k].eq("").any():
            raise ValueError(f"Clave vacia: {k}")
    for field in ["factor","est_dis","upm"]:
        if h[field].eq("").any(): raise ValueError(f"Campo diseno vacio: {field}")
    agg=(p.groupby(HK,dropna=False,sort=False)
          .agg(personas_registradas=("numren","size"),
               edades_informadas=("edad",lambda s: int(s.str.fullmatch(r"\d+").fillna(False).sum())))
          .reset_index())
    combined=h.merge(agg,on=HK,how="left",validate="one_to_one",indicator=True)
    if not combined["_merge"].eq("both").all() or len(combined)!=len(h):
        raise ValueError("No coinciden hogares-personas tras merge")
    combined=combined.drop(columns="_merge")
    for field in ("ing_cor","gasto_mon","salud","cuidados","alimentos","factor"):
        numeric=pd.to_numeric(combined[field],errors="coerce")
        combined[field+"_num"]=numeric
    # Distribuciones de codigo sin clasificar; nunca se agregan niveles sin catalogo.
    code_profiles={}
    for var in DISC_FIELDS:
        vc=p[var].fillna("").value_counts(dropna=False)
        code_profiles[var]={str(k) if str(k) else "(blanco)":int(v)
                            for k,v in vc.items()}
    if combined["factor_num"].isna().any() or combined["factor_num"].le(0).any():
        raise ValueError("Factor de hogar invalido")
    if not combined["personas_registradas"].ge(1).all():
        raise ValueError("Hogares sin integrantes")
    DEST.parent.mkdir(parents=True,exist_ok=True)
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    combined.to_parquet(DEST,index=False)
    report={
      "fecha_utc":datetime.now(timezone.utc).isoformat(),
      "estado":"BASE_PRELIMINAR_SIN_ESTIMACIONES",
      "fuente":"ENIGH 2024 Nueva Serie CSV",
      "hogares":int(len(combined)),
      "personas":int(len(p)),
      "filas_base":int(len(combined)),
      "columnas_base":list(combined.columns),
      "perfiles_codigos_dificultad_funcional":code_profiles,
      "advertencias":[
        "Los codigos de disc_* son perfiles descriptivos de respuesta y no diagnosticos.",
        "No asignar categoria de discapacidad antes de validar catalogos/cuestionarios.",
        "Concentradohogar presenta montos agregados; verificar periodo y definiciones oficiales.",
        "No son estimaciones ponderadas ni nacionales.",
        "El parquet contiene informacion de microdatos y permanece local.",
        "El numero de personas se usa solo para validar vinculacion; comparar con tot_integ segun diccionario."
      ]}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"BASE PRELIMINAR ENIGH: {len(combined):,} hogares; {len(p):,} personas asociadas.")
    print(f"PARQUET LOCAL: {DEST}")
    print(f"REPORTE: {REPORT}")
    print("CODIGOS DE DIFICULTAD FUNCIONAL: ver reporte, SIN interpretar.")
    print("NO SE GENERARON ESTIMACIONES POBLACIONALES.")

if __name__=="__main__":
    main()
