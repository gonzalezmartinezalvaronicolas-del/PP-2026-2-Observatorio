"""Auditoria inicial de ENIGH 2024 Nueva Serie (CSV) directamente del ZIP.

No extrae ni publica microdatos; solo metadatos agregados localmente.
No estima poblaciones ni asume codificaciones de discapacidad.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "01_DATOS_RAW/INEGI/ENIGH_2024/conjunto_de_datos_enigh2024_ns_csv.zip"
OUT = ROOT / "08_DOCUMENTACION/auditorias/ENIGH_2024"
PRIORITARIAS = {"concentradohogar","poblacion","hogares","gastoshogar","gastospersona"}
ANCLAJES = ("folioviv","foliohog","numren")
CAMPOS_DISENO = ("factor","est_dis","upm")

def main():
    if not ZIP.is_file():
        raise SystemExit(f"No se encuentra el ZIP: {ZIP}")
    reportes = []
    with zipfile.ZipFile(ZIP) as z:
        archivos = [
            name for name in z.namelist()
            if "/conjunto_de_datos/" in name.lower() and name.lower().endswith(".csv")
        ]
        if not archivos:
            raise ValueError("No se encontraron CSV de microdatos en el ZIP")
        for name in sorted(archivos):
            tabla = Path(name).stem.replace("conjunto_de_datos_","").replace("_enigh2024_ns","")
            with z.open(name) as source:
                txt = io.TextIOWrapper(source,encoding="utf-8-sig",errors="replace",newline="")
                reader = csv.reader(txt)
                cabecera = next(reader)
                conteo = sum(1 for _ in reader)
            reportes.append({
                "tabla":tabla, "registros":conteo, "columnas":len(cabecera),
                "campos_clave_presentes":";".join(c for c in ANCLAJES if c in cabecera),
                "campos_diseno_presentes":";".join(c for c in CAMPOS_DISENO if c in cabecera),
                "prioridad":"PRIORITARIA" if tabla in PRIORITARIAS else "SECUNDARIA",
                "columnas_disponibles":";".join(cabecera),
                "ruta_en_zip":name,
            })
            print(f"{tabla}: {conteo:,} registros x {len(cabecera)} columnas")
    OUT.mkdir(parents=True,exist_ok=True)
    output = OUT/"inventario_tablas_enigh_2024.csv"
    with output.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=reportes[0].keys())
        writer.writeheader()
        writer.writerows(reportes)
    sha=hashlib.sha256()
    with ZIP.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            sha.update(chunk)
    metadata={
        "fecha_utc":datetime.now(timezone.utc).isoformat(),
        "fuente":"ENIGH 2024 Nueva Serie, paquete CSV",
        "zip":str(ZIP.relative_to(ROOT)),
        "sha256":sha.hexdigest(),
        "tablas":len(reportes),
        "tablas_prioritarias":sorted(PRIORITARIAS),
        "estado":"AUDITORIA_ESTRUCTURAL_SIN_ESTIMACIONES",
        "advertencias":[
            "Los conteos de diferentes tablas corresponden a diferentes unidades de analisis; no sumar como personas.",
            "Campos del diseno solo identificados por nombre; verificar documentacion oficial.",
            "Las variables de dificultad funcional no acreditan diagnostico de discapacidad intelectual.",
            "Sin validacion de relaciones, factores, universos, catálogos ni indicadores poblacionales.",
            "Los conteos y nombres de campos son metadatos; no subir microdatos ni identificadores originales."
        ]
    }
    (OUT/"protocolo_inventario_enigh_2024.json").write_text(
        json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"AUDITORIA INICIAL COMPLETA: {len(reportes)} tablas")
    print(f"REPORTES: {output} y protocolo_inventario_enigh_2024.json")
    print("AUN NO HAY INDICADORES ECONOMICOS CALCULADOS.")

if __name__=="__main__":
    main()
