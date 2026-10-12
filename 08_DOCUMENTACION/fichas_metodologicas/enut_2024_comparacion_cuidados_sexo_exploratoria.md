# ENUT 2024 — Comparación exploratoria de cuidados por sexo

**Estado:** cálculo interno del PP a partir de registros TVAR_CREA; descriptivo, sin ponderar. No es una estimación oficial ni representativa de México.

**Auditorías locales:** `08_DOCUMENTACION/auditorias/ENUT_2024/diagnostico_relaciones_enut_2024.json` y `comparacion_cuidados_sexo_exploratoria.json`.

## Población de la muestra analizada

74,053 personas de TVAR_CREA: 39,910 registros con sexo codificado 2 (mujeres) y 34,143 con sexo codificado 1 (hombres). Las claves `llavehog + n_ren` resultaron únicas en TSDEM, TMODULO y TVAR_CREA; relaciones comprobadas sin huérfanos ni discrepancias en estrato/UPM y factor FAC_PER en el emparejamiento correspondiente.

## Resultados exploratorios

| Medida | Mujeres | Hombres | Total |
|---|---:|---:|---:|
| Registros | 39,910 | 34,143 | 74,053 |
| `cuid_esp_disc_enf`: valor positivo | 1,371 | 805 | 2,176 |
| `cuid_esp_disc_enf`: porcentaje positivo sin ponderar | 3.435% | 2.358% | 2.938% |
| `cuid_esp_disc_enf`: media entre positivos (unidad por confirmar) | 7.2545 | 6.2988 | 6.9009 |
| `trab_no_rem_cuid_hog`: valor positivo | 28,718 | 22,127 | 50,845 |
| `trab_no_rem_cuid_hog`: media entre positivos (unidad por confirmar) | 13.6634 | 8.5737 | 11.4484 |
| `cuid_esp_int_hog_con_cp`: valor positivo | 3,997 | 2,753 | 6,750 |
| `cuid_esp_int_hog_sin_cp`: valor positivo | 3,819 | 2,542 | 6,361 |

Datos extraídos del JSON de exploración recibido el 12 de octubre de 2026.

## Distinción respecto de cifras oficiales

Las cifras oficiales ENUT 2024 sobre tiempo de cuidados con/sin pasivos (referencias en `08_DOCUMENTACION/fuentes_oficiales/biblioteca_evidencia_inegi.md`) tienen universos, procesos de expansión y definiciones específicas. **No cotejar directamente medias entre positivos del PP con promedios oficiales sin reproducir esos universos y denominadores.**

## Limitaciones obligatorias para presentaciones

1. Descriptivos muestrales **sin FAC_PER ni error estándar**; no son porcentajes de México.
2. `cuid_esp_disc_enf` incluye enfermedad o discapacidad: **no equivale a discapacidad intelectual o síndrome de Down**.
3. Se debe confirmar documentalmente el significado, unidad, periodo, inclusión/exclusión de cuidado pasivo, y denominadores de cada variable de TVAR_CREA.
4. Hay registros de `trab_no_rem_cuid_hog` y `cuid_esp_int_hog_con_cp` mayores que 168, posiblemente por superposición u otras reglas; no censurar automáticamente.
5. No sumar categorías de cuidados antes de validar posibles solapamientos.
6. No inferir causalidad ni impacto económico en personas concretas.
7. No exponer microdatos ni llaves personales en diapositivas o GitHub.

## Siguientes acciones

- Localizar ficha oficial completa de `TVAR_CREA` y confirmar nomenclatura `cuid_esp_disc_enf`, `trab_no_rem_cuid_hog`, `cuid_esp_int_hog_con_cp` y `cuid_esp_int_hog_sin_cp`.
- Preparar indicadores por sexo ponderados con `fac_per`, `est_dis`, `upm_dis` y varianzas del diseño, **solo después de confirmar los universos y variables**.
- Integrar resultados nacionales confirmados en diapositivas junto a resultados propios debidamente identificados.
