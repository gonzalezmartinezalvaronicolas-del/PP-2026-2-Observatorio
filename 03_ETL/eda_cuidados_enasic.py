"""EDA descriptivo de cuidados ENASIC 2022 — SIN ponderacion.

Produce frecuencias de P6_7, P6_8, P6_39_1 y comparaciones laborales
en TPOB_CUI; conserva como categorias separadas los codigos especiales.
No infiere prevalencias, estadisticas poblacionales ni causalidad.
"""
from __future__ import annotations

import csv
import io
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "05_BASE_ANALITICA/ENASIC_2022/tpob_cui_analitica_preliminar.parquet"
ZIP = ROOT / "01_DATOS_RAW/INEGI/ENASIC_2022/conjunto_de_datos_enasic_2022_csv.zip"
DEST = ROOT / "08_DOCUMENTACION/auditorias/ENASIC_2022"
VARIABLES = ("P6_7", "P6_8", "P6_39_1")
FIELDS = ("P6_1", "P6_12_2", "P6_12_5") + VARIABLES


def catalog(zf: ZipFile, variable: str) -> list[tuple[str, str]]:
    target = f"/catalogos/{variable.lower()}.csv"
    matches = [
        name for name in zf.namelist()
        if "tpob_cui" in name.lower() and name.lower().endswith(target)
    ]
    if len(matches) != 1:
        raise ValueError(f"Catalogo no unico para {variable}: {matches}")
    with zf.open(matches[0]) as raw:
        reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
        return [(row["cve"].strip(), row["descrip"].strip()) for row in reader]


def label_for(value: str, entries: list[tuple[str, str]]) -> tuple[str, str]:
    if not value:
        return "[CELDA VACIA]", "BLANCO"
    direct = dict(entries)
    if value in direct:
        return direct[value], "EXACTO"
    if value.isdecimal():
        v = int(value)
        for code, label in entries:
            if code.isdecimal() and int(code) == v:
                return label, "CODIGO_NUMERICO_EQUIVALENTE"
        for code, label in entries:
            normalized = code.replace("…", "...").replace("–", "...").replace("-", "...")
            bounds = [x.strip() for x in normalized.split("...")]
            if len(bounds) == 2 and all(x.isdecimal() for x in bounds):
                if int(bounds[0]) <= v <= int(bounds[1]):
                    return label, "INTERVALO"
    return "[SIN COBERTURA]", "REVISAR"


def save_csv(name: str, rows: list[dict], fields: list[str]) -> None:
    with (DEST / name).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    if not SOURCE.exists() or not ZIP.exists():
        print("ERROR: falta la base analitica o el ZIP original.", file=sys.stderr)
        return 1

    df = pd.read_parquet(SOURCE, columns=list(FIELDS))
    if len(df) != 5677:
        raise ValueError(f"Se esperaban 5677 registros, hay {len(df)}")
    scope = df["P6_1"].eq("1")
    if int(scope.sum()) != 636:
        raise ValueError("El bloque P6_1=1 dejo de contener 636 registros")
    DEST.mkdir(parents=True, exist_ok=True)
    frequency_rows = []
    summary_rows = []
    with ZipFile(ZIP) as zf:
        for variable in VARIABLES:
            entries = catalog(zf, variable)
            for group_name, mask in (
                ("TOTAL_TABLA", pd.Series(True, index=df.index)),
                ("P6_1_IGUAL_1", scope),
                ("FUERA_BLOQUE_P6_1", ~scope),
            ):
                values = df.loc[mask, variable].fillna("").astype(str)
                counts = Counter(values)
                total = len(values)
                for code, n in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
                    label, status = label_for(code, entries)
                    frequency_rows.append({
                        "variable": variable, "grupo": group_name,
                        "codigo_observado": code, "descripcion_catalogo": label,
                        "regla_catalogo": status, "frecuencia": n,
                        "denominador_grupo": total,
                        "porcentaje_muestral_no_ponderado": round(n / total * 100, 3)
                        if total else None,
                    })
                summary_rows.append({
                    "variable": variable, "grupo": group_name,
                    "registros": total, "respondidos": total - counts.get("", 0),
                    "blancos": counts.get("", 0),
                    "codigos_distintos_no_blancos": sum(1 for key in counts if key),
                    "sin_cobertura_catalogo": sum(
                        n for code, n in counts.items()
                        if label_for(code, entries)[1] == "REVISAR"
                    ),
                })

    labor_rows = []
    observed = df.loc[scope]
    for (a, b), n in sorted(
        Counter(zip(observed["P6_12_2"], observed["P6_12_5"])).items()
    ):
        labor_rows.append({
            "P6_12_2": a, "P6_12_5": b,
            "registros_no_ponderados": n,
            "total_bloque": len(observed),
            "porcentaje_no_ponderado": round(n / len(observed) * 100, 3),
        })

    save_csv("eda_frecuencias_cuidados.csv", frequency_rows, [
        "variable", "grupo", "codigo_observado", "descripcion_catalogo",
        "regla_catalogo", "frecuencia", "denominador_grupo",
        "porcentaje_muestral_no_ponderado",
    ])
    save_csv("eda_resumen_cuidados.csv", summary_rows, [
        "variable", "grupo", "registros", "respondidos", "blancos",
        "codigos_distintos_no_blancos", "sin_cobertura_catalogo",
    ])
    save_csv("eda_cruce_laboral.csv", labor_rows, [
        "P6_12_2", "P6_12_5", "registros_no_ponderados",
        "total_bloque", "porcentaje_no_ponderado",
    ])
    report = {
        "ejecutado_utc": datetime.now(timezone.utc).isoformat(),
        "estado": "OK",
        "fuente": str(SOURCE.relative_to(ROOT)),
        "universo_exploratorio": "P6_1 = 1 en TPOB_CUI",
        "n_total": len(df), "n_bloque": len(observed),
        "variables": list(VARIABLES),
        "restricciones": [
            "Frecuencias descriptivas sin factor de expansion.",
            "P6_39_1 tiene respuestas fuera del bloque P6_1=1: no usar denominador 636 para toda la tabla.",
            "No se calculan promedios de horas: codigo 98 es top-coded (98 o mas).",
            "No se interpreta P6_8 sin las condiciones del cuestionario.",
            "No se deducen inferencias causales ni indicadores de discapacidad intelectual.",
            "No publicar microdatos ni identificadores personales."
        ],
    }
    (DEST / "eda_reporte_cuidados.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"EDA OK: {len(df):,} filas; bloque P6_1=1: {len(observed):,}")
    for row in summary_rows:
        if row["grupo"] == "P6_1_IGUAL_1":
            print(f"{row['variable']}: respondidos={row['respondidos']}, "
                  f"blancos={row['blancos']}, codigos_sin_cobertura={row['sin_cobertura_catalogo']}")
    print(f"ARCHIVOS: {DEST}")
    print("EDA descriptivo NO ponderado. Falta validacion de universos y diseno muestral.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
