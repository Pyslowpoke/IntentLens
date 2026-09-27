import json
import httpx
import pytest
from fastapi.testclient import TestClient
from services.api import store
from services.api.main import app
from services.api.providers import ProviderAdapter, DecisionAdvice


@pytest.fixture
def fixture(monkeypatch,tmp_path):
    monkeypatch.setenv('WORKBENCH_DATA',str(tmp_path))
    monkeypatch.setenv('PROVIDER','deepseek')
    monkeypatch.setenv('MODEL_API_KEY','fixture-key')
    client=TestClient(app)
    p=client.post('/projects',json={'name':'test'}).json()
    revision={'id':'rev','dataset_id':'ds','plan':{'aggregation':'sum','goal':'growth'},'result':{'records':[{'region':'A','value':30}], 'labels':{'value':'Sales'}}}
    store.put('revision',revision)
    with store.connect() as c: c.execute('UPDATE projects SET head=?,dataset_id=? WHERE id=?',('rev','ds',p['id']))
    return client,p['id'],revision


def advice(ids=None):
    return DecisionAdvice(summary='建议小规模验证',actions=[{'action':'测试区域 A','evidence_ids':ids or [1],'rationale':'销售为30','risk':'无成本数据','next_step':'补充成本'}],limitations=['描述性数据不能证明因果'])


def test_decision_evidence_and_persistence(fixture,monkeypatch):
    client,id,r=fixture
    def request(self,prompt,contract):
        payload=json.loads(prompt)
        assert payload['evidence']==[{'id':1,'values':{'region':'A','value':30}}]
        assert 'fixture-key' not in prompt
        return advice()
    monkeypatch.setattr(ProviderAdapter,'request',request)
    response=client.post(f'/projects/{id}/decision',json={'revision_id':'rev'})
    assert response.status_code==200,response.text
    assert response.json()['provider']=='deepseek'
    assert client.get(f'/projects/{id}/decision').json()==response.json()
    assert 'fixture-key' not in client.get('/model/status').text
    assert client.post(f'/projects/{id}/decision',json={'revision_id':'old'}).status_code==422
    r['plan']['aggregation']='raw';store.put('revision',r)
    assert client.post(f'/projects/{id}/decision',json={'revision_id':'rev'}).status_code==422


def test_invalid_evidence_rejected(fixture,monkeypatch):
    client,id,r=fixture
    monkeypatch.setattr(ProviderAdapter,'request',lambda *args:advice([999]))
    response=client.post(f'/projects/{id}/decision',json={'revision_id':'rev'})
    assert response.status_code==422
    assert client.get(f'/projects/{id}/decision').json() is None


def test_evidence_limit_and_changed_revision(fixture,monkeypatch):
    client,id,r=fixture
    r['result']['records']=[{'value':i} for i in range(130)]
    store.put('revision',r)
    def request(self,prompt,contract):
        payload=json.loads(prompt)
        assert len(payload['evidence'])==100
        assert payload['total_groups']==130
        with store.connect() as c: c.execute('UPDATE projects SET head=NULL WHERE id=?',(id,))
        return advice()
    monkeypatch.setattr(ProviderAdapter,'request',request)
    assert client.post(f'/projects/{id}/decision',json={'revision_id':'rev'}).status_code==422
    assert client.get(f'/projects/{id}/decision').json() is None


def test_deepseek_defaults(monkeypatch):
    for name in ('MODEL','MODEL_BASE_URL','MODEL_API_KEY'): monkeypatch.delenv(name,raising=False)
    adapter=ProviderAdapter('deepseek',key='fixture-key')
    assert adapter.base=='https://api.deepseek.com'
    assert adapter.model=='deepseek-flash'
    assert adapter.status()['ready']


@pytest.mark.parametrize('content',['', '{"secret":"fixture-key"}', 'not json'])
def test_bad_output_redacted(content):
    adapter=ProviderAdapter('deepseek','https://api.deepseek.com','deepseek-flash','fixture-key',httpx.MockTransport(lambda r:httpx.Response(200,json={'choices':[{'message':{'content':content}}]})))
    with pytest.raises(ValueError,match='格式无效') as e: adapter.request('test')
    assert 'fixture-key' not in str(e.value)
