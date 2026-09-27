"""Live local API evaluation. Creates labeled synthetic evaluation projects only."""
import json
import time
from pathlib import Path
import httpx

CASES = [
    ("overview", "sales", "帮我看看这份数据", "Generic descriptive overview is acceptable"),
    ("pretty", "sales", "做个好看的图，适合给老板看", "Ask about audience/metric or state presentation assumptions"),
    ("anomaly", "sales", "哪里不太对劲？", "Clarify anomaly definition or perform explicit anomaly checks"),
    ("growth", "sales", "最近是不是不行了？帮我找原因", "Clarify metric/period and avoid causal conclusions or incomplete-month comparisons"),
    ("share", "sales", "看看各地区占比", "Compute region revenue / total revenue, or clarify intended metric"),
    ("conversion", "product", "转化怎么样，哪个平台更好？", "Compute sum(conversions)/sum(visitors) by platform"),
    ("penetration", "hospital", "哪些城市渗透率低，应该优先拓展？", "Ask for target hospital population; never fabricate penetration"),
    ("english", "sales", "Something looks off. What should I focus on?", "Clarify intended metric/definition or qualify exploratory alternatives"),
]


def main():
    base=Path(__file__).resolve().parents[1]
    output={"model_status":None,"cases":[],"notes":"Real API/worker/rendering; synthetic data only. First offered plan executed, not silently optimized by evaluator."}
    with httpx.Client(base_url="http://127.0.0.1:8000",timeout=90) as client:
        output["model_status"]=client.get('/model/status').json()
        for name,sample,goal,expected in CASES:
            project=client.post('/projects',json={"name":"[意图评估] "+name}).json()
            dataset=client.post(f'/projects/{project["id"]}/sample/{sample}',json={}).json()
            start=time.perf_counter()
            response=client.post(f'/projects/{project["id"]}/recommend',json={"goal":goal,"mode":"rule","language":"en" if name=="english" else "zh"})
            response.raise_for_status(); recommendation=response.json()
            elapsed=time.perf_counter()-start
            proposals=recommendation['proposals']
            result=client.post(f'/projects/{project["id"]}/runs',json={"plan":proposals[0]['plan'],"spec":proposals[0]['spec'],"expected_head":None})
            result.raise_for_status(); run=result.json()
            deadline=time.monotonic()+120
            while run['status'] in ('queued','running') and time.monotonic()<deadline:
                time.sleep(.5)
                run=client.get('/runs/'+run['id']).json()
            state=client.get('/projects/'+project['id']).json()
            revision=state.get('revision')
            evidence={"case":name,"goal":goal,"expected":expected,"project_id":project['id'],"fields":{f['id']:f['name'] for f in dataset['fields']},"recommend_ms":round(elapsed*1000,1),"questions":recommendation['questions'],"plans":[p['plan'] for p in proposals],"titles":[p['title'] for p in proposals],"status":run['status'],"error":run.get('error'),"warnings":revision['result'].get('warnings',[]) if revision else [],"records":revision['result']['records'] if revision else [],"artifacts":revision['artifacts'] if revision else {}}
            if revision:
                png=client.get(f'/revisions/{revision["id"]}/artifact/png')
                evidence['png_http_status']=png.status_code
                evidence['png_signature_valid']=png.content.startswith(b'\x89PNG\r\n\x1a\n')
                if name=='overview':
                    for text in ('更直观一点','改成蓝色'):
                        edit=client.post(f'/projects/{project["id"]}/edit',json={"text":text,"mode":"rule","chart_id":state['chart_id'],"revision_id":state['head']})
                        evidence.setdefault('edit_checks',[]).append({"text":text,"http_status":edit.status_code,"response":edit.json()})
                    decision=client.post(f'/projects/{project["id"]}/decision',json={"revision_id":state['head'],"goal":goal})
                    evidence['decision_check']={"http_status":decision.status_code,"response":decision.json()}
            output['cases'].append(evidence)
            print(name,run['status'],'questions=',len(recommendation['questions']),flush=True)
    # Comparison excludes goal text, so cosmetic goal echo cannot count as intent understanding.
    sales=[c for c in output['cases'] if c['case'] in ('overview','pretty','anomaly','growth','share','english')]
    fingerprints=[json.dumps([{k:v for k,v in plan.items() if k not in ('goal','limitations')} for plan in c['plans']],sort_keys=True) for c in sales]
    output['distinct_sales_plan_structures']=len(set(fingerprints))
    path=base/'docs/evidence/ambiguous-intent-evaluation.json'
    path.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Evidence:',path)


if __name__=='__main__': main()
