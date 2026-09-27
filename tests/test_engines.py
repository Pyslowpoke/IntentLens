import json
from pathlib import Path
import pytest
from PIL import Image
from services.api.render import render,resolve
from services.api.contracts import ChartSpec

BASE={'records':[{'region':'华东 / East','value':400},{'region':'华南 / South','value':200},{'region':'华北 / North','value':-50}],'columns':['region','value'],'labels':{'region':'地区 / Region','value':'收入 / Revenue'}}

@pytest.mark.parametrize('engine',['plotly','matplotlib','altair','echarts','plottable'])
def test_real_engines(engine,tmp_path):
    spec=ChartSpec(engine=engine,kind='table' if engine=='plottable' else 'bar',title='中文销售分析 / Sales',annotation='合成数据 · 负数与边距检查',width=1000,height=560)
    dest=tmp_path/engine
    artifacts=render(BASE,spec,dest)
    assert 'png' in artifacts
    image=Image.open(dest/artifacts['png']).convert('RGB')
    assert image.width>500 and image.height>250
    assert len(image.getcolors(image.width*image.height))>20
    assert image.size==(1000,560)
    assert [r['value'] for r in BASE['records']]==[400,200,-50]

def test_incompatible():
    with pytest.raises(ValueError,match='不兼容'):resolve(ChartSpec(engine='plotly',kind='sankey'))

def test_specialty(tmp_path):
    result={'records':[{'x':float(i%100),'value':float(i%70)} for i in range(10000)],'columns':['x','value']}
    render(result,ChartSpec(kind='density',width=640,height=400),tmp_path/'density')
    render(result,ChartSpec(kind='density',width=640,height=400,extensions={'viewport':{'x':[0,20],'y':[0,20]}}),tmp_path/'zoom')
    a=json.loads((tmp_path/'density/density.json').read_text());b=json.loads((tmp_path/'zoom/density.json').read_text())
    assert a['points_in_view']==10000 and 0<b['points_in_view']<10000
    geo={'records':[{'lon':121.47,'value':31.23},{'lon':120.15,'value':30.27}],'columns':['lon','value']}
    assert render(geo,ChartSpec(kind='geo',width=640,height=400),tmp_path/'geo')=={'html':'chart.html','png':'chart.png'}
