import json
from pathlib import Path
from services.api.render import render
from services.api.contracts import ChartSpec
out=Path('docs/evidence/gallery');out.mkdir(parents=True,exist_ok=True)
base={'records':[{'region':'华东 / East','value':400},{'region':'华南 / South','value':200},{'region':'华北 / North','value':-50}],'columns':['region','value'],'labels':{'region':'地区 / Region','value':'销售额 / CNY'}}
manifest=[]
for engine,kind in [('plotly','bar'),('matplotlib','bar'),('altair','bar'),('echarts','bar'),('plottable','table')]:
    spec=ChartSpec(engine=engine,kind=kind,title='区域销售表现 / Regional sales',annotation='合成数据 · 包含负值',width=1000,height=560)
    artifacts=render(base,spec,out/engine)
    manifest.append({'engine':engine,'artifacts':artifacts,'values':[400,200,-50]})
    print(engine,'rendered',flush=True)
for kind in ['sankey','tree','funnel']:
    result={'records':[{'source':'访问','target':'注册','value':100},{'source':'注册','target':'付费','value':30}],'columns':['source','target','value']}
    render(result,ChartSpec(kind=kind,title='合成转化流程 / Synthetic flow'),out/kind);print(kind,'rendered',flush=True)
for kind in ['facet','linked']:
    result={'records':[{'region':r,'segment':s,'value':v} for r,s,v in [('华东','产品 A',10),('华南','产品 A',20),('华东','产品 B',15),('华南','产品 B',30)]],'columns':['region','segment','value']}
    render(result,ChartSpec(kind=kind,title='分面与联动 / Facet and linked'),out/kind);print(kind,'rendered',flush=True)
geo={'records':[{'lon':121.47,'value':31.23,'category':'A'},{'lon':120.15,'value':30.27,'category':'B'},{'lon':118.78,'value':32.04,'category':'A'}],'columns':['lon','category','value']}
render(geo,ChartSpec(kind='geo',title='合成医院点位 / WGS84',annotation='无底图 · 不调用地理编码服务',extensions={'longitude':'lon','latitude':'value','color_field':'category'}),out/'geo')
import numpy as np
rng=np.random.default_rng(20260927)
density={'records':[{'x':float(x),'value':float(y)} for x,y in zip(rng.normal(size=100000),rng.normal(size=100000))],'columns':['x','value']}
render(density,ChartSpec(kind='density',width=1000,height=560),out/'density')
render(density,ChartSpec(kind='density',width=1000,height=560,extensions={'viewport':{'x':[-1,1],'y':[-1,1]}}),out/'density-zoom')
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
