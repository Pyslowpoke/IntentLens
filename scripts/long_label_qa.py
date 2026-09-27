from pathlib import Path
import json
from PIL import Image
from services.api.render import render
from services.api.contracts import ChartSpec
result={'records':[{'region':'华东地区·首次签约的新客户（包含线上渠道与线下业务拓展）','value':.4},{'region':'华南地区·已有客户的续约业务（仅包含已确认收入的合同）','value':.25},{'region':'华北地区·本期退货冲减（合成数据中的负值展示样本）','value':-.05}],'columns':['region','value'],'labels':{'region':'完整长标签 / Wrapped labels','value':'占比 / Share'},'value_format':'percent'}
manifest=[]
for engine in ['plotly','matplotlib','altair','echarts']:
    folder=Path('docs/evidence/long-labels')/engine
    artifacts=render(result,ChartSpec(engine=engine,title='长中文标签与比例 / Long labels & ratios',annotation='合成数据 · 负值 · 标签不丢失',width=1200,height=700),folder)
    assert Image.open(folder/'chart.png').size==(1200,700)
    manifest.append({'engine':engine,'dimensions':[1200,700],'artifacts':artifacts})
    print(engine,'OK',flush=True)
Path('docs/evidence/long-labels/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
