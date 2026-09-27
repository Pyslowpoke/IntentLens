from typing import Literal, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0"] = "1.0"


class DatasetField(Contract):
    id: str
    name: str
    dtype: Literal["string", "number", "date", "boolean"]
    meaning: str = ""
    nulls: int = 0
    unique: int = 0


class DatasetSnapshot(Contract):
    id: str
    source: str
    fields: list[DatasetField]
    rows: int
    checksum: str
    snapshot: str
    raw: str
    warnings: list[str] = []
    transforms: list[dict] = []
    profile: dict = {}


class Filter(Contract):
    field: str
    op: Literal["eq", "ne", "gt", "gte", "lt", "lte", "contains", "in"]
    value: Any


class AnalysisPlan(Contract):
    goal: str = ""
    group_by: list[str] = Field(default_factory=list, max_length=3)
    metric: str | None = None
    denominator: str | None = None
    aggregation: Literal["sum", "mean", "count", "min", "max", "ratio_total", "ratio_mean", "raw"] = "sum"
    filters: list[Filter] = []
    time_grain: Literal["none", "day", "week", "month", "year"] = "none"
    missing: Literal["error", "exclude", "keep"] = "error"
    duplicates: Literal["keep", "drop_exact"] = "keep"
    sort: Literal["none", "asc", "desc", "label"] = "none"
    unit: str = ""
    limitations: list[str] = []

    @model_validator(mode="after")
    def ratio_fields(self):
        if self.aggregation.startswith("ratio") and (not self.metric or not self.denominator):
            raise ValueError("Ratio requires numerator and denominator / 比例需要分子与分母")
        return self


class ChartSpec(Contract):
    kind: Literal["line", "bar", "scatter", "area", "histogram", "box", "heatmap", "violin", "facet", "linked", "sankey", "tree", "funnel", "density", "geo", "table"] = "bar"
    engine: Literal["auto", "plotly", "matplotlib", "altair", "echarts", "datashader", "geo", "plottable"] = "auto"
    title: str = "分析结果 / Analysis"
    color: str = Field(default="#256b88", pattern=r"^#[0-9a-fA-F]{6}$")
    theme: Literal["light", "dark", "report"] = "light"
    font: Literal["sans-serif", "Noto Sans CJK SC", "Microsoft YaHei"] = "sans-serif"
    font_size: int = Field(default=16, ge=8, le=40)
    width: int = Field(default=1000, ge=320, le=2400)
    height: int = Field(default=560, ge=240, le=1600)
    annotation: str = Field(default="", max_length=1000)
    mapping: dict[str,str] = {}
    extensions: dict = {}


class ChartRevision(Contract):
    id: str
    chart_id: str
    parent_id: str | None = None
    dataset_id: str
    plan: AnalysisPlan
    spec: ChartSpec
    code: str
    result: dict
    summary: str
    artifacts: dict[str, str] = {}
    created_at: str


class Run(Contract):
    id: str
    project_id: str
    chart_id: str
    dataset_id: str
    generation: int
    parent_id: str | None = None
    status: Literal["queued", "running", "completed", "failed", "cancelled", "stale"] = "queued"
    stage: str = "queued"
    error: str | None = None
    event_seq: int = 0
    created_at: str
    updated_at: str
    artifacts: dict = {}
