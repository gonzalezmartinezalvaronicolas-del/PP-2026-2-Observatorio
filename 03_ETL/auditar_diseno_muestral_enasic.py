"""Auditoria reproducible del diseno muestral ENASIC 2022.

Inspecciona todas las tablas Parquet ya validadas y el grupo observado
P6_1=1, sin calcular estimaciones ni modificar microdatos. Solo exporta
metadatos y diagnosticos agregados.
"""
from __future__ import annotations
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "04_DATOS_LIMPIOS/ENASIC_2022"
OUT = ROOT / "08_DOCUMENTACION/auditorias/ENASIC_2022"
TABLES = ("tcsdempo", "thog_unip", "thogar", "tper_ele", "tpob_cui", "tvivienda")
PATTERN = re.compile(r"FAC_|FACTOR|ESTRAT|EST_DIS|UPM|CONGLOM|DOMINIO|ENTIDAD|ZONA|TAM_LOC", re.I)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    field_rows = []
    for table in TABLES:
        path = DATA / f"{table}.parquet"
        if not path.is_file():
            raise SystemExit(f"Falta {path}. Ejecuta antes limpiar_enasic.py")
        metadata = pq.ParquetFile(path)
        fields = metadata.schema_arrow.names
        for column in fields:
            if PATTERN.search(column):
                field_rows.append({
                    "tabla": table.upper(), "variable": column,
                    "observaciones_tabla": metadata.metadata.num_rows,
                    "clasificacion": "CANDIDATA_POR_NOMBRE_NO_VALIDADA"
                })
        print(f"{table.upper()}: {metadata.metadata.num_rows:,} registros; "
              f"columnas candidatas de diseno/factor: "
              f"{', '.join(f for f in fields if PATTERN.search(f)) or 'NINGUNA'}")

    path = DATA / "tpob_cui.parquet"
    columns = pq.read_schema(path).names
    if "P6_1" not in columns:
        raise SystemExit("TPOB_CUI no contiene P6_1")
    available = [c for c in columns if PATTERN.search(c)]
    df = pd.read_parquet(path, columns=["P6_1"] + available)
    scope = df["P6_1"].eq("1")
    if int(scope.sum()) != 636 or len(df) != 5677:
        raise SystemExit("Cambio inesperado en el grupo observado o los registros")

    diagnostics = []
    for column in available:
        for label, mask in (("TODA_TPOB_CUI", pd.Series(True, index=df.index)),
                            ("BLOQUE_P6_1_1", scope)):
            vals = df.loc[mask, column].fillna("").astype(str).str.strip()
            nonempty = vals[vals.ne("")]
            numeric = pd.to_numeric(nonempty, errors="coerce")
            is_factor = column.upper().startswith("FAC_") or column.upper() == "FACTOR"
            diagnostics.append({
                "variable": column,
                "grupo": label,
                "registros": int(mask.sum()),
                "no_vacios": len(nonempty),
                "vacios": int(vals.eq("").sum()),
                "codigos_unicos_no_vacios": int(nonempty.nunique()),
                "tipo_exploratorio": "factor_candidato" if is_factor else "diseno_o_geografia_candidato",
                "numericos_validos": int(numeric.notna().sum()) if is_factor else None,
                "pesos_no_positivos": int(numeric.le(0).sum()) if is_factor else None,
                "interpretacion": "POR_CONFIRMAR_CON_DOCUMENTACION_OFICIAL"
            })
    if not available:
        print("ADVERTENCIA: no hay campos de diseno detectados por nombre en TPOB_CUI")
    manifest = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "estado": "DIAGNOSTICO_NO_ESTIMACION",
        "fuente": "ENASIC 2022 — Parquet conservador local",
        "documentacion": [
            "https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/nueva_estruc/889463927082.pdf",
            "https://en.www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/nueva_estruc/889463909798.pdf"
        ],
        "hallazgo_documental": "FAC_CUI es factor de personas cuidadoras de 15 anios y mas; verificar universo y diseno antes de estimar.",
        "alerta_nomenclatura": "La guia describe FAC_SEL pero auditoria previa encontro FAC_ELE en TPER_ELE: comprobar contra diccionario original.",
        "registros_tpob_cui": len(df),
        "bloque_observado_p6_1_1": int(scope.sum()),
        "campos_candidatos_tpob_cui": available,
        "no_interpretar": [
            "Un campo candidato de estrato o UPM no es necesariamente el campo oficial del diseno",
            "No se aplicaron pesos, varianzas, errores estandar ni CV",
            "Un peso sin UPM/estrato verificados no autoriza intervalos de confianza",
            "Nunca calcular sumas de pesos como poblacion sin validar universo"
        ]
    }
    field_path = OUT / "campos_diseno_enasic.csv"
    with field_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["tabla", "variable", "observaciones_tabla", "clasificacion"])
        w.writeheader(); w.writerows(field_rows)
    diag_path = OUT / "diagnostico_diseno_tpob_cui.csv"
    with diag_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=[
            "variable", "grupo", "registros", "no_vacios", "vacios",
            "codigos_unicos_no_vacios", "tipo_exploratorio",
            "numericos_validos", "pesos_no_positivos", "interpretacion"
        ])
        w.writeheader(); w.writerows(diagnostics)
    manifest_path = OUT / "protocolo_diseno_muestral.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("AUDITORIA COMPLETA: no se generaron estimaciones.")
    print(f"RESULTADOS: {field_path.name}, {diag_path.name}, {manifest_path.name}")


if __name__ == "__main__":
    main()
