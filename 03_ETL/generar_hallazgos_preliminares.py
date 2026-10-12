"""Hallazgos descriptivos iniciales ENASIC 2022 para el Observatorio.

Genera un RESUMEN AGREGADO, sin identificadores ni microdatos individuales.
Conserva estrictamente el universo observado P6_1=1; NO pondera.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "05_BASE_ANALITICA/ENASIC_2022/tpob_cui_analitica_preliminar.parquet"
OUT = ROOT / "08_DOCUMENTACION/auditorias/ENASIC_2022"
NEEDED = ["P6_1", "P6_7", "P6_8", "P6_39_1", "P6_12_2", "P6_12_5"]


def main() -> None:
    frame = pd.read_parquet(SOURCE, columns=NEEDED)
    subset = frame.loc[frame["P6_1"].eq("1")].copy()
    n = len(subset)
    if len(frame) != 5677 or n != 636:
        raise ValueError("Cambio inesperado en el universo de trabajo; detener analisis.")
    for name in ("P6_8", "P6_39_1", "P6_12_2", "P6_12_5"):
        if not subset[name].isin(["1", "2"]).all():
            raise ValueError(f"Codigos inesperados en {name}.")
    hours = pd.to_numeric(subset["P6_7"], errors="coerce")
    if hours.isna().any() or hours.lt(1).any() or hours.gt(98).any():
        raise ValueError("Horas fuera de 01..98 o no numericas; revisar P6_7.")

    labor = subset["P6_12_2"].eq("1") | subset["P6_12_5"].eq("1")
    flags = {
        "horas_40_o_mas": hours.ge(40),
        "horas_98_o_mas_codificadas": hours.eq(98),
        "sin_apoyo_economico_o_especie_familiar": subset["P6_8"].eq("2"),
        "con_apoyo_economico_o_especie_familiar": subset["P6_8"].eq("1"),
        "insatisfaccion_tiempo_libre": subset["P6_39_1"].eq("2"),
        "afectacion_laboral_alguna_dos_opciones": labor,
        "horas_40_o_mas_y_afectacion_laboral": hours.ge(40) & labor,
        "insatisfaccion_tiempo_libre_y_afectacion_laboral":
            subset["P6_39_1"].eq("2") & labor,
    }
    definitions = {
        "horas_40_o_mas": "Horas exclusivas semanales >=40; 98 representa 98 o mas.",
        "horas_98_o_mas_codificadas": "Horas exclusivas semanales en categoria 98 o mas.",
        "sin_apoyo_economico_o_especie_familiar":
            "No recibio apoyo economico o en especie del hogar o familia (P6_8=2).",
        "con_apoyo_economico_o_especie_familiar":
            "Si recibio apoyo economico o en especie del hogar o familia (P6_8=1).",
        "insatisfaccion_tiempo_libre": "No esta satisfecho con su tiempo libre (P6_39_1=2).",
        "afectacion_laboral_alguna_dos_opciones":
            "Si en P6_12_2 y/o P6_12_5; no equivale a cualquier repercusion laboral.",
        "horas_40_o_mas_y_afectacion_laboral":
            "Interseccion descriptiva; NO prueba causalidad.",
        "insatisfaccion_tiempo_libre_y_afectacion_laboral":
            "Interseccion descriptiva; NO prueba causalidad.",
    }
    result = [{
        "indicador_exploratorio": name,
        "definicion": definitions[name],
        "casos": int(flag.sum()),
        "universo_observado": n,
        "porcentaje_muestral_sin_ponderar": round(float(flag.mean()) * 100, 2),
        "validacion": "PRELIMINAR_NO_POBLACIONAL",
    } for name, flag in flags.items()]
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "hallazgos_preliminares_cuidados.csv").open(
            "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(result[0]))
        writer.writeheader()
        writer.writerows(result)

    notes = {
        "fuente": str(SOURCE.relative_to(ROOT)),
        "registros_base": len(frame),
        "universo_observado": "P6_1=1 en TPOB_CUI",
        "n": n,
        "estado": "DESCRIPTIVO_NO_PONDERADO",
        "fuente_preguntas": "https://www.inegi.org.mx/contenidos/programas/enasic/2022/doc/enasic_2022_cuestionario.pdf",
        "advertencias": [
            "No son tasas de Mexico, Ciudad de Mexico ni Estado de Mexico.",
            "P6_8 se limita a apoyo economico/en especie del hogar o familia.",
            "98 en P6_7 esta censurado por arriba (98 horas o mas).",
            "P6_39_1 cubre tambien registros fuera del bloque P6_1=1.",
            "No se verifica aqui representatividad ni diseno muestral.",
            "Ninguna variable identifica especificamente un diagnostico de discapacidad intelectual.",
            "Los cruces no demuestran causalidad ni justifican por si solos una intervencion."
        ],
    }
    (OUT / "hallazgos_preliminares_cuidados.json").write_text(
        json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"LISTO: {len(result)} indicadores exploratorios; universo observado n={n}.")
    for row in result:
        print(f"{row['indicador_exploratorio']}: {row['casos']}/{n} ({row['porcentaje_muestral_sin_ponderar']}%)")
    print(f"REPORTES: {OUT}")
    print("Resultados no ponderados. Pendientes: diseno muestral, territorios y piloto.")


if __name__ == "__main__":
    main()
