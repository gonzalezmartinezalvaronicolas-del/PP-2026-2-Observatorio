# Validacion externa con R survey, no oficial.
if (!requireNamespace('survey', quietly=TRUE)) stop("Instala survey: Rscript -e \"install.packages('survey', repos='https://cloud.r-project.org')\"")
p <- '05_BASE_ANALITICA/ENASIC_2022/validacion_R_diseno.csv'
if (!file.exists(p)) stop(paste('Falta:',p))
d <- read.csv(p, colClasses='character', na.strings=NULL, check.names=FALSE)
if(nrow(d)!=5677L || sum(d$P6_1=='1')!=636L) stop('Totales inesperados')
d$FAC_CUI <- as.numeric(d$FAC_CUI)
if(any(!is.finite(d$FAC_CUI)) || any(d$FAC_CUI<=0)) stop('Pesos no validos')
domain <- d$P6_1=='1'
for(nm in c('P6_8','P6_11_3','P6_12_2','P6_12_5','P6_39_1')) if(!all(d[[nm]][domain] %in% c('1','2'))) stop(paste('Codigos invalidos:',nm))
h <- suppressWarnings(as.numeric(d$P6_7))
if(any(is.na(h[domain]) | h[domain]<1 | h[domain]>98)) stop('Horas invalidas')
metrics <- c('cansancio_si','dejar_trabajo_si','jornada_horario_si','alguna_dos_afectaciones_laborales','cuidado_40_horas_o_mas','sin_apoyo_familiar','insatisfaccion_tiempo_libre')
d$cansancio_si <- as.integer(d$P6_11_3=='1')
d$dejar_trabajo_si <- as.integer(d$P6_12_2=='1')
d$jornada_horario_si <- as.integer(d$P6_12_5=='1')
d$alguna_dos_afectaciones_laborales <- as.integer(d$P6_12_2=='1' | d$P6_12_5=='1')
d$cuidado_40_horas_o_mas <- as.integer(!is.na(h) & h>=40)
d$sin_apoyo_familiar <- as.integer(d$P6_8=='2')
d$insatisfaccion_tiempo_libre <- as.integer(d$P6_39_1=='2')
for(nm in metrics) d[[nm]][!domain] <- 0L
# Construir diseño con todos los registros ANTES de seleccionar dominio.
design <- survey::svydesign(ids=~UPM_DIS, strata=~EST_DIS, weights=~FAC_CUI, data=d, nest=TRUE)
dsub <- subset(design, P6_1=='1')
results <- do.call(rbind, lapply(metrics, function(nm) {
  est <- survey::svymean(as.formula(paste0('~',nm)), dsub, na.rm=FALSE)
  p <- as.numeric(coef(est)[1]); se <- as.numeric(survey::SE(est)[1])
  data.frame(indicador=nm, estimacion_R=p, error_estandar_R=se, cv_R=se/p, n_grupo=sum(domain), version_survey=as.character(utils::packageVersion('survey')))
}))
out <- '08_DOCUMENTACION/auditorias/ENASIC_2022/validacion_externa_R_survey.csv'
dir.create(dirname(out),recursive=TRUE,showWarnings=FALSE)
write.csv(results,out,row.names=FALSE)
cat('R SURVEY COMPLETADO:',nrow(results),'indicadores.\nRESULTADOS:',out,'\nNO son cifras oficiales.\n')
