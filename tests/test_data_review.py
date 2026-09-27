import pandas as pd
from services.api.ingest import snapshot
from services.api.data_review import review
from services.api.compute import compute
from services.api.contracts import AnalysisPlan


def test_summary_candidates_are_evidence_not_automatic_deletion(tmp_path, monkeypatch):
    monkeypatch.setenv('WORKBENCH_DATA', str(tmp_path))
    df = pd.DataFrame({'f1': ['A', 'A', 'B', '合计'], 'f2': [10, 10, 20, 40]})
    ds = snapshot(df, ['地区', '收入'], 'test')
    evidence = review(ds)
    assert evidence['exact_duplicate_rows'] == 1
    assert evidence['possible_summary_rows'] == [{'field': 'f1', 'value': '合计', 'rows': 1}]
    original = compute(df, AnalysisPlan(group_by=['f1'], metric='f2'), ds)
    assert original['analyzed_rows'] == 4
    prepared = compute(df, AnalysisPlan(group_by=['f1'], metric='f2', duplicates='drop_exact', filters=[{'field': 'f1', 'op': 'ne', 'value': '合计'}]), ds)
    assert prepared['duplicate_rows_removed'] == 1
    assert prepared['analyzed_rows'] == 2
    assert sum(row['value'] for row in prepared['records']) == 30
    assert len(pd.read_parquet(tmp_path / ds['snapshot'])) == 4
