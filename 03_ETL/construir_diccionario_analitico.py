"""Construye un inventario analitico trazable desde diccionarios INEGI ENASIC 2022.

No procesa microdatos, no asigna significados a codigos ni calcula indicadores.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "02_DICCIONARIOS" / "ENASIC_2022"
DEST = ROOT / "08_DOCUMENTACION" / "auditorias" / "ENASIC_2022"

# Hipotesis de relevancia para el observatorio. No son definiciones oficiales.
FOCUS = {
    "TCSDEMPO": {
        "P3_8": "condicion_y_autonomia", "P3_8A": "autonomia",
        "P4_3": "red_de_cuidados", "P4_3A": "red_de_cuidados",
        "P4_30": "red_de_cuidados", "P4_32": "economia_del_cuidado",
        "P4_33": "economia_del_cuidado", "P4_39": "necesidades_de_cuidado",
    },
    "THOGAR": {"HN_CDISC": "necesidades_de_cuidado"},
    "TPOB_CUI": {
        "P6_7": "carga_de_cuidados", "P6_8": "economia_del_cuidado",
        "P6_8A": "economia_del_cuidado", "P6_9_3": "capacitacion",
        "P6_39_1": "bienestar_del_cuidador",
        "P6_45_03": "acceso_a_servicios", "COND_DISC": "condicion_y_autonomia",
    },
    "TPER_ELE": {"COND_DISC": "condicion_y_autonomia",
                 "P6_45_03": "acceso_a_servicios"},
    "THOG_UNIP": {"COND_DISC": "condicion_y_autonomia",
                  "P6_45_03": "acceso_a_servicios"},
}
KEYWORDS = {
    "autonomia": ("independiente", "autonomia", "dependencia"),
    "necesidades_de_cuidado": ("necesita cuidados", "necesidad de cuidados"),
    "carga_de_cuidados": ("horas", "tiempo que dedica", "carga"),
    "economia_del_cuidado": ("economico", "pagan", "pago", "trabaj", "ingreso"),
    "red_de_cuidados": ("cuidador", "cuidadora", "persona de otro hogar"),
    "acceso_a_servicios": ("servicios", "guarderia", "centro de dia"),
    "bienestar_del_cuidador": ("satisfecha", "tiempo libre", "salud"),
}


def classify(table: str, var: str, question: str) -> tuple[str, str]:
    if var in ("LLAVEVIV", "LLAVEHOG", "LLAVESDE", "LLAVEMOD"):
        return "identificacion", "identificador"
    if var.startswith("FAC_"):
        return "factor_de_expansion", "factor"
    if var in FOCUS.get(table, {}):
        return FOCUS[table][var], "prioritaria"
    normalized = question.casefold()
    for domain, words in KEYWORDS.items():
        if any(w in normalized for w in words):
            return domain, "candidata_automatica"
    return "sin_clasificar", "inventario"


def main() -> None:
    expected = ("TCSDEMPO", "THOGAR", "THOG_UNIP", "TPER_ELE",
                "TPOB_CUI", "TVIVIENDA")
    DEST.mkdir(parents=True, exist_ok=True)
    found = set()
    output = []
    for file in sorted(SOURCE.glob("diccionario_datos_*_enasic_2022.csv")):
        table = file.stem.removeprefix("diccionario_datos_").removesuffix("_enasic_2022").upper()
        if table not in expected or table in found:
            raise SystemExit(f"Nombre de diccionario desconocido o repetido: {file.name}")
        found.add(table)
        with file.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            required = {"nombre_campo", "longitud", "tipo", "nemónico", "catálogo", "rango_claves"}
            if not required.issubset(set(reader.fieldnames or [])):
                raise SystemExit(f"Encabezados no esperados en {file.name}: {reader.fieldnames}")
            seen = set()
            for entry in reader:
                var = (entry.get("nemónico") or "").strip().upper()
                if not var:
                    raise SystemExit(f"Nemónico vacío en {file.name}")
                if var in seen:
                    raise SystemExit(f"Nemónico repetido en {file.name}: {var}")
                seen.add(var)
                question = (entry.get("nombre_campo") or "").strip()
                domain, priority = classify(table, var, question)
                output.append({
                    "tabla": table, "variable": var,
                    "descripcion_oficial": question,
                    "tipo_oficial": (entry.get("tipo") or "").strip(),
                    "longitud_oficial": (entry.get("longitud") or "").strip(),
                    "catalogo_referenciado": (entry.get("catálogo") or "").strip(),
                    "rango_claves_oficial": (entry.get("rango_claves") or "").strip(),
                    "dimension_propuesta": domain, "seleccion": priority,
                    "interpretacion_codigos": "PENDIENTE_CATALOGO",
                    "filtros_aplicabilidad": "PENDIENTE_CUESTIONARIO",
                    "validacion_metodologica": "PENDIENTE",
                })
    if found != set(expected):
        raise SystemExit(f"Diccionarios faltantes: {sorted(set(expected) - found)}")

    headers = list(output[0])
    inventory = DEST / "diccionario_analitico_completo.csv"
    with inventory.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(output)

    candidates = [r for r in output if r["seleccion"] in ("prioritaria", "candidata_automatica")]
    with (DEST / "variables_candidatas.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(candidates)

    counts = Counter(r["tabla"] for r in output)
    priorities = Counter(r["seleccion"] for r in output)
    print("Diccionarios procesados:", len(found))
    for table in sorted(counts):
        print(f"  {table}: {counts[table]} variables")
    print("Variables totales:", len(output))
    print("Prioritarias:", priorities["prioritaria"])
    print("Candidatas por palabras clave (sin validar):", priorities["candidata_automatica"])
    print("Archivos generados:")
    print(" ", inventory)
    print(" ", DEST / "variables_candidatas.csv")
    print("IMPORTANTE: clasificaciones propuestas; sin decodificar catalogos, filtros ni universos.")


if __name__ == "__main__":
    main()
