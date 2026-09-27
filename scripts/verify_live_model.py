"""Explicit opt-in live validation. Never runs in public CI; records every attempt."""
import json
import os
from pathlib import Path
import pandas as pd
from services.api.providers import recommend
from services.api.ingest import snapshot
from services.api.compute import compute
from services.api.contracts import AnalysisPlan

if os.getenv('ALLOW_LIVE_MODEL_TEST')!='1':raise SystemExit('Set ALLOW_LIVE_MODEL_TEST=1 on the API-side environment to authorize live tests; do not paste keys into chat.')
df=pd.DataFrame({'f1':['East','East','West'],'f2':[100,300,200]})
ds=snapshot(df,['region','revenue'],'synthetic live model fixture')
report={'provider':os.getenv('PROVIDER'),'model':os.getenv('MODEL'),'prompt_version':'1.0','attempts':[],'expected_region_totals':{'East':400,'West':200}}
for attempt in range(3):
    try:
        proposals=recommend(ds,'Sum revenue by region; descending order; do not change the metric.','model')
        plan=AnalysisPlan.model_validate(proposals['proposals'][0]['plan'])
        result=compute(df,plan,ds)
        actual={r.get('f1'):r.get('value') for r in result['records']}
        report['attempts'].append({'attempt':attempt+1,'success':actual=={'East':400,'West':200},'plan':plan.model_dump(),'actual':actual})
    except Exception as e:report['attempts'].append({'attempt':attempt+1,'success':False,'error_type':type(e).__name__})
report['success_count']=sum(r['success'] for r in report['attempts'])
Path('docs/evidence/live-model.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(f"{report['success_count']}/3 successes; all attempts retained")
