"""ENASIC 2022: validacion de llaves e integridad referencial (solo lectura)."""
from __future__ import annotations

import csv
import io
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "01_DATOS_RAW" / "INEGI" / "ENASIC_2022"
OUT = ROOT / "08_DOCUMENTACION" / "auditorias" / "ENASIC_2022"

# Relaciones basadas en INEGI, Conociendo la base de datos, sec. 1.6-1.7.
PRIMARY = {
    "TVIVIENDA": "LLAVEVIV",
    "THOGAR": "LLAVEHOG",
    "TCSDEMPO": "LLAVESDE",
    "TPOB_CUI": "LLAVEMOD",
    "THOG_UNIP": "LLAVEMOD",
    "TPER_ELE": "LLAVEMOD",
}
RELATIONS = [
    ("THOGAR", "TVIVIENDA", "LLAVEVIV"),
    ("TCSDEMPO", "THOGAR", "LLAVEHOG"),
    ("TPOB_CUI", "TCSDEMPO", "LLAVEMOD", "LLAVESDE"),
    ("THOG_UNIP", "TCSDEMPO", "LLAVEMOD", "LLAVESDE"),
    ("TPER_ELE", "TCSDEMPO", "LLAVEMOD", "LLAVESDE"),
]
FACTORS = ("FAC_VIV", "FAC_HOG", "FAC_CUI", "FAC_ELE", "FAC_UNI")


def identify(name: str) -> str | None:
    stem = Path(name).stem.upper()
    for table in PRIMARY:
        if stem == table or stem.startswith(table + "_") or ("_" + table + "_") in stem:
            return table
    return None


def export(name: str, rows: list[dict], fields: list[str]) -> None:
    with (OUT / name).open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    archives = list(RAW.glob("*.zip"))
    if len(archives) != 1:
        raise SystemExit(f"Se requiere exactamente un ZIP en {RAW}. Encontrados: {len(archives)}")
    OUT.mkdir(parents=True, exist_ok=True)

    dataset: dict[str, dict] = {}
    with ZipFile(archives[0]) as z:
        paths = {}
        for name in z.namelist():
            if not name.lower().endswith(".csv") or "/conjunto_de_datos/" not in name.lower():
                continue
            table = identify(name)
            if table:
                if table in paths:
                    raise SystemExit(f"Tabla duplicada en ZIP: {table}")
                paths[table] = name
        missing = sorted(set(PRIMARY) - set(paths))
        if missing:
            raise SystemExit(f"Faltan tablas: {missing}")

        for table, name in sorted(paths.items()):
            # Solo guardamos en memoria identificadores para diagnostico;
            # nunca exportamos valores de llaves individuales.
            wanted = {PRIMARY[table]}
            for rel in RELATIONS:
                if rel[0] == table:
                    wanted.add(rel[2])
                if rel[1] == table:
                    wanted.add(rel[3] if len(rel) == 4 else rel[2])
            seen = {key: set() for key in wanted}
            duplicates = {key: 0 for key in wanted}
            missing_keys = {key: 0 for key in wanted}
            rows = 0
            with z.open(name) as bf:
                reader = csv.DictReader(
                    io.TextIOWrapper(bf, encoding="utf-8-sig", errors="replace", newline="")
                )
                cols = reader.fieldnames or []
                indices = set(cols)
                absent = sorted(wanted - indices)
                if absent:
                    raise SystemExit(f"{table} carece de columnas requeridas: {absent}")
                for row in reader:
                    rows += 1
                    for key in wanted:
                        value = (row.get(key) or "").strip()
                        if not value:
                            missing_keys[key] += 1
                        elif value in seen[key]:
                            duplicates[key] += 1
                        else:
                            seen[key].add(value)
            dataset[table] = dict(
                rows=rows, columns=cols, seen=seen,
                duplicates=duplicates, missing=missing_keys,
            )
            print(f"{table}: {rows:,} filas; llave primaria {PRIMARY[table]}")

    primary_report = []
    factor_report = []
    for table in sorted(PRIMARY):
        d = dataset[table]
        key = PRIMARY[table]
        primary_report.append(dict(
            tabla=table, llave_primaria=key, filas=d["rows"],
            llaves_vacias=d["missing"][key],
            duplicados_llave_primaria=d["duplicates"][key],
            valores_distintos_no_vacios=len(d["seen"][key]),
            resultado=("REVISAR" if d["missing"][key] or d["duplicates"][key] else "OK"),
        ))
        for factor in FACTORS:
            factor_report.append(dict(
                tabla=table, factor=factor,
                presente="SI" if factor in d["columns"] else "NO",
            ))

    relation_report = []
    for child, parent, child_key, *parent_key_list in RELATIONS:
        parent_key = parent_key_list[0] if parent_key_list else child_key
        child_values = dataset[child]["seen"][child_key]
        parent_values = dataset[parent]["seen"][parent_key]
        unmatched = len(child_values - parent_values)
        relation_report.append(dict(
            origen=child, destino=parent, llave_origen=child_key,
            llave_destino=parent_key,
            identificadores_distintos_origen=len(child_values),
            identificadores_sin_coincidencia=unmatched,
            filas_con_llave_vacia=dataset[child]["missing"][child_key],
            resultado=("REVISAR" if unmatched or dataset[child]["missing"][child_key] else "OK"),
        ))
        print(f"{child} -> {parent}: {unmatched} llaves distintas sin coincidencia")

    export("validacion_llaves.csv", primary_report, [
        "tabla", "llave_primaria", "filas", "llaves_vacias",
        "duplicados_llave_primaria", "valores_distintos_no_vacios", "resultado"
    ])
    export("integridad_referencial.csv", relation_report, [
        "origen", "destino", "llave_origen", "llave_destino",
        "identificadores_distintos_origen", "identificadores_sin_coincidencia",
        "filas_con_llave_vacia", "resultado"
    ])
    export("factores_detectados.csv", factor_report, ["tabla", "factor", "presente"])
    print(f"Listo. Tres reportes locales en: {OUT}")
    print("AVISO: Los factores solo se detectaron; aun NO se validaron para estimaciones.")
    print("AVISO: No se evaluaron filtros, dominios ni codigos especiales de no respuesta.")


if __name__ == "__main__":
    main()
