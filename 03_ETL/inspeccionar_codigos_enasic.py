"""Inspeccion metodologica preliminar de 33 variables ENASIC 2022.

Solo lectura de microdatos en ZIP: reporta frecuencias NO ponderadas,
catalogos INEGI y posibles valores no cubiertos por codigos explicitos.
NO identifica saltos, valores perdidos ni universos automaticamente.
"""
from __future__ import annotations

import csv
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "01_DATOS_RAW" / "INEGI" / "ENASIC_2022" / "conjunto_de_datos_enasic_2022_csv.zip"
REPORTS = ROOT / "08_DOCUMENTACION" / "auditorias" / "ENASIC_2022"

# Seleccion congelada de la matriz preliminar de 33 variables (octubre 2026).
# No significa aprobacion metodologica.
SELECTED = {
    "TCSDEMPO": "P3_8 P3_8A P4_3 P4_3A P4_9 P4_12 P4_30 P4_32 P4_33 P4_39",
    "THOGAR": "HN_CDISC HN_C",
    "TPOB_CUI": (
        "P6_7 P6_8 P6_8A P6_9_3 P6_11_1 P6_12_1 P6_12_2 "
        "P6_12_5 P6_26 P6_30_1 P6_31_2 P6_31_5 P6_33_1 "
        "P6_39_1 P6_39_3 P6_45_03 P6_48 COND_DISC"
    ),
    "TPER_ELE": "COND_DISC P6_45_03",
    "THOG_UNIP": "COND_DISC",
}
SELECTED = {table: values.split() for table, values in SELECTED.items()}


def save_csv(name: str, rows: list[dict], columns: list[str]) -> None:
    with (REPORTS / name).open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def get_main_file(paths: list[str], table: str) -> str:
    prefix = f"conjunto_de_datos_{table.lower()}_enasic_2022/"
    hits = [p for p in paths if p.lower().startswith(prefix)
            and "/conjunto_de_datos/" in p.lower() and p.lower().endswith(".csv")]
    if len(hits) != 1:
        raise ValueError(f"{table}: se esperaba una tabla principal; encontrados {len(hits)}")
    return hits[0]


def get_catalog(zf: ZipFile, paths: list[str], table: str, variable: str):
    prefix = f"conjunto_de_datos_{table.lower()}_enasic_2022/catalogos/"
    expected = prefix + variable.lower() + ".csv"
    matches = [p for p in paths if p.lower() == expected]
    if not matches:
        return None, [], False
    with zf.open(matches[0]) as raw:
        reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
        if not {"cve", "descrip"}.issubset(reader.fieldnames or []):
            raise ValueError(f"Catalogo inesperado: {matches[0]} -> {reader.fieldnames}")
        entries = [(r["cve"].strip(), r["descrip"].strip()) for r in reader]
    has_ranges = any("..." in code or "…" in code for code, _ in entries)
    return matches[0], entries, has_ranges


def describe_value(value: str, entries: list[tuple[str, str]]) -> tuple[str, str]:
    """Compara primero codigos exactos; despues normaliza numeros y rangos."""
    if not value:
        return "", "BLANCO"
    exact = dict(entries)
    if value in exact:
        return exact[value], "SI_EXACTO"
    if value.isdecimal():
        number = int(value)
        for code, description in entries:
            if code.isdecimal() and int(code) == number:
                return description, "SI_NORMALIZADO"
        for code, description in entries:
            normalized = code.replace("…", "...").replace("–", "...").replace("-", "...")
            parts = normalized.split("...")
            if len(parts) == 2 and all(part.strip().isdecimal() for part in parts):
                low, high = map(int, parts)
                if low <= number <= high:
                    return description, "SI_RANGO"
    return "", "REVISAR_CODIGO"


def main() -> None:
    if not RAW.is_file():
        raise SystemExit(f"No se encuentra el ZIP original: {RAW}")
    REPORTS.mkdir(parents=True, exist_ok=True)
    profiles, frequencies, catalogs = [], [], []
    with ZipFile(RAW) as zf:
        paths = zf.namelist()
        for table, variables in SELECTED.items():
            name = get_main_file(paths, table)
            counters = {variable: Counter() for variable in variables}
            total = 0
            with zf.open(name) as raw:
                reader = csv.DictReader(
                    io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
                )
                missing_columns = sorted(set(variables) - set(reader.fieldnames or []))
                if missing_columns:
                    raise ValueError(f"{table}: columnas ausentes: {missing_columns}")
                for row in reader:
                    total += 1
                    for variable in variables:
                        counters[variable][(row[variable] or "").strip()] += 1

            for variable in variables:
                catalog_path, entries, has_ranges = get_catalog(zf, paths, table, variable)
                descriptions = {code: label for code, label in entries}
                explicit_codes = set(descriptions)
                observed = counters[variable]
                blank = observed.get("", 0)
                outside = sum(count for value, count in observed.items()
                              if describe_value(value, entries)[1] == "REVISAR_CODIGO")
                profiles.append({
                    "tabla": table, "variable": variable, "registros_tabla": total,
                    "blancos": blank, "porcentaje_blancos": round(100 * blank / total, 2) if total else 0,
                    "valores_distintos_no_vacios": len([v for v in observed if v]),
                    "archivo_catalogo": catalog_path or "NO_ENCONTRADO",
                    "catalogo_con_rangos": "SI" if has_ranges else "NO",
                    "valores_sin_cobertura_catalogo": outside,
                    "interpretacion": "PENDIENTE_VALIDACION_DE_FILTROS_Y_CODIGOS",
                    "nota": ("NO considerar los valores fuera de lista como invalidos si el "
                             "catalogo contiene rangos; los blancos pueden ser saltos."),
                })
                for code, label in entries:
                    catalogs.append({
                        "tabla": table, "variable": variable,
                        "codigo_catalogo": code, "descripcion_oficial": label
                    })
                for value, count in observed.items():
                    frequencies.append({
                        "tabla": table, "variable": variable, "valor_observado": value,
                        "frecuencia_no_ponderada": count,
                        "porcentaje_sobre_toda_tabla": round(100 * count / total, 4) if total else 0,
                        "descripcion_catalogo": describe_value(value, entries)[0],
                        "estado_codigo": describe_value(value, entries)[1],
                    })
            print(f"{table}: {total:,} registros, {len(variables)} variables inspeccionadas")

    save_csv("perfil_33_variables.csv", profiles,
             list(profiles[0]))
    save_csv("frecuencias_33_variables.csv", frequencies,
             list(frequencies[0]))
    save_csv("catalogos_33_variables.csv", catalogs,
             ["tabla", "variable", "codigo_catalogo", "descripcion_oficial"])
    (REPORTS / "advertencias_33_variables.json").write_text(
        json.dumps({
            "variables": len(profiles),
            "catalogos_no_encontrados": [
                f"{r['tabla']}.{r['variable']}" for r in profiles
                if r["archivo_catalogo"] == "NO_ENCONTRADO"
            ],
            "alcance": "Frecuencias NO ponderadas, exploracion tecnica y no inferencia poblacional.",
            "restricciones": [
                "Un blanco no implica necesariamente no respuesta: revisar filtros del cuestionario.",
                "Codigos 8/9/98/99 no son automaticamente faltantes: revisar cada catalogo.",
                "Los catalogos pueden contener intervalos 01...97 o categorias top-coded.",
                "Los valores fuera de codigos explicitos NO implican error si existen rangos.",
                "No se identificaron automaticamente universos, saltos ni denominadores.",
                "Aun no se validaron factores, diseno muestral ni varianzas para estimaciones.",
                "La condicion mental reportada no equivale a diagnostico de discapacidad intelectual."
            ]
        }, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"LISTO: {len(profiles)} variables y 4 archivos en {REPORTS}")
    print("No hay porcentajes ponderados ni indicadores poblacionales en estos reportes.")


if __name__ == "__main__":
    main()
