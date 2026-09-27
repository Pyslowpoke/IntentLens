from services.config import load_environment


def test_env_precedence_and_no_interpolation(tmp_path, monkeypatch):
    path=tmp_path/'.env'
    path.write_text('PROVIDER=deepseek\nMODEL_API_KEY="literal-${HOME}"\nWORKBENCH_DATA=fixture\n',encoding='utf-8')
    monkeypatch.setenv('PROVIDER','rule')
    monkeypatch.delenv('MODEL_API_KEY',raising=False)
    monkeypatch.delenv('WORKBENCH_DATA',raising=False)
    load_environment('api',path)
    import os
    assert os.environ['PROVIDER']=='rule'
    assert os.environ['MODEL_API_KEY']=='literal-${HOME}'
    assert os.environ['WORKBENCH_DATA']=='fixture'


def test_worker_does_not_load_model_or_database_secrets(tmp_path,monkeypatch):
    path=tmp_path/'.env'
    path.write_text('MODEL_API_KEY=secret\nDB_SOURCES_JSON=secret\nRUN_TIMEOUT=23\n',encoding='utf-8')
    for key in ('MODEL_API_KEY','DB_SOURCES_JSON','RUN_TIMEOUT'): monkeypatch.delenv(key,raising=False)
    load_environment('worker',path)
    import os
    assert 'MODEL_API_KEY' not in os.environ
    assert 'DB_SOURCES_JSON' not in os.environ
    assert os.environ['RUN_TIMEOUT']=='23'
