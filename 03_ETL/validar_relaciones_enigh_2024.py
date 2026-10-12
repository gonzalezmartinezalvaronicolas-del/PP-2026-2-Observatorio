"""ENIGH 2024: auditar relaciones y diseño entre hogar y persona.

Usa CSV originales dentro del ZIP. No publica microdatos, ni nombres de
identificadores. Reporta conteos agregados sin cálculos poblacionales.
"""
from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "01_DATOS_RAW/INEGI/ENIGH_2024/conjunto_de_datos_enigh2024_ns_csv.zip"
OUT = ROOT / "08_DOCUMENTACION/auditorias/ENIGH_2024"
FIELDS = {
    "concentradohogar": ["folioviv", "foliohog", "est_dis", "upm", "factor",
                         "ing_cor", "gasto_mon", "salud", "cuidados", "tot_integ"],
    "hogares": ["folioviv", "foliohog", "est_dis", "upm", "factor"],
    "poblacion": ["folioviv", "foliohog", "numren", "est_dis", "upm", "factor",
                  "disc_apren", "disc_habla", "disc_acti"],
}
HK = ["folioviv", "foliohog"]
PK = HK + ["numren"]
DESIGN = ["est_dis", "upm", "factor"]


def member(z, table):
    candidates = [n for n in z.namelist()
                  if n.lower().endswith(".csv") and
                  "/conjunto_de_datos/" in n.lower() and
                  Path(n).stem.lower().replace("conjunto_de_datos_", "")
                  .replace("_enigh2024_ns", "") == table]
    if len(candidates) != 1:
        raise ValueError(f"Esperaba un CSV para {table}, hallé {len(candidates)}")
    return candidates[0]


def load(z, table):
    with z.open(member(z, table)) as f:
        df = pd.read_csv(f, usecols=FIELDS[table], dtype="string",
                         keep_default_na=False, low_memory=False, encoding="utf-8-sig")
    return df


def profile(df, table, key):
    bad_key = df[key].eq("").any(axis=1).sum()
    key_dupes = df.duplicated(subset=key).sum()
    missing_design = {c: int(df[c].eq("").sum()) for c in DESIGN}
    weights = pd.to_numeric(df["factor"], errors="coerce")
    invalid_weight = int((weights.isna() | weights.le(0)).sum())
    return {"tabla": table, "registros": len(df),
            "clave": "+".join(key), "llaves_incompletas": int(bad_key),
            "claves_duplicadas": int(key_dupes),
            "faltantes_campos_diseno": missing_design,
            "factores_no_numericos_o_no_positivos": invalid_weight,
            "estratos_distintos": int(df["est_dis"].nunique()),
            "upm_distintas": int(df["upm"].nunique())}


def compare(base, other, base_name, other_name, key):
    b = base[key + DESIGN].rename(columns={c: c+"_base" for c in DESIGN})
    o = other[key + DESIGN].rename(columns={c: c+"_otro" for c in DESIGN})
    match = o.merge(b, on=key, how="left", validate="many_to_one",
                    indicator=True)
    paired = match["_merge"].eq("both")
    inconsistent = {}
    for field in DESIGN:
        different = match[field+"_otro"].ne(match[field+"_base"]) & paired
        inconsistent[field] = int(different.fillna(False).sum())
    return {"relacion": other_name+" -> "+base_name, "campos_llave": key,
            "registros_origen": len(other),
            "registros_sin_hogar_correspondiente": int((~paired).sum()),
            "inconsistencias_diseno_en_coincidentes": inconsistent}


def main():
    if not ARCHIVE.is_file():
        raise SystemExit(f"No existe ZIP: {ARCHIVE}")
    with zipfile.ZipFile(ARCHIVE) as z:
        h = load(z, "concentradohogar")
        ho = load(z, "hogares")
        p = load(z, "poblacion")

    tables = [profile(h, "concentradohogar", HK),
              profile(ho, "hogares", HK),
              profile(p, "poblacion", PK)]
    for t in tables:
        print(f"{t['tabla']}: {t['registros']:,} filas; claves duplicadas: "
              f"{t['claves_duplicadas']}; llaves incompletas: {t['llaves_incompletas']}")
    if h.duplicated(HK).any():
        raise ValueError("La clave de concentradohogar no es única; no efectuar unión.")
    if ho.duplicated(HK).any():
        raise ValueError("La clave de hogares no es única; no efectuar unión.")

    relations = [compare(h, ho, "concentradohogar", "hogares", HK),
                 compare(h, p, "concentradohogar", "poblacion", HK)]
    households_in_p = p[HK].drop_duplicates()
    h_without_person = h[HK].merge(households_in_p, on=HK, how="left",
                                   indicator=True)["_merge"].eq("left_only").sum()
    report = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "estado": "AUDITORIA_RELACIONES_SIN_ESTIMACIONES",
        "tablas": tables,
        "relaciones": relations,
        "hogares_concentrado_sin_personas_poblacion": int(h_without_person),
        "advertencias": [
            "Validación técnica de cardinalidad, claves y campos, no de universos estadísticos.",
            "Posibles discrepancias de factor por unidad analítica deben revisarse contra diccionario.",
            "No interpretar disc_apren ni disc_habla como diagnóstico intelectual.",
            "No se estiman ingresos ni gastos nacionales en este paso.",
            "No publicar identificadores de microdatos."
        ]}
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "diagnostico_relaciones_enigh_2024.json"
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    for rel in relations:
        print(rel["relacion"] + ": faltantes="
              + str(rel["registros_sin_hogar_correspondiente"])
              + "; discrepancias diseño=" + str(rel["inconsistencias_diseno_en_coincidentes"]))
    print(f"Hogares sin personas en poblacion: {h_without_person}")
    print("REPORTE:", dest)
    print("SIN ESTIMACIONES POBLACIONALES. Validar definiciones con INEGI.")


if __name__ == "__main__":
    main()
