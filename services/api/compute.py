import hashlib
import json
import pandas as pd
from .contracts import AnalysisPlan
from .ingest import records


def validate(plan: AnalysisPlan, dataset):
    fields = {f["id"]: f for f in dataset["fields"]}
    for id in [*plan.group_by, plan.metric, plan.denominator, *[f.field for f in plan.filters]]:
        if id and id not in fields:
            raise ValueError(f"Unknown field ID: {id}")
    if plan.aggregation not in ("count", "raw"):
        if not plan.metric or fields[plan.metric]["dtype"] != "number":
            raise ValueError("Choose a numeric metric / 请选择数字指标")
    if plan.denominator and fields[plan.denominator]["dtype"] != "number":
        raise ValueError("Denominator must be numeric")
    if plan.time_grain != "none" and (not plan.group_by or fields[plan.group_by[0]]["dtype"] != "date"):
        raise ValueError("Time grain requires a date as the first grouping field")


def cache_key(dataset, plan):
    schema=json.dumps(dataset["fields"],ensure_ascii=False,sort_keys=True)
    return hashlib.sha256((dataset["checksum"] + schema + plan.model_dump_json()).encode()).hexdigest()


def compute(df, plan: AnalysisPlan, dataset):
    validate(plan, dataset)
    df = df.copy()
    warnings = list(plan.limitations)
    input_rows = len(df)
    duplicate_rows_removed = 0
    if plan.duplicates == "drop_exact":
        duplicate_rows_removed = int(df.duplicated().sum())
        df = df.drop_duplicates()
        warnings.append(f"Explicit exact-row deduplication: removed {duplicate_rows_removed} rows / 按方案去除完全重复行")
    for f in plan.filters:
        s, v = df[f.field], f.value
        if pd.api.types.is_datetime64_any_dtype(s):
            v = pd.to_datetime(v)
        if f.op == "eq": mask = s == v
        elif f.op == "ne": mask = s != v
        elif f.op == "gt": mask = s > v
        elif f.op == "gte": mask = s >= v
        elif f.op == "lt": mask = s < v
        elif f.op == "lte": mask = s <= v
        elif f.op == "contains": mask = s.astype("string").str.contains(str(v), regex=False, na=False)
        else: mask = s.isin(v if isinstance(v, list) else [v])
        df = df[mask.fillna(False)]
    filtered_rows = len(df)
    selected = list(dict.fromkeys([*plan.group_by, *([plan.metric] if plan.metric else []), *([plan.denominator] if plan.denominator else [])]))
    missing = int(df[selected].isna().any(axis=1).sum()) if selected else 0
    if missing:
        if plan.missing == "error":
            raise ValueError(f"{missing} rows have missing analysis fields; explicitly choose exclude or keep / 请指定缺失值策略")
        if plan.missing == "exclude":
            df = df.dropna(subset=selected)
        warnings.append(f"Missing fields: {missing} rows; policy={plan.missing}. Null metrics are not imputed; aggregations ignore null metrics.")
    if df.empty:
        raise ValueError("No data after filters / 筛选后无数据，请调整条件")
    if plan.time_grain != "none":
        col = plan.group_by[0]
        dates = pd.to_datetime(df[col])
        if plan.time_grain == "month":
            warnings.append(f"Observed range {dates.min().date()}–{dates.max().date()}; edge months may be incomplete. Compare the same observed day window, not full months / 边界月份可能不完整，不代表整月环比")
        freq = {"day": "D", "week": "W", "month": "M", "year": "Y"}[plan.time_grain]
        df[col] = dates.dt.to_period(freq).astype(str)
    if plan.aggregation == "raw":
        out = df[selected or list(df.columns)].copy()
        if plan.metric:
            out = out.rename(columns={plan.metric: "value"})
    else:
        groups = plan.group_by
        if not groups:
            df["_all"] = "All / 全部"
            groups = ["_all"]
        g = df.groupby(groups, dropna=False, observed=True, sort=False)
        if plan.aggregation == "count":
            out = g.size().rename("value").reset_index()
        elif plan.aggregation in ("ratio_total", "ratio_mean"):
            if plan.aggregation == "ratio_total":
                sums = g[[plan.metric, plan.denominator]].sum(min_count=1)
                if (sums[plan.denominator] == 0).any():
                    raise ValueError("Zero group denominator / 分组分母为零")
                out = (sums[plan.metric] / sums[plan.denominator]).rename("value").reset_index()
                warnings.append("Overall ratio = sum(numerator) / sum(denominator); weighted by denominator / 总体比例")
            else:
                if (df[plan.denominator] == 0).any():
                    raise ValueError("Zero row denominator / 行分母为零")
                df["_ratio"] = df[plan.metric] / df[plan.denominator]
                out = df.groupby(groups, dropna=False, observed=True)["_ratio"].mean().rename("value").reset_index()
                warnings.append("Simple mean ratio = mean(each row numerator / denominator); equal row weight / 简单平均比例")
        else:
            series = g[plan.metric].sum(min_count=1) if plan.aggregation == "sum" else getattr(g[plan.metric], plan.aggregation)()
            out = series.rename("value").reset_index()
    if plan.sort in ("asc", "desc") and "value" in out:
        out = out.sort_values("value", ascending=plan.sort == "asc", kind="stable")
    elif plan.sort == "label":
        out = out.sort_values(out.columns[0], kind="stable")
    labels = {f["id"]: f["name"] for f in dataset["fields"]}
    labels.update(value=labels.get(plan.metric, "Count / 记录数") + (f" ({plan.unit})" if plan.unit else ""), _all="All / 全部")
    result = dict(records=records(out), columns=list(out.columns), labels=labels, input_rows=input_rows, filtered_rows=filtered_rows, analyzed_rows=len(df), duplicate_rows_removed=duplicate_rows_removed, warnings=warnings, value_format="percent" if plan.aggregation.startswith("ratio") else "number", unit=plan.unit)
    if "value" in out and plan.aggregation != "raw":
        result["summary"] = {"groups": len(out), "min": float(out.value.min()) if out.value.notna().any() else None, "max": float(out.value.max()) if out.value.notna().any() else None}
    return result
