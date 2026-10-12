"""Diagnostico NO ponderado de aplicabilidad para indicadores de ENASIC 2022.

Contrasta variables objetivo con filtros/proxies presentes en TPOB_CUI.
No decide automaticamente universos definitivos ni elimina observaciones.
Referencia: cuestionario ENASIC 2022, seccion 6 (INEGI).
"""
from __future__ import annotations
import csv
import io
import json
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "01_DATOS_RAW/INEGI/ENASIC_2022/conjunto_de_datos_enasic_2022_csv.zip"
DEST = ROOT / "08_DOCUMENTACION/auditorias/ENASIC_2022"
TARGETS = ["P6_7", "P6_8", "P6_12_2", "P6_12_5", "P6_39_1"]
FILTER_CANDIDATES = ["P6_1", "FILTRO10", "FILTRO_10", "P6_38", "P6_13",
                     "P6_15", "P6_17", "P6_19", "P6_21"]
QUESTIONNAIRE = "https://www.inegi.org.mx/contenidos/programas/enasic/2022/doc/enasic_2022_cuestionario.pdf"


def write_csv(name, data, fields):
    with (DEST / name).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(data)


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    with ZipFile(SOURCE) as z:
        found = [n for n in z.namelist() if "/conjunto_de_datos/" in n.lower()
                 and n.lower().endswith("conjunto_de_datos_tpob_cui_enasic_2022.csv")]
        if len(found) != 1:
            raise SystemExit(f"No se identifico una unica tabla TPOB_CUI: {len(found)}")
        with z.open(found[0]) as data:
            reader = csv.DictReader(io.TextIOWrapper(data, encoding="utf-8-sig", newline=""))
            columns = reader.fieldnames or []
            missing = [v for v in TARGETS if v not in columns]
            if missing:
                raise SystemExit(f"Variables no encontradas: {missing}")
            filters = [c for c in FILTER_CANDIDATES if c in columns]
            summaries = {t: Counter() for t in TARGETS}
            cross = {(t, f): Counter() for t in TARGETS for f in filters}
            count = 0
            for record in reader:
                count += 1
                for t in TARGETS:
                    value = (record.get(t) or "").strip()
                    summaries[t]["blanco" if not value else "respondido"] += 1
                    for f in filters:
                        group = (record.get(f) or "").strip() or "[BLANCO]"
                        cross[(t, f)][(group, "blanco" if not value else "respondido")] += 1

    overview = []
    for t in TARGETS:
        overview.append({
            "tabla": "TPOB_CUI", "variable": t,
            "filas_en_tabla": count,
            "con_respuesta": summaries[t]["respondido"],
            "sin_respuesta": summaries[t]["blanco"],
            "porcentaje_sin_respuesta": round(
                100 * summaries[t]["blanco"] / count, 2) if count else 0,
            "universo_verificado": "NO",
            "nota": "No interpretar blancos como cero o no respuesta sin verificar rutas del cuestionario."
        })
    write_csv("diagnostico_universos_inicial.csv", overview, list(overview[0]))
    detail = []
    for (target, f), counts in cross.items():
        for (value, response), n in sorted(counts.items()):
            detail.append({
                "variable_objetivo": target, "variable_exploratoria": f,
                "codigo_exploratorio": value, "estado_objetivo": response,
                "registros_no_ponderados": n,
                "interpretacion_filtro": "PENDIENTE_VERIFICACION_MANUAL"
            })
    write_csv("cruces_exploratorios_filtros.csv", detail, [
        "variable_objetivo", "variable_exploratoria",
        "codigo_exploratorio", "estado_objetivo",
        "registros_no_ponderados", "interpretacion_filtro"
    ])
    (DEST / "protocolo_universos.json").write_text(json.dumps({
        "fuente_cuestionario": QUESTIONNAIRE,
        "tabla": "TPOB_CUI",
        "variables_objetivo": TARGETS,
        "campos_exploratorios_presentes": filters,
        "filtros_confirmados_en_microdatos": [],
        "reglas_del_cuestionario_por_verificar": [
            "6.7 y 6.12: confirmar acceso desde identificacion de cuidador de discapacidad y seccion 6",
            "6.8a: solo si 6.8 corresponde a respuesta si",
            "6.39: examinar FILTRO 10, que precede a 6.38-6.40"
        ],
        "limitaciones": [
            "Cruces son diagnosticos y no prueban elegibilidad.",
            "No hacer estimaciones poblacionales con estas cifras.",
            "Los campos FILTRO10/P6_1 son candidatos exploratorios, no filtros certificados.",
            "No se permite imputar blancos ni utilizar codigos de otra tabla."
        ]
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Tabla TPOB_CUI: {count:,} registros")
    print("Campos exploratorios presentes:", ", ".join(filters) if filters else "NINGUNO")
    for row in overview:
        print(f"{row['variable']}: {row['con_respuesta']:,} respondidos; {row['sin_respuesta']:,} blancos")
    print("Reportes guardados:", DEST)
    print("IMPORTANTE: diagnostico exploratorio, NO validacion final de universos.")


if __name__ == "__main__":
    main()
