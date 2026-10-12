"""Primera base analitica exploratoria: cuidados y consecuencias laborales.

Fuente: capa Parquet conservadora ENASIC 2022, tabla TPOB_CUI.
No se consideran estimaciones poblacionales; no se aplican factores.
Se preservan datos originales; solo se derivan indicadores donde hay
respuestas observadas con codigos oficiales 1=Si, 2=No.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "04_DATOS_LIMPIOS/ENASIC_2022/tpob_cui.parquet"
OUTPUT_DIR = ROOT / "05_BASE_ANALITICA/ENASIC_2022"
AUDIT_DIR = ROOT / "08_DOCUMENTACION/auditorias/ENASIC_2022"
REQUIRED = ("LLAVEMOD", "P6_1", "P6_7", "P6_8", "P6_12_2", "P6_12_5", "P6_39_1")
LABOR = ("P6_12_2", "P6_12_5")


def main() -> int:
    if not SOURCE.is_file():
        print(f"ERROR: No se encuentra {SOURCE}. Ejecuta primero limpiar_enasic.py", file=sys.stderr)
        return 1
    source = pd.read_parquet(SOURCE)
    missing = [c for c in REQUIRED if c not in source.columns]
    if missing:
        print(f"ERROR: faltan columnas en TPOB_CUI: {missing}", file=sys.stderr)
        return 1
    if source["LLAVEMOD"].isna().any() or source["LLAVEMOD"].duplicated().any():
        print("ERROR: LLAVEMOD no es una llave unica y completa", file=sys.stderr)
        return 1

    # Se conserva cada columna original, sin convertir codigos ni blancos.
    base = source.copy()
    scope = base["P6_1"].eq("1")
    complete = base[list(LABOR) + ["P6_7", "P6_8"]].ne("").all(axis=1)
    any_response = base[list(LABOR) + ["P6_7", "P6_8"]].ne("").any(axis=1)
    if not scope.equals(complete) or not complete.equals(any_response):
        print("ERROR: los patrones observados cambiaron respecto al diagnostico previo.", file=sys.stderr)
        print("Revisar universos antes de crear indicadores.", file=sys.stderr)
        return 1

    for field in LABOR:
        unexpected = sorted(set(base.loc[scope, field]) - {"1", "2"})
        if unexpected:
            print(f"ERROR: valores de {field} fuera de 1/2 en bloque: {unexpected}", file=sys.stderr)
            return 1

    # Indicador exploratorio de 'Si' para al menos una de las dos opciones
    # de la pregunta 6.12. <NA> fuera del universo observado.
    for col in LABOR:
        derived = pd.Series(pd.NA, index=base.index, dtype="Int64")
        derived.loc[scope] = base.loc[scope, col].eq("1").astype("int64")
        base[f"{col}_SI"] = derived

    base["AFECTACION_LABORAL_2_OPCIONES"] = pd.Series(pd.NA, index=base.index, dtype="Int64")
    base.loc[scope, "AFECTACION_LABORAL_2_OPCIONES"] = (
        base.loc[scope, list(LABOR)].eq("1").any(axis=1).astype("int64")
    )
    base["AMBAS_OPCIONES_LABORALES"] = pd.Series(pd.NA, index=base.index, dtype="Int64")
    base.loc[scope, "AMBAS_OPCIONES_LABORALES"] = (
        base.loc[scope, list(LABOR)].eq("1").all(axis=1).astype("int64")
    )
    # Marcador de seleccion OBSERVADA, no certificacion de universo INEGI.
    base["BLOQUE_P6_1_SI_OBSERVADO"] = scope.astype("int64")

    n_yes_a = int(base.loc[scope, "P6_12_2_SI"].sum())
    n_yes_b = int(base.loc[scope, "P6_12_5_SI"].sum())
    n_any = int(base.loc[scope, "AFECTACION_LABORAL_2_OPCIONES"].sum())
    n_both = int(base.loc[scope, "AMBAS_OPCIONES_LABORALES"].sum())
    n_scope = int(scope.sum())

    report = {
        "generado_utc": datetime.now(timezone.utc).isoformat(),
        "origen": str(SOURCE.relative_to(ROOT)),
        "unidad": "registros de TPOB_CUI (no personas estimadas)",
        "filas_base": int(len(base)),
        "columnas_originales": int(len(source.columns)),
        "columnas_finales": int(len(base.columns)),
        "bloque_observado_p6_1_igual_1": n_scope,
        "p6_12_2_si": n_yes_a,
        "p6_12_5_si": n_yes_b,
        "alguna_de_las_dos_opciones": n_any,
        "ambas_opciones": n_both,
        "ninguna_de_las_dos_opciones": n_scope - n_any,
        "proporciones_muestrales_no_ponderadas": {
            "p6_12_2": round(n_yes_a / n_scope, 6) if n_scope else None,
            "p6_12_5": round(n_yes_b / n_scope, 6) if n_scope else None,
            "alguna": round(n_any / n_scope, 6) if n_scope else None,
            "ambas": round(n_both / n_scope, 6) if n_scope else None,
        },
        "advertencias": [
            "Exploracion descriptiva NO ponderada; no son estimaciones poblacionales.",
            "P6_1=1 coincide con el bloque de respuestas, pero cada indicador exige validar universo oficial.",
            "No equivale a prevalencia de discapacidad intelectual ni sindrome de Down.",
            "Los campos FAC_CUI y demas originales se conservaron, NO fueron aplicados.",
            "Variables laborales binarias son opciones de una pregunta de respuesta multiple.",
            "P6_39_1 tiene una cobertura distinta y NO se incluye en el indicador derivado.",
            "Los valores fuera de los 636 registros se representan como NA en indicadores, NO como cero.",
            "La base conserva microdatos y queda fuera de GitHub; compartir solo resumen auditado."
        ],
        "estado": "OK"
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUTPUT_DIR / "tpob_cui_analitica_preliminar.parquet"
    temp = OUTPUT_DIR / ".tpob_cui_analitica_preliminar.parquet.partial"
    try:
        base.to_parquet(temp, index=False, engine="pyarrow", compression="zstd")
        check = pd.read_parquet(temp)
        if len(check) != len(source) or not check["LLAVEMOD"].equals(source["LLAVEMOD"]):
            raise ValueError("No se conservaron filas y orden de LLAVEMOD.")
        os.replace(temp, target)
    except Exception:
        if temp.exists():
            temp.unlink()
        raise

    report_path = AUDIT_DIR / "base_analitica_preliminar.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"BASE: {target}")
    print(f"FILAS: {len(base):,} | COLUMNAS: {len(base.columns)}")
    print(f"BLOQUE P6_1=1: {n_scope:,} | OTRAS FILAS: {len(base)-n_scope:,}")
    print(f"P6_12_2 SI: {n_yes_a} | P6_12_5 SI: {n_yes_b}")
    print(f"ALGUNA: {n_any} | AMBAS: {n_both} | NINGUNA: {n_scope-n_any}")
    print(f"REPORTE: {report_path}")
    print("IMPORTANTE: no son porcentajes ponderados ni poblacionales.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
