"""ENUT 2024: valida relaciones y diseno entre cinco tablas originales.

No genera microdatos, ni estimaciones poblacionales, ni indicadores de horas.
Conserva cadenas para no perder ceros iniciales en las llaves.
"""
from __future__ import annotations
import io
import json
import zipfile
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
ZIP=ROOT/"01_DATOS_RAW/INEGI/ENUT_2024/conjunto_de_datos_enut_2024_csv.zip"
OUT=ROOT/"08_DOCUMENTACION/auditorias/ENUT_2024/diagnostico_relaciones_enut_2024.json"
SPECS={
 "tvivienda":(["llaveviv"],["llaveviv","est_dis","upm_dis","fac_viv"]),
 "thogar":(["llavehog"],["llavehog","llaveviv","est_dis","upm_dis","fac_hog"]),
 "tsdem":(["llavehog","n_ren"],["llavesde","llaveviv","llavehog","n_ren","est_dis","upm_dis","fac_hog"]),
 "tmodulo":(["llavehog","n_ren"],["llavemod","llaveviv","llavehog","n_ren","est_dis","upm_dis","fac_per"]),
 "tvar_crea":(["llavehog","n_ren"],["llavemod","llaveviv","llavehog","n_ren","est_dis","upm_dis","fac_per"]),
}
COUNTS={"tvivienda":28714,"thogar":29181,"tsdem":94565,"tmodulo":74053,"tvar_crea":74053}

def get_member(z,table):
    found=[n for n in z.namelist() if "/conjunto_de_datos/" in n.lower()
           and n.lower().endswith(".csv") and
           Path(n).stem.lower().replace("conjunto_de_datos_enut_2024_","")==table]
    if len(found)!=1:
        raise ValueError(f"CSV unico no encontrado para {table}: {len(found)}")
    return found[0]

def read(z,table):
    _,cols=SPECS[table]
    with z.open(get_member(z,table)) as f:
        return pd.read_csv(f,usecols=cols,dtype="string",keep_default_na=False,
                           encoding="utf-8-sig",low_memory=False)

def table_info(t,d):
    keys,_=SPECS[t]
    factor="fac_viv" if t=="tvivienda" else "fac_per" if t in ("tmodulo","tvar_crea") else "fac_hog"
    weights=pd.to_numeric(d[factor],errors="coerce")
    return {"tabla":t,"registros":len(d),"llave":keys,
            "claves_duplicadas":int(d.duplicated(keys).sum()),
            "claves_vacias":int(d[keys].eq("").any(axis=1).sum()),
            "diseno_vacio":{k:int(d[k].eq("").sum()) for k in ("est_dis","upm_dis",factor)},
            "factor_invalido":int((weights.isna() | weights.le(0)).sum()),
            "estratos_distintos":int(d.est_dis.nunique()),
            "upm_distintas":int(d.upm_dis.nunique())}

def relation(parent,child,parent_name,child_name,left_key,right_key=None,compare_factor=False):
    right_key=right_key or left_key
    if parent.duplicated(right_key).any():
        raise ValueError(f"Clave padre no es unica: {parent_name}, {right_key}")
    pdsg=parent[right_key+["est_dis","upm_dis"]+
                (["fac_per"] if compare_factor else [])]
    merged=child.merge(pdsg,left_on=left_key,right_on=right_key,
                       how="left",validate="many_to_one",indicator=True,
                       suffixes=("","_padre"))
    matches=merged["_merge"].eq("both")
    mismatch={c:int((matches & merged[c].ne(merged[c+"_padre"])).sum())
              for c in ("est_dis","upm_dis")}
    if compare_factor:
        mismatch["fac_per"]=int((matches & merged.fac_per.ne(merged.fac_per_padre)).sum())
    return {"relacion":child_name+" -> "+parent_name,
            "origen":len(child),
            "sin_padre":int((~matches).sum()),
            "inconsistencias_en_coincidentes":mismatch}

def main():
    if not ZIP.is_file():raise SystemExit(f"No se encuentra {ZIP}")
    with zipfile.ZipFile(ZIP) as z:
        data={t:read(z,t) for t in SPECS}
    report={"fecha_utc":datetime.now(timezone.utc).isoformat(),
            "estado":"AUDITORIA_RELACIONES_SIN_ESTIMACIONES","tablas":[],"relaciones":[]}
    for t,d in data.items():
        if len(d)!=COUNTS[t]:raise ValueError(f"Conteo inesperado {t}: {len(d)}")
        s=table_info(t,d)
        if s["claves_duplicadas"] or s["claves_vacias"]:
            print(f"ADVERTENCIA: {t} presenta problemas en clave compuesta propuesta {s['llave']}")
        report["tablas"].append(s)
        print(f"{t}: {len(d):,} filas; duplicadas={s['claves_duplicadas']}; factor_invalido={s['factor_invalido']}")
    for parent,child,k,cf in [
      ("tvivienda","thogar",["llaveviv"],False),
      ("thogar","tsdem",["llavehog"],False),
      ("thogar","tmodulo",["llavehog"],False),
      ("tmodulo","tvar_crea",["llavehog","n_ren"],True)]:
        r=relation(data[parent],data[child],parent,child,k,compare_factor=cf)
        r["clave_usada"]=k
        report["relaciones"].append(r)
        print(f"{r['relacion']}: sin_padre={r['sin_padre']}, discrepancias={r['inconsistencias_en_coincidentes']}")
    if any(item["claves_duplicadas"] or item["claves_vacias"] or item["factor_invalido"] for item in report["tablas"]):
        raise ValueError("Hay duplicados, claves vacias o pesos invalidos: revisar auditoria")
    if any(item["sin_padre"] or any(item["inconsistencias_en_coincidentes"].values()) for item in report["relaciones"]):
        raise ValueError("Hay huerfanos o campos de diseno inconsistentes")
    report["advertencias"]=[
      "LLAVEHOG + N_REN es unica en TSDEM, TMODULO y TVAR_CREA segun diagnostico empirico; confirmar en documentacion oficial.",
      "FAC_HOG en TSDEM no implica factor de expansion de personas; utilizar factor segun unidad oficial.",
      "La auditoria no valida unidades de tiempo, valores especiales ni calculos del diseno de encuesta.",
      "No se infiere discapacidad intelectual ni se publican resultados muestrales."
    ]
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("REPORTE:",OUT)
    print("NO SE GENERARON ESTIMACIONES POBLACIONALES.")

if __name__=="__main__":
    main()
