"""Local diagnostics for planning; never send entire source rows to a model."""
import pandas as pd
from . import store


def review(dataset):
    df = pd.read_parquet(store.root() / dataset['snapshot'])
    totals = {'all', 'total', 'subtotal', 'grand total', '合计', '总计', '小计', '全部'}
    suspects = []
    for field in dataset['fields']:
        if field['dtype'] != 'string':
            continue
        counts = df[field['id']].dropna().astype(str).str.strip().str.casefold().value_counts()
        for value, count in counts.items():
            if value in totals:
                suspects.append({'field': field['id'], 'value': value, 'rows': int(count)})
    return {
        'rows': len(df),
        'exact_duplicate_rows': int(df.duplicated().sum()),
        'possible_summary_rows': suspects,
        'warnings': dataset.get('warnings', []),
        'policy': 'Summary labels are candidates, not proof. Confirm their meaning before excluding. Duplicate rows may be legitimate repeated events. No automatic deletion.',
        'tools': {
            'compute': 'pandas: explicit filters, missing-value policy, exact-row deduplication, grouping, time bucketing, aggregations and ratios',
            'unsupported': 'Cross-sheet joins, arbitrary formulas, unit conversion and imputation are not executable in AnalysisPlan. Ask for a prepared dataset instead of pretending they were performed.',
        },
    }
