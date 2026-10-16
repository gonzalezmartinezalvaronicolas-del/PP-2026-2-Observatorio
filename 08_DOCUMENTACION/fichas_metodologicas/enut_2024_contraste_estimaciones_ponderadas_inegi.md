# ENUT 2024 — Contraste de cálculos ponderados del PP con INEGI

**Estado:** comprobación preliminar de estimadores puntuales. Pendiente inspeccionar CSV con errores estándar e intervalos. Fecha: 2026-10-15.

## Proceso reproducible

Insumo local: `08_DOCUMENTACION/auditorias/ENUT_2024/base_minima_enut_2024_para_R.csv`, obtenido con `03_ETL/exportar_enut_2024_para_R.py`; no subir ni versionar el insumo. Estimaciones con `03_ETL/estimar_cuidados_enut_2024_R.R` y biblioteca R `survey`, ponderación `fac_per`, estratos `est_dis`, PSU `upm_dis`, universo 74,053 personas de TVAR_CREA, 342 estratos, 4,200 combinaciones estrato-UPM. No hubo estratos solitarios en muestra completa.

Fuente documental de las variables: descriptor INEGI ENUT 2024, hoja TVAR_CREA; documentación técnica en `enut_2024_variables_cuidados_descriptor.md`.

## Resultados puntuales: medias entre quienes realizaron cuidados especiales a integrantes del hogar

| Variable y sexo | PP ponderado R survey, log | INEGI publicado (horas semanales, un decimal) | Coincide al redondear |
|---|---:|---:|---|
| `cuid_esp_int_hog_sin_cp`, mujeres | 12.789 | 12.8 | Sí |
| `cuid_esp_int_hog_sin_cp`, hombres | 7.546 | 7.5 | Sí |
| `cuid_esp_int_hog_con_cp`, mujeres | 23.772 | 23.8 | Sí |
| `cuid_esp_int_hog_con_cp`, hombres | 13.129 | 13.1 | Sí |

**Fuente oficial INEGI:** Encuesta Nacional sobre Uso del Tiempo (ENUT) 2024, comunicado de prensa 121/25, **28 de agosto de 2025, página 5, gráfica 4 y texto inmediatamente posterior**: https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/enut/enut2024_CP.pdf . El comunicado indica promedios semanales de tiempo de cuidados a integrantes del hogar con enfermedad crónica, temporal o discapacidad; distingue exclusión e inclusión de cuidados pasivos. En la hoja descriptora TVAR_CREA, las dos variables relevantes también incluyen cuidados emocionales.

**Lo que demuestra el cotejo:** coincidencia a una décima de las cuatro medias puntuales de tiempo de cuidados especiales. Es una señal fuerte de consistencia de selección de variables, universo de participantes, ponderación y cálculo de medias condicionales.

**Lo que NO demuestra:** equivalencia exacta de decimales no publicados, precisión de varianza (errores estándar, CV, IC), exhaustividad de códigos especiales, validación oficial del script o pertinencia para discapacidad intelectual exclusivamente. La replicación propia no sustituye un dictamen metodológico del INEGI.

## Otras estimaciones preliminares propias del log (no cifras publicadas)

- Participación ponderada en cuidados especiales del hogar sin pasivos: total 7.879%, mujeres 8.820%, hombres 6.795%.
- Participación ponderada en cuidados especiales del hogar con pasivos: total 8.347%, mujeres 9.178%, hombres 7.392%.
- `trab_no_rem_cuid_hog`: participación total 67.764%; media condicional total 11.427, mujeres 13.605 y hombres 8.664.
- `cuid_esp_disc_enf`: es ayuda gratuita a **otros hogares familiares** con personas enfermas o con discapacidad. Participación total 2.787%; media condicional total 7.549. No mezclar con cuidados especiales en el propio hogar.

## Evidencia y validaciones siguientes

1. Solicitar y revisar `08_DOCUMENTACION/auditorias/ENUT_2024/indicadores_cuidados_ponderados_preliminares.csv` generado localmente; no se ha recibido en esta revisión. Revisar las 24 filas, SE, CV, IC95%, grados de libertad, denominadores.
2. Comprobar validez del diseño de varianza y si las estimaciones por dominio reproducen correctamente las condiciones oficiales. Comparar por separado las dos variantes de cuidados, sin sumar con y sin pasivos.
3. Reportar las cifras propias únicamente con fuente, universo, intervalo y calificación metodológica.
4. Mantener la comparación oficial bajo una nota: «Reproducción independiente preliminar del valor puntual publicado por INEGI, a una decimal»; no proclamar certificación oficial ni hacer inferencia causal.
