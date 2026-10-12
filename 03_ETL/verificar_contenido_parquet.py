"""Verificacion de contenido ENASIC 2022: CSV originales vs Parquet.

Compara celda por celda, orden de filas, valores vacios y columnas.
No altera ni los CSV ni los Parquet. Reporta solo resumen por tabla.
"""
from __future__ import annotations

import csv
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "01_DATOS_RAW/INEGI/ENASIC_2022/conjunto_de_datos_enasic_2022_csv.zip"
PARQUETS = ROOT / "04_DATOS_LIMPIOS/ENASIC_2022"
OUT = ROOT / "08_DOCUMENTACION/auditorias/ENASIC_2022/verificacion_contenido_parquet.json"
TABLES = ("TCSDEMPO", "THOG_UNIP", "THOGAR", "TPER_ELE", "TPOB_CUI", "TVIVIENDA")


def find_member(names: list[str], table: str) -> str:
    prefix = f"conjunto_de_datos_{table.lower()}_"
    found = [
        n for n in names
        if "/conjunto_de_datos/" in n.lower()
        and n.lower().endswith(".csv")
        and Path(n).name.lower().startswith(prefix)
    ]
    if len(found) != 1:
        raise ValueError(f"{table}: CSV principal ambiguo, coincidencias={found}")
    return found[0]


def compare_table(zf: ZipFile, names: list[str], table: str) -> dict:
    member = find_member(names, table)
    parquet_path = PARQUETS / f"{table.lower()}.parquet"
    if not parquet_path.is_file():
        raise FileNotFoundError(parquet_path)

    parquet = pq.ParquetFile(parquet_path)
    count = 0
    differences = 0
    examples = []
    with zf.open(member) as raw:
        reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""), strict=True)
        headers = next(reader)
        if parquet.schema_arrow.names != headers:
            raise ValueError(f"{table}: orden o nombres de columnas no coinciden")
        if any(not str(field.type) == "string" for field in parquet.schema_arrow):
            raise ValueError(f"{table}: hay columnas no-string en Parquet")
        iterator = iter(reader)
        for batch in parquet.iter_batches(batch_size=1024):
            columns = [arr.to_pylist() for arr in batch.columns]
            for i in range(batch.num_rows):
                try:
                    original = next(iterator)
                except StopIteration:
                    raise ValueError(f"{table}: Parquet tiene mas filas que CSV")
                if len(original) != len(headers):
                    raise ValueError(f"{table}: fila CSV {count + 2} con longitud incorrecta")
                for idx, expected in enumerate(original):
                    actual = columns[idx][i]
                    if expected != actual:
                        differences += 1
                        if len(examples) < 5:
                            examples.append({
                                "fila_datos": count + 1, "variable": headers[idx],
                                "valor_csv": expected, "valor_parquet": actual
                            })
                count += 1
        sentinel = next(iterator, None)
        if sentinel is not None:
            raise ValueError(f"{table}: CSV tiene mas filas que Parquet")
    if parquet.metadata.num_rows != count:
        raise ValueError(f"{table}: metadatos Parquet inconsistentes")
    return {
        "tabla": table, "filas_comparadas": count,
        "columnas_comparadas": len(headers),
        "celdas_comparadas": count * len(headers),
        "diferencias": differences, "ejemplos": examples,
        "estado": "OK" if differences == 0 else "DIFERENCIAS"
    }


def main() -> int:
    if not SOURCE.is_file():
        print(f"ERROR: fuente ausente: {SOURCE}", file=sys.stderr)
        return 1
    report = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "tipo": "igualdad_exacta_contenido_csv_parquet",
        "nota": "Validacion tecnica, no equivale a validacion de codigos, universos ni ponderacion.",
        "tablas": [], "estado": "EN_PROCESO"
    }
    try:
        with ZipFile(SOURCE) as zf:
            names = zf.namelist()
            for table in TABLES:
                item = compare_table(zf, names, table)
                report["tablas"].append(item)
                print(f"{item['estado']} {table}: {item['filas_comparadas']:,} filas, "
                      f"{item['celdas_comparadas']:,} celdas, "
                      f"{item['diferencias']} diferencias")
        report["estado"] = (
            "OK" if all(t["diferencias"] == 0 for t in report["tablas"]) else "DIFERENCIAS"
        )
    except Exception as error:
        report["estado"] = "ERROR"
        report["detalle_error"] = str(error)
        print(f"ERROR: {error}", file=sys.stderr)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"REPORTE: {OUT}")
    return 0 if report["estado"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
