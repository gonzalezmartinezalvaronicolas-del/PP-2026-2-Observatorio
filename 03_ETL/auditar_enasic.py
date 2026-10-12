"""Auditoria inicial de ENASIC 2022. No modifica los microdatos originales."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, BadZipFile

RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / "01_DATOS_RAW" / "INEGI" / "ENASIC_2022"
SALIDA = RAIZ / "08_DOCUMENTACION" / "auditorias" / "ENASIC_2022"
CLAVES = ("LLAVESDE", "LLAVEVIV", "LLAVEHOG", "LLAVEMOD")


def guardar_csv(ruta: Path, campos: list[str], filas: list[dict]) -> None:
    with ruta.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)


def main() -> None:
    zips = sorted(ENTRADA.glob("*.zip"))
    if len(zips) != 1:
        raise SystemExit(f"Se esperaba 1 ZIP de ENASIC en {ENTRADA}; encontrados: {len(zips)}")
    archivo = zips[0]
    SALIDA.mkdir(parents=True, exist_ok=True)
    resumen: list[dict] = []
    variables: list[dict] = []

    with ZipFile(archivo) as zf:
        tablas = sorted(n for n in zf.namelist()
                        if "/conjunto_de_datos/" in n.lower() and n.lower().endswith(".csv"))
        if len(tablas) != 6:
            print(f"ADVERTENCIA: se esperaban seis tablas principales y se encontraron {len(tablas)}")
        for nombre in tablas:
            tabla = Path(nombre).stem.removeprefix("conjunto_de_datos_").replace("_enasic_2022", "")
            total = 0
            campos: list[str] = []
            vacios: Counter[str] = Counter()
            errores_longitud = 0
            unicos: dict[str, set[str]] = {}
            duplicados_clave: Counter[str] = Counter()
            with zf.open(nombre) as binario:
                lector = csv.reader(io.TextIOWrapper(binario, encoding="utf-8-sig", errors="replace", newline=""))
                campos = next(lector, [])
                claves_disponibles = [k for k in CLAVES if k in campos]
                unicos = {k: set() for k in claves_disponibles}
                for fila in lector:
                    total += 1
                    if len(fila) != len(campos):
                        errores_longitud += 1
                        continue
                    for indice, campo in enumerate(campos):
                        valor = fila[indice].strip()
                        if not valor:
                            vacios[campo] += 1
                        if campo in unicos and valor:
                            if valor in unicos[campo]:
                                duplicados_clave[campo] += 1
                            else:
                                unicos[campo].add(valor)

            for campo in campos:
                variables.append({
                    "tabla": tabla, "variable": campo,
                    "vacios_celda": vacios[campo],
                    "porcentaje_vacios_celda": round(100 * vacios[campo] / total, 2) if total else 0,
                })
            resumen.append({
                "tabla": tabla, "filas": total, "columnas": len(campos),
                "filas_longitud_incorrecta": errores_longitud,
                "claves_presentes": "; ".join(unicos),
                "duplicados_por_clave_individual": "; ".join(
                    f"{k}:{duplicados_clave[k]}" for k in unicos
                ),
                "ruta_interna": nombre,
            })
            print(f"{tabla}: {total:,} filas, {len(campos)} columnas, {errores_longitud} errores de longitud")

    guardar_csv(SALIDA / "resumen_tablas.csv",
                ["tabla", "filas", "columnas", "filas_longitud_incorrecta",
                 "claves_presentes", "duplicados_por_clave_individual", "ruta_interna"], resumen)
    guardar_csv(SALIDA / "calidad_variables.csv",
                ["tabla", "variable", "vacios_celda", "porcentaje_vacios_celda"], variables)
    huella = hashlib.sha256()
    with archivo.open("rb") as fh:
        for bloque in iter(lambda: fh.read(1024 * 1024), b""):
            huella.update(bloque)
    manifiesto = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "fuente": archivo.name, "sha256": huella.hexdigest(),
        "tablas_detectadas": len(resumen),
        "nota": (
            "Los vacios son celdas vacias, no codigos especiales de no respuesta. "
            "Los duplicados de una clave individual NO prueban duplicados de registros. "
            "Se deben validar las llaves compuestas, dominios, filtros y factores de expansion "
            "con el diccionario y manual oficiales antes de calcular indicadores."
        ),
    }
    (SALIDA / "manifiesto.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Auditoria finalizada. Reportes guardados en: {SALIDA}")


if __name__ == "__main__":
    try:
        main()
    except (BadZipFile, UnicodeError, csv.Error) as exc:
        raise SystemExit(f"Error leyendo ENASIC: {exc}") from exc
