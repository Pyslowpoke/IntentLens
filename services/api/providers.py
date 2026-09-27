import json
import os
import httpx
from pathlib import Path
from pydantic import Field
from .contracts import Contract, AnalysisPlan, ChartSpec
from .compute import validate
from .visualization_prompt import VISUALIZATION_SYSTEM


class Proposal(Contract):
    title: str
    explanation: str
    assumptions: list[str] = []
    plan: AnalysisPlan
    spec: ChartSpec


class Proposals(Contract):
    proposals: list[Proposal] = Field(default_factory=list,max_length=4)
    questions: list[str] = []
    analysis: str = ""


class DecisionAction(Contract):
    action: str
    evidence_ids: list[int] = Field(min_length=1)
    rationale: str
    risk: str
    next_step: str


class DecisionAdvice(Contract):
    summary: str
    actions: list[DecisionAction] = Field(min_length=1, max_length=5)
    limitations: list[str] = Field(min_length=1)
    questions: list[str] = []


class ProviderAdapter:
    """Distinct wire protocols; configuration and secrets never leave the API."""
    def __init__(self, provider=None, base=None, model=None, key=None, transport=None):
        config_path=Path(__file__).resolve().parents[2]/".local"/"model.json"
        config=json.loads(config_path.read_text(encoding="utf-8-sig")) if config_path.exists() else {}
        self.provider=provider or os.getenv("PROVIDER") or config.get("provider","rule")
        defaults={"openai":"https://api.openai.com/v1","deepseek":"https://api.deepseek.com","anthropic":"https://api.anthropic.com/v1","ollama":"http://127.0.0.1:11434"}
        local=config if config.get("provider")==self.provider else {}
        self.base=(base or os.getenv("MODEL_BASE_URL") or local.get("base") or defaults.get(self.provider,"")).rstrip("/")
        self.model=model or os.getenv("MODEL") or local.get("model") or ("deepseek-flash" if self.provider=="deepseek" else "")
        self.key=key or os.getenv("MODEL_API_KEY") or local.get("key","")
        self.transport=transport

    def status(self):
        return {"provider":self.provider,"model":self.model,"ready":self.provider in ("openai","deepseek","anthropic","ollama") and bool(self.model) and bool(self.key or self.provider=="ollama")}

    def request(self, prompt, contract=Proposals):
        if not self.model: raise ValueError("Configure MODEL on the API server / 请在服务端配置模型")
        if self.provider != "ollama" and not self.key: raise ValueError("Missing server-side API key; use rule mode or configure environment")
        system=VISUALIZATION_SYSTEM+json.dumps(contract.model_json_schema())
        messages=[{"role":"system","content":system},{"role":"user","content":prompt}]
        headers={}
        if self.provider in ("openai","deepseek"):
            path="/chat/completions"
            payload={"model":self.model,"messages":messages,"response_format":{"type":"json_object"}}
            headers["Authorization"]="Bearer "+self.key
            if self.provider=="deepseek":
                payload.update(max_tokens=8192, thinking={"type":"disabled"})
        elif self.provider=="anthropic":
            path="/messages"
            payload={"model":self.model,"system":system,"messages":messages[1:],"max_tokens":4096}
            headers={"x-api-key":self.key,"anthropic-version":"2023-06-01"}
        elif self.provider=="ollama":
            path="/api/chat"
            payload={"model":self.model,"messages":messages,"stream":False,"format":contract.model_json_schema()}
        else: raise ValueError("Unknown provider")
        try:
            with httpx.Client(timeout=60,transport=self.transport) as client:
                r=client.post(self.base+path,json=payload,headers=headers)
            if r.status_code in (401,403): raise ValueError("Model authentication failed; check the server-side key / 模型密钥无效")
            if r.status_code==429: raise ValueError("Model rate limit; retry later / 模型限流")
            if r.is_error: raise ValueError(f"Model service HTTP {r.status_code}; response body withheld to protect secrets")
            try:
                obj=r.json()
            except ValueError as e:
                raise ValueError("Model returned invalid JSON / 模型响应不是有效 JSON") from e
            if self.provider in ("openai","deepseek"):
                choice=obj["choices"][0]
                if choice.get("finish_reason")=="length": raise ValueError("Model output truncated; simplify the question / 模型输出被截断，请简化问题")
                content=choice["message"]["content"]
            elif self.provider=="anthropic": content="".join(c["text"] for c in obj["content"] if c["type"]=="text")
            else: content=obj["message"]["content"]
            try:
                return contract.model_validate_json(content)
            except ValueError as e:
                raise ValueError("Model returned invalid structured output; retry / 模型返回格式无效，请重试") from e
        except (KeyError,IndexError,TypeError) as e: raise ValueError("Model returned an invalid response / 模型响应无效") from e
        except httpx.TimeoutException as e: raise ValueError("Model request timed out / 模型请求超时") from e
        except httpx.RequestError as e: raise ValueError("Model connection failed; verify base URL / 模型连接失败") from e


def recommend(dataset, goal, mode="rule", language="zh", history=None, visualization_context=None):
    if mode=="model":
        adapter=ProviderAdapter()
        from .data_review import review
        data_review=review(dataset)
        result=adapter.request(json.dumps({"goal":goal,"data_review":data_review,"conversation":history or [],"visualization_context":visualization_context or {},"fields":dataset["fields"],"statistics":dataset["profile"],"rows":dataset["rows"],"response_language":"English" if language=="en" else "简体中文","policy":"summary-only, no row samples","instruction":"Continue this dataset's conversation. Explain your understanding and data limitations in analysis (a concise user-facing explanation, not private reasoning). Ask at most two necessary questions if metric, denominator, timeframe or comparison is ambiguous. Offer 0-2 executable proposals, preferably one recommendation: none if missing prerequisites prevent a meaningful analysis, otherwise describe provisional assumptions. Never claim results before calculation. Use prior user answers; do not repeat already answered questions. For a request to modify a previous proposal, preserve its unrequested semantics. Visualization preferences are defaults, not constraints. Use the supplied current chart and engine capabilities. If the user criticizes the appearance or interaction (including matlib/matplotlib complaints), recommend a compatible alternative engine rather than blindly reusing the preference. Explain the tradeoff in analysis and proposal explanation, set spec.engine explicitly, and preserve the current analysis plan when only appearance is criticized. Do not claim one engine is universally prettier. Do not change saved preferences; the user chooses whether to execute your proposal.","prompt_version":"2.0"},ensure_ascii=False))
        if not (result.proposals or result.questions): raise ValueError("Model returned neither a plan nor a clarification question / 模型未返回方案或澄清问题")
        # Providers sometimes return display names despite the stable-ID schema.
        # Resolve only unique exact names; ambiguous/unknown fields still fail.
        names={}
        for field in dataset["fields"]: names.setdefault(field["name"],[]).append(field["id"])
        ids={f["id"] for f in dataset["fields"]}
        def field_id(value):
            return names[value][0] if value not in ids and value in names and len(names[value])==1 else value
        valid_proposals=[]
        for p in result.proposals:
            p.plan.group_by=[field_id(v) for v in p.plan.group_by]
            p.plan.metric=field_id(p.plan.metric)
            p.plan.denominator=field_id(p.plan.denominator)
            for f in p.plan.filters: f.field=field_id(f.field)
            p.spec.mapping={axis:("value" if field_id(value)==p.plan.metric else field_id(value)) for axis,value in p.spec.mapping.items()}
            validate(p.plan,dataset)
            output_fields = set(p.plan.group_by or ['_all']) | {'value'}
            if p.plan.aggregation == 'raw':
                output_fields = set(p.plan.group_by + ([p.plan.denominator] if p.plan.denominator else [])) | ({'value'} if p.plan.metric else set())
                if not output_fields: output_fields = ids
            if any(value not in output_fields for axis,value in p.spec.mapping.items() if axis in ('x','y')):
                result.analysis += ('\n方案的绘图字段与计算结果不一致，已阻止执行；请重新生成方案。' if language!='en' else '\nA proposal mapped nonexistent result columns and was blocked. Please regenerate the plan.')
                continue
            from .render import resolve
            resolve(p.spec)
            valid_proposals.append(p)
        result.proposals=valid_proposals
        if not result.proposals and not result.questions:
            result.questions.append('是否根据现有字段重新生成可执行方案？' if language!='en' else 'Regenerate an executable proposal using the available fields?')
        return dict(mode=adapter.provider,**result.model_dump())
    fields=dataset["fields"]
    nums=[f for f in fields if f["dtype"]=="number"]
    groups=[f for f in fields if f["dtype"]=="date" or (f["dtype"]=="string" and f.get("unique",0)<=max(10,dataset["rows"]*.7))]
    metric=nums[-1]["id"] if nums else None
    # Prefer financial amount when present, not identifiers or ratios.
    for f in nums:
        if any(w in f["name"].lower() for w in ("销售额","收入","revenue","amount")): metric=f["id"]; break
    questions=[]
    if any(w in goal.lower() for w in ("渗透率","penetration")) and not any("目标" in f["name"] or "target" in f["name"].lower() for f in fields):
        questions.append("缺少目标总体分母，不能计算渗透率。请补充目标医院总数；以下方案仅描述现有数据 / Target population is missing.")
    proposals=[]
    dims=groups[:3] or [None]
    for i,g in enumerate(dims):
        isdate=g and g["dtype"]=="date"
        plan=AnalysisPlan(goal=goal,group_by=[g["id"]] if g else [],metric=metric,aggregation="sum" if metric else "count",sort="label" if isdate else "desc",time_grain="month" if isdate else "none",missing="keep",limitations=["Descriptive analysis, not causal / 描述性分析，不代表因果"])
        title=(g["name"] if g else "总体")+" · "+("趋势 / Trend" if isdate else "对比 / Compare")
        proposals.append(Proposal(title=title,explanation="按所选维度真实汇总；执行前可修改字段与口径。 / Aggregate the selected measure by dimension.",assumptions=["空值保留；聚合忽略空指标，不自动填零 / Nulls are not imputed",*questions],plan=plan,spec=ChartSpec(kind="line" if isdate else "bar",title=title)))
    if len(proposals)<2:
        proposals.append(Proposal(title="记录数量 / Record count",explanation="计算每组记录数，不推断缺少的业务口径。",plan=AnalysisPlan(goal=goal,group_by=[dims[0]["id"]] if dims[0] else [],aggregation="count",missing="keep"),spec=ChartSpec(title="记录数量 / Record count")))
    if language=="en":
        questions=["Target population is missing; provide the denominator before calculating penetration."] if questions else []
        for proposal in proposals:
            dimension=next((f["name"] for f in fields if f["id"] in proposal.plan.group_by),"Overall")
            proposal.title=dimension+" · "+("Trend" if proposal.spec.kind=="line" else "Compare")
            proposal.spec.title=proposal.title
            proposal.explanation="Aggregate the selected measure by dimension. Review fields and calculation rules before running."
            proposal.assumptions=["Nulls are kept, not imputed; aggregate metrics ignore null values.",*questions]
            proposal.plan.limitations=["Descriptive analysis does not establish causality."]
    return dict(mode="rule",**Proposals(proposals=proposals,questions=questions,analysis="当前为规则模式：这些是按字段生成的探索方案，没有调用大模型，也不能理解开放式追问。请切换模型模式继续讨论。" if language!="en" else "Rule mode: these are field-based exploratory plans, not an AI response. Switch to model mode for contextual follow-up.").model_dump())
