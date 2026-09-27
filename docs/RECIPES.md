# Engine recipes / 专项配置示例

Import the indicated synthetic dataset, run a basic plan, then use **Edit plan & chart JSON**. Replace only the following plan/spec fields; retain the remaining validated defaults. The calculation result is shared by all compatible engines.

| Path | Dataset | Plan fields | Chart fields |
|---|---|---|---|
| Density | sales | `group_by:["f5"], metric:"f6", aggregation:"raw", missing:"exclude"` | `kind:"density",engine:"datashader"`; viewport inputs are x=quantity, y=revenue |
| Geo | hospital | `group_by:["f4","f3"],metric:"f5",aggregation:"raw",missing:"exclude"` | `kind:"geo",engine:"geo",extensions:{"longitude":"f4","latitude":"value","color_field":"f3"}` |
| KPI table | sales | `group_by:["f3"],metric:"f6",aggregation:"sum",sort:"desc"` | `kind:"table",engine:"plottable"` |
| Facet | sales | `group_by:["f3","f4"],metric:"f6",aggregation:"sum"` | `kind:"facet",engine:"altair"` |
| Linked view | sales | same region/product grouping as facet | `kind:"linked",engine:"altair"`; drag a brush in the left view to filter the right |
| Sankey | sales | same region/product grouping as facet | `kind:"sankey",engine:"echarts"`; first group=source, second=target, value=flow |
| Funnel/tree | sales | `group_by:["f3"],metric:"f6",aggregation:"sum"` | `kind:"funnel"` or `"tree"`, `engine:"echarts"` |
| Distribution | sales | `group_by:["f3"],metric:"f6",aggregation:"raw"` | histogram/box/violin, compatible engine |
| Overall conversion | product | `group_by:["f2"],metric:"f4",denominator:"f3",aggregation:"ratio_total",unit:"%"` | bar, Plotly |
| Simple average conversion | product | same fields, `aggregation:"ratio_mean"` | bar, Plotly; equal weight per row, not per visitor |

Datashader exports counts per pixel with logarithmic color. Viewport bounds recompute the aggregate from the whole result, never a prefix sample. The point map uses WGS84 and deliberately has no network basemap; PNG is the static GeoPandas equivalent, not a screenshot of a paid map provider. Numeric `color_field` produces a continuous viridis encoding; categorical values use an explicit shared palette.

Some engines change interaction when switching (e.g. Matplotlib is static). The capability registry explains this difference. Unavailable kinds fail explicitly instead of changing the chart silently.
