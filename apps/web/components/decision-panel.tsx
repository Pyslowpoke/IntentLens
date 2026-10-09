"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

type Decision = {
  revision_id: string; provider: string; model: string; total_groups: number;
  advice: { summary: string; actions: { action: string; evidence_ids: number[]; rationale: string; risk: string; next_step: string }[]; limitations: string[]; questions: string[] };
  evidence: { id: number; values: Record<string, unknown> }[];
};
export function DecisionPanel({ projectId, revisionId, goal, language }: { projectId: string; revisionId: string; goal: string; language: "zh" | "en" }) {
  const t = (zh: string, en: string) => language === "zh" ? zh : en;
  const [decision, setDecision] = useState<Decision | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [consent, setConsent] = useState(false);
  useEffect(() => {
    let active = true;
    setDecision(null); setConsent(false); setError("");
    api<Decision | null>(`/projects/${projectId}/decision`).then(d => {
      if (active && d?.revision_id === revisionId) setDecision(d);
    }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [projectId, revisionId]);
  async function generate() {
    setBusy(true); setError("");
    try { setDecision(await api<Decision>(`/projects/${projectId}/decision`, { revision_id: revisionId, goal, language, allow_aggregate_send: consent })); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  }
  return <section className="panel decision-panel">
    <div className="section-heading"><h2>{t("AI 决策建议", "AI decision support")}</h2><Button disabled={busy || !consent} onClick={generate}>{busy ? t("正在分析依据…", "Reviewing evidence…") : decision ? t("重新生成建议", "Regenerate advice") : t("生成决策建议", "Generate advice")}</Button></div>
    <p className="privacy-note">{t("发送当前方案与最多 100 组聚合结果，不发送原始明细。建议由模型生成，证据编号经程序校验，推断需结合业务验证。", "Sends the current plan and up to 100 aggregate groups, not raw rows. Evidence references are checked; model interpretations still need business validation.")}</p>
    <label className="remote-consent"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} /> {t("我确认允许把本版本的聚合结果发送给所配置的模型服务。", "Allow this revision's aggregate results to be sent to the configured model service.")}</label>
    {error && <p role="alert" className="warning">{error}</p>}
    {decision && <>
      <small>{decision.provider} · {decision.model} · {t("版本", "Revision")} {revisionId.slice(0, 8)} · {t("依据", "Evidence")} {decision.evidence.length}/{decision.total_groups} {t("组", "groups")}</small>
      <p style={{ margin: "16px 0" }}>{decision.advice.summary}</p>
      {decision.advice.actions.map((a, i) => <article key={i} style={{ borderTop: "1px solid #e2e8f0", padding: "16px 0" }}>
        <h3>{i + 1}. {a.action}</h3><p>{t("依据：", "Rationale: ")}{a.rationale} ({t("证据", "Evidence")} {a.evidence_ids.join("、")})</p><p>{t("风险：", "Risk: ")}{a.risk}</p><p>{t("下一步：", "Next step: ")}{a.next_step}</p>
      </article>)}
      <div className="warning">{decision.advice.limitations.join("；")}</div>
      {decision.advice.questions.map((q, i) => <p key={i}>{t("待补充：", "Open question: ")}{q}</p>)}
      <details><summary>{t("查看实际计算证据", "Inspect computed evidence")}</summary><pre style={{ overflow: "auto", maxHeight: 300 }}>{JSON.stringify(decision.evidence, null, 2)}</pre></details>
    </>}
  </section>;
}
