"""Exportacion local de campos minimos para R survey. No subir CSV a GitHub."""
from pathlib import Path
import pandas as pd
import numpy as np
R = Path(__file__).resolve().parents[1]
src = R/'04_DATOS_LIMPIOS/ENASIC_2022/tpob_cui.parquet'
dest = R/'05_BASE_ANALITICA/ENASIC_2022/validacion_R_diseno.csv'
cols = ['EST_DIS','UPM_DIS','FAC_CUI','P6_1','P6_7','P6_8','P6_11_3','P6_12_2','P6_12_5','P6_39_1']
d = pd.read_parquet(src, columns=cols)
assert len(d)==5677 and d.P6_1.eq('1').sum()==636
assert not d[['EST_DIS','UPM_DIS','FAC_CUI']].eq('').any().any()
w = pd.to_numeric(d.FAC_CUI,errors='raise')
assert np.isfinite(w).all() and w.gt(0).all()
dest.parent.mkdir(parents=True,exist_ok=True)
d.to_csv(dest,index=False,encoding='utf-8')
print('EXPORTACION LOCAL COMPLETA:',dest)
print('5677 registros, 636 del dominio. No publicar el CSV.')
