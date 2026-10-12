# Hito de validación numérica externa — ENASIC 2022

**Proyecto:** PP 2026-2 · Observatorio de Autonomía, Cuidados y Sostenibilidad Económica.

**Estado: COMPARACIÓN NUMÉRICA EXTERNA COMPLETADA. VALIDACIÓN METODOLÓGICA OFICIAL PENDIENTE.**

## Evidencia de ejecución local

El usuario ejecutó en Windows 11, R 4.6.1 con paquete `survey`, los archivos locales:

- `03_ETL/exportar_validacion_R.py`: creó `05_BASE_ANALITICA/ENASIC_2022/validacion_R_diseno.csv` con 5,677 observaciones y 636 del dominio `P6_1=1`.
- `03_ETL/validar_estimador_con_R.R`: generó `08_DOCUMENTACION/auditorias/ENASIC_2022/validacion_externa_R_survey.csv` para siete indicadores.
- `03_ETL/comparar_R_Python.py`: comparó valores contra `estimadores_taylor_experimentales.csv` y devolvió **`RESULTADO: COINCIDENCIA_EXTERNA_NUMERICA`**.

Los scripts de validación R se entregaron como paquete ZIP separado; **su integración a GitHub sigue pendiente**. No se ha subido el archivo de microdatos auxiliar al repositorio.

## Resultados de comparación

Los siete indicadores coincidieron en estimación, error estándar y CV, dentro de la tolerancia programada:

| Indicador | Estado |
|---|---|
| cansancio_si | COINCIDE |
| dejar_trabajo_si | COINCIDE |
| jornada_horario_si | COINCIDE |
| alguna_dos_afectaciones_laborales | COINCIDE |
| cuidado_40_horas_o_mas | COINCIDE |
| sin_apoyo_familiar | COINCIDE |
| insatisfaccion_tiempo_libre | COINCIDE |

Las diferencias absolutas mostradas en consola fueron de aproximadamente 0 a 5 × 10⁻¹⁶, es decir, de la magnitud esperada para aritmética de coma flotante.

## Qué confirma y qué no confirma

Esta comparación confirma **equivalencia numérica** de dos implementaciones, Python y el paquete independiente `survey` de R, con el mismo archivo de entrada, definición de dominio y supuestos de diseño. **No valida por sí sola** que la tabla `TPOB_CUI` incluya todas las UPM del diseño necesarias para el cálculo oficial de varianzas, ni valida la semántica/universos de las variables o las reglas de difusión del INEGI.

Los 148 estratos y 861 pares estrato–UPM observados proceden únicamente de `TPOB_CUI`; la tabla del dominio `P6_1=1` tiene 636 registros y 28 estratos con una sola UPM observada. No construir el diseño a partir del dominio recortado.

## Siguiente punto de control

1. Verificar documentación oficial ENASIC: `FAC_CUI`, `EST_DIS`, `UPM_DIS` y universo, filtros y unidades analíticas para cada indicador.
2. Comprobar cobertura de conglomerados respecto al diseño completo pertinente y si se requieren unidades sin cuidadores para varianzas de dominio.
3. Revisar decisiones del estimador para horas top-coded, codificaciones de apoyo familiar e insatisfacción de tiempo libre.
4. Contrastar con criterios de intervalos, precisión, CV, y difusión del INEGI antes de publicar.
5. Mantener microdatos, identificadores y archivos agregados internos fuera de GitHub público o cualquier servicio de difusión. Mantener dashboard exploratorio sin cifras experimentales.

**No representar estos resultados como estimaciones oficiales de personas con discapacidad intelectual, síndrome de Down o efectos causales.**
