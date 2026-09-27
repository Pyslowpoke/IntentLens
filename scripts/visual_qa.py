from pathlib import Path
import json
from PIL import Image
from services.api.render import render
from services.api.contracts import ChartSpec
base={'records':[{'region':'华东 / East','value':400},{'region':'华南 / South','value':200},{'region':'华北 / North','value':-50}],'columns':['region','value'],'labels':{'region':'地区 / Region','value':'销售额 / CNY'}}
report=[]
for engine in ['plotly','matplotlib','altair','echarts']:
    for theme in ['light','dark','report']:
        folder=Path('docs/evidence/themes')/engine/theme
        spec=ChartSpec(engine=engine,theme=theme,title='中文主题检查 / Theme QA',annotation='合成数据 · 含负值 · 1000 × 560',width=1000,height=560)
        render(base,spec,folder)
        size=Image.open(folder/'chart.png').size
        assert size==(1000,560),(engine,theme,size)
        report.append({'engine':engine,'theme':theme,'size':size,'image':str(folder/'chart.png')})
        print(engine,theme,size,flush=True)
Path('docs/evidence/themes/manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
