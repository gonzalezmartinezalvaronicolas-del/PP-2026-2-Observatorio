"""Prepara base minima, local y anonima, para R survey ENUT 2024.

Separa cuidados dentro del hogar (con/sin pasivos) de ayuda a otros hogares.
No calcula indicadores ni sube microdatos al repositorio.
"""
from __future__ import annotations
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "01_DATOS_RAW/INEGI/ENUT_2024/conjunto_de_datos_enut_2024_csv.zip"
OUT = ROOT / "08_DOCUMENTACION/auditorias/ENUT_2024"
FIELDS = ["sexo", "edad", "est_dis", "upm_dis", "fac_per",
          "cuid_esp_int_hog_sin_cp", "cuid_esp_int_hog_con_cp",
          "trab_no_rem_cuid_hog", "cuid_esp_disc_enf"]
NUMERIC = ["fac_per", "cuid_esp_int_hog_sin_cp",
           "cuid_esp_int_hog_con_cp", "trab_no_rem_cuid_hog",
           "cuid_esp_disc_enf"]

def main():
    if not ZIP.is_file():
        raise SystemExit(f"No existe ZIP: {ZIP}")
    with zipfile.ZipFile(ZIP) as archive:
        paths = [p for p in archive.namelist()
                 if p.lower().endswith("/conjunto_de_datos_enut_2024_tvar_crea.csv")]
        if len(paths) != 1:
            raise ValueError(f"TVAR_CREA inesperada: {len(paths)} archivos")
        with archive.open(paths[0]) as handle:
            d = pd.read_csv(handle, usecols=FIELDS, dtype="string",
                            keep_default_na=False, encoding="utf-8-sig")
    if len(d) != 74053:
        raise ValueError(f"Registros inesperados: {len(d)}")
    if set(d.sexo.unique()) != {"1", "2"}:
        raise ValueError("Codigos sexo inesperados")
    ages = pd.to_numeric(d.edad, errors="coerce")
    if ages.isna().any() or ages.lt(12).any() or ages.gt(120).any():
        raise ValueError("Edad fuera del universo esperado")
    for key in ("est_dis", "upm_dis"):
        if d[key].eq("").any():
            raise ValueError(f"Campos vacios en {key}")
    for key in NUMERIC:
        values = pd.to_numeric(d[key], errors="coerce")
        if values.isna().any() or values.lt(0).any():
            raise ValueError(f"Numerico invalido: {key}")
        if key == "fac_per" and values.le(0).any():
            raise ValueError("FAC_PER debe ser positivo")
        d[key] = values
    strata_counts = d.groupby("est_dis").upm_dis.nunique()
    # No se descartan ni recodifican observaciones con tiempo > 168.
    report = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "estado": "EXPORTACION_LOCAL_NO_PUBLICABLE",
        "registros": int(len(d)),
        "estratos": int(strata_counts.size),
        "estratos_con_una_upm_muestra_completa": int(strata_counts.eq(1).sum()),
        "unidades_estrato_upm": int(len(d[["est_dis", "upm_dis"]].drop_duplicates())),
        "positivos_cuidados_propio_hogar_sin_cp": int(d.cuid_esp_int_hog_sin_cp.gt(0).sum()),
        "positivos_cuidados_propio_hogar_con_cp": int(d.cuid_esp_int_hog_con_cp.gt(0).sum()),
        "advertencia": "Archivo CSV local de insumo; no publicar como estimacion poblacional."
    }
    OUT.mkdir(parents=True, exist_ok=True)
    csvpath = OUT / "base_minima_enut_2024_para_R.csv"
    # Sin identificadores personales LLAVEHOG, N_REN ni llaves de viviendas.
    d[FIELDS].to_csv(csvpath, index=False, encoding="utf-8")
    meta = OUT / "control_exportacion_enut_2024_R.json"
    report["csv_sha256"] = hashlib.sha256(csvpath.read_bytes()).hexdigest()
    meta.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                    encoding="utf-8")
    print("ENUT EXPORTADA: ", report["registros"], "registros")
    print("ESTRATOS: ", report["estratos"],
          " | ESTRATOS SOLITARIOS: ", report["estratos_con_una_upm_muestra_completa"])
    print("INSUMO LOCAL: ", csvpath)
    print("CONTROL: ", meta)
    print("NO SUBIR EL CSV DE INSUMO A GITHUB.")

if __name__ == "__main__":
    main()
