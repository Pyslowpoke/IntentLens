"""Chart delivery must not depend on optional static-export infrastructure."""
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api import store
from services.api.contracts import ChartSpec
from services.api.render import render
from services.worker.main import step


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv('WORKBENCH_DATA', str(tmp_path / 'delivery'))


def test_plotly_preview_does_not_start_static_export(tmp_path, monkeypatch):
    import plotly.io as pio
    def forbidden(*args, **kwargs):
        raise AssertionError('Preview must not require Chrome or static exports')
    monkeypatch.setattr(pio, 'write_images', forbidden)
    result = {'records': [{'region': 'East', 'value': 100}], 'columns': ['region', 'value']}
    artifacts = render(result, ChartSpec(engine='plotly'), tmp_path / 'preview', preview_only=True)
    assert set(artifacts) == {'html', 'plotly'}
    assert 'Plotly.newPlot' in (tmp_path / 'preview' / artifacts['html']).read_text(encoding='utf-8')


def test_altair_preview_does_not_convert_static_files(tmp_path, monkeypatch):
    import vl_convert
    def forbidden(*args, **kwargs):
        raise AssertionError('Static conversion must not block the interactive chart')
    monkeypatch.setattr(vl_convert, 'vegalite_to_svg', forbidden)
    result = {'records': [{'region': 'East', 'value': 100}], 'columns': ['region', 'value']}
    artifacts = render(result, ChartSpec(engine='altair'), tmp_path / 'altair', preview_only=True)
    assert artifacts == {'html': 'chart.html'}
    assert 'vegaEmbed' in (tmp_path / 'altair' / 'chart.html').read_text(encoding='utf-8')


def create_run():
    client = TestClient(app)
    response = client.post('/projects', json={'name': 'Synthetic delivery regression'})
    assert response.status_code == 200, response.json()
    project = response.json()
    client.post(f"/projects/{project['id']}/paste", json={'text': 'region\trevenue\nEast\t100\nWest\t200'})
    run = client.post(f"/projects/{project['id']}/runs", json={'plan': {'group_by': ['f1'], 'metric': 'f2'}, 'spec': {'engine': 'plotly'}, 'expected_head': None}).json()
    return client, project, run


def test_abandoned_queue_expires_without_browser_polling(monkeypatch):
    import time
    monkeypatch.setenv('TASK_SWEEP_INTERVAL','.1')
    monkeypatch.setenv('RUN_QUEUE_TIMEOUT','.1')
    with TestClient(app):
        _,_,run=create_run()
        def current():
            with store.connect() as c:
                return json.loads(c.execute('SELECT body FROM jobs WHERE id=?',(run['id'],)).fetchone()[0])
        deadline=time.monotonic()+3
        while time.monotonic()<deadline and current()['status']=='queued':
            time.sleep(.05)
        assert current()['status']=='failed'
        assert 'Queue timed out' in current()['error']


def test_real_worker_delivers_preview_and_on_demand_png(monkeypatch):
    client, project, run = create_run()
    # Even an unusable configured browser cannot prevent first delivery.
    monkeypatch.setenv('BROWSER_PATH', 'nonexistent-browser.exe')
    step()
    assert client.get('/runs/' + run['id']).json()['status'] == 'completed'
    revision = client.get('/projects/' + project['id']).json()['revision']
    assert revision['result']['records'] == [{'f1': 'East', 'value': 100}, {'f1': 'West', 'value': 200}]
    assert 'png' not in revision['artifacts']
    assert 'png' in revision['available_exports']
    assert client.get(f"/revisions/{run['id']}/artifact/html").status_code == 200
    png = client.get(f"/revisions/{run['id']}/artifact/png?download=true")
    assert png.status_code == 200, png.text[:300] if png.status_code != 200 else ''
    assert png.content.startswith(b'\x89PNG\r\n\x1a\n')


def test_failed_export_keeps_completed_chart(monkeypatch):
    client, project, run = create_run()
    step()
    process = Mock(returncode=1)
    monkeypatch.setattr(subprocess, 'Popen', lambda *args, **kwargs: process)
    export = client.get(f"/revisions/{run['id']}/artifact/png?download=true")
    assert export.status_code == 422
    assert '图表已保留' in export.json()['detail']
    assert client.get('/runs/' + run['id']).json()['status'] == 'completed'
    assert client.get(f"/revisions/{run['id']}/artifact/html").status_code == 200


def test_missing_child_output_terminates_failed_job(monkeypatch):
    client, project, run = create_run()
    original = subprocess.Popen
    monkeypatch.setattr(subprocess, 'Popen', lambda args, **kwargs: original([sys.executable, '-c', 'pass'], **kwargs))
    assert step() is True
    assert client.get('/runs/' + run['id']).json()['status'] == 'failed'


@pytest.mark.parametrize('status', ['queued', 'running'])
def test_abandoned_jobs_stop_waiting(status):
    client, project, run = create_run()
    run['status'] = status
    run['updated_at'] = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    with store.connect() as connection:
        connection.execute('UPDATE jobs SET status=?,body=? WHERE id=?', (status, json.dumps(run), run['id']))
    result = client.get('/runs/' + run['id']).json()
    assert result['status'] == 'failed'
    assert result['error']
