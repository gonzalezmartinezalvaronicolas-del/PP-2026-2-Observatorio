# Auditoría metodológica — Agrupación muestral ENASIC 2022

**Proyecto:** PP 2026-2 · Observatorio de Autonomía, Cuidados y Sostenibilidad Económica  
**Estado:** diagnóstico de agrupación concluido; estimación poblacional pendiente.

## Evidencia comprobada

Fuente de resultados: `08_DOCUMENTACION/auditorias/ENASIC_2022/diagnostico_agrupacion_muestral.json` y `distribucion_upm_por_estrato.csv`, ejecución del script `03_ETL/diagnosticar_agrupacion_muestral.py`.

| Métrica | Toda TPOB_CUI | Grupo exploratorio P6_1=1 |
|---|---:|---:|
| Filas | 5,677 | 636 |
| Estratos EST_DIS observados | 148 | 126 |
| UPM_DIS distintas | 861 | 326 |
| Pares estrato–UPM distintos | 861 | 326 |
| Estratos con una UPM observada | 0 | 28 |
| Estratos con dos o más UPM observadas | 148 | 98 |

Las UPM observadas no se repiten entre estratos en estos registros. `FAC_CUI` es numérico, finito y positivo en los 5,677 registros de `TPOB_CUI`, según diagnóstico local previo. `P6_1` contiene 5,041 blancos, atribuibles a su aplicación condicionada; **no es campo del diseño**.

## Interpretación

Los 28 estratos con una UPM del grupo `P6_1=1` **no son automáticamente estratos unitarios del diseño completo**. Para analizar este dominio mediante linealización, la pertenencia al dominio debe codificarse dentro de una estructura de diseño conservada: no basta con recortar a las 636 filas antes de reconstruir estratos y conglomerados.

La tabla completa `TPOB_CUI` cuenta con dos o más UPM observadas en todos sus 148 estratos, pero esto **NO certifica** que incluya todas las unidades requeridas para el cálculo oficial de varianzas de personas cuidadoras. La verificación documental/empírica de esta suficiencia es prioritaria.

## Referencia metodológica

INEGI, *Diseño muestral de la Encuesta Nacional para el Sistema de Cuidados (ENASIC) 2022*, apartados 2.8 (Estimadores), 2.9 (Estimadores de errores por muestreo) y 2.10 (Homologación de semaforización). El documento describe conglomerados últimos y series de Taylor para estimadores de razón:

https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/nueva_estruc/889463909798.pdf

También consultar *Conociendo la base de datos* para significado de `FAC_CUI`, `EST_DIS`, `UPM_DIS` y universo de `TPOB_CUI`:
https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/nueva_estruc/889463927082.pdf

## Próximo protocolo antes de publicación

1. Corroborar de forma explícita el significado de `EST_DIS`, `UPM_DIS` y `FAC_CUI` en los diccionarios/documentos oficiales y la equivalencia con el diseño descrito.
2. Determinar la población y base de diseño necesarias para el universo `P6_1=1`, sin inventar registros UPM ausentes.
3. Elaborar una implementación de **prueba** de estimadores por razón con indicador de dominio, aportaciones por conglomerado y varianza de Taylor; documentar la convención para estratos unitarios del diseño completo.
4. Validar la implementación mediante ejemplos/manual oficial o una segunda herramienta estadística independiente y verificar el método de precisión y semaforización del INEGI.
5. Solo después producir estimaciones ponderadas, SE, CV, intervalos, advertencias de fiabilidad y actualizar el dashboard.
6. Mantener sin cambios el módulo exploratorio HTML hasta certificar los indicadores; nunca cambiar las cifras de muestra por cifras poblacionales silenciosamente.

**Precaución:** ENASIC no permite diagnosticar automáticamente discapacidad intelectual, síndrome de Down o causalidad. No confundir encuesta nacional con piloto local de la asociación.
