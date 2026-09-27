import json
import io
import zipfile
from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from services.api.contracts import AnalysisPlan, ChartSpec, DatasetSnapshot, Run, ChartRevision
from services.api.compute import compute
from services.api.ingest import parse, snapshot
from services.api import store
from services.api.main import app


@pytest.fixture(autouse=True)
def isolated(tmp_path,monkeypatch):
    monkeypatch.setenv('WORKBENCH_DATA',str(tmp_path/'data'))
    monkeypatch.setenv('PROVIDER','rule')


def fixture_data():
    df=pd.DataFrame({'f1':['A','A'],'f2':[1.,90.],'f3':[2.,100.]})
    ds=snapshot(df,['group','converted','visitors'],'known answer')
    return df,ds


def test_contracts_and_ratios():
    df,ds=fixture_data()
    DatasetSnapshot.model_validate(ds)
    common=dict(group_by=['f1'],metric='f2',denominator='f3')
    total=compute(df,AnalysisPlan(**common,aggregation='ratio_total'),ds)
    simple=compute(df,AnalysisPlan(**common,aggregation='ratio_mean'),ds)
    assert total['records'][0]['value']==pytest.approx(91/102)
    assert simple['records'][0]['value']==pytest.approx(.7)
    assert total['records'][0]['value']!=simple['records'][0]['value']
    with pytest.raises(ValueError): AnalysisPlan(aggregation='ratio_total',metric='f2')
    with pytest.raises(ValueError): ChartSpec(color='javascript:alert(1)')
    with pytest.raises(ValueError): ChartSpec(width=90000)
    with pytest.raises(ValueError): AnalysisPlan.model_validate({'execute':'rm -rf /'})


def test_excel_and_csv():
    root=Path(__file__).resolve().parents[1]/'samples'
    raw=(root/'中文多工作表.xlsx').read_bytes()
    df,names,warnings,sheets=parse(raw,'test.xlsx','中文销售',2)
    assert len(df)==4 and names==['日期','地区','销售额']
    assert sheets==['说明','中文销售']
    assert df['f3'].isna().sum()==2
    assert any('Formula cache missing' in s for s in warnings)
    ds=snapshot(df,names,'excel',raw,warnings)
    assert ds['fields'][0]['dtype']=='date'
    with pytest.raises(ValueError): compute(pd.read_parquet(store.root()/ds['snapshot']),AnalysisPlan(group_by=['f2'],metric='f3'),ds)
    result=compute(pd.read_parquet(store.root()/ds['snapshot']),AnalysisPlan(group_by=['f2'],metric='f3',missing='keep'),ds)
    assert result['input_rows']==4
    assert result['records'][0]['value']==400
    raw=(root/'重复表头-gb18030.csv').read_bytes()
    with pytest.raises(ValueError,match='Encoding'): parse(raw,'bad.csv')
    df,names,warnings,_=parse(raw,'bad.csv',encoding='gb18030')
    assert names==['地区','金额','金额'] and list(df.columns)==['f1','f2','f3']
    ds=snapshot(df,names,'csv',raw,warnings)
    assert ds['fields'][1]['dtype']=='string' and ds['rows']==2
    with pytest.raises(ValueError,match='非法数字'): snapshot(df,names,'csv',overrides={'f2':{'dtype':'number'}})
    with pytest.raises(ValueError,match='Row 2'): parse(b'a,b\n1,2,3','x.csv')


def test_month_filter_and_missing():
    df=pd.DataFrame({'f1':pd.to_datetime(['2026-01-01','2026-01-31','2026-02-04']),'f2':[100,200,50]})
    ds=snapshot(df,['date','amount'],'known')
    result=compute(df,AnalysisPlan(group_by=['f1'],metric='f2',time_grain='month'),ds)
    assert [r['value'] for r in result['records']]==[300,50]
    assert 'incomplete' in result['warnings'][0]
    with pytest.raises(ValueError): compute(df,AnalysisPlan(metric='not-a-field'),ds)


def test_recommendations_missing_denominator():
    from services.api.providers import recommend
    df=pd.DataFrame({'f1':['A','B'],'f2':[1,3]});ds=snapshot(df,['医院','拜访次数'],'test')
    result=recommend(ds,'计算医院渗透率')
    assert result['mode']=='rule' and len(result['proposals'])>=2
    assert result['questions'] and all(p['plan']['aggregation']!='ratio_total' for p in result['proposals'])


def test_sqlite_real_readonly(monkeypatch):
    from services.api.database import query,sqlite_connection,browse
    path=Path(__file__).resolve().parents[1]/'samples/sample.sqlite'
    monkeypatch.setenv('SQLITE_FILES_JSON',json.dumps({'test':str(path)}))
    df,names=query('test','SELECT region, SUM(amount) AS revenue FROM orders GROUP BY region')
    assert names==['region','revenue'];assert df.to_dict('records')==[{'f1':'East','f2':400.},{'f1':'West','f2':200.}]
    assert browse('test')['rows']
    with pytest.raises(ValueError): query('test','DELETE FROM orders')
    with pytest.raises(ValueError): query('test','SELECT * FROM orders',1)
    with sqlite_connection('test') as c:
        with pytest.raises(Exception): c.execute('DELETE FROM orders')
        with pytest.raises(Exception): c.execute("ATTACH DATABASE ':memory:' AS extra")
        with pytest.raises(Exception): c.execute("SELECT load_extension('evil')")
    with pytest.raises(ValueError): query('../../secret','SELECT 1')


def test_persistence_cancel_recovery_stale():
    from services.worker.main import recover
    client=TestClient(app)
    p=client.post('/projects',json={'name':'Persistence'}).json()
    client.post(f"/projects/{p['id']}/paste",json={'text':'group\tamount\nA\t100\nB\t200'})
    body={'plan':{'group_by':['f1'],'metric':'f2'},'spec':{},'expected_head':None}
    r=client.post(f"/projects/{p['id']}/runs",json=body).json()
    assert r['status']=='queued'
    second=client.post(f"/projects/{p['id']}/runs",json=body).json()
    assert client.get('/runs/'+r['id']).json()['status']=='stale'
    assert client.post('/runs/'+second['id']+'/cancel').json()['status']=='cancelled'
    retry=client.post('/runs/'+second['id']+'/retry').json()
    with store.connect() as c: store.event(c,retry,'render','running')
    recover()
    assert client.get('/runs/'+retry['id']).json()['status']=='failed'
    reopened=TestClient(app).get('/projects/'+p['id']).json()
    assert reopened['dataset']['rows']==2
    assert reopened['name']=='Persistence'


def test_bound_edits_and_bundle():
    client=TestClient(app);p=client.post('/projects',json={'name':'history'}).json()
    ds=client.post(f"/projects/{p['id']}/paste",json={'text':'地区\t金额\n华东\t100\n华南\t200'}).json()
    df=pd.read_parquet(store.root()/ds['snapshot']);plan=AnalysisPlan(group_by=['f1'],metric='f2')
    rev=ChartRevision(id=store.uid(),chart_id=p['chart_id'],dataset_id=ds['id'],plan=plan,spec=ChartSpec(),code='controlled',result=compute(df,plan,ds),summary='initial',created_at=store.now()).model_dump()
    store.put('revision',rev)
    with store.connect() as c:c.execute('UPDATE projects SET head=? WHERE id=?',(rev['id'],p['id']))
    invalid=client.post(f"/projects/{p['id']}/edit",json={'chart_id':'wrong','revision_id':rev['id'],'text':'blue'})
    assert invalid.status_code==422
    response=client.post(f"/projects/{p['id']}/edit",json={'chart_id':p['chart_id'],'revision_id':rev['id'],'text':'筛选 地区=华东'})
    assert response.status_code==200
    with store.connect() as c: payload=json.loads(c.execute('SELECT payload FROM jobs WHERE id=?',(response.json()['id'],)).fetchone()[0])
    assert compute(df,AnalysisPlan.model_validate(payload['plan']),ds)['records']==[{'f1':'华东','value':100}]
    z=zipfile.ZipFile(io.BytesIO(client.get(f"/revisions/{rev['id']}/bundle").content))
    assert 'data.parquet' not in z.namelist()
    assert 'raw' not in json.loads(z.read('dataset.json'))
