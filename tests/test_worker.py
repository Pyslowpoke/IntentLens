import json
import threading
import time
import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api import store
from services.worker.main import step,recover

@pytest.fixture(autouse=True)
def isolated(tmp_path,monkeypatch):monkeypatch.setenv('WORKBENCH_DATA',str(tmp_path/'worker'))

def setup():
    client=TestClient(app)
    p=client.post('/projects',json={'name':'worker evidence'}).json()
    client.post(f"/projects/{p['id']}/paste",json={'text':'地区\t收入\n华东\t100\n华南\t200'})
    body={'plan':{'group_by':['f1'],'metric':'f2'},'spec':{'engine':'matplotlib'},'expected_head':None}
    return client,p,body

def test_late_real_worker_cannot_replace_new_dataset():
    client,p,body=setup()
    run=client.post(f"/projects/{p['id']}/runs",json=body).json()
    thread=threading.Thread(target=step);thread.start()
    deadline=time.monotonic()+10
    while client.get('/runs/'+run['id']).json()['status']=='queued' and time.monotonic()<deadline:time.sleep(.01)
    assert client.get('/runs/'+run['id']).json()['status']=='running'
    client.post(f"/projects/{p['id']}/paste",json={'text':'地区\t收入\n新数据\t999'})
    thread.join(60);assert not thread.is_alive()
    assert client.get('/runs/'+run['id']).json()['status']=='stale'
    restored=TestClient(app).get('/projects/'+p['id']).json()
    assert restored['head'] is None and restored['dataset']['rows']==1

def test_real_worker_timeout_retry_and_result_cache(monkeypatch):
    client,p,body=setup()
    run=client.post(f"/projects/{p['id']}/runs",json=body).json()
    monkeypatch.setenv('RUN_TIMEOUT','0.01');step()
    assert client.get('/runs/'+run['id']).json()['status']=='failed'
    assert 'Timeout' in client.get('/runs/'+run['id']).json()['error']
    monkeypatch.setenv('RUN_TIMEOUT','60')
    retry=client.post('/runs/'+run['id']+'/retry').json();step()
    assert client.get('/runs/'+retry['id']).json()['status']=='completed'
    project=client.get('/projects/'+p['id']).json();before=project['revision']['result']['records']
    edit=client.post(f"/projects/{p['id']}/edit",json={'chart_id':p['chart_id'],'revision_id':project['head'],'text':'blue'}).json();step()
    after=TestClient(app).get('/projects/'+p['id']).json()
    assert after['revision']['result']['records']==before==[{'f1':'华东','value':100},{'f1':'华南','value':200}]
    assert after['revision']['result']['execution']['compute_cache_hit'] is True
    assert len(after['history'])==2

def test_real_cancel_during_execution():
    client,p,body=setup();run=client.post(f"/projects/{p['id']}/runs",json=body).json()
    thread=threading.Thread(target=step);thread.start()
    deadline=time.monotonic()+10
    while client.get('/runs/'+run['id']).json()['status']=='queued' and time.monotonic()<deadline:time.sleep(.01)
    client.post('/runs/'+run['id']+'/cancel');thread.join(30)
    assert not thread.is_alive()
    assert client.get('/runs/'+run['id']).json()['status']=='cancelled'
    assert client.get('/projects/'+p['id']).json()['head'] is None


def test_verbose_child_error_does_not_deadlock(monkeypatch):
    import subprocess,sys
    client,p,body=setup();run=client.post(f"/projects/{p['id']}/runs",json=body).json()
    original=subprocess.Popen
    def verbose_child(args,**kwargs):
        return original([sys.executable,'-c',"import sys; sys.stderr.write('warning '*200000); sys.stderr.write('EXPECTED_FAILURE'); sys.exit(1)"],**kwargs)
    monkeypatch.setattr(subprocess,'Popen',verbose_child)
    monkeypatch.setenv('RUN_TIMEOUT','5')
    step()
    result=client.get('/runs/'+run['id']).json()
    assert result['status']=='failed'
    assert 'EXPECTED_FAILURE' in result['error']
    assert 'Timeout' not in result['error']
