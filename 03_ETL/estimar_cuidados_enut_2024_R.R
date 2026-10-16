# ENUT 2024: estimaciones propias preliminares con diseno complejo R survey.
# NO son cifras publicadas por INEGI. Preparar insumo con exportar_enut_2024_para_R.py.
# Ejecutar desde la raiz del repositorio: Rscript 03_ETL/estimar_cuidados_enut_2024_R.R

userlib <- file.path(Sys.getenv("USERPROFILE"), "R", "library")
if (dir.exists(userlib)) .libPaths(c(userlib, .libPaths()))
if (!requireNamespace("survey", quietly=TRUE)) {
  stop("Falta paquete survey en R. Instalarlo en la biblioteca de usuario.")
}

src <- file.path("08_DOCUMENTACION", "auditorias", "ENUT_2024",
                 "base_minima_enut_2024_para_R.csv")
out <- file.path("08_DOCUMENTACION", "auditorias", "ENUT_2024",
                 "indicadores_cuidados_ponderados_preliminares.csv")
if (!file.exists(src)) stop(paste("No existe insumo:", src))

d <- read.csv(src, stringsAsFactors=FALSE,
              colClasses=c(sexo="character", edad="integer",
                           est_dis="character", upm_dis="character",
                           fac_per="numeric"), check.names=FALSE)
expected <- c("cuid_esp_int_hog_sin_cp", "cuid_esp_int_hog_con_cp",
              "trab_no_rem_cuid_hog", "cuid_esp_disc_enf")
if (nrow(d) != 74053L) stop("Cantidad inesperada de registros")
if (!identical(sort(unique(d$sexo)), c("1", "2"))) stop("Codigos sexo inesperados")
if (any(is.na(d$edad) | d$edad < 12 | d$edad > 120)) stop("Edad invalida")
if (any(!is.finite(d$fac_per) | d$fac_per <= 0)) stop("FAC_PER invalido")
if (any(is.na(d$est_dis) | d$est_dis == "" |
        is.na(d$upm_dis) | d$upm_dis == "")) stop("Faltan identificadores de diseno")

for (v in expected) {
  if (!v %in% names(d)) stop(paste("Falta variable", v))
  d[[v]] <- suppressWarnings(as.numeric(d[[v]]))
  if (any(!is.finite(d[[v]]) | d[[v]] < 0)) stop(paste("Tiempo invalido", v))
  d[[paste0("positivo_",v)]] <- as.integer(d[[v]] > 0)
}

# La muestra COMPLETA determina el diseno; no filtrar por actividad antes.
# En todo el modulo se observaron 342 estratos y al menos dos UPM por estrato.
options(survey.lonely.psu="fail")
design <- survey::svydesign(ids=~upm_dis, strata=~est_dis,
                             weights=~fac_per, nest=TRUE, data=d)
if (survey::degf(design) <= 0) stop("Grados de libertad no positivos")
stratum_psus <- tapply(design$variables$upm_dis, design$variables$est_dis,
                       function(x) length(unique(x)))
if (any(stratum_psus < 2)) stop("Existe al menos un estrato con una sola UPM")

get_groups <- function(which) {
  if (which == "mujeres") return(subset(design, sexo == "2"))
  if (which == "hombres") return(subset(design, sexo == "1"))
  design
}

make_row <- function(group, variable, measure, n, positive, estimate, se, df) {
  critical <- stats::qt(0.975, df=df)
  lo <- estimate - critical*se
  hi <- estimate + critical*se
  if (measure == "participacion_porcentaje") {
    lo <- max(0, lo); hi <- min(100, hi)
  }
  data.frame(grupo=group, variable=variable, medida=measure,
             n_muestra=n, n_positivos=positive,
             estimacion=estimate, error_estandar=se,
             cv=if (estimate > 0) se/estimate else NA_real_,
             lim_inf_95=lo, lim_sup_95=hi,
             grados_libertad=df, calculo="R_survey_Taylor_preliminar",
             stringsAsFactors=FALSE)
}

rows <- list()
for (group in c("total", "mujeres", "hombres")) {
  subdesign <- get_groups(group)
  n <- nrow(subdesign$variables)
  df <- survey::degf(subdesign)
  if (!is.finite(df) || df < 1) stop(paste("Grados de libertad insuficientes:", group))
  for (v in expected) {
    indicator <- paste0("positivo_", v)
    positive <- sum(subdesign$variables[[indicator]] == 1L)
    if (positive == 0) stop(paste("No hay observaciones positivas:", group, v))
    # Participacion entre TODAS las personas de 12+ del grupo.
    p <- survey::svymean(stats::as.formula(paste0("~", indicator)),
                         design=subdesign, na.rm=FALSE)
    rows[[length(rows)+1L]] <- make_row(group, v, "participacion_porcentaje",
      n, positive, as.numeric(stats::coef(p)[1])*100,
      as.numeric(survey::SE(p)[1])*100, df)
    # Media SOLO de quienes registran actividad: razon de totales
    # calculada sobre el diseno completo del grupo, sin filtrar previamente
    # unidades primarias ni estratos.
    r <- survey::svyratio(
      numerator=stats::as.formula(paste0("~",v)),
      denominator=stats::as.formula(paste0("~",indicator)),
      design=subdesign, na.rm=FALSE)
    rows[[length(rows)+1L]] <- make_row(group, v, "media_condicional_unidad_original",
      n, positive, as.numeric(stats::coef(r)[1]),
      as.numeric(survey::SE(r)[1]), df)
    cat(group, v, "participacion (%)=",
        round(as.numeric(stats::coef(p)[1])*100, 3),
        "media_positivos=", round(as.numeric(stats::coef(r)[1]), 3), "\n")
  }
}
res <- do.call(rbind, rows)
dir.create(dirname(out), recursive=TRUE, showWarnings=FALSE)
utils::write.csv(res, out, row.names=FALSE, fileEncoding="UTF-8")
cat("ESTIMACION CON DISENO COMPLETADA:", nrow(res), "filas; estratos=",
    length(stratum_psus), "; PSU-estrato=", sum(stratum_psus), "\n")
cat("REPORTE:", out, "\n")
cat("ESTADO: PRELIMINAR. No atribuir como cifras publicadas por INEGI.",
    "Verificar universo, periodicidad y definicion antes de difundir.\n")
