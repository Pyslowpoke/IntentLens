"use client";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { defaults, engines, type Preferences } from "@/lib/preferences";

export function SettingsDialog({ open, value, onClose, onSave }: { open: boolean; value: Preferences; onClose: () => void; onSave: (value: Preferences) => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [draft, setDraft] = useState(value);
  const [error, setError] = useState("");
  const t = (zh: string, en: string) => draft.language === "zh" ? zh : en;
  useEffect(() => {
    if (open) { setDraft(value); setError(""); dialog.current?.showModal(); }
    else dialog.current?.close();
  }, [open, value]);
  const descriptions: Record<string, string> = {
    auto: t("根据图表类型自动匹配", "Match the chart type automatically"),
    plotly: t("交互图表 · 悬停、缩放", "Interactive charts · hover and zoom"),
    matplotlib: t("静态图表 · 适合报告", "Static charts · ready for reports"),
    altair: t("声明式图表 · 联动选择", "Declarative charts · linked selections"),
    echarts: t("交互图表 · 流向与层级", "Interactive charts · flows and hierarchies"),
    datashader: t("大规模散点密度图", "Large-scale point density"),
    geo: t("地理数据 · 经纬度点位", "Geographic coordinates and points"),
    plottable: t("排名与指标表格", "Rankings and metric tables"),
  };
  return <dialog ref={dialog} className="settings-dialog" aria-labelledby="settings-title" onCancel={onClose} onClick={e => { if (e.target === dialog.current) onClose(); }}>
    <form onSubmit={e => { e.preventDefault(); try { onSave({...draft, nickname: draft.nickname.trim()}); onClose(); } catch { setError(t("无法保存，请允许浏览器使用本地存储。", "Unable to save. Allow browser local storage.")); } }}>
      <div className="settings-heading"><div><span>INTENTLENS / PREFERENCES</span><h2 id="settings-title">{t("让工作台，更合你的习惯", "Make this workspace yours")}</h2></div><button type="button" onClick={onClose} aria-label={t("关闭设置", "Close settings")}>×</button></div>
      <p className="settings-intro">{t("偏好保存在当前浏览器。新分析使用你的默认配置，已有图表保持原样。", "Preferences stay in this browser. Defaults apply to new analyses; existing charts stay unchanged.")}</p>
      <label>{t("界面语言", "Interface language")}<select aria-label="Interface language" value={draft.language} onChange={e => setDraft({...draft, language: e.target.value as "zh" | "en"})}><option value="zh">简体中文</option><option value="en">English</option></select></label>
      <label>{t("你的昵称", "Your nickname")}<input aria-label="Nickname" maxLength={32} value={draft.nickname} placeholder={t("怎么称呼你？", "What should we call you?")} onChange={e => setDraft({...draft, nickname: e.target.value})} /><small>{t("最多 32 个字符，仅用于本机界面展示。", "Up to 32 characters, for local display only.")}</small></label>
      <fieldset><legend>{t("偏好的可视化工具", "Preferred visualization tool")}</legend><div className="engine-choices">{engines.map(engine => <label key={engine} className={draft.engine === engine ? "chosen" : ""}><input type="radio" name="preferred-engine" value={engine} checked={draft.engine === engine} onChange={() => setDraft({...draft, engine})} /><span><strong>{engine === "auto" ? t("智能匹配", "Automatic") : engine === "geo" ? "GeoPandas / pydeck" : engine === "matplotlib" ? "Matplotlib / Seaborn" : engine === "echarts" ? "ECharts" : engine.charAt(0).toUpperCase()+engine.slice(1)}</strong><small>{descriptions[engine]}</small></span></label>)}</div><p className="settings-intro">{t("不支持所选图表类型时会自动匹配兼容工具，并显示提示。", "If your preferred tool cannot render a chart type, a compatible tool is selected and a notice is shown.")}</p></fieldset>
      <label>{t("默认图表主题", "Default chart theme")}<select aria-label="Default chart theme" value={draft.theme} onChange={e => setDraft({...draft, theme:e.target.value})}><option value="light">{t("商务浅色", "Light")}</option><option value="dark">{t("深色", "Dark")}</option><option value="report">{t("简洁报告", "Report")}</option></select></label>
      {error && <p role="alert">{error}</p>}
      <div className="settings-actions"><Button type="button" variant="ghost" onClick={() => setDraft({...defaults})}>{t("恢复默认", "Reset defaults")}</Button><Button type="submit">{t("保存设置", "Save settings")}</Button></div>
    </form>
  </dialog>;
}
