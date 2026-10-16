"""Reproduce 24 estimaciones ENUT 2024 sin usar R ni survey.

Validación NUMÉRICA cruzada de estimadores y errores estándar Taylor,
con estratos y UPM anidados. Para dominios por sexo conserva TODOS los
conglomerados de la muestra completa con aportaciones cero fuera del dominio.

Entrada: archivos locales NO versionados en 08_DOCUMENTACION/auditorias/ENUT_2024.
Salida: solo un JSON agregado con diferencias máximas y estatus.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "08_DOCUMENTACION/auditorias/ENUT_2024"
INPUT = DIRECTORY / "base_minima_enut_2024_para_R.csv"
R_RESULTS = DIRECTORY / "indicadores_cuidados_ponderados_preliminares.csv"
OUTPUT = DIRECTORY / "validacion_independiente_python_R_enut_2024.json"
VARIABLES = {
    "cuid_esp_int_hog_sin_cp",
    "cuid_esp_int_hog_con_cp",
    "trab_no_rem_cuid_hog",
    "cuid_esp_disc_enf",
}
GROUPS = {"total", "mujeres", "hombres"}
MEASURES = {"participacion_porcentaje", "media_condicional_unidad_original"}
EXPECTED = {(g, v, m) for g in GROUPS for v in VARIABLES for m in MEASURES}


def main() -> None:
    if not INPUT.is_file() or not R_RESULTS.is_file():
        raise SystemExit("Faltan CSV locales de insumo o resultados de R")
    data = pd.read_csv(INPUT, dtype={"est_dis": "string", "upm_dis": "string"})
    results = pd.read_csv(R_RESULTS)

    if len(data) != 74053 or len(results) != 24:
        raise ValueError("Conteos inesperados")
    identifiers = list(zip(results.grupo, results.variable, results.medida))
    if len(set(identifiers)) != 24 or set(identifiers) != EXPECTED:
        raise ValueError("No hay exactamente las 24 combinaciones esperadas")
    if set(data.sexo.unique()) != {1, 2}:
        raise ValueError("Codigos sexo desconocidos")
    for field in VARIABLES | {"fac_per"}:
        if not np.isfinite(data[field]).all() or data[field].lt(0).any():
            raise ValueError(f"Numericos invalidos en {field}")
    if data.fac_per.le(0).any():
        raise ValueError("Factores no positivos")

    full_psu = data[["est_dis", "upm_dis"]].drop_duplicates()
    nh = full_psu.groupby("est_dis").size()
    if int((nh < 2).sum()):
        raise ValueError("Estratos solitarios en muestra total")

    w = data.fac_per.to_numpy(dtype=float)
    max_point = max_se = max_cv = 0.0
    checked = 0
    for row in results.itertuples(index=False):
        if row.grupo == "total":
            domain = np.ones(len(data), dtype=float)
        else:
            sex = 2 if row.grupo == "mujeres" else 1
            domain = data.sexo.eq(sex).to_numpy(dtype=float)

        raw = data[row.variable].to_numpy(dtype=float)
        activity = (raw > 0).astype(float)
        if row.medida == "participacion_porcentaje":
            numerator = w * domain * activity
            denominator = w * domain
            scale = 100.0
        else:
            numerator = w * domain * raw
            denominator = w * domain * activity
            scale = 1.0

        denom_sum = denominator.sum()
        if denom_sum <= 0:
            raise ValueError("Denominador no positivo")
        ratio = numerator.sum() / denom_sum
        estimate = ratio * scale

        # UPM anidadas dentro de estratos. Las contribuciones fuera del
        # dominio son cero, pero sus conglomerados siguen presentes.
        contributions = pd.DataFrame({
            "estrato": data.est_dis.to_numpy(),
            "upm": data.upm_dis.to_numpy(),
            "linearizado": numerator - ratio * denominator,
        })
        psus = contributions.groupby(["estrato", "upm"], sort=False)[
            "linearizado"
        ].sum().reset_index()
        psus["centrado"] = psus.linearizado - psus.groupby(
            "estrato"
        ).linearizado.transform("mean")
        cluster_counts = psus.groupby("estrato").linearizado.transform("size")
        variance = float(np.sum(
            (cluster_counts / (cluster_counts - 1)) * psus.centrado ** 2
        )) / (denom_sum ** 2)
        se = float(np.sqrt(variance) * scale)
        cv = se / estimate if estimate > 0 else float("nan")

        positive = int(np.sum((activity > 0) & (domain > 0)))
        n_group = int(domain.sum())

        # Como en subset(svydesign) de R, grados de libertad del dominio
        # dependen de PSU con observaciones en el dominio. El calculo SE
        # conserva el universo original de PSU.
        sub = data.loc[domain.astype(bool), ["est_dis", "upm_dis"]].drop_duplicates()
        df_expected = len(sub) - sub.est_dis.nunique()
        comparisons = [
            ("estimacion", estimate, row.estimacion, 1e-9),
            ("error_estandar", se, row.error_estandar, 1e-9),
            ("cv", cv, row.cv, 1e-9),
        ]
        for label, recalculated, reported, tolerance in comparisons:
            if not np.isfinite(reported) or abs(recalculated - reported) > tolerance:
                raise ValueError(
                    f"Discrepancia {label} en {row.grupo}/{row.variable}/{row.medida}: "
                    f"{recalculated} vs {reported}"
                )
        if positive != row.n_positivos or n_group != row.n_muestra:
            raise ValueError("Conteos del dominio no coinciden")
        if df_expected != row.grados_libertad:
            raise ValueError("Grados de libertad inconsistentes")
        if not row.lim_inf_95 <= row.estimacion <= row.lim_sup_95:
            raise ValueError("Intervalo de confianza no contiene estimacion")
        if abs((row.lim_sup_95-row.estimacion) -
               (row.estimacion-row.lim_inf_95)) > 1e-9:
            raise ValueError("Intervalo de confianza no simetrico")
        max_point = max(max_point, abs(estimate - row.estimacion))
        max_se = max(max_se, abs(se - row.error_estandar))
        max_cv = max(max_cv, abs(cv - row.cv))
        checked += 1

    report = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "estado": "COINCIDENCIA_NUMERICA_24_DE_24",
        "metodo": "Taylor de conglomerados estratificados con linealizacion de razon",
        "origen": "Python numpy/pandas; cotejado contra R survey",
        "n_registros": len(data),
        "n_estratos": int(nh.size),
        "n_psu_por_estrato_en_total": int(len(full_psu)),
        "indicadores_recalculados": checked,
        "diferencia_maxima_estimacion": max_point,
        "diferencia_maxima_error_estandar": max_se,
        "diferencia_maxima_cv": max_cv,
        "advertencias": [
            "Validacion numerica, NO certificacion oficial del INEGI.",
            "Los intervalos fueron verificados por consistencia interna, "
            "no contra intervalos oficiales.",
            "Falta documentar criterios de publicacion y universos exactos.",
            "No hay indicadores especificos de discapacidad intelectual.",
            "Los microdatos CSV de entrada permanecen locales."
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print("VALIDACION INDEPENDIENTE COMPLETADA:", checked, "indicadores")
    print("DIFERENCIA MAXIMA ESTIMACION:", max_point)
    print("DIFERENCIA MAXIMA SE:", max_se)
    print("REPORTE:", OUTPUT)


if __name__ == "__main__":
    main()
