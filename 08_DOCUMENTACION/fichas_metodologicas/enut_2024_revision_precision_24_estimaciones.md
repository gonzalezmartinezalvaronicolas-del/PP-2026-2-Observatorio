# ENUT 2024 — Revisión de 24 estimaciones ponderadas de cuidados

**Corte de revisión:** 2026-10-15. **Estado:** validación numérica independiente de puntos y errores estándar; no certificación metodológica oficial ni cifras publicadas por INEGI.

## Archivos locales auditados

- `08_DOCUMENTACION/auditorias/ENUT_2024/base_minima_enut_2024_para_R.csv`: insumo de 74,053 registros (mantener LOCAL; nunca versionar ni compartir públicamente).
- `08_DOCUMENTACION/auditorias/ENUT_2024/indicadores_cuidados_ponderados_preliminares.csv`: 24 filas, columnas de grupo, indicador, medida, estimación, SE, CV, IC95% y grados de libertad.
- Reproducción independiente versionada: `03_ETL/validar_independiente_enut_2024_python.py`.
- Script de origen R: `03_ETL/estimar_cuidados_enut_2024_R.R`.

## Comprobaciones efectuadas

- 24 combinaciones esperadas: 3 grupos (total/mujeres/hombres) × 4 variables × 2 métricas (participación y media condicional). **24/24**.
- Sin filas duplicadas por grupo-variable-métrica; sin NA en 9 columnas de insumo; SE positivos y finitos; 24 intervalos contienen el estimador.
- **24/24 estimaciones puntuales reproducidas desde datos con pesos FAC_PER.**
- **24/24 errores estándar Taylor reproducidos de forma independiente en Python**, con residuos linealizados por UPM anidada en estrato, sin eliminar PSU externas al dominio por sexo.
- Diferencia absoluta máxima frente a R: estimador **4.62e-14**; SE **5.00e-16**. CV coherentes con SE/estimación; IC95% coherentes con errores y cuantiles t de grados de libertad reportados.
- Muestra completa: 74,053 registros, 342 estratos, 4,200 PSU-estrato; 0 estratos singleton en muestra completa. Grados de libertad que reporta R: total 3,858; mujeres 3,851; hombres 3,834.
- CV de las 24 medidas entre 0.578% y 7.683%; máximo en media condicional de ayuda gratuita a otros hogares familiares, hombres.

## Indicadores centrales: tiempo de cuidados especiales A INTEGRANTES DEL PROPIO HOGAR

Los promedios se calculan ENTRE QUIENES REALIZARON LA ACTIVIDAD, no sobre todas las personas del universo; horas por semana sujetas a las precisiones de la publicación oficial.

| Indicador | Grupo | Estimación PP | SE | IC95% |
|---|---|---:|---:|---|
| Sin pasivos, media condicional | Mujeres | 12.789 | 0.336 | 12.131–13.447 |
| Sin pasivos, media condicional | Hombres | 7.546 | 0.239 | 7.077–8.014 |
| Con pasivos, media condicional | Mujeres | 23.772 | 0.663 | 22.473–25.071 |
| Con pasivos, media condicional | Hombres | 13.129 | 0.427 | 12.291–13.967 |
| Sin pasivos, participación (%) | Mujeres | 8.820 | 0.238 pp | 8.354–9.287% |
| Sin pasivos, participación (%) | Hombres | 6.795 | 0.221 pp | 6.361–7.230% |
| Con pasivos, participación (%) | Mujeres | 9.178 | 0.244 pp | 8.699–9.656% |
| Con pasivos, participación (%) | Hombres | 7.392 | 0.231 pp | 6.938–7.845% |

Cotejo oficial INEGI en promedios: mujeres 12.8 y hombres 7.5 h/semana sin pasivos; mujeres 23.8 y hombres 13.1 h/semana con pasivos. **Coinciden a una decimal.** Fuente: INEGI, ENUT 2024, comunicado 121/25, p. 5, https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/enut/enut2024_CP.pdf .

### Otros indicadores explorados

- `trab_no_rem_cuid_hog` es cuidados no remunerados a integrantes del hogar, sin cuidados pasivos: participación ponderada total 67.764% (IC95% 66.996–68.532), media condicional total 11.427 (IC95% 11.204–11.651).
- `cuid_esp_disc_enf` se refiere a ayuda gratuita a personas de **otros hogares familiares** por enfermedad o discapacidad; participación ponderada total 2.787% (IC95% 2.609–2.966), media condicional total 7.549 (IC95% 6.834–8.264). **No equivale a cuidado dentro del propio hogar**.

## Precauciones para difundir

1. La coincidencia de estimadores puntuales con publicación del INEGI y la reproducción de SE entre lenguajes **NO es certificación oficial** de los estimadores propios.
2. Revisar los universos de tabulados y normas para expresar intervalos / CV; el cotejo con cifras oficiales cubre **solo cuatro medias**, no los 24 indicadores ni sus intervalos.
3. El diseño usa `FAC_PER`, `EST_DIS`, `UPM_DIS` y varianza de Taylor por conglomerados estratificados. En los dominios se debe conservar la información de conglomerados de la muestra completa; el código de validación independiente documenta esa decisión.
4. `CUID_ESP_INT_HOG_CON_CP` y `SIN_CP` no representan grupos de actividades disjuntos; no sumar ni restar sus medias condicionales como si correspondieran a las mismas personas.
5. La encuesta considera enfermedad o discapacidad general, NO diagnóstico de discapacidad intelectual/síndrome de Down.
6. Interpretación causal, extrapolación a la asociación y unión fila a fila de ENASIC, ENIGH y ENUT no están sustentadas.
7. Para mostrar una **brecha estadísticamente inferencial** entre sexos, calcular formalmente la diferencia con su covarianza/SE; las tablas de esta ficha presentan la diferencia descriptiva de medias.

## Próximo entregable

Incorporar al tablero una vista de ENUT con indicadores oficiales de referencia y cálculos propios validados, cada uno etiquetado con fuente, grupo, universo, factor, variante pasivos e IC, sujeto a aprobación de ficha final.
