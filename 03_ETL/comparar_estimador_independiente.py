"""Validacion numerica INDEPENDIENTE del estimador experimental ENASIC 2022.

Segunda implementacion mediante bucles por estrato y UPM; no importa ni
reutiliza la funcion de 03_ETL/estimar_dominio_experimental.py.
Compara 7 indicadores con CSV experimental previo y falla si difieren.
NO valida universo, cobertura del marco de UPM, ni la metodologia oficial.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "04_DATOS_LIMPIOS/ENASIC_2022/tpob_cui.parquet"
REF = ROOT / "08_DOCUMENTACION/auditorias/ENASIC_2022/estimadores_taylor_experimentales.csv"
OUT = ROOT / "08_DOCUMENTACION/auditorias/ENASIC_2022"
COLS = ["EST_DIS","UPM_DIS","FAC_CUI","P6_1","P6_7","P6_8",
        "P6_11_3","P6_12_2","P6_12_5","P6_39_1"]


def indicators(d):
    return {
        "cansancio_si": d["P6_11_3"].eq("1"),
        "dejar_trabajo_si": d["P6_12_2"].eq("1"),
        "jornada_horario_si": d["P6_12_5"].eq("1"),
        "alguna_dos_afectaciones_laborales":
            d["P6_12_2"].eq("1") | d["P6_12_5"].eq("1"),
        "cuidado_40_horas_o_mas":
            pd.to_numeric(d["P6_7"], errors="coerce").ge(40),
        "sin_apoyo_familiar": d["P6_8"].eq("2"),
        "insatisfaccion_tiempo_libre": d["P6_39_1"].eq("2"),
    }


def independent_estimator(df, y, domain):
    w = pd.to_numeric(df["FAC_CUI"], errors="raise").to_numpy(dtype=float)
    if not np.isfinite(w).all() or np.any(w <= 0):
        raise ValueError("Pesos no positivos/no finitos")
    if not y[domain].isin([True, False]).all():
        raise ValueError("Indicador incompleto en dominio")
    d = domain.to_numpy(dtype=bool).astype(float)
    v = y.to_numpy(dtype=bool).astype(float)
    denom = math.fsum(float(a*b) for a,b in zip(w,d))
    numer = math.fsum(float(a*b*c) for a,b,c in zip(w,d,v))
    p = numer/denom

    # Implementacion independiente: suma residual por UPM dentro de cada estrato
    design = df[["EST_DIS","UPM_DIS"]].copy()
    design["residuo"] = w*d*(v-p)
    grouped = design.groupby("EST_DIS",sort=False)
    variance_numerator = 0.0
    strata_count = 0
    psu_count = 0
    for _, block in grouped:
        sums = block.groupby("UPM_DIS",sort=False)["residuo"].sum().to_numpy(dtype=float)
        m = len(sums)
        if m < 2:
            raise ValueError("Estrato con menos de dos UPM en marco de calculo")
        strata_count += 1
        psu_count += m
        center = math.fsum(sums)/m
        variance_numerator += m/(m-1)*math.fsum((float(vv)-center)**2 for vv in sums)
    se = math.sqrt(variance_numerator)/denom
    return {
        "estimacion_ponderada_experimental":p,
        "error_estandar_taylor_experimental":se,
        "cv_experimental":se/p if p>0 else None,
        "denominador_ponderado_experimental":denom,
        "estratos_base_diseno":strata_count,
        "pares_estrato_upm_base_diseno":psu_count,
    }


def main():
    if not REF.is_file():
        raise SystemExit(f"Falta estimacion anterior: {REF}")
    df = pd.read_parquet(SOURCE,columns=COLS)
    if len(df)!=5677:
        raise ValueError("TPOB_CUI no tiene 5677 filas")
    domain = df["P6_1"].eq("1")
    if domain.sum()!=636:
        raise ValueError("Dominio P6_1=1 no tiene 636 filas")
    with REF.open(encoding="utf-8-sig",newline="") as f:
        rows = list(csv.DictReader(f))
    ref = {r["indicador"]:r for r in rows}
    keys = indicators(df)
    if set(keys)!=set(ref):
        raise ValueError("Lista de indicadores entre implementaciones es distinta")
    checks = []
    tolerance_absolute = 1e-9
    for key, flag in keys.items():
        calc=independent_estimator(df, flag,domain)
        original=ref[key]
        parts=[]
        for field,value in calc.items():
            expected=float(original[field])
            valid=math.isclose(float(value),expected,rel_tol=1e-9,abs_tol=tolerance_absolute)
            parts.append(valid)
        passed=all(parts)
        checks.append({
            "indicador":key, "comparacion": "COINCIDE" if passed else "DIFIERE",
            "estimador_independiente":calc["estimacion_ponderada_experimental"],
            "error_estandar_independiente":calc["error_estandar_taylor_experimental"],
            "cv_independiente":calc["cv_experimental"],
            "referencia_p":float(original["estimacion_ponderada_experimental"]),
            "referencia_se":float(original["error_estandar_taylor_experimental"]),
            "referencia_cv":float(original["cv_experimental"]),
        })
        print(f"{key}: {'COINCIDE' if passed else 'DIFIERE'}")
    result={
        "alcance":"Comprobacion numerica entre dos implementaciones sobre los mismos datos y supuestos",
        "estado":"COINCIDENCIA_NUMERICA_EXPERIMENTAL" if all(x["comparacion"]=="COINCIDE" for x in checks) else "DIFERENCIAS",
        "tolerancia_absoluta":tolerance_absolute,
        "checks":checks,
        "no_equivale_a":[
            "validacion externa con herramienta estadistica independiente",
            "verificacion oficial de la base de diseno TPOB_CUI",
            "certificacion de varianzas ni CV segun criterios INEGI",
            "autorizacion para publicar estimaciones poblacionales"
        ]
    }
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/"comparacion_estimador_independiente.json"
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"REPORTE: {path}")
    print("RESULTADO:",result["estado"])
    if result["estado"]!="COINCIDENCIA_NUMERICA_EXPERIMENTAL":
        raise SystemExit(1)


if __name__=="__main__":
    main()
