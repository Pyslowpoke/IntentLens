export type Field = {
  id: string;
  name: string;
  dtype: string;
  nulls: number;
  unique: number;
  meaning: string;
};
export type Dataset = {
  id: string;
  source: string;
  rows: number;
  fields: Field[];
  warnings: string[];
  profile: Record<string, unknown>;
};
export type Plan = {
  schema_version: string;
  goal: string;
  group_by: string[];
  metric: string | null;
  denominator: string | null;
  aggregation: string;
  filters: unknown[];
  time_grain: string;
  missing: string;
  sort: string;
  unit: string;
  limitations: string[];
};
export type Spec = {
  schema_version: string;
  kind: string;
  engine: string;
  title: string;
  color: string;
  theme: string;
  font: string;
  font_size: number;
  width: number;
  height: number;
  annotation: string;
  extensions: Record<string, unknown>;
};
export type Revision = {
  id: string;
  chart_id: string;
  parent_id: string | null;
  dataset_id: string;
  plan: Plan;
  spec: Spec;
  result: {
    records: Record<string, unknown>[];
    columns: string[];
    warnings: string[];
    analyzed_rows: number;
    input_rows: number;
    summary?: { groups: number; min: number; max: number };
    execution: {
      compute_ms: number;
      render_ms: number;
      compute_cache_hit: boolean;
      engine: string;
    };
  };
  summary: string;
  created_at: string;
  artifacts: Record<string, string>;
};
export type Run = {
  id: string;
  status: string;
  stage: string;
  error: string | null;
};
export type Project = {
  id: string;
  name: string;
  head: string | null;
  chart_id: string;
  dataset: Dataset | null;
  revision: Revision | null;
  history: Revision[];
  runs: Run[];
};
export type Proposal = {
  title: string;
  explanation: string;
  assumptions: string[];
  plan: Plan;
  spec: Spec;
};
export async function api<T>(path: string, body?: unknown): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 90000);
  try {
  const r = await fetch("/api" + path, {
    signal: controller.signal,
    method: body === undefined ? "GET" : "POST",
    headers:
      body instanceof FormData
        ? undefined
        : { "Content-Type": "application/json" },
    body:
      body === undefined
        ? undefined
        : body instanceof FormData
          ? body
          : JSON.stringify(body),
  });
  if (!r.ok) {
    const e = await r.json().catch(() => ({ detail: r.statusText }));
    throw Error(
      typeof e.detail === "string" ? e.detail : JSON.stringify(e.detail),
    );
  }
  return await r.json();
  } catch (error) {
    if (controller.signal.aborted) throw Error("请求超时，请刷新确认任务状态后重试 / Request timed out; refresh to check task status before retrying");
    if (error instanceof TypeError) throw Error("无法连接服务，请检查服务是否启动 / Cannot connect to the service");
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
export function formatNumber(value: number | undefined | null) {
  return value == null
    ? "—"
    : new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 2 }).format(
        value,
      );
}
