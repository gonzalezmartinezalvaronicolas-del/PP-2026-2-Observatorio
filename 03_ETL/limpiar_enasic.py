"""ETL tecnica conservadora ENASIC 2022: CSV dentro de ZIP -> Parquet.

Principios:
* No modificar los archivos fuente.
* Preservar TODAS las variables como texto y sus valores tal como vienen.
* Preservar blancos como cadenas vacias (no suponer valores perdidos).
* No filtrar registros, hacer joins, ponderar, imputar ni recodificar.
* Verificar paridad de numero de filas y columnas y producir reporte de auditoria.
* Escribir en bloques para controlar memoria y publicar archivos de forma atomica.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT / "01_DATOS_RAW" / "INEGI" / "ENASIC_2022" / "conjunto_de_datos_enasic_2022_csv.zip"
DEST = ROOT / "04_DATOS_LIMPIOS" / "ENASIC_2022"
AUDIT = ROOT / "08_DOCUMENTACION" / "auditorias" / "ENASIC_2022"
TABLES = ["TCSDEMPO", "THOG_UNIP", "THOGAR", "TPER_ELE", "TPOB_CUI", "TVIVIENDA"]
BATCH_SIZE = 10000


def source_member(names: list[str], table: str) -> str:
    """Localiza un unico CSV principal por tabla, tolerando erratas del nombre ZIP.

    La auditoria inicial de ENASIC detecto variaciones de nomenclatura
    (p. ej., THOGAR con 'ensasic'). Exigimos la carpeta /conjunto_de_datos/
    y el prefijo de tabla, pero no un sufijo escrito exactamente.
    """
    prefix = f"conjunto_de_datos_{table.lower()}_"
    matches = [
        name for name in names
        if "/conjunto_de_datos/" in name.lower()
        and name.lower().endswith(".csv")
        and Path(name).name.lower().startswith(prefix)
    ]
    if len(matches) != 1:
        candidates = [
            name for name in names
            if "/conjunto_de_datos/" in name.lower() and name.lower().endswith(".csv")
        ]
        raise ValueError(
            f"{table}: se esperaba un unico CSV principal; hallados {len(matches)}. "
            f"CSV principales disponibles: {candidates}"
        )
    return matches[0]


def zip_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def convert_table(zip_file: ZipFile, member: str, table: str) -> dict:
    target = DEST / f"{table.lower()}.parquet"
    temporary = DEST / f".{table.lower()}.parquet.partial"
    writer = None
    row_count = 0
    ncols = 0
    headers = []
    try:
        with zip_file.open(member) as source:
            # newline="" keeps the CSV parser's quote and newline semantics.
            text = io.TextIOWrapper(source, encoding="utf-8-sig", newline="")
            reader = csv.reader(text, strict=True)
            try:
                headers = next(reader)
            except StopIteration:
                raise ValueError(f"CSV sin encabezado: {member}")
            if not headers or any(not h for h in headers) or len(set(headers)) != len(headers):
                raise ValueError(f"Encabezados vacios o duplicados: {member}")
            ncols = len(headers)
            schema = pa.schema([pa.field(h, pa.string(), nullable=False) for h in headers],
                               metadata={
                                   b"source_table": table.encode("utf-8"),
                                   b"transformation": b"conservative_csv_to_parquet_all_strings",
                                   b"blank_policy": b"preserve_empty_string",
                               })
            writer = pq.ParquetWriter(temporary, schema, compression="zstd")
            columns = [[] for _ in headers]

            def flush() -> None:
                if not columns[0]:
                    return
                arrays = [pa.array(col, type=pa.string()) for col in columns]
                writer.write_table(pa.Table.from_arrays(arrays, schema=schema))
                for col in columns:
                    col.clear()

            for line_number, values in enumerate(reader, start=2):
                if len(values) != ncols:
                    raise ValueError(
                        f"{table}: fila CSV {line_number}: {len(values)} campos, esperados {ncols}"
                    )
                for dest_col, value in zip(columns, values):
                    dest_col.append(value)
                row_count += 1
                if row_count % BATCH_SIZE == 0:
                    flush()
            flush()
        writer.close()
        writer = None
        metadata = pq.ParquetFile(temporary).metadata
        if metadata.num_rows != row_count or metadata.num_columns != ncols:
            raise ValueError(
                f"{table}: paridad fallida; CSV={row_count}x{ncols}; "
                f"Parquet={metadata.num_rows}x{metadata.num_columns}"
            )
        read_headers = pq.read_schema(temporary).names
        if read_headers != headers:
            raise ValueError(f"{table}: columnas y orden distintos tras conversion")
        os.replace(temporary, target)
        return {
            "tabla": table, "fuente_zip": member, "archivo_parquet": str(target.relative_to(ROOT)),
            "registros_csv": row_count, "registros_parquet": metadata.num_rows,
            "columnas_csv": ncols, "columnas_parquet": metadata.num_columns,
            "columnas_orden_igual": True, "tipos": "string",
            "blancos": "cadena_vacia_preservada", "estado": "OK",
            "bytes_parquet": target.stat().st_size,
        }
    except Exception:
        if writer is not None:
            writer.close()
        if temporary.exists():
            temporary.unlink()
        raise


def main() -> int:
    if not ZIP_PATH.is_file():
        print(f"ERROR: no existe el ZIP original: {ZIP_PATH}", file=sys.stderr)
        return 1
    DEST.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    source_sha256 = zip_hash(ZIP_PATH)
    results = []
    try:
        with ZipFile(ZIP_PATH, "r") as zip_file:
            bad_member = zip_file.testzip()
            if bad_member is not None:
                raise ValueError(f"ZIP corrupto, primer archivo con fallo CRC: {bad_member}")
            names = zip_file.namelist()
            for table in TABLES:
                member = source_member(names, table)
                result = convert_table(zip_file, member, table)
                results.append(result)
                print(f"OK {table}: {result['registros_csv']:,} filas x "
                      f"{result['columnas_csv']} columnas -> "
                      f"{result['archivo_parquet']}")
    except Exception as exc:
        print(f"ERROR ETL: {exc}", file=sys.stderr)
        print("No se emite un reporte de ejecucion exitosa.", file=sys.stderr)
        return 1

    report = {
        "proceso": "ENASIC_2022_ETL_TECNICA_CONSERVADORA",
        "ejecutado_utc": datetime.now(timezone.utc).isoformat(),
        "fuente_zip": str(ZIP_PATH.relative_to(ROOT)),
        "sha256_zip": source_sha256,
        "politica": [
            "Los archivos originales no fueron modificados.",
            "Todas las columnas se conservan como string en Parquet.",
            "Los blancos se mantienen como cadena vacia: no son NA automaticamente.",
            "No se han definido saltos, universos, estimadores ni variables analiticas.",
            "No hay joins ni eliminacion de observaciones.",
            "Los resultados de distintas tablas NO se suman como personas unicas.",
            "Los parquet no deben publicarse en GitHub por contener microdatos."
        ],
        "tablas": results,
        "total_filas_acumuladas_entre_tablas": sum(x["registros_csv"] for x in results),
        "total_variables_acumuladas_entre_tablas": sum(x["columnas_csv"] for x in results),
        "estado": "OK"
    }
    target = AUDIT / "etl_tecnica_conservadora.json"
    temporary = AUDIT / ".etl_tecnica_conservadora.json.partial"
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, target)
    print(f"\nVALIDACION COMPLETA: {len(results)} tablas, "
          f"{report['total_filas_acumuladas_entre_tablas']:,} filas acumuladas, "
          f"{report['total_variables_acumuladas_entre_tablas']:,} columnas acumuladas.")
    print(f"REPORTE: {target}")
    print("SIGUIENTE: validar contenido y reglas antes de construir indicadores.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
