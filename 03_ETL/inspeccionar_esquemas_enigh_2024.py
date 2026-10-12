"""Diagnostico de encabezados y claves ENIGH 2024, sin cargar filas masivas.

Lee exclusivamente encabezados del ZIP de microdatos y escribe metadata
local. No estima indicadores, no infiere discapacidad intelectual.
"""
from __future__ import annotations
import csv, io, json, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ZIP=ROOT/"01_DATOS_RAW/INEGI/ENIGH_2024/conjunto_de_datos_enigh2024_ns_csv.zip"
OUT=ROOT/"08_DOCUMENTACION/auditorias/ENIGH_2024"
TARGET=("concentradohogar","hogares","poblacion","gastoshogar","gastospersona","ingresos","viviendas")
TOKENS=("folio","numren","factor","est_dis","upm","ing_","ingreso","gasto","salud","disc_","limit","dific","cuid","transf","edad","sexo","clave")
def main():
    if not ZIP.exists(): raise SystemExit(f"ZIP no encontrado: {ZIP}")
    records=[]
    with zipfile.ZipFile(ZIP) as z:
        for path in sorted(z.namelist()):
            if not path.lower().endswith(".csv") or "/conjunto_de_datos/" not in path.lower():
                continue
            table=Path(path).stem.replace("conjunto_de_datos_","").replace("_enigh2024_ns","")
            if table not in TARGET: continue
            with z.open(path) as f:
                reader=csv.reader(io.TextIOWrapper(f,encoding="utf-8-sig",newline=""))
                fields=next(reader)
            pick=[x for x in fields if any(t in x.lower() for t in TOKENS)]
            records.append({"tabla":table,"columnas_total":len(fields),"columnas_de_interes":pick,
                            "columnas_completas":fields})
            print(f"\\n{table.upper()} | {len(fields)} columnas")
            print("  CAMPOS DE INTERES:",", ".join(pick) or "(ninguno detectado)")
            print("  CABECERA COMPLETA:",", ".join(fields))
    missing=set(TARGET)-{x["tabla"] for x in records}
    if missing: raise ValueError(f"Faltan tablas esperadas: {sorted(missing)}")
    OUT.mkdir(parents=True,exist_ok=True)
    dest=OUT/"esquemas_prioritarios_enigh_2024.json"
    dest.write_text(json.dumps({"estado":"DIAGNOSTICO_DE_ESQUEMAS_SIN_ESTIMACIONES",
                    "tablas":records},ensure_ascii=False,indent=2),encoding="utf-8")
    print("\\nREPORTE:",dest)
    print("SIGUIENTE: confirmar llaves, factores y definiciones mediante diccionarios INEGI.")
if __name__=="__main__":
    main()
