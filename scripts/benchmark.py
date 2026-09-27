"""Fixed seed, full aggregation, separately measured native compute/render/cache; no model time."""
import json
import time
import platform
import os
from pathlib import Path
import statistics
import psutil
import numpy as np
import pandas as pd
from services.api.compute import compute,cache_key
from services.api.ingest import snapshot
from services.api.contracts import AnalysisPlan,ChartSpec
from services.api.render import render

out=Path('docs/evidence/benchmark');out.mkdir(parents=True,exist_ok=True)
proc=psutil.Process();report={'hardware':{'platform':platform.platform(),'processor':platform.processor(),'logical_cpus':os.cpu_count(),'ram_bytes':psutil.virtual_memory().total},'seed':20260927,'columns':4,'repeats':3,'chart':'bar, 20 aggregated groups','model_time':'not applicable: rule mode','runs':[]}
for n in (10000,100000,1000000):
    rng=np.random.default_rng(20260927)
    df=pd.DataFrame({'f1':rng.integers(0,20,n).astype(str),'f2':rng.uniform(1,100,n),'f3':rng.normal(size=n),'f4':rng.normal(size=n)})
    ds=snapshot(df,['group','revenue','x','y'],'synthetic benchmark')
    plan=AnalysisPlan(group_by=['f1'],metric='f2',sort='desc')
    times=[];rss=[]
    for i in range(3):
        start=time.perf_counter();result=compute(df,plan,ds);times.append((time.perf_counter()-start)*1000);rss.append(proc.memory_info().rss)
    serialized=json.dumps(result).encode();cache=out/f'{n}-result.json';cache.write_bytes(serialized)
    start=time.perf_counter();json.loads(cache.read_bytes());warm=(time.perf_counter()-start)*1000
    start=time.perf_counter();render(result,ChartSpec(engine='matplotlib',title=f'{n:,} rows / 20 groups'),out/str(n));export=(time.perf_counter()-start)*1000
    report['runs'].append({'rows':n,'cold_compute_ms':times[0],'repeat_compute_ms':times,'warm_json_cache_ms':warm,'style_edit_compute':'cache reuse; no aggregation','static_render_and_png_svg_pdf_ms':export,'serialized_bytes':len(serialized),'rss_bytes_after_each_repeat':rss,'rss_is_peak':False,'result_groups':len(result['records'])})
    print(n,report['runs'][-1],flush=True)
(out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
