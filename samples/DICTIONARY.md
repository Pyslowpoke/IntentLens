# Synthetic data dictionary / 合成数据字典

All rows are generated with seed 20260927; no real personal, hospital or company data.

| Dataset | Fields | Scope |
|---|---|---|
| sales | order ID, order date, region, product, quantity, revenue (CNY) | 720 generated orders; date range Jan 1–Jun 16 2026; June is incomplete |
| product | date, platform, visitors, conversions | 270 synthetic records; overall conversion = sum(conversions)/sum(visitors), not average of ratios |
| hospital | synthetic hospital name, city, stage, longitude, latitude, visit count | WGS84 points; no target hospital population, so no penetration-rate claim |
| 中文多工作表.xlsx | instructions and sales sheets, header row 2 | dates, blank metric, missing formula cache; 4 data rows |
| 重复表头-gb18030.csv | region, amount, amount | GB18030; duplicate headers and invalid number |
| sample.sqlite | orders(id,region,amount) | East=400, West=200, total=600 |

No synthetic data is a business recommendation or representative statistic.
