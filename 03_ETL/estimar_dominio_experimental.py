"""Estimador PILOTO de razon para dominio ENASIC 2022.

Conserva TODA la tabla TPOB_CUI al calcular contribuciones por UPM.
Calcula proporciones ponderadas con linealizacion de Taylor para estratos
y conglomerados ultimos. NO son cifras oficiales ni aptas para difusion:
falta verificacion independiente y confirmacion de base muestral INEGI.

Salida: resumen SOLO AGREGADO local en 08_DOCUMENTACION/auditorias.
"""
from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "04_DATOS_LIMPIOS/ENASIC_2022/tpob_cui.parquet"
OUT = ROOT / "08_DOCUMENTACION/auditorias/ENASIC_2022"
COLUMNS = [
    "EST_DIS", "UPM_DIS", "FAC_CUI", "P6_1", "P6_7", "P6_8",
    "P6_11_3", "P6_12_2", "P6_12_5", "P6_39_1",
]
METRICS = {
    "cansancio_si": lambda d: d["P6_11_3"].eq("1"),
    "dejar_trabajo_si": lambda d: d["P6_12_2"].eq("1"),
    "jornada_horario_si": lambda d: d["P6_12_5"].eq("1"),
    "alguna_dos_afectaciones_laborales": lambda d: (
        d["P6_12_2"].eq("1") | d["P6_12_5"].eq("1")
    ),
    "cuidado_40_horas_o_mas": lambda d: pd.to_numeric(
        d["P6_7"], errors="coerce"
    ).ge(40),
    "sin_apoyo_familiar": lambda d: d["P6_8"].eq("2"),
    "insatisfaccion_tiempo_libre": lambda d: d["P6_39_1"].eq("2"),
}


def linearized_domain_ratio(
    strata: np.ndarray, psu: np.ndarray, weights: np.ndarray,
    domain: np.ndarray, indicator: np.ndarray
) -> dict:
    """Varianza Taylor por conglomerados ultimos, sin correccion FPC.

    Estimador R = sum(w*d*y)/sum(w*d).
    z_hi = sum_(j en UPM hi) w_j*d_j*(y_j - R).
    V(R) = sum_h [m_h/(m_h-1) sum_i (z_hi-z_bar_h)^2] / Den^2.
    Se conservan UPM con 0 casos del dominio, contribucion z=0.
    """
    if not all(len(v) == len(weights) for v in (strata, psu, domain, indicator)):
        raise ValueError("Dimensiones incompatibles")
    if not np.isfinite(weights).all() or (weights <= 0).any():
        raise ValueError("Ponderadores invalidos")
    if not np.isin(indicator[domain], [0, 1]).all():
        raise ValueError("Indicador no binario en dominio")
    w_domain = weights * domain.astype(float)
    denominator = float(w_domain.sum())
    if denominator <= 0:
        raise ValueError("Denominador ponderado vacio")
    ratio = float((w_domain * indicator).sum() / denominator)
    linear = w_domain * (indicator - ratio)

    # Mantener las UPM de TODOS los registros del marco de TPOB_CUI.
    clusters = pd.DataFrame({
        "estrato": strata, "upm": psu, "linear": linear
    }).groupby(["estrato", "upm"], sort=False, observed=True)["linear"].sum()
    psu_table = clusters.reset_index()
    nh = psu_table.groupby("estrato", observed=True)["upm"].size()
    singleton = nh[nh < 2]
    if not singleton.empty:
        raise ValueError(
            f"Estratos con menos de dos UPM en base de diseno: {len(singleton)}"
        )
    centered = psu_table["linear"] - psu_table.groupby(
        "estrato", observed=True
    )["linear"].transform("mean")
    sizes = psu_table["estrato"].map(nh).astype(float)
    var = float(((sizes / (sizes - 1)) * centered.pow(2)).sum()
                / (denominator ** 2))
    if var < 0 or not math.isfinite(var):
        raise ValueError("Varianza invalida")
    se = math.sqrt(var)
    return {
        "estimacion_ponderada_experimental": ratio,
        "error_estandar_taylor_experimental": se,
        "cv_experimental": (se / ratio if ratio > 0 else None),
        "li_95_normal_sin_truncar": ratio - 1.96 * se,
        "ls_95_normal_sin_truncar": ratio + 1.96 * se,
        "denominador_ponderado_experimental": denominator,
        "estratos_base_diseno": int(len(nh)),
        "pares_estrato_upm_base_diseno": int(len(psu_table)),
    }


def test_formula() -> None:
    # Un estrato, dos UPM, una observacion por UPM, pesos=1, y=[1,0].
    # R=.5; z=[.5,-.5]; V=2*(.5)/4=.25.
    trial = linearized_domain_ratio(
        np.array(["s", "s"]), np.array(["a", "b"]),
        np.array([1.0, 1.0]), np.array([True, True]),
        np.array([1.0, 0.0])
    )
    assert math.isclose(trial["estimacion_ponderada_experimental"], .5)
    assert math.isclose(trial["error_estandar_taylor_experimental"], .5)
    # Incluir una UPM sin dominio: el marco permanece con dos UPM.
    other = linearized_domain_ratio(
        np.array(["s", "s"]), np.array(["a", "b"]),
        np.array([1.0, 1.0]), np.array([True, False]),
        np.array([1.0, 0.0])
    )
    assert other["pares_estrato_upm_base_diseno"] == 2


def main() -> None:
    test_formula()
    if not SOURCE.exists():
        raise SystemExit(f"No se encontro: {SOURCE}")
    df = pd.read_parquet(SOURCE, columns=COLUMNS)
    if len(df) != 5677:
        raise ValueError(f"Numero inesperado de filas: {len(df)}")
    for field in ["EST_DIS", "UPM_DIS", "FAC_CUI"]:
        if df[field].isna().any() or df[field].eq("").any():
            raise ValueError(f"Campo del diseno incompleto: {field}")
    weight = pd.to_numeric(df["FAC_CUI"], errors="coerce").to_numpy(dtype=float)
    domain = df["P6_1"].eq("1").to_numpy(dtype=bool)
    if int(domain.sum()) != 636:
        raise ValueError("Cambio de universo observado: distinto de 636")
    for column in ["P6_8", "P6_11_3", "P6_12_2", "P6_12_5", "P6_39_1"]:
        if not df.loc[domain, column].isin(["1", "2"]).all():
            raise ValueError(f"Codigos sin validar en {column}")

    answers = pd.to_numeric(df.loc[domain, "P6_7"], errors="coerce")
    if answers.isna().any() or answers.lt(1).any() or answers.gt(98).any():
        raise ValueError("P6_7 fuera de los codigos previstos 01..98")
    rows = []
    for name, make_indicator in METRICS.items():
        y = make_indicator(df).astype(int).to_numpy(dtype=float)
        result = linearized_domain_ratio(
            df["EST_DIS"].to_numpy(), df["UPM_DIS"].to_numpy(),
            weight, domain, y
        )
        rows.append({
            "indicador": name,
            "casos_si_en_dominio": int(y[domain].sum()),
            "registros_dominio": int(domain.sum()),
            **result,
            "estado": "EXPERIMENTAL_NO_VALIDADO",
        })
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / "estimadores_taylor_experimentales.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    metadata = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "estado": "EXPERIMENTAL_NO_VALIDADO",
        "base": str(SOURCE.relative_to(ROOT)),
        "registros_diseno_utilizados": len(df),
        "registros_dominio_p6_1_1": int(domain.sum()),
        "prueba_sintetica": "OK",
        "metodo_prototipo": "Razon ponderada; Taylor PSU dentro de estratos; sin FPC.",
        "advertencias": [
            "Resultados experimentales; no publicar ni integrar aun en dashboard.",
            "Validar documentalmente que TPOB_CUI sea la base del diseno pertinente.",
            "Verificar convenciones de varianza, dominio, grados de libertad y CV INEGI.",
            "Comparar con una herramienta estadistica independiente y resultados oficiales.",
            "Intervalos normales sin truncar no son intervalos certificados; pueden exceder [0,1].",
            "El marco TPOB_CUI solo incluye conglomerados presentes en esa tabla.",
            "No infiere discapacidad intelectual ni efectos causales."
        ],
    }
    json_path = OUT / "protocolo_estimador_experimental.json"
    json_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PRUEBA SINTETICA DE FORMULA: OK")
    print(f"BASE DE DISENO: {len(df):,} registros | DOMINIO OBSERVADO: {int(domain.sum())}")
    print(f"INDICADORES CALCULADOS SOLO EN MODO EXPERIMENTAL: {len(rows)}")
    print(f"RESULTADOS: {csv_path}")
    print(f"PROTOCOLO: {json_path}")
    print("NO UTILIZAR ESTAS ESTIMACIONES EN EL DASHBOARD O ENTREGABLES AUN.")


if __name__ == "__main__":
    main()
