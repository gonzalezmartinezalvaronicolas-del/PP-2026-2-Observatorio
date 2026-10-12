# ENIGH 2024 — Comparación económica exploratoria

**Estado:** descriptivo muestral sin ponderar; NO son estimaciones nacionales.

## Alcance y datos de origen

Reporte local: `08_DOCUMENTACION/auditorias/ENIGH_2024/comparacion_economica_exploratoria.json`. ENIGH 2024 Nueva Serie, 91,414 hogares y 308,598 personas en las tablas utilizadas. Grupo exploratorio: hogares con al menos una persona que reporta códigos 3 o 4 en al menos uno de `disc_apren`, `disc_habla` o `disc_acti`; 8,125 hogares. Comparación: 83,289 hogares restantes, que **pueden incluir dificultades leves y respuestas no especificadas (&)**.

## Resultados muestrales sin ponderar

| Medida | Con dificultad grave en alguna de las 3 actividades | Resto |
|---|---:|---:|
| Hogares en la muestra | 8,125 | 83,289 |
| Mediana de ingreso corriente (`ing_cor`) | 51,532.24 | 56,059.63 |
| Mediana de gasto monetario (`gasto_mon`) | 30,619.49 | 34,499.98 |
| Mediana de gasto en salud (`salud`) | 410.86 | 176.07 |
| Media de gasto en salud (`salud`) | 2,624.24 | 1,415.71 |

Las medianas de ingreso difieren en aproximadamente -8.1% y las de gasto de salud tienen una razón aproximada de 2.33. Estas comparaciones NO constituyen diferencias representativas o causales.

## Controles y límites de interpretación

- No se han aplicado factores de expansión, varianzas del diseño ni intervalos.
- Los montos conservan las unidades originales de las variables del concentrado ENIGH; antes de publicar, corroborar periodos y definiciones en los diccionarios oficiales.
- `disc_apren` trata dificultades para recordar o concentrarse; no equivale a discapacidad intelectual.
- Los grupos no equiparan diagnóstico clínico ni situación de cuidado.
- Las categorías con códigos 3 y 4 son dificultades funcionales significativas; la categoría restante incluye respuestas 1, 2 o `&`.
- `cuidados` de ENIGH refiere gasto en cuidados personales, no horas de cuidado no remunerado.
- Investigar factores de confusión (tamaño del hogar, edad, composición demográfica) antes de inferencia.
- No combinar registros individuales ENIGH y ENASIC.

## Próximo paso del PP

Incorporar ENUT 2024 como módulo separado para tiempo, trabajo no remunerado y cuidados. Mantener pendientes ENIGH: validación documental de conceptos, ponderaciones por dominio y revisión de indicadores económicos antes de publicarlos como poblacionales.
