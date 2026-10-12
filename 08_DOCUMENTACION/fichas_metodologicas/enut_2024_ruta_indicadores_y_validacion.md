# ENUT 2024 — Ruta hacia indicadores defendibles

Fecha de actualización: 2026-10-12.

## Estado comprobado con microdatos (proyecto)

- Cinco tablas: TVIVIENDA 28,714, THOGAR 29,181, TSDEM 94,565, TMODULO 74,053, TVAR_CREA 74,053.
- Auditoría de relaciones final: 0 duplicados usando LLAVEHOG + N_REN para personas; 0 registros sin padre en relaciones validadas; 0 inconsistencias muestrales comparadas.
- Variables exploradas: `cuid_esp_disc_enf`, `trab_no_rem_cuid_hog`, `cuid_esp_int_hog_con_cp`, `cuid_esp_int_hog_sin_cp`.
- `cuid_esp_disc_enf`: 2,176 observaciones positivas; mujeres 1,371/39,910 (3.435%) y hombres 805/34,143 (2.358%). **Sin ponderación**, por lo tanto NO representan porcentajes nacionales.
- `trab_no_rem_cuid_hog`: 50,845 registros positivos. Hay valores mayores a 168 en algunas variables; requieren revisar simultaneidad y método de agregación.

## Respaldo documental oficial

- Ficha ENUT 2024: https://www.inegi.org.mx/programas/enut/2024/
  - Universo objetivo: personas de 12 años y más.
  - Diseño: probabilístico, por etapas, estratificado y conglomerados.
  - Cobertura: nacional, por tamaño de localidad y entidad federativa.
  - Levantamiento: 7 oct–29 nov 2024.
- Documento conceptual oficial, subtema trabajo no remunerado de cuidado a integrantes del hogar, pp. 80-81 aprox. en la paginación impresa: https://www.inegi.org.mx/contenidos/programas/enut/2024/doc/889463921929.pdf
  - Diferencia cuidados especiales por discapacidad, enfermedad crónica o temporal de cuidados según edades.
  - Distingue cuidados con y sin cuidados pasivos y define indicadores como horas semanales.
  - **No** afirma que el campo preciso de microdatos `cuid_esp_disc_enf` sea idéntico a la variable del indicador publicado: verificar ficha TVAR_CREA y metodología de derivación.
- Catálogo de materiales y diseño muestral: https://www.inegi.org.mx/rnm/index.php/catalog/1127/related-materials
- Biblioteca de cifras oficiales para presentación: `08_DOCUMENTACION/fuentes_oficiales/biblioteca_evidencia_inegi.md`.

## Validaciones antes de publicar nuevas cifras nacionales

1. Obtener **descriptor TVAR_CREA** (no confundir con TVIVIENDA), incluidas unidades y tratamiento de cuidados pasivos.
2. Confirmar codificación exacta de `sexo`, `edad`, `cond_disc` y de todos los tiempos; confirmar si los valores son horas decimales por semana, solapamientos y si se incluyen simultáneas.
3. Verificar denominador: personas que realizaron la actividad versus todas las personas del universo objetivo.
4. Calcular medias y participación usando `fac_per` y dominios de 12+; estimar varianzas del diseño con `est_dis` y `upm_dis`; estudiar estratos singleton sin filtrar prematuramente.
5. Confrontar resultados con cifras oficiales solo cuando definición, universo y variante con/sin pasivos coincidan.
6. Reportar SE, CV, intervalos y límites de confiabilidad donde aplique; no afirmar resultados por discapacidad intelectual o síndrome de Down.
7. El Observatorio separará «indicadores oficiales INEGI» de «indicadores propios PP» y distinguirá descriptivos sin ponderar de estimaciones validadas.

## Nivel de evidencia en diapositivas

**Nivel A:** resultados publicados oficialmente por INEGI, con página y gráfica.
**Nivel B:** estimaciones propias replicables, ponderadas, con diseño, errores y validación documental.
**Nivel C:** diagnósticos exploratorios muestrales, claramente etiquetados como no representativos.
**Nivel D:** hallazgos cualitativos del trabajo posterior con asociación (consentimiento y resguardo).

No sumar observaciones de encuestas diferentes ni pretender que ENUT identifica diagnósticos clínicos.
