import pytest
from services.api.render import render
from services.api.contracts import ChartSpec

@pytest.mark.parametrize('engine,kind',[
 ('plotly','line'),('plotly','scatter'),('plotly','area'),('plotly','histogram'),('plotly','box'),('plotly','heatmap'),
 ('matplotlib','histogram'),('matplotlib','box'),('matplotlib','violin'),('matplotlib','heatmap'),
 ('echarts','scatter'),('echarts','line'),
])
def test_additional_chart_types(engine,kind,tmp_path):
    result={'records':[{'group':'A','segment':'X','value':1},{'group':'A','segment':'Y','value':2},{'group':'B','segment':'X','value':3},{'group':'B','segment':'Y','value':4}],'columns':['group','segment','value']}
    if kind=='scatter':
        result={'records':[{'x':1,'value':2},{'x':3,'value':4}],'columns':['x','value']}
    artifacts=render(result,ChartSpec(engine=engine,kind=kind,width=640,height=400),tmp_path/engine/kind)
    assert 'png' in artifacts
