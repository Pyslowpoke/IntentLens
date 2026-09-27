import os
import json
import pytest
import sqlalchemy as sa
from services.api.database import query,browse

@pytest.mark.database
@pytest.mark.parametrize('kind',['postgresql','mysql'])
def test_real_database(kind,monkeypatch):
    # Deliberately fail, not skip, if the explicitly requested integration environment is absent.
    urls={'postgresql':'postgresql+psycopg://workbench_reader:fixture_reader_only@127.0.0.1:55432/workbench_test','mysql':'mysql+pymysql://workbench_reader:fixture_reader_only@127.0.0.1:53306/workbench_test'}
    url=os.getenv('TEST_'+kind.upper()+'_URL',urls[kind])
    monkeypatch.setenv('DB_SOURCES_JSON',json.dumps({'fixture':url}))
    df,_=query('fixture','SELECT region,SUM(amount) FROM orders GROUP BY region ORDER BY region')
    assert df.iloc[:,1].tolist()==[400,200]
    assert browse('fixture')['rows']
    engine=sa.create_engine(url)
    try:
        with engine.connect() as c:
            with pytest.raises(sa.exc.DBAPIError):c.execute(sa.text('DELETE FROM orders'))
            c.rollback()
    finally:engine.dispose()
