"""Compara R survey y Python; aun no certifica diseno oficial."""
from pathlib import Path
import math, json
import pandas as pd
P=Path(__file__).resolve().parents[1]/'08_DOCUMENTACION/auditorias/ENASIC_2022'
a=pd.read_csv(P/'estimadores_taylor_experimentales.csv').set_index('indicador')
b=pd.read_csv(P/'validacion_externa_R_survey.csv').set_index('indicador')
assert set(a.index)==set(b.index) and len(a)==7
checks=[]
for key in a.index:
    pairs=[('estimacion_ponderada_experimental','estimacion_R'),('error_estandar_taylor_experimental','error_estandar_R'),('cv_experimental','cv_R')]
    diffs={rb:abs(float(a.loc[key,py])-float(b.loc[key,rb])) for py,rb in pairs}
    status='COINCIDE' if all(math.isfinite(v) and v<=1e-7 for v in diffs.values()) else 'REVISAR'
    checks.append({'indicador':key,'estado':status,'diferencias':diffs})
    print(key, status, diffs)
status='COINCIDENCIA_EXTERNA_NUMERICA' if all(r['estado']=='COINCIDE' for r in checks) else 'DIFERENCIAS_A_INVESTIGAR'
(P/'comparacion_externa_R_Python.json').write_text(json.dumps({'estado':status,'indicadores':checks,'nota':'No es validacion oficial de universo, UPM, ni CV.'},indent=2,ensure_ascii=False),encoding='utf-8')
print('RESULTADO:',status)
if status!='COINCIDENCIA_EXTERNA_NUMERICA':raise SystemExit(1)
