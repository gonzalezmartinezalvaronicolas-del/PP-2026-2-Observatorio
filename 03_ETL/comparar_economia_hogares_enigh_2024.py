"""ENIGH 2024: comparación económica DESCRIPTIVA entre grupos de hogares.

No pondera ni estima poblaciones. No interpreta dificultades funcionales
como diagnóstico intelectual y conserva las unidades originales de ENIGH.
No exporta llaves de hogares, registros individuales ni microdatos.
"""
from __future__ import annotations
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "01_DATOS_RAW/INEGI/ENIGH_2024/conjunto_de_datos_enigh2024_ns_csv.zip"
BASE = ROOT / "05_BASE_ANALITICA/ENIGH_2024/hogares_economica_preliminar.parquet"
OUT = ROOT / "08_DOCUMENTACION/auditorias/ENIGH_2024/comparacion_economica_exploratoria.json"
KEY = ["folioviv", "foliohog"]
FUNCTIONAL = ["disc_apren", "disc_habla", "disc_acti"]
MONEY = {
    "ingreso_corriente": "ing_cor_num",
    "gasto_monetario": "gasto_mon_num",
    "gasto_salud": "salud_num",
    "gasto_alimentacion": "alimentos_num",
    "gasto_cuidados_personales": "cuidados_num",
}

def source_name(z):
    candidates = [
        n for n in z.namelist()
        if "/conjunto_de_datos/" in n.lower()
        and n.lower().endswith(".csv")
        and Path(n).stem.lower().replace("conjunto_de_datos_", "")
            .replace("_enigh2024_ns", "") == "poblacion"
    ]
    if len(candidates) != 1:
        raise ValueError("No fue posible encontrar exactamente un CSV de población.")
    return candidates[0]

def summaries(data):
    result = {"hogares_muestra": len(data), "variables": {}}
    for label, field in MONEY.items():
        vals = pd.to_numeric(data[field], errors="coerce")
        if vals.isna().any():
            raise ValueError(f"Montos faltantes o no numéricos en {field}")
        result["variables"][label] = {
            "media_sin_ponderar": float(vals.mean()),
            "mediana_sin_ponderar": float(vals.median()),
            "hogares_gasto_o_ingreso_cero": int(vals.eq(0).sum()),
        }
    return result

def main():
    h = pd.read_parquet(BASE)
    if len(h) != 91414 or h.duplicated(KEY).any():
        raise ValueError("Base hogar inválida o número inesperado de registros")
    with zipfile.ZipFile(ZIP) as z, z.open(source_name(z)) as f:
        p = pd.read_csv(
            f, usecols=KEY + ["numren"] + FUNCTIONAL, dtype="string",
            keep_default_na=False, low_memory=False, encoding="utf-8-sig"
        )
    if len(p) != 308598 or p.duplicated(KEY + ["numren"]).any():
        raise ValueError("Base población inválida")
    # No transformar & a 1 ni interpretarlo como ausencia de dificultad.
    unexpected = {}
    for field in FUNCTIONAL:
        unusual = set(p[field].dropna().unique()) - {"1", "2", "3", "4", "&"}
        if unusual:
            unexpected[field] = sorted(unusual)
    if unexpected:
        raise ValueError(f"Códigos imprevistos: {unexpected}")
    flags = p[KEY].copy()
    for field in FUNCTIONAL:
        flags[field + "_grave"] = p[field].isin(["3", "4"])
    flags["alguna_grave"] = flags[[x+"_grave" for x in FUNCTIONAL]].any(axis=1)
    hh_flags = flags.groupby(KEY, sort=False).agg({
        field + "_grave": "any" for field in FUNCTIONAL
    } | {"alguna_grave": "any"}).reset_index()
    hh = h.merge(hh_flags, on=KEY, how="left", validate="one_to_one")
    if len(hh) != len(h) or hh["alguna_grave"].isna().any():
        raise ValueError("Unión hogar-persona incompleta")
    groups = {
        "total_hogares": pd.Series(True, index=hh.index),
        "alguna_dificultad_grave_en_tres_actividades": hh["alguna_grave"],
        "sin_dificultad_grave_en_tres_actividades": ~hh["alguna_grave"],
        "alguna_dificultad_recordar_concentrarse": hh["disc_apren_grave"],
        "alguna_dificultad_hablar_comunicarse": hh["disc_habla_grave"],
        "alguna_dificultad_actividades_cotidianas": hh["disc_acti_grave"],
    }
    output = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "estado": "COMPARACION_DESCRIPTIVA_SIN_PONDERAR",
        "fuente": "ENIGH 2024 Nueva Serie",
        "hogares_muestra": len(hh),
        "personas_muestra": len(p),
        "grupos": {name: summaries(hh.loc[mask]) for name, mask in groups.items()},
        "advertencias": [
            "Descriptivos de la muestra; no representan totales o medias nacionales.",
            "Los grupos por actividad se superponen y no deben sumarse.",
            "El grupo sin dificultad grave puede contener respuesta & y dificultad leve.",
            "Ningún indicador identifica diagnósticos de discapacidad intelectual.",
            "Los montos permanecen en la unidad/periodo del concentrado original: validar en documentación INEGI antes de etiquetar o comparar con otras fuentes.",
            "El rubro cuidados corresponde a gasto en cuidados personales, no cuidados no remunerados.",
            "No es evidencia causal de efectos económicos de discapacidad o cuidados."
        ]
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print("COMPARACION ECONOMICA EXPLORATORIA ENIGH 2024")
    for name, stats in output["grupos"].items():
        print(f"{name}: {stats['hogares_muestra']:,} hogares muestrales")
        print(f"  ingreso mediana (unidad original): {stats['variables']['ingreso_corriente']['mediana_sin_ponderar']:,.2f}")
        print(f"  salud mediana (unidad original): {stats['variables']['gasto_salud']['mediana_sin_ponderar']:,.2f}")
    print("REPORTE:", OUT)
    print("SIN PONDERACION; SIN INTERPRETACION CAUSAL O DIAGNOSTICA.")

if __name__ == "__main__":
    main()
