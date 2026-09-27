export const preferenceKey = "intentlens.preferences.v1";
export const engines = ["auto", "plotly", "matplotlib", "altair", "echarts", "datashader", "geo", "plottable"] as const;
export type Preferences = { language: "zh" | "en"; nickname: string; engine: string; theme: string };
export const defaults: Preferences = { language: "zh", nickname: "", engine: "auto", theme: "light" };
export function parsePreferences(raw: string | null): Preferences {
  try {
    const v = JSON.parse(raw || "{}");
    return { language: v.language === "en" ? "en" : "zh", nickname: typeof v.nickname === "string" ? v.nickname.trim().slice(0, 32) : "", engine: engines.includes(v.engine) ? v.engine : "auto", theme: ["light", "dark", "report"].includes(v.theme) ? v.theme : "light" };
  } catch { return { ...defaults }; }
}
export function preferredSpec<T extends {engine: string; theme: string; kind: string}>(spec: T, preferences: Preferences, capabilities: Record<string, {kinds: string[]}>, honorRecommendation = false) {
  if (honorRecommendation && spec.engine !== "auto") return {spec: {...spec}, fallback: false};
  const compatible = preferences.engine === "auto" || capabilities[preferences.engine]?.kinds.includes(spec.kind);
  return { spec: { ...spec, engine: compatible ? preferences.engine : "auto", theme: honorRecommendation ? spec.theme : preferences.theme }, fallback: !compatible };
}
