# Observatorio PP 2026-2 — vistas y publicación

## Módulo ENUT 2024

**Generador:** `03_ETL/generar_modulo_enut_observatorio.py`.

**Insumo local agregado:** `08_DOCUMENTACION/auditorias/ENUT_2024/indicadores_cuidados_ponderados_preliminares.csv`. Si existe, comprueba el archivo local `validacion_independiente_python_R_enut_2024.json` antes de mostrar el estado de verificación.

Desde la raíz del repositorio, en CMD de Windows:

```bat
git pull --ff-only origin main
.venv\Scripts\python.exe 03_ETL\generar_modulo_enut_observatorio.py
start "" "06_OBSERVATORIO\enut_2024_cuidados.html"
```

Si el HTML ya existe y fue generado por el mismo script, ejecutar con `--overwrite` para actualizarlo. El script se niega a reemplazar archivos HTML ajenos.

La vista es **independiente**, HTML offline, sin librerías externas, con 24 estimaciones agregadas, intervalos y comparaciones oficiales solo cuando son conceptualmente equivalentes. No se debe interpretar como integración completa de ENASIC/ENIGH ni como programa social final.

### Seguridad y evidencia

- Nunca versionar `base_minima_enut_2024_para_R.csv`, ni archivos originales con llaves de hogares/personas.
- El HTML contiene únicamente resultados agregados; aun así, revisar todas las advertencias antes de distribuirlo.
- Cuidados pasivos con/sin CP: no sumarlos y no inferir diferencia causal entre géneros.
- `cuid_esp_disc_enf` mide ayuda a otros hogares familiares, no a integrantes del propio hogar.
- Ni el módulo ni las publicaciones oficiales analizadas identifican de forma exclusiva discapacidad intelectual.
- Mantener distintos niveles: cifras publicadas INEGI; estimaciones propias ponderadas; descriptivos exploratorios; y evidencia del futuro trabajo con la asociación.
- Biblioteca de fuentes: `08_DOCUMENTACION/fuentes_oficiales/biblioteca_evidencia_inegi.md`.
- Informe de 24 indicadores: `08_DOCUMENTACION/fichas_metodologicas/enut_2024_revision_precision_24_estimaciones.md`.

## Próximas integraciones

ENASIC, ENIGH y ENUT son encuestas distintas y se presentan en vistas diferenciadas. Incorporar metadatos y filtros de cada fuente solo después de validar diseño, unidad de análisis y limitaciones; no fusionar registros entre encuestas. Definir después el alcance territorial y las necesidades de la organización aliada antes de plantear la intervención.
