"""Diagnóstico no destructivo de posibles claves compuestas ENUT 2024.

Lee únicamente identificadores de TSDEM, TMODULO y TVAR_CREA desde ZIP.
Presenta conteos agregados, sin exponer llaves ni microdatos.
"""
from pathlib import Path
import json,zipfile
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/"01_DATOS_RAW/INEGI/ENUT_2024/conjunto_de_datos_enut_2024_csv.zip"
OUT=ROOT/"08_DOCUMENTACION/auditorias/ENUT_2024/diagnostico_claves_personas.json"
TABLES=["tsdem","tmodulo","tvar_crea"]
CANDIDATES=[
 ["llavesde"],["llavemod"],["llavehog","llavesde"],["llavehog","llavemod"],
 ["llavehog","n_ren"],["llaveviv","llavehog","n_ren"],
 ["control","viv_sel","hogar","n_ren"],["llavemod","n_ren"],
 ["llavehog","llavemod","n_ren"]]
COLS=["llavesde","llavemod","llaveviv","llavehog","control","viv_sel","hogar","n_ren"]
def member(z,t):
    candidates=[n for n in z.namelist() if "/conjunto_de_datos/" in n.lower()
       and n.lower().endswith(".csv") and
       Path(n).stem.lower().replace("conjunto_de_datos_enut_2024_","")==t]
    if len(candidates)!=1: raise ValueError(f"{t}: {len(candidates)} CSV encontrados")
    return candidates[0]
def main():
    data={}
    with zipfile.ZipFile(ARCHIVE) as z:
        for t in TABLES:
            with z.open(member(z,t)) as f:
                # Cargar únicamente columnas presentes de entre las candidatas
                d=pd.read_csv(f,dtype="string",usecols=lambda c:c in COLS,
                              keep_default_na=False,encoding="utf-8-sig")
            data[t]=d
    result={"estado":"DIAGNOSTICO_CLAVES_SIN_MICRODATOS","tablas":{},"intersecciones":{}}
    for t,d in data.items():
        combos=[]
        for k in CANDIDATES:
            if not set(k).issubset(d.columns):continue
            combos.append({"campos":k,"duplicados":int(d.duplicated(k).sum()),
                           "nulos_o_blancos":int(d[k].eq("").any(axis=1).sum())})
        result["tablas"][t]={"filas":len(d),"combinaciones":combos}
        print(f"{t.upper()}: {len(d):,} filas")
        for entry in combos:
            print(f"  {'+'.join(entry['campos'])}: duplicados={entry['duplicados']:,}, vacios={entry['nulos_o_blancos']:,}")
    a=data["tmodulo"]
    b=data["tvar_crea"]
    for key in [["llavehog","n_ren"],["llaveviv","llavehog","n_ren"],
                ["control","viv_sel","hogar","n_ren"]]:
        if not (set(key).issubset(a.columns) and set(key).issubset(b.columns)): continue
        ak=pd.MultiIndex.from_frame(a[key]);bk=pd.MultiIndex.from_frame(b[key])
        result["intersecciones"]["+".join(key)]={
            "tm_keys_unique":int(ak.nunique()),"tc_keys_unique":int(bk.nunique()),
            "tmodulo_sin_tvar":int((~ak.isin(bk)).sum()),
            "tvar_sin_tmodulo":int((~bk.isin(ak)).sum())}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("REPORTE:",OUT)
    print("NO SE HICIERON UNIONES NI ESTIMACIONES.")
if __name__=="__main__":main()
