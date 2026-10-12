"""Auditoría estructural inicial ENUT 2024: lectura directa del ZIP.

Solo genera estadísticas de estructura (sin microdatos, estimaciones ni
identificadores personales). La columna de factor cambia según la unidad.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "01_DATOS_RAW/INEGI/ENUT_2024/conjunto_de_datos_enut_2024_csv.zip"
OUT = ROOT / "08_DOCUMENTACION/auditorias/ENUT_2024"
EXPECTED = {"tvar_crea", "tvivienda", "thogar", "tmodulo", "tsdem"}
FACTORS = ("fac_viv", "fac_hog", "fac_per")
KEYS = ("llaveviv", "llavehog", "llavesde", "llavemod")
DESIGN = ("est_dis", "upm_dis")
INTEREST = ("cuid", "trab_no_rem", "trab_merc", "activ_prod", "sexo", "edad")

def table_name(path: str) -> str:
    return Path(path).stem.lower().replace("conjunto_de_datos_enut_2024_", "")

def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"No se encontro ZIP: {SOURCE}")
    results = []
    with zipfile.ZipFile(SOURCE) as archive:
        members = [name for name in archive.namelist()
                   if "/conjunto_de_datos/" in name.lower()
                   and name.lower().endswith(".csv")]
        actual = {table_name(n) for n in members}
        if actual != EXPECTED or len(members) != len(EXPECTED):
            raise ValueError(f"Tablas no esperadas: {sorted(actual)}")
        for name in sorted(members):
            with archive.open(name) as stream:
                reader = csv.reader(io.TextIOWrapper(stream, encoding="utf-8-sig",
                                                     newline=""))
                fields = next(reader)
                if len(fields) != len(set(fields)):
                    raise ValueError(f"Columnas repetidas en {table_name(name)}")
                rows = sum(1 for _ in reader)
            info = {
                "tabla": table_name(name),
                "registros": rows,
                "columnas": len(fields),
                "llaves_presentes": [x for x in KEYS if x in fields],
                "diseno_presente": [x for x in DESIGN if x in fields],
                "factor_presente": [x for x in FACTORS if x in fields],
                "columnas_tematica_exploratoria":
                    [x for x in fields if any(s in x.lower() for s in INTEREST)],
                "encabezados": fields,
            }
            results.append(info)
            print(f"{info['tabla'].upper()}: {rows:,} registros x "
                  f"{len(fields)} columnas; factores={info['factor_presente']}")
    digest = hashlib.sha256()
    with SOURCE.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    report = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "estado": "AUDITORIA_ESTRUCTURAL_ENUT_SIN_ESTIMACIONES",
        "archivo": str(SOURCE.relative_to(ROOT)),
        "sha256": digest.hexdigest(),
        "tablas": results,
        "advertencias": [
            "No sumar conteos de tablas: viviendas, hogares y personas son unidades distintas.",
            "Factores FAC_VIV, FAC_HOG y FAC_PER requieren universos y diseño correctos.",
            "La coincidencia de nombres no valida llaves, poblaciones ni códigos.",
            "No hay todavía estimaciones de horas de cuidado ni discapacidad intelectual."
        ]
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "inventario_estructura_enut_2024.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    print(f"AUDITORIA ENUT COMPLETADA: {len(results)} tablas")
    print("REPORTE:", path)
    print("SIN ESTIMACIONES POBLACIONALES.")

if __name__ == "__main__":
    main()
