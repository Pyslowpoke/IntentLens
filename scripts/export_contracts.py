import json
from pathlib import Path
from services.api.contracts import DatasetSnapshot,AnalysisPlan,ChartSpec,ChartRevision,Run
out=Path('packages/contracts');out.mkdir(parents=True,exist_ok=True)
for model in (DatasetSnapshot,AnalysisPlan,ChartSpec,ChartRevision,Run):
    (out/(model.__name__+'.schema.json')).write_text(json.dumps(model.model_json_schema(),indent=2,ensure_ascii=False),encoding='utf-8')
print('Exported five versioned contracts')
