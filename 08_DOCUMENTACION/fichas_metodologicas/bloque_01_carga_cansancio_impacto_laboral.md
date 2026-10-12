# Fichas metodológicas preliminares — Bloque 01 ENASIC 2022

**Proyecto:** PP 2026-2 — Observatorio de Autonomía, Cuidados y Sostenibilidad Económica  
**Corte:** 12 de octubre de 2026  
**Estado:** validación parcial de códigos y distribuciones; **NO** estimaciones poblacionales

## Alcance y trazabilidad

- Fuente: INEGI, ENASIC 2022; tabla `TPOB_CUI` del conjunto de datos CSV original.
- Cuestionario: sección 6, actividades de cuidados e impactos en personas cuidadoras; materiales en https://www.inegi.org.mx/rnm/index.php/catalog/922/related-materials
- Tabla: 5,677 registros. Grupo observado: 636 filas con `P6_1='1'`. Las restantes 5,041 tienen vacíos en las cuatro variables de este bloque, que **no se deben convertir en ceros ni respuestas «No»**.
- Los conteos y porcentajes siguientes se verificaron sobre el CSV principal de `TPOB_CUI` dentro del ZIP `conjunto_de_datos_enasic_2022_csv.zip`.
- Los factores de expansión aparecen en la tabla (incluido `FAC_CUI`), pero **todavía no se certificaron la población objetivo, unidades primarias, estratos, ajustes, fórmulas de varianza ni coeficientes de variación** para estas estimaciones. No hacer ponderación automática solo por la presencia del campo.
- La clasificación clínica «discapacidad intelectual» y síndrome de Down **no pueden inferirse** automáticamente de la ENASIC.

## Matriz inicial

| Variable | Unidad de análisis en microdatos | Contenido comprobado | Códigos y blancos | Resultado muestral no ponderado | Universo / filtro | Factor / precisión | Uso decisional |
|---|---|---|---|---|---|---|---|
| `P6_7` | Registro de persona cuidadora en `TPOB_CUI` | Horas semanales dedicadas de manera exclusiva al cuidado de persona(s) del hogar identificada(s) en la sección 6 | 01…97 = horas; 98 = 98 o más; 5,041 celdas vacías fuera del grupo observado | 636 respuestas; 189 registros con código numérico ≥40 (29.72%); 22 con código 98 (3.46%) | Patrón observado idéntico a `P6_1=1`; confirmar rutas y alcance en manual | Candidato `FAC_CUI`; metodología y CV pendientes | Priorizar intensidad de cuidados y respiro, sujeto a corroboración local |
| `P6_11_3` | Registro de persona cuidadora en `TPOB_CUI` | «¿Por el cuidado que usted otorga… se siente cansada(o)?» | 1 = Sí; 2 = No; 5,041 celdas vacías fuera del grupo observado | 284 Sí; 352 No; 284/636 = 44.65% | Patrón observado: 636 con `P6_1=1`, verificar ruta de aplicación | Candidato `FAC_CUI`; metodología y CV pendientes | Explorar cansancio y estrategias de respiro |
| `P6_12_2` | Registro de persona cuidadora en `TPOB_CUI` | «¿Por el cuidado que da a esta(s) persona(s), usted… ha tenido que dejar de trabajar?» | 1 = Sí; 2 = No; 5,041 celdas vacías fuera del grupo observado | 143 Sí; 493 No; 143/636 = 22.48% | Patrón observado: 636 con `P6_1=1`, verificar ruta de aplicación | Candidato `FAC_CUI`; metodología y CV pendientes | Explorar continuidad de empleo y apoyos |
| `P6_12_5` | Registro de persona cuidadora en `TPOB_CUI` | «¿… ha tenido que reducir su jornada de trabajo o tiene problemas para cumplir sus horarios laborales?» | 1 = Sí; 2 = No; 5,041 celdas vacías fuera del grupo observado | 99 Sí; 537 No; 99/636 = 15.57% | Patrón observado: 636 con `P6_1=1`, verificar ruta de aplicación | Candidato `FAC_CUI`; metodología y CV pendientes | Explorar flexibilidad laboral y apoyos |

## Regla de indicadores derivados

- `AFECTACION_LABORAL_2_OPCIONES`: `P6_12_2 == 1 OR P6_12_5 == 1`, solo en el grupo observado `P6_1=1`. Resultado descriptivo: 192/636 (30.19%).
- Intersección entre las dos opciones laborales: 50/636 (7.86%). **No sumar los conteos de Sí** de ambas preguntas para obtener personas distintas.
- **No inferir causalidad** a partir de asociaciones descriptivas.
- `P6_11_3` **no integraba la selección inicial de 33 variables**, aunque está presente en la tabla y tiene catálogo oficial. Incorporarla al inventario formal como variable adicional/candidata mediante control de versiones; no llamarla automáticamente «variable número 34» aprobada.

## Verificaciones pendientes ANTES de cifras representativas

1. Validar con cuestionario y manual el filtro 1 de sección 6, la población que puede responder `P6_1`, y las diferencias entre «cuida de alguien con discapacidad», «requiere cuidados» y «discapacidad intelectual».
2. Confirmar unidad, universo y peso correcto mediante documentación de diseño de ENASIC; no reutilizar factores de otras tablas por su nombre.
3. Localizar variables de estratos y unidades primarias del diseño, procedimientos de estimación de varianzas, CV y recomendaciones de publicación.
4. Validar denominadores de preguntas laborales y reglas sobre el significado del «No» en población sin experiencia laboral.
5. Incorporar `P6_11_3` en un nuevo EDA versionado y en el tablero **solo como exploratorio**, con etiqueta clara y sin alterar las cifras ya verificadas.
6. Distinguir descriptivos nacionales de diagnóstico territorial/local; la colaboración con la asociación no se presume formalizada.

**Conservación de datos:** publicar en GitHub solo estas fichas y scripts; nunca microdatos ni identificadores del piloto.
