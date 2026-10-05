"use client";
import { useEffect, useRef, useState } from "react";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  BarChart3,
  Check,
  ChevronDown,
  ChevronRight,
  Clock3,
  Code2,
  Database,
  FileSpreadsheet,
  FolderOpen,
  Globe2,
  History,
  Layers3,
  LoaderCircle,
  Plus,
  Send,
  Settings2,
  ShieldCheck,
  Sparkles,
  Table2,
  Undo2,
  Upload,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { SettingsDialog } from "@/components/settings-dialog";
import { defaults, parsePreferences, preferenceKey, preferredSpec, type Preferences } from "@/lib/preferences";
import { DecisionPanel } from "@/components/decision-panel";
import {
  api,
  formatNumber,
  type Project,
  type Proposal,
  type Run,
  type Spec,
  type Plan,
} from "@/lib/api";

type Preview = {
  id: string;
  names: string[];
  rows: number;
  preview: Record<string, unknown>[];
  warnings: string[];
  sheets: string[];
  sheet: string;
  header: number;
  delimiter: string;
  encoding: string;
};
type Cap = {
  kinds: string[];
  formats: string[];
  interaction: string;
  limits: string;
};
export default function Home() {
  const [preferences, setPreferences] = useState<Preferences>({...defaults});
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [preferenceNotice, setPreferenceNotice] = useState("");
  const lang = preferences.language;
  function savePreferences(next: Preferences) {
    localStorage.setItem(preferenceKey, JSON.stringify(next));
    setPreferences(next);
  }
  useEffect(() => {
    try { setPreferences(parsePreferences(localStorage.getItem(preferenceKey))); } catch { /* Use defaults if storage is unavailable. */ }
    const sync = (event: StorageEvent) => { if (event.key === preferenceKey) setPreferences(parsePreferences(event.newValue)); };
    window.addEventListener("storage", sync);
    return () => window.removeEventListener("storage", sync);
  }, []);
  useEffect(() => {
    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
    document.title = lang === "zh" ? "观意 IntentLens · 意图驱动的数据分析工作台" : "IntentLens · Intent-driven data analysis";
    setGoal(previous => previous === "分析不同地区的销售表现，找出增长机会" || previous === "Analyze regional sales performance and identify growth opportunities" ? (lang === "zh" ? "分析不同地区的销售表现，找出增长机会" : "Analyze regional sales performance and identify growth opportunities") : previous);
  }, [lang]);
  const t = (zh: string, en: string) => (lang === "zh" ? zh : en);
  const [projects, setProjects] = useState<{ id: string; name: string }[]>([]);
  const [project, setProject] = useState<Project | null>(null);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [goal, setGoal] = useState("分析不同地区的销售表现，找出增长机会");
  const [mode, setMode] = useState("rule");
  const [modelStatus, setModelStatus] = useState({provider: "rule", model: "", ready: false});
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(false);
  const [actionLabel, setActionLabel] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState("");
  const [run, setRun] = useState<Run | null>(null);
  const [command, setCommand] = useState("");
  const [tab, setTab] = useState("chart");
  const [modal, setModal] = useState<"import" | "database" | "advanced" | null>(
    null,
  );
  const [caps, setCaps] = useState<Record<string, Cap>>({});
  const [preview, setPreview] = useState<Preview | null>(null);
  const [sheetList, setSheetList] = useState<{name:string;rows:number;columns:number;hidden:boolean;preview:string[][]}[]>([]);
  const fileRequest = useRef(0);
  async function chooseFile(next: File | null) {
    const request = ++fileRequest.current;
    setFile(next); setPreview(null); setSheet(""); setHeader(1); setSheetList([]);
    if (next?.name.toLowerCase().endsWith(".xlsx")) {
      const fd = new FormData(); fd.set("file",next);
      const result = await api<{sheets:typeof sheetList}>("/imports/sheets",fd);
      if(request===fileRequest.current) setSheetList(result.sheets);
    }
  }
  const [messages, setMessages] = useState<{role:string;content:string}[]>([]);
  const conversationView = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const view=conversationView.current;
    if(view) view.scrollTop=view.scrollHeight;
  },[messages]);
  const [analysis, setAnalysis] = useState("");
  const [reply, setReply] = useState("");
  const [responseMode, setResponseMode] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [sheet, setSheet] = useState("");
  const [header, setHeader] = useState(1);
  const [encoding, setEncoding] = useState("utf-8-sig");
  const [delimiter, setDelimiter] = useState(",");
  const [paste, setPaste] = useState("");
  const [editJson, setEditJson] = useState("");
  const [sources, setSources] = useState<Record<string, { kind: string }>>({});
  const [source, setSource] = useState("");
  const [sql, setSql] = useState("SELECT * FROM orders LIMIT 100");
  const [dbResult, setDbResult] = useState<unknown>(null);
  const [sqlGoal, setSqlGoal] = useState("");
  const [sqlTable, setSqlTable] = useState("orders");
  const [questions, setQuestions] = useState<string[]>([]);
  const [density, setDensity] = useState({
    xmin: "",
    xmax: "",
    ymin: "",
    ymax: "",
  });
  const fileInput = useRef<HTMLInputElement>(null);
  const activeId = useRef("");
  const eventRef = useRef<EventSource | null>(null);
  async function downloadChart(id: string, format: string) {
    if (exporting) return;
    setExporting(format); setError("");
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 60000);
    try {
      const response = await fetch(`/api/revisions/${id}/artifact/${format}?download=true`, {signal: controller.signal});
      if (!response.ok) {
        const failure = await response.json().catch(() => ({}));
        throw Error(typeof failure.detail === "string" ? failure.detail : t("文件导出失败，图表已保留。", "Export failed; chart remains available."));
      }
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = url; link.download = `intentlens-${id.slice(0,8)}.${format}`;
      document.body.appendChild(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (failure) {
      setError(controller.signal.aborted ? t("文件导出超时，图表已保留。", "Export timed out; chart remains available.") : failure instanceof Error ? failure.message : String(failure));
    } finally { clearTimeout(timeout); setExporting(""); }
  }
  async function guarded(fn: () => Promise<unknown>, label = t("正在处理…", "Processing…")) {
    if (busyRef.current) return;
    busyRef.current = true;
    setActionLabel(label);
    setNotice("");
    setError("");
    setBusy(true);
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  }
  async function refresh(id: string) {
    const p = await api<Project>("/projects/" + id);
    if (activeId.current === id) {
      setProject(p);
      setRun(p.runs.find((r) => ["running", "queued"].includes(r.status)) || p.runs[0] || null);
    }
    setProjects(await api("/projects"));
    return p;
  }
  async function open(id: string) {
    eventRef.current?.close();
    activeId.current = id;
    localStorage.setItem("workbench-project", id);
    setProposals([]); setMessages([]); setAnalysis(""); setQuestions([]); setResponseMode("");
    setRun(null);
    const p = await refresh(id);
    const c = await api<{
      goal: string;
      proposals: { proposals: Proposal[]; analysis?:string; questions?:string[]; mode?:string } | null;
      messages?: {role:string;content:string}[];
    }>(`/projects/${id}/context`);
    if (c.goal) setGoal(c.goal);
    if (activeId.current !== id) return;
    if (c.proposals) { setProposals(c.proposals.proposals); setAnalysis(c.proposals.analysis || ""); setQuestions(c.proposals.questions || []); setResponseMode(c.proposals.mode || ""); }
    setMessages(c.messages || []);
    const r = p.runs.find((r) => ["running", "queued"].includes(r.status));
    if (r) watch(r, id);
  }
  async function create() {
    const p = await api<Project>("/projects", {
      name: t("我的业务分析", "My business analysis"),
    });
    await open(p.id);
    return p.id;
  }
  useEffect(() => {
    guarded(async () => {
      setCaps(await api("/capabilities"));
      const model = await api<{provider: string; model: string; ready: boolean}>("/model/status");
      setModelStatus(model);
      if (model.ready) setMode("model");
      const ps = await api<{ id: string; name: string }[]>("/projects");
      setProjects(ps);
      const saved = localStorage.getItem("workbench-project");
      // A user may create/open a project while initial discovery is in flight.
      // Do not replace that selection with an older project when discovery returns.
      if (!activeId.current && ps.length)
        await open(ps.some((p) => p.id === saved) ? saved! : ps[0].id);
    });
    return () => eventRef.current?.close();
  }, []);
  useEffect(() => {
    if(!run || !["running","queued"].includes(run.status) || !project) return;
    const id=project.id;
    const timer=setInterval(()=>{refresh(id).catch(e=>setError(e.message));},3000);
    return ()=>clearInterval(timer);
  }, [run?.id, run?.status, project?.id]);
  function watch(r: Run, id: string) {
    eventRef.current?.close();
    setRun(r);
    const es = new EventSource(`/api/runs/${r.id}/events`);
    eventRef.current = es;
    es.onmessage = (e) => {
      const state = JSON.parse(e.data) as Run;
      if (activeId.current !== id) {
        es.close();
        return;
      }
      setRun(state);
      if (
        ["completed", "failed", "cancelled", "stale"].includes(state.status)
      ) {
        es.close();
        if (state.error) setError(state.error);
        refresh(id).catch((e) => setError(e.message));
      }
    };
  }
  async function sample(name: string) {
    const id = project?.id || (await create());
    await api(`/projects/${id}/sample/${name}`, {});
    setProposals([]); setMessages([]); setAnalysis("");
    setQuestions([]);
    await refresh(id);
  }
  async function recommend(followup?: string) {
    if (!project?.dataset) return;
    const id = project.id;
    const res = await api<{ proposals: Proposal[]; questions: string[]; analysis:string; mode:string; messages:{role:string;content:string}[] }>(
      `/projects/${project.id}/recommend`,
      { goal: followup || goal, mode, language: lang, reset: !followup, preferred_engine: preferences.engine },
    );
    if(activeId.current !== id) return;
    setMessages(res.messages || []); setAnalysis(res.analysis); setResponseMode(res.mode); setReply("");
    setProposals(res.proposals);
    setQuestions(res.questions);
    setNotice(res.proposals.length ? t(`已生成 ${res.proposals.length} 个方案，请选择执行。`, `${res.proposals.length} proposal(s) ready. Choose one to run.`) : t("需要补充信息，请查看分析与追问。", "Please answer the clarification below."));
    requestAnimationFrame(() => document.querySelector(".conversation-panel")?.scrollIntoView({behavior:"smooth",block:"start"}));
  }
  async function execute(proposal: Proposal) {
    if (!project) return;
    const current = await refresh(project.id);
    if (current.dataset?.id !== project.dataset?.id) throw Error(t("数据已变化，请重新生成方案。", "Dataset changed. Generate a new proposal."));
    const preferred = preferredSpec(proposal.spec, preferences, caps, !!responseMode && responseMode !== "rule");
    setPreferenceNotice(preferred.fallback ? t(`偏好的 ${preferences.engine} 不支持 ${proposal.spec.kind}，本次已自动匹配兼容工具。`, `${preferences.engine} does not support ${proposal.spec.kind}; a compatible tool was selected for this chart.`) : "");
    watch(
      await api(`/projects/${project.id}/runs`, {
        plan: proposal.plan,
        spec: preferred.spec,
        expected_head: current.head,
      }),
      project.id,
    );
    setTab("chart");
    requestAnimationFrame(() => document.querySelector(".result-panel")?.scrollIntoView({behavior:"smooth",block:"start"}));
  }
  async function edit(text: string, extra: Record<string, unknown> = {}) {
    if (!project?.revision) return;
    watch(
      await api(`/projects/${project.id}/edit`, {
        text,
        mode,
        chart_id: project.chart_id,
        revision_id: project.head,
        ...extra,
      }),
      project.id,
    );
    setCommand("");
  }
  async function patchSpec(patch: Partial<Spec>) {
    if (!project?.revision) return;
    await edit(t("调整图表配置", "Update chart configuration"), {
      spec: { ...project.revision.spec, ...patch },
    });
  }
  async function uploadPreview() {
    if (!file) throw Error(t("请选择文件", "Choose a file"));
    const fd = new FormData();
    fd.set("file", file);
    fd.set("sheet", sheet);
    fd.set("header", String(header));
    fd.set("encoding", encoding);
    fd.set("delimiter", delimiter);
    setPreview(await api("/imports/preview", fd));
  }
  const r = project?.revision;
  const ds = project?.dataset;
  const working = !!run && ["queued", "running"].includes(run.status);
  const previewStale =
    !!preview &&
    (preview.sheet !== sheet ||
      preview.header !== header ||
      preview.encoding !== encoding ||
      preview.delimiter !== delimiter);
  return (
    <div className="app-shell">
      {(busy || working || error || notice) && <div className={`operation-feedback ${error ? "operation-error" : ""}`} role={error ? "alert" : "status"} aria-live="polite">
        {(busy || working) && !error && <LoaderCircle size={17} className="spin" />}
        <span>{error || (busy ? actionLabel : working ? t(`正在绘图 · ${run?.stage}，请稍候`, `Rendering · ${run?.stage}, please wait`) : notice)}</span>
        {!busy && !working && <button aria-label="关闭操作提示 / Dismiss notification" onClick={()=>{setError("");setNotice("");}}><X size={16}/></button>}
      </div>}
      <aside className="sidebar">
        <div className="wordmark">
          <span className="logo">
            <span className="lens-mark" aria-hidden="true"><i /><i /><i /></span>
          </span>
          <div>
            {t("观意", "IntentLens")}<span>{t("INTENTLENS", "INTENT → EVIDENCE")}</span>
          </div>
        </div>
        <Button
          className="new-project"
          variant="outline"
          disabled={busy}
          onClick={() => guarded(create)}
        >
          <Plus size={16} />
          {t("新建分析项目", "New analysis")}
        </Button>
        <div className="nav-caption">{t("工作空间", "WORKSPACE")}</div>
        <button className={`nav-item ${tab === "chart" ? "active" : ""}`} onClick={() => { setTab("chart"); document.querySelector(".result-panel")?.scrollIntoView({behavior: "smooth", block: "start"}); }}>
          <Layers3 size={17} />
          {t("分析工作台", "Analysis studio")}
          <span className="nav-dot" />
        </button>
        <button className={`nav-item ${tab === "data" ? "active" : ""}`} onClick={() => { setTab("data"); document.querySelector(".result-panel")?.scrollIntoView({behavior: "smooth", block: "start"}); }}>
          <Database size={17} />
          {t("数据与字段", "Data & fields")}
        </button>
        <button className={`nav-item ${tab === "history" ? "active" : ""}`} onClick={() => { setTab("history"); document.querySelector(".result-panel")?.scrollIntoView({behavior: "smooth", block: "start"}); }}>
          <History size={17} />
          {t("版本历史", "Version history")}
          <small>{project?.history.length || 0}</small>
        </button>
        <div className="nav-caption project-label">
          {t("最近项目", "RECENT PROJECTS")}
          <FolderOpen size={14} />
        </div>
        <div className="project-list">
          {projects.map((p) => (
            <button
              key={p.id}
              className={project?.id === p.id ? "selected" : ""}
              onClick={() => guarded(() => open(p.id))}
            >
              <span className="project-square" />
              {p.name}
              <ChevronRight size={13} />
            </button>
          ))}
        </div>
        <div className="sidebar-bottom">
          <div className="local-icon">
            <ShieldCheck size={18} />
          </div>
          <strong>{t("本地工作空间", "Local workspace")}</strong>
          <p>{t("数据保存在本机 · 单用户", "Stored locally · Single user")}</p>
          <span className="status-dot" />
          {t("可复现，才可信", "Reproducible by design")}
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <div className="breadcrumb">
            {t("工作空间", "Workspace")}
            <ChevronRight size={13} />
            <strong>
              {project?.name || t("新的分析旅程", "A new analysis")}
            </strong>
          </div>
          <div className="top-actions">
            <span className="saved">
              <Check size={13} />
              {t("自动保存", "Autosaved")}
            </span>
            <button
              className="language"
              onClick={() => setSettingsOpen(true)}
            >
              <Globe2 size={15} />
              {t("设置", "Settings")}
            </button>
            <button className="avatar" onClick={() => setSettingsOpen(true)} title={preferences.nickname || t("个人设置", "Personal settings")}>{preferences.nickname ? Array.from(preferences.nickname)[0].toUpperCase() : t("意", "I")}</button>
          </div>
        </header>
        <div className="workspace">
          <section className="page-title">
            <div>
              <div className="eyebrow">{preferences.nickname ? t(`${preferences.nickname}，欢迎回到观意`, `Welcome back, ${preferences.nickname}`) : "INTENT → VIEW → EVIDENCE"}</div>
              <h1>
                {t("先理解问题，再看见答案。", "A clear question. A clearer view.")}
              </h1>
              <p>
                {t(
                  "观意，把你想了解的事，变成有依据的视图。",
                  "IntentLens turns what you want to understand into a view you can verify.",
                )}
              </p>
            </div>
            <div className="hero-signature" aria-hidden="true"><span>01 / DATA</span><span>02 / INTENT</span><span>03 / INSIGHT <b>↗</b></span></div>
          </section>
          {run?.status === "failed" && <div className="error" role="alert">{t("绘图任务失败：", "Chart task failed: ")}{run.error || run.stage}</div>}
          {error && (
            <div className="error" role="alert">
              <strong>{t("需要处理", "Action needed")}</strong>
              <span>{error}</span>
              <button onClick={() => setError("")} aria-label="Dismiss">
                <X size={16} />
              </button>
            </div>
          )}
          <div className="workspace-status"><span><span className="status-dot" />{t("分析工作空间", "ANALYSIS WORKSPACE")}</span><span className="mode-pill"><span />{modelStatus.ready ? `${modelStatus.provider} · ${modelStatus.model}` : t("规则模式 · 模型待配置", "Rule mode · Model not configured")}</span></div>
          {preferenceNotice && <p className="warning" role="status">{preferenceNotice}</p>}
          <div className="workflow">
            <span className={ds ? "done" : "current"}>
              <b>{ds ? <Check size={12} /> : 1}</b>
              {t("连接数据", "Connect data")}
            </span>
            <i />
            <span className={proposals.length ? "done" : ds ? "current" : ""}>
              <b>2</b>
              {t("表达意图", "Express intent")}
            </span>
            <i />
            <span className={r ? "current" : ""}>
              <b>3</b>
              {t("验证视图", "Verify the view")}
            </span>
            <i />
            <span>
              <b>4</b>
              {t("沉淀洞察", "Keep the insight")}
            </span>
          </div>
          <div className="studio-grid">
            <div className="primary-column">
              <section className="panel data-panel">
                <div className="panel-heading">
                  <div>
                    <span className="section-index">01</span>
                    <h2>{t("带入数据", "Your starting point")}</h2>
                  </div>
                  <span className="hint">CSV · XLSX · TSV · SQL</span>
                </div>
                {ds ? (
                  <div className="dataset-banner">
                    <div className="dataset-icon">
                      <FileSpreadsheet size={24} />
                    </div>
                    <div>
                      <strong>{ds.source}</strong>
                      <p>
                        {formatNumber(ds.rows)} {t("行", "rows")}
                        <span>·</span>
                        {ds.fields.length} {t("个字段", "fields")}
                        <span>·</span>
                        {t("快照已保存", "Snapshot saved")}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setModal("import")}
                    >
                      {t("更换数据", "Replace")}
                    </Button>
                  </div>
                ) : (
                  <div
                    className="dropzone"
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      guarded(() => chooseFile(e.dataTransfer.files[0] || null));
                      setModal("import");
                    }}
                  >
                    <span className="upload-symbol">
                      <Upload size={25} />
                    </span>
                    <h3>
                      {t(
                        "把数据带进来，让洞察发生",
                        "Bring your data. Discover what matters.",
                      )}
                    </h3>
                    <p>
                      {t(
                        "拖入表格文件，或从本地选择。导入前可以预览与调整。",
                        "Drop a spreadsheet here, or choose a local file. Preview before importing.",
                      )}
                    </p>
                    <div>
                      <Button
                        disabled={busy}
                        onClick={() => {
                          setPreview(null);
                          setModal("import");
                        }}
                      >
                        <Plus size={15} />
                        {t("导入数据", "Import data")}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() =>
                          guarded(async () => {
                            setSources(await api("/database/sources"));
                            setModal("database");
                          })
                        }
                      >
                        <Database size={14} />
                        {t("连接数据库", "Connect database")}
                      </Button>
                    </div>
                  </div>
                )}
                <div className="sample-row">
                  <span>{t("用合成数据试一试", "Try synthetic data")}</span>
                  {[
                    ["sales", t("销售订单", "Sales")],
                    ["product", t("产品使用", "Product")],
                    ["hospital", t("医院拓展", "Hospitals")],
                  ].map(([id, name]) => (
                    <button
                      disabled={busy || working}
                      onClick={() => guarded(() => sample(id))}
                      key={id}
                    >
                      {name}
                      <ArrowRight size={12} />
                    </button>
                  ))}
                </div>
              </section>
              <section className="panel goal-panel">
                <div className="panel-heading">
                  <div>
                    <span className="section-index">02</span>
                    <h2>
                      {t("这次，你想看清什么？", "What would you like to know?")}
                    </h2>
                  </div>
                  <Sparkles size={17} className="purple" />
                </div>
                <textarea
                  aria-label="Business question"
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  placeholder={t(
                    "例如：哪些地区贡献了最多销售额？",
                    "For example: which regions contribute the most revenue?",
                  )}
                />
                <div className="intent-prompts" aria-label="分析意图示例">
                  <span>{t("从一个意图开始", "START WITH AN INTENT")}</span>
                  {[
                    [t("比较差异", "Compare"), t("比较不同类别的表现，找出差异最大的部分", "Compare categories and identify the largest differences")],
                    [t("观察趋势", "Find trends"), t("观察指标随时间的变化，识别增长与回落", "Explore how the metric changes over time")],
                    [t("理解构成", "Understand shares"), t("分析各类别对总体的贡献，明确占比口径", "Analyze category contributions with an explicit denominator")],
                  ].map(([label, prompt]) => <button key={label} disabled={busy || working} onClick={() => setGoal(prompt)}>{label}<ArrowRight size={12} /></button>)}
                </div>
                <div className="prompt-footer">
                  <select
                    aria-label="Analysis mode"
                    value={mode}
                    onChange={(e) => setMode(e.target.value)}
                  >
                    <option value="rule">
                      {t("规则模式 · 无模型调用", "Rule mode · No model call")}
                    </option>
                    <option value="model" disabled={!modelStatus.ready}>
                      {t(
                        "服务端模型 · 仅发送字段摘要",
                        "Server model · Summary only",
                      )}
                    </option>
                  </select>
                  <Button
                    disabled={!ds || busy || working}
                    onClick={() => guarded(() => recommend(), t("正在生成方案，模型响应可能需要约一分钟…", "Generating proposals; the model may take about a minute…"))}
                  >
                    {busy ? (
                      <LoaderCircle className="spin" size={15} />
                    ) : (
                      <Sparkles size={15} />
                    )}{" "}
                    {t("生成分析方案", "Generate plans")}
                    <ArrowRight size={14} />
                  </Button>
                </div>
                <p className="privacy-note">
                  <ShieldCheck size={12} />
                  {t(
                    "规则模式不调用 AI。模型模式默认仅发送字段与统计摘要，不发送原始行。",
                    "Rule mode does not use AI. Model mode sends field metadata and statistics, not raw rows.",
                  )}
                </p>
                {questions.map((q) => (
                  <div className="warning" key={q}>
                    {q}
                  </div>
                ))}
              </section>
              {(busy || messages.length>0) && <section className="panel conversation-panel" aria-label="Analysis conversation">
                <h2>{t("分析与追问", "Analysis discussion")}</h2>
                <p className="response-source">{responseMode ? t(`本轮来源：${responseMode}`, `Response source: ${responseMode}`) : t("等待分析结果", "Awaiting analysis")}</p>
                <div className="conversation-history" ref={conversationView}>{messages.map((message,index) => {
                  let content=message.content;
                  if(message.role==="assistant") { try {const parsed=JSON.parse(content);content=[parsed.analysis || parsed.proposals?.map((p:Proposal)=>p.explanation).join("\n"),...(parsed.questions || [])].filter(Boolean).join("\n");} catch {} }
                  return <div key={index} className={`conversation-message ${message.role}`}><strong>{message.role==="user"?t("你", "You"):t("分析助手", "Analyst")}</strong><p>{content}</p></div>;
                })}</div>
                {busy && <p role="status">{actionLabel}</p>}
                <textarea aria-label="Analysis follow-up" value={reply} onChange={e=>setReply(e.target.value)} placeholder={t("补充口径、回答上方问题，或继续追问。对话绑定当前数据快照。", "Clarify a metric, answer a question, or ask a follow-up. History is tied to this dataset.")} />
                <Button disabled={busy || !reply.trim() || !ds} onClick={()=>guarded(()=>recommend(reply))}>{t("继续讨论", "Continue discussion")}</Button>
                <small>{t("最多保留本次数据的 20 轮讨论；点击“生成分析方案”开始新讨论。", "Up to 20 turns per discussion. Generate plans starts a new discussion.")}</small>
              </section>}
              {!!proposals.length && (
                <section className="proposal-section">
                  <div className="list-heading">
                    <h2>
                      {t("把问题，转成可验证的视图", "Plans for your dataset")}
                    </h2>
                    <span>
                      {t("规则/模型标识见上方模式", "See selected mode above")}
                    </span>
                  </div>
                  <div className="proposal-grid">
                    {proposals.map((p, i) => (
                      <button
                        key={i}
                        className="proposal"
                        disabled={working || busy}
                        onClick={() => guarded(() => execute(p), t("正在提交绘图任务…", "Submitting chart task…"))}
                      >
                        <span className="proposal-icon">
                          <BarChart3 size={19} />
                        </span>
                        <small>
                          0{i + 1} / {p.spec.kind.toUpperCase()}
                        </small>
                        <h3>{p.title}</h3>
                        <p>{t("建议工具：", "Suggested tool: ")}{p.spec.engine === "auto" ? t("自动匹配 / 默认偏好", "Automatic / preference") : p.spec.engine}</p>
                        <p>{p.explanation}</p>
                        <div className="proposal-assumptions">
                          {p.assumptions.join(" · ")}
                        </div>
                        <span className="proposal-cta">
                          {t("执行此方案", "Run this plan")}
                          <ArrowRight size={14} />
                        </span>
                      </button>
                    ))}
                  </div>
                </section>
              )}
              <section className="panel result-panel">
                <div className="result-tabs">
                  <div>
                    {[
                      ["chart", t("可视化", "Visualization"), BarChart3],
                      ["data", t("数据明细", "Data"), Table2],
                      ["history", t("版本记录", "History"), History],
                    ].map(([key, label, Icon]) => {
                      const I = Icon as typeof BarChart3;
                      return (
                        <button
                          className={tab === key ? "selected" : ""}
                          onClick={() => setTab(key as string)}
                          key={key as string}
                        >
                          <I size={15} />
                          {label as string}
                        </button>
                      );
                    })}
                  </div>
                  {r && (
                    <span className="engine-tag">
                      {r.result.execution.engine} · {r.id.slice(0, 6)}
                    </span>
                  )}
                </div>
                {working && (
                  <div className="running">
                    <LoaderCircle size={19} className="spin" />
                    <div>
                      <strong>
                        {t("正在计算并绘制", "Computing & rendering")}
                      </strong>
                      <p>{run?.stage}</p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        guarded(() => api(`/runs/${run?.id}/cancel`, {}))
                      }
                    >
                      {t("取消", "Cancel")}
                    </Button>
                  </div>
                )}
                {tab === "chart" ? (
                  r ? (
                    <>
                      <div className="chart-heading">
                        <div>
                          <h3>{r.spec.title}</h3>
                          <p>
                            {r.plan.aggregation} · {r.result.analyzed_rows}{" "}
                            {t("行参与计算", "rows analyzed")} ·{" "}
                            {r.result.execution.compute_cache_hit
                              ? t("复用计算结果", "Computed result reused")
                              : t("已重新计算", "Recomputed")}
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Undo"
                          disabled={working || !r.parent_id}
                          onClick={() => guarded(() => edit("undo"))}
                        >
                          <Undo2 size={17} />
                        </Button>
                      </div>
                      <div className="chart-downloads" aria-label="Chart downloads">
                        {["png","svg","pdf","html"].filter(format=>r.artifacts[format] || r.available_exports?.includes(format)).map(format=><Button key={format} disabled={!!exporting} onClick={()=>downloadChart(r.id,format)}><ArrowDownToLine size={16}/>{exporting===format ? t("正在导出…", "Exporting…") : format==="png" ? t("下载图片", "Download image") : format.toUpperCase()}</Button>)}
                        <small>{t("先显示图表，下载时生成所需文件。", "Chart first; export files are generated on download.")}</small>
                      </div>
                      <div className="chart-preview">
                        {r.artifacts.html ? (
                          <iframe
                            key={r.id}
                            title="Chart preview"
                            sandbox="allow-scripts"
                            src={`/api/revisions/${r.id}/artifact/html`}
                            style={{
                              height: Math.min(r.spec.height + 20, 640),
                            }}
                          />
                        ) : (
                          <img
                            alt={r.spec.title}
                            src={`/api/revisions/${r.id}/artifact/png`}
                          />
                        )}
                      </div>
                      {r.result.summary && (
                        <div className="metrics">
                          <div>
                            <span>{t("分析分组", "Groups")}</span>
                            <strong>
                              {formatNumber(r.result.summary.groups)}
                            </strong>
                          </div>
                          <div>
                            <span>{t("最大值", "Maximum")}</span>
                            <strong>
                              {formatNumber(r.result.summary.max)}
                            </strong>
                          </div>
                          <div>
                            <span>{t("最小值", "Minimum")}</span>
                            <strong>
                              {formatNumber(r.result.summary.min)}
                            </strong>
                          </div>
                          <div>
                            <span>{t("计算耗时", "Compute time")}</span>
                            <strong>
                              {formatNumber(r.result.execution.compute_ms)}
                              <small>ms</small>
                            </strong>
                          </div>
                        </div>
                      )}
                      {r.result.warnings.map((w) => (
                        <p className="result-warning" key={w}>
                          {w}
                        </p>
                      ))}
                      <div className="refine">
                        <div className="refine-label">
                          <Sparkles size={14} />
                          {t("继续修改这张图", "Refine this chart")}
                          <span>
                            {t(
                              "绑定当前图表与版本",
                              "Bound to current chart & revision",
                            )}
                          </span>
                        </div>
                        <form
                          onSubmit={(e) => {
                            e.preventDefault();
                            guarded(() => edit(command));
                          }}
                        >
                          <input
                            aria-label="Chart edit"
                            value={command}
                            onChange={(e) => setCommand(e.target.value)}
                            placeholder={t(
                              "例如：改成蓝色 / 标题：地区销售表现 / 筛选 地区=华东",
                              "Try: blue / title: Regional sales / filter Region=East",
                            )}
                          />
                          <Button
                            size="icon"
                            disabled={working || busy || !command}
                            aria-label="Apply edit"
                          >
                            <Send size={16} />
                          </Button>
                        </form>
                        <div className="quick-edits">
                          {[
                            t("改成蓝色", "blue"),
                            t("按数值降序", "descending"),
                            t("撤销", "undo"),
                          ].map((s) => (
                            <button
                              disabled={working}
                              key={s}
                              onClick={() => guarded(() => edit(s))}
                            >
                              {s}
                            </button>
                          ))}
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="empty-chart">
                      <div className="mini-bars">
                        <i />
                        <i />
                        <i />
                        <i />
                        <i />
                        <i />
                      </div>
                      <h3>
                        {t(
                          "下一个洞察，从这里开始",
                          "Your next insight starts here",
                        )}
                      </h3>
                      <p>
                        {t(
                          "导入数据，描述目标，选择方案后生成真实图表。",
                          "Import data, describe your goal, then run a plan to create a real chart.",
                        )}
                      </p>
                      <span>REAL DATA. REAL CALCULATIONS.</span>
                    </div>
                  )
                ) : tab === "data" ? (
                  <div className="data-view">
                    {ds ? (
                      <>
                        <h3>
                          {t(
                            "字段画像与类型修正",
                            "Field profile & type correction",
                          )}
                        </h3>
                        <table>
                          <thead>
                            <tr>
                              <th>{t("字段 / ID", "Field / ID")}</th>
                              <th>{t("类型", "Type")}</th>
                              <th>{t("空值", "Nulls")}</th>
                              <th>{t("唯一值", "Unique")}</th>
                              <th>{t("业务含义", "Meaning")}</th>
                            </tr>
                          </thead>
                          <tbody>
                            {ds.fields.map((f) => (
                              <tr key={f.id}>
                                <td>
                                  {f.name}
                                  <small>{f.id}</small>
                                </td>
                                <td>
                                  <select
                                    value={f.dtype}
                                    onChange={(e) =>
                                      guarded(async () => {
                                        await api(
                                          `/projects/${project!.id}/types`,
                                          {
                                            overrides: {
                                              [f.id]: { dtype: e.target.value },
                                            },
                                          },
                                        );
                                        setProposals([]);
                                        await refresh(project!.id);
                                      })
                                    }
                                  >
                                    {[
                                      "string",
                                      "number",
                                      "date",
                                      "boolean",
                                    ].map((type) => (
                                      <option key={type}>{type}</option>
                                    ))}
                                  </select>
                                </td>
                                <td>{f.nulls}</td>
                                <td>{f.unique}</td>
                                <td>
                                  <input
                                    aria-label={`Meaning ${f.id}`}
                                    defaultValue={f.meaning}
                                    key={ds.id + f.id}
                                    onBlur={(e) => {
                                      if (e.target.value !== f.meaning)
                                        guarded(async () => {
                                          await api(
                                            `/projects/${project!.id}/types`,
                                            {
                                              overrides: {
                                                [f.id]: {
                                                  meaning: e.target.value,
                                                },
                                              },
                                            },
                                          );
                                          setProposals([]);
                                          await refresh(project!.id);
                                        });
                                    }}
                                  />
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {ds.warnings.map((w) => (
                          <p className="warning" key={w}>
                            {w}
                          </p>
                        ))}
                        {r && (
                          <>
                            <h3>{t("实际计算结果", "Computed records")}</h3>
                            <DataTable
                              rows={r.result.records}
                              columns={r.result.columns}
                            />
                          </>
                        )}
                      </>
                    ) : (
                      <p>{t("请先导入数据", "Import a dataset first")}</p>
                    )}
                  </div>
                ) : (
                  <div className="history-view">
                    {project?.history.length ? (
                      project.history
                        .slice()
                        .reverse()
                        .map((v, i) => (
                          <div className="history-item" key={v.id}>
                            <span className="history-node" />
                            <div>
                              <strong>{v.summary}</strong>
                              <p>
                                {v.id.slice(0, 8)} ·{" "}
                                {new Date(v.created_at).toLocaleString()} ·{" "}
                                {v.spec.kind}
                              </p>
                              <small>
                                {t("父版本", "Parent")}:{" "}
                                {v.parent_id?.slice(0, 8) || "—"}
                              </small>
                            </div>
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={working || v.dataset_id !== ds?.id}
                              onClick={() =>
                                guarded(() => edit("", { restore_id: v.id }))
                              }
                            >
                              {t("从此版本继续", "Restore")}
                            </Button>
                          </div>
                        ))
                    ) : (
                      <p>
                        {t(
                          "执行第一个方案后，版本会保存在这里。",
                          "Run a plan to start a version history.",
                        )}
                      </p>
                    )}
                    {project?.runs
                      .filter(
                        (v) =>
                          v.status === "failed" || v.status === "cancelled",
                      )
                      .map((v) => (
                        <div className="history-item" key={v.id}>
                          <div>
                            <strong>{v.status}</strong>
                            <p>{v.error}</p>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              guarded(async () =>
                                watch(
                                  await api(`/runs/${v.id}/retry`, {}),
                                  project.id,
                                ),
                              )
                            }
                          >
                            {t("重试", "Retry")}
                          </Button>
                        </div>
                      ))}
                  </div>
                )}
              </section>
              {project?.revision && <DecisionPanel key={project.revision.id} projectId={project.id} revisionId={project.revision.id} goal={goal} language={lang} />}
            </div>
            <aside className="inspector">
              <section className="panel inspector-panel">
                <div className="panel-heading">
                  <div>
                    <Settings2 size={16} />
                    <h2>{t("图表设置", "Chart settings")}</h2>
                  </div>
                </div>
                <div className="inspector-body">
                  <label>
                    {t("绘图引擎", "RENDER ENGINE")}
                    <select
                      disabled={!r || working}
                      value={r?.spec.engine || preferences.engine}
                      onChange={(e) =>
                        guarded(() => patchSpec({ engine: e.target.value }))
                      }
                    >
                      <option value="auto">{t("自动选择", "Automatic")}</option>
                      {Object.keys(caps).map((k) => (
                        <option
                          disabled={!!r && !caps[k].kinds.includes(r.spec.kind)}
                          key={k}
                        >
                          {k}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    {t("图表类型", "CHART TYPE")}
                    <select
                      disabled={!r || working}
                      value={r?.spec.kind || "bar"}
                      onChange={(e) =>
                        guarded(() =>
                          patchSpec({ kind: e.target.value, engine: "auto" }),
                        )
                      }
                    >
                      {Array.from(
                        new Set(Object.values(caps).flatMap((c) => c.kinds)),
                      ).map((k) => (
                        <option key={k}>{k}</option>
                      ))}
                    </select>
                  </label>
                  <label>{t("视觉主题", "THEME")}</label>
                  <div className="theme-options">
                    {[
                      ["light", t("商务浅色", "Light")],
                      ["dark", t("深色", "Dark")],
                      ["report", t("简洁报告", "Report")],
                    ].map(([id, name]) => (
                      <button
                        disabled={!r || working}
                        className={
                          r?.spec.theme === id || (!r && id === preferences.theme)
                            ? "selected"
                            : ""
                        }
                        onClick={() => guarded(() => patchSpec({ theme: id }))}
                        key={id}
                      >
                        <span className={"theme-swatch " + id}>
                          <i />
                          <i />
                          <i />
                        </span>
                        {name}
                      </button>
                    ))}
                  </div>
                  <label>{t("主色", "ACCENT COLOR")}</label>
                  <div className="colors">
                    {[
                      "#5470ef",
                      "#2563eb",
                      "#059669",
                      "#d97706",
                      "#dc2626",
                      "#7c3aed",
                    ].map((c) => (
                      <button
                        key={c}
                        aria-label={"Color " + c}
                        disabled={!r || working}
                        style={{ background: c }}
                        className={r?.spec.color === c ? "chosen" : ""}
                        onClick={() => guarded(() => patchSpec({ color: c }))}
                      />
                    ))}
                  </div>
                  <div className="dimensions">
                    <label>
                      {t("宽度", "WIDTH")}
                      <input
                        aria-label="Width"
                        type="number"
                        min="320"
                        max="2400"
                        defaultValue={r?.spec.width || 1000}
                        key={"w" + r?.id}
                        disabled={!r || working}
                        onBlur={(e) =>
                          r &&
                          Number(e.target.value) !== r.spec.width &&
                          guarded(() =>
                            patchSpec({ width: Number(e.target.value) }),
                          )
                        }
                      />
                    </label>
                    <span>×</span>
                    <label>
                      {t("高度", "HEIGHT")}
                      <input
                        aria-label="Height"
                        type="number"
                        min="240"
                        max="1600"
                        defaultValue={r?.spec.height || 560}
                        key={"h" + r?.id}
                        disabled={!r || working}
                        onBlur={(e) =>
                          r &&
                          Number(e.target.value) !== r.spec.height &&
                          guarded(() =>
                            patchSpec({ height: Number(e.target.value) }),
                          )
                        }
                      />
                    </label>
                  </div>
                  <Button
                    variant="outline"
                    className="full-width"
                    disabled={!r}
                    onClick={() => {
                      setEditJson(
                        JSON.stringify(
                          { plan: r!.plan, spec: r!.spec },
                          null,
                          2,
                        ),
                      );
                      setModal("advanced");
                    }}
                  >
                    <Code2 size={14} />
                    {t("编辑分析与图表配置", "Edit plan & chart JSON")}
                  </Button>
                  {r && (
                    <p className="capability-note">
                      {caps[r.result.execution.engine]?.limits}
                    </p>
                  )}
                  {r?.spec.kind === "density" && (
                    <div>
                      <label>{t("视口重算范围", "Viewport bounds")}</label>
                      {Object.entries(density).map(([k, v]) => (
                        <input
                          key={k}
                          placeholder={k}
                          value={v}
                          onChange={(e) =>
                            setDensity({ ...density, [k]: e.target.value })
                          }
                        />
                      ))}
                      <Button
                        disabled={working}
                        onClick={() =>
                          guarded(() =>
                            patchSpec({
                              extensions: {
                                ...r.spec.extensions,
                                viewport: {
                                  x: [
                                    Number(density.xmin),
                                    Number(density.xmax),
                                  ],
                                  y: [
                                    Number(density.ymin),
                                    Number(density.ymax),
                                  ],
                                },
                              },
                            }),
                          )
                        }
                      >
                        {t("重算视口", "Recompute viewport")}
                      </Button>
                    </div>
                  )}
                </div>
                <div className="export-box">
                  <h3>{t("带走你的洞察", "Take your insight with you")}</h3>
                  <p>
                    {t(
                      "文件按需导出，失败不影响已生成的图表",
                      "Export on demand; export failures do not remove the chart",
                    )}
                  </p>
                  <div className="export-links">
                    {r ? (
                      Array.from(new Set([...Object.keys(r.artifacts), ...(r.available_exports || [])]))
                        .filter((f) =>
                          ["png", "svg", "pdf", "html"].includes(f),
                        )
                        .map((f) => (
                          <button
                            key={f}
                            disabled={!!exporting}
                            onClick={()=>downloadChart(r.id,f)}
                          >
                            <ArrowDownToLine size={13} />
                            {exporting===f ? t("正在导出…", "Exporting…") : f.toUpperCase()}
                          </button>
                        ))
                    ) : (
                      <span className="unavailable">
                        {t(
                          "生成图表后可导出",
                          "Exports appear after rendering",
                        )}
                      </span>
                    )}
                  </div>
                  {r && (
                    <>
                      <a
                        className="bundle"
                        href={`/api/revisions/${r.id}/bundle`}
                      >
                        <Layers3 size={14} />
                        {t(
                          "下载可复现包（不含数据）",
                          "Reproduction bundle (no data)",
                        )}
                      </a>
                      <a
                        className="bundle"
                        href={`/api/revisions/${r.id}/bundle?include_data=true`}
                      >
                        {t("明确包含数据快照的包", "Bundle with data snapshot")}
                      </a>
                    </>
                  )}
                </div>
              </section>
              <section className="guide-card">
                <span className="guide-icon">
                  <Sparkles size={19} />
                </span>
                <h3>
                  {t("每一步，都有依据。", "Every step has a foundation.")}
                </h3>
                <p>
                  {t(
                    "计算口径、数据版本与修改记录一起保存。回到任何一个版本，继续探索。",
                    "Calculations, data versions and edits stay together. Return to a version and keep exploring.",
                  )}
                </p>
                <div>
                  <Check size={13} />
                  {t("真实计算，不猜数字", "Computed values, never guessed")}
                </div>
                <div>
                  <Check size={13} />
                  {t("样式修改复用计算结果", "Style edits reuse results")}
                </div>
                <div>
                  <Check size={13} />
                  {t("默认不导出原始数据", "Raw data excluded by default")}
                </div>
              </section>
              <div className="build-note">
                INTENTLENS · DEVELOPMENT
                <br />
                {t(
                  "合成样例仅用于演示",
                  "Synthetic samples are for demonstration",
                )}
              </div>
            </aside>
          </div>
        </div>
        <footer>
          {t(
            "从数据到决策，保留每一步的来路。",
            "From data to decisions, with every step accounted for.",
          )}
          <span>LOCAL-FIRST ANALYTICS</span>
        </footer>
      </main>
      <SettingsDialog open={settingsOpen} value={preferences} onSave={savePreferences} onClose={() => setSettingsOpen(false)} />
      {modal && (
        <div className="modal-backdrop" onClick={() => setModal(null)}>
          <section className="modal" onClick={(e) => e.stopPropagation()}>
            <header>
              <h2>
                {modal === "import"
                  ? t("导入与预览", "Import & preview")
                  : modal === "database"
                    ? t("只读数据库", "Read-only database")
                    : t("高级配置", "Advanced configuration")}
              </h2>
              <button onClick={() => setModal(null)} aria-label="Close">
                <X size={19} />
              </button>
            </header>
            {modal === "import" ? (
              <>
                <input
                  ref={fileInput}
                  type="file"
                  disabled={busy}
                  accept=".csv,.tsv,.xlsx"
                  onChange={(e) => {
                    guarded(() => chooseFile(e.target.files?.[0] || null));
                  }}
                />
                <div className="import-settings">
                  <label>
                    {t("工作表", "Worksheet")}
                    <select aria-label="Worksheet" value={sheet} onChange={e => {setSheet(e.target.value);setPreview(null);}} disabled={!sheetList.length}>
                      <option value="">{t("请明确选择工作表", "Select a worksheet")}</option>
                      {sheetList.map(s => <option key={s.name} value={s.name}>{s.name} · {s.rows} × {s.columns}{s.hidden ? t("（隐藏）", " (hidden)") : ""}</option>)}
                    </select>
                  </label>
                  <label>
                    {t("表头行", "Header row")}
                    <input
                      type="number"
                      min="1"
                      value={header}
                      onChange={(e) => setHeader(Number(e.target.value))}
                    />
                  </label>
                  <label>
                    {t("编码", "Encoding")}
                    <select
                      value={encoding}
                      onChange={(e) => setEncoding(e.target.value)}
                    >
                      <option>utf-8-sig</option>
                      <option>gb18030</option>
                      <option>utf-16</option>
                    </select>
                  </label>
                  <label>
                    {t("分隔符", "Delimiter")}
                    <select
                      value={delimiter}
                      onChange={(e) => setDelimiter(e.target.value)}
                    >
                      <option value=",">Comma ,</option>
                      <option value={"\t"}>Tab</option>
                      <option value=";">Semicolon ;</option>
                    </select>
                  </label>
                </div>
                {!!sheetList.length && <div className="sheet-catalog"><p>{t("工作簿包含以下工作表。点击查看前 5 行，再选择表头行并解析。", "Choose a sheet, inspect its first 5 rows, then set the header row and preview.")}</p>{sheetList.map(item => <details key={item.name} open={sheet===item.name}><summary onClick={() => setSheet(item.name)}>{item.name} · {item.rows} × {item.columns}</summary><table><tbody>{item.preview.map((row,i)=><tr key={i}><th>{i+1}</th>{row.map((v,j)=><td key={j}>{v || "—"}</td>)}</tr>)}</tbody></table><Button size="sm" onClick={() => {setSheet(item.name);setPreview(null);}}>{t("选择此工作表", "Use this sheet")}</Button></details>)}</div>}
                <Button
                  disabled={!file || busy || (file.name.toLowerCase().endsWith(".xlsx") && !sheet)}
                  onClick={() => guarded(uploadPreview)}
                >
                  {t("解析并预览", "Parse & preview")}
                </Button>
                {preview && (
                  <>
                    <p>
                      {preview.rows}{" "}
                      {t(
                        "行，完整导入；下方仅预览 12 行",
                        "rows to import; 12 preview rows below",
                      )}
                    </p>
                    {preview.warnings.map((w) => (
                      <p className="warning" key={w}>
                        {w}
                      </p>
                    ))}
                    <DataTable
                      rows={preview.preview}
                      columns={Object.keys(preview.preview[0] || {})}
                      labels={preview.names}
                    />
                    <Button
                      disabled={busy || previewStale}
                      onClick={() =>
                        guarded(async () => {
                          const id = project?.id || (await create());
                          await api(`/projects/${id}/import`, {
                            upload_id: preview.id,
                            sheet,
                            header,
                            encoding,
                            delimiter,
                          });
                          await refresh(id);
                          setModal(null);
                          setProposals([]); setMessages([]); setAnalysis(""); setQuestions([]);
                        })
                      }
                    >
                      {t("确认导入", "Import snapshot")}
                    </Button>
                    {previewStale && (
                      <p className="warning">
                        {t(
                          "导入设置已改变，请重新解析预览。",
                          "Import settings changed. Parse and preview again.",
                        )}
                      </p>
                    )}
                  </>
                )}
                <hr />
                <h3>
                  {t(
                    "或粘贴表格（Tab 分隔）",
                    "Or paste a tab-separated table",
                  )}
                </h3>
                <textarea
                  value={paste}
                  onChange={(e) => setPaste(e.target.value)}
                  placeholder={t("地区\t销售额\n华东\t1200", "Region\tRevenue\nEast\t1200")}
                />
                <Button
                  variant="outline"
                  disabled={!paste || busy}
                  onClick={() =>
                    guarded(async () => {
                      const id = project?.id || (await create());
                      await api(`/projects/${id}/paste`, { text: paste });
                      await refresh(id);
                      setModal(null);
                    })
                  }
                >
                  {t("导入粘贴内容", "Import pasted data")}
                </Button>
              </>
            ) : modal === "advanced" ? (
              <>
                <p>
                  {t(
                    "字段使用稳定 ID。所有计划先校验再执行；不支持任意脚本。",
                    "Use stable field IDs. Plans are validated before execution; arbitrary scripts are disabled.",
                  )}
                </p>
                <textarea
                  className="code-editor"
                  aria-label="Advanced JSON"
                  value={editJson}
                  onChange={(e) => setEditJson(e.target.value)}
                />
                <Button
                  disabled={busy || working}
                  onClick={() =>
                    guarded(async () => {
                      await edit(
                        "更新分析配置 / Update plan",
                        JSON.parse(editJson),
                      );
                      setModal(null);
                    })
                  }
                >
                  {t("校验并执行", "Validate & run")}
                </Button>
              </>
            ) : (
              <>
                <p>
                  {t(
                    "连接由服务端环境配置；仅接受预先登记的数据源，不在浏览器保存密码。",
                    "Sources are configured on the server. No database passwords are stored in the browser.",
                  )}
                </p>
                {!Object.keys(sources).length && (
                  <p className="warning">
                    {t(
                      "尚未配置数据源。参见 README 中 DB_SOURCES_JSON 与 SQLITE_FILES_JSON。",
                      "No sources configured. See README for DB_SOURCES_JSON / SQLITE_FILES_JSON.",
                    )}
                  </p>
                )}
                <select
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                >
                  <option value="">
                    {t("选择已配置数据源", "Choose configured source")}
                  </option>
                  {Object.entries(sources).map(([id, s]) => (
                    <option key={id} value={id}>
                      {id} · {s.kind}
                    </option>
                  ))}
                </select>
                <Button
                  variant="outline"
                  disabled={!source}
                  onClick={() =>
                    guarded(async () =>
                      setDbResult(await api(`/database/${source}/browse`)),
                    )
                  }
                >
                  {t("测试连接与浏览字段", "Test & browse")}
                </Button>
                <textarea
                  aria-label="SQL query"
                  value={sql}
                  onChange={(e) => setSql(e.target.value)}
                />
                <div className="import-settings">
                  <label>
                    {t("所选表（规则预览）", "Selected table (rule preview)")}
                    <input
                      aria-label="SQL table"
                      value={sqlTable}
                      onChange={(e) => setSqlTable(e.target.value)}
                    />
                  </label>
                  <label>
                    {t("查询目标（模型模式）", "Query goal (model mode)")}
                    <input
                      aria-label="SQL goal"
                      value={sqlGoal}
                      onChange={(e) => setSqlGoal(e.target.value)}
                    />
                  </label>
                </div>
                <Button
                  variant="outline"
                  disabled={!source || busy}
                  onClick={() =>
                    guarded(async () => {
                      const draft = await api<{ sql: string; note: string }>(
                        `/database/${source}/draft`,
                        { mode, table: sqlTable, goal: sqlGoal },
                      );
                      setSql(draft.sql);
                      setDbResult({
                        draft: draft.note,
                        review: t(
                          "请检查上方 SQL，再手动预览或保存快照。",
                          "Review the SQL above before previewing or saving a snapshot.",
                        ),
                      });
                    })
                  }
                >
                  {t("生成 SQL 草稿（不执行）", "Draft SQL (no execution)")}
                </Button>
                <Button
                  disabled={!source}
                  onClick={() =>
                    guarded(async () =>
                      setDbResult(
                        await api(`/database/${source}/query`, { sql }),
                      ),
                    )
                  }
                >
                  {t("预览只读查询", "Preview read-only query")}
                </Button>
                <Button
                  variant="outline"
                  disabled={!source}
                  onClick={() =>
                    guarded(async () => {
                      const id = project?.id || (await create());
                      await api(`/database/${source}/query`, {
                        sql,
                        project_id: id,
                      });
                      await refresh(id);
                      setModal(null);
                    })
                  }
                >
                  {t("保存查询快照", "Save query snapshot")}
                </Button>
                {dbResult !== null && (
                  <pre>{JSON.stringify(dbResult, null, 2)}</pre>
                )}
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
function DataTable({
  rows,
  columns,
  labels,
}: {
  rows: Record<string, unknown>[];
  columns: string[];
  labels?: string[];
}) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {columns.map((c, i) => (
              <th key={c}>{labels?.[i] || c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 100).map((row, i) => (
            <tr key={i}>
              {columns.map((c) => (
                <td key={c}>{row[c] === null ? "∅" : String(row[c] ?? "")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > 100 && (
        <p>Preview: 100 / {rows.length} rows. Calculation uses all rows.</p>
      )}
    </div>
  );
}
