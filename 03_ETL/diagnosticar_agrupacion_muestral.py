"""Auditoria avanzada del diseno muestral ENASIC 2022, sin estimadores.

Distingue los conglomerados observados en TODA TPOB_CUI de los observados
en el dominio exploratorio P6_1=1. Los conteos de UPM dentro del dominio
NO definen por si solos estratos solitarios del diseno completo.
No publica identificadores UPM/estrato, solo histogramas agregados.
"""
from __future__ import annotations
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "04_DATOS_LIMPIOS/ENASIC_2022/tpob_cui.parquet"
OUTPUT = ROOT / "08_DOCUMENTACION/auditorias/ENASIC_2022"
FIELDS = ["P6_1", "UPM_DIS", "EST_DIS", "FAC_CUI"]


def describe_design(df: pd.DataFrame) -> dict:
    strata = df.groupby("EST_DIS", dropna=False)
    by_stratum = strata.apply(
        lambda x: x["UPM_DIS"].nunique(), include_groups=False
    )
    multiplicity = Counter(int(v) for v in by_stratum.to_numpy())
    repeated_upm_across_strata = (
        df[["UPM_DIS", "EST_DIS"]].drop_duplicates()
        .groupby("UPM_DIS")["EST_DIS"].nunique()
    )
    return {
        "registros": len(df),
        "estratos_distintos": int(df["EST_DIS"].nunique()),
        "upm_distintas_sin_estrato": int(df["UPM_DIS"].nunique()),
        "pares_estrato_upm_distintos": int(
            df[["EST_DIS", "UPM_DIS"]].drop_duplicates().shape[0]
        ),
        "estratos_con_una_upm_observada": int((by_stratum == 1).sum()),
        "estratos_con_dos_o_mas_upm": int((by_stratum >= 2).sum()),
        "codigos_upm_presentes_en_mas_de_un_estrato":
            int((repeated_upm_across_strata > 1).sum()),
        "distribucion_num_upm_por_estrato": dict(sorted(multiplicity.items()))
    }


def main():
    df = pd.read_parquet(INPUT, columns=FIELDS)
    if len(df) != 5677:
        raise ValueError(f"Se esperaban 5677 registros, encontrados {len(df)}")
    if df[FIELDS].isna().any().any() or df[FIELDS].eq("").any().any():
        raise ValueError("Hay campos vacios o nulos; revisar origen.")
    factor = pd.to_numeric(df["FAC_CUI"], errors="coerce")
    if factor.isna().any() or not factor.map(math.isfinite).all() or factor.le(0).any():
        raise ValueError("FAC_CUI contiene pesos no validos, no finitos o no positivos")
    observed = df.loc[df["P6_1"].eq("1")]
    if len(observed) != 636:
        raise ValueError("El universo exploratorio no coincide con 636 registros")

    all_design = describe_design(df)
    selected_design = describe_design(observed)
    hist = []
    for label, result in (("TODA_TPOB_CUI", all_design),
                          ("DOMINIO_OBSERVADO_P6_1_1", selected_design)):
        for upm_count, strata_count in result["distribucion_num_upm_por_estrato"].items():
            hist.append({
                "grupo": label,
                "upm_observadas_en_estrato": upm_count,
                "cantidad_de_estratos": strata_count
            })
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "distribucion_upm_por_estrato.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "grupo", "upm_observadas_en_estrato", "cantidad_de_estratos"
        ])
        writer.writeheader()
        writer.writerows(hist)

    results = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "estado": "DIAGNOSTICO_DE_AGRUPACION_SIN_ESTIMACIONES",
        "tabla_completa": all_design,
        "bloque_exploratorio": selected_design,
        "factor": "FAC_CUI",
        "factor_numerico_positivo_en_todos_los_registros": True,
        "advertencias": [
            "No aplicar tratamiento de estratos solitarios a partir del dominio filtrado.",
            "No se confirman UPM, estratos ni diseño solo por el nombre de columnas.",
            "No se estiman totales, medias, errores estandar, CV ni intervalos.",
            "La identificacion definitiva y el tratamiento de estratos unitarios deben venir del diseno oficial INEGI.",
            "Los codigos de UPM/EST_DIS no se publican; solo conteos agregados."
        ]
    }
    path = OUTPUT / "diagnostico_agrupacion_muestral.json"
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print("AUDITORIA DE AGRUPACION ENASIC 2022")
    for label, item in (("TODA TPOB_CUI", all_design), ("BLOQUE P6_1=1", selected_design)):
        print(f"{label}: {item['registros']:,} registros; "
              f"{item['estratos_distintos']} estratos; "
              f"{item['pares_estrato_upm_distintos']} pares estrato-UPM")
        print(f"  Estratos con solo 1 UPM observada: {item['estratos_con_una_upm_observada']}")
        print(f"  Estratos con 2 o mas UPM: {item['estratos_con_dos_o_mas_upm']}")
    print(f"REPORTES: {path} y distribucion_upm_por_estrato.csv")
    print("NO SE GENERARON ESTIMACIONES POBLACIONALES.")
if __name__ == "__main__":
    main()
