"""Lazy engine adapters. All adapters consume the same computed records."""
import json
import textwrap
from pathlib import Path
from .contracts import ChartSpec

REGISTRY = {
    "plotly": {"kinds": ["line", "bar", "scatter", "area", "histogram", "box", "heatmap"], "formats": ["png", "svg", "pdf", "html"], "interaction": "hover, zoom", "limits": "SVG/PDF scatter may contain raster layers; maximum 20000 output marks"},
    "matplotlib": {"kinds": ["line", "bar", "scatter", "histogram", "box", "violin", "heatmap"], "formats": ["png", "svg", "pdf"], "interaction": "static", "limits": "Vector SVG/PDF; no hover"},
    "altair": {"kinds": ["line", "bar", "scatter", "area", "facet", "linked"], "formats": ["png", "svg", "pdf", "html"], "interaction": "interval brush, linked selection", "limits": "Vega-Lite; maximum 20000 output marks"},
    "echarts": {"kinds": ["bar", "line", "scatter", "sankey", "tree", "funnel"], "formats": ["html", "png"], "interaction": "hover, legend", "limits": "PNG uses backend Chromium; offline bundled ECharts"},
    "datashader": {"kinds": ["density"], "formats": ["png"], "interaction": "viewport recomputation", "limits": "Pixel counts, no per-point hover; PNG only"},
    "geo": {"kinds": ["geo"], "formats": ["html", "png"], "interaction": "pydeck point tooltips", "limits": "WGS84 EPSG:4326. No basemap or geocoding. PNG is a static GeoPandas view"},
    "plottable": {"kinds": ["table"], "formats": ["png", "svg", "pdf"], "interaction": "static", "limits": "Maximum 40 ranked rows; user must aggregate/filter first"},
}


def resolve(spec):
    if spec.engine != "auto":
        if spec.kind not in REGISTRY[spec.engine]["kinds"]:
            raise ValueError(f"{spec.engine} does not support {spec.kind}; choose a compatible engine / 引擎不兼容，不会静默降级")
        return spec.engine
    for engine, cap in REGISTRY.items():
        if spec.kind in cap["kinds"]:
            return engine
    raise ValueError("Unsupported chart")


def mpl_setup(spec):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt, font_manager
    plt.style.use("dark_background" if spec.theme == "dark" else "default")
    candidates = [spec.font, "Noto Sans CJK SC", "Microsoft YaHei", "Noto Sans SC", "SimHei", "DejaVu Sans"]
    installed = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams["font.sans-serif"] = [f for f in candidates if f in installed]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["font.size"] = spec.font_size
    return plt


def render(result, spec: ChartSpec, dest: Path, preview_only=False):
    import pandas as pd
    dest.mkdir(parents=True, exist_ok=True)
    engine = resolve(spec)
    df = pd.DataFrame(result["records"])
    if df.empty:
        raise ValueError("No chart records")
    if len(df) > 20000 and engine not in ("datashader", "geo"):
        raise ValueError("Over 20000 output marks; aggregate first or use density / 请先聚合或使用密度图")
    cols = result["columns"]
    x = spec.mapping.get("x",cols[0])
    y = spec.mapping.get("y","value" if "value" in cols else cols[-1])
    if x not in cols or y not in cols: raise ValueError("Chart mappings must refer to analysis result columns / 映射字段不在计算结果中")
    if x == y and len(cols) == 1:
        df["_index"] = range(len(df))
        x = "_index"
    labels = result.get("labels", {})
    artifacts = {}
    bg = "#171c2c" if spec.theme == "dark" else "#ffffff"
    fg = "#e7eaf2" if spec.theme == "dark" else "#24304a"
    percent = result.get("value_format")=="percent"
    horizontal_bar=spec.kind=="bar" and pd.api.types.is_numeric_dtype(df[x]) and not pd.api.types.is_numeric_dtype(df[y])
    long_labels=not pd.api.types.is_numeric_dtype(df[x]) and df[x].astype(str).str.len().max()>18
    if long_labels and engine in ("altair","echarts"):
        df[x]=df[x].map(lambda value:textwrap.fill(str(value),18))
    if engine == "plotly":
        import plotly.express as px
        options = dict(data_frame=df, x=x, y=y, title=spec.title, labels=labels, color_discrete_sequence=[spec.color])
        if spec.kind == "histogram":
            fig = px.histogram(df, x=y, title=spec.title, color_discrete_sequence=[spec.color])
        elif spec.kind == "heatmap":
            if len(cols) < 3: raise ValueError("Heatmap requires two groups and one numeric metric")
            fig = px.imshow(df.pivot(index=cols[0], columns=cols[1], values=y), color_continuous_scale="Blues", title=spec.title, aspect="auto")
        else:
            fig = getattr(px, spec.kind)(**options)
        fig.update_layout(width=spec.width, height=spec.height, paper_bgcolor=bg, plot_bgcolor=bg, font=dict(family="Microsoft YaHei, Noto Sans CJK SC, sans-serif", size=spec.font_size, color=fg), margin=dict(l=85,r=40,t=90,b=95), template="plotly_dark" if spec.theme == "dark" else "plotly_white")
        fig.update_layout(font_family=f"{spec.font}, Microsoft YaHei, Noto Sans CJK SC, sans-serif")
        fig.update_layout(title_x=0.04, hoverlabel=dict(bgcolor=bg,font_color=fg))
        fig.update_yaxes(gridcolor="#334155" if spec.theme=="dark" else "#edf1f5",zerolinecolor="#cbd5e1")
        if spec.kind=="bar":
            (fig.update_xaxes if horizontal_bar else fig.update_yaxes)(rangemode="tozero")
            if len(df)<=12:
                axis_name="x" if horizontal_bar else "y"
                fig.update_traces(texttemplate="%{"+axis_name+(":.1%}" if percent else ":,.3~g}"),textposition="outside",cliponaxis=False)
                fig.update_layout(uniformtext_minsize=max(10,spec.font_size-2),uniformtext_mode="hide")
        if percent: (fig.update_xaxes if horizontal_bar else fig.update_yaxes)(tickformat=".1%")
        if long_labels:
            fig.update_xaxes(tickmode="array",tickvals=df[x].tolist(),ticktext=[textwrap.fill(str(v),18).replace("\n","<br>") for v in df[x]],tickangle=0,automargin=True)
        if spec.theme=="report": fig.update_xaxes(showgrid=False); fig.update_yaxes(showgrid=False,showline=True)
        if spec.annotation:
            fig.add_annotation(text=spec.annotation.replace("<", "&lt;"), x=.5, y=1.08, xref="paper", yref="paper", showarrow=False)
        (dest / "plotly.json").write_text(fig.to_json(), encoding="utf-8")
        if not preview_only:
            configure_export_browser()
            import plotly.io as pio
            formats=["png","svg","pdf"]
            pio.write_images([fig]*3,[str(dest/f"chart.{fmt}") for fmt in formats],format=formats,width=spec.width,height=spec.height)
            artifacts.update({fmt:f"chart.{fmt}" for fmt in formats})
        fig.update_layout(width=None, autosize=True)
        fig.write_html(str(dest / "chart.html"), include_plotlyjs=True, full_html=True, config={"responsive":True})
        artifacts.update(html="chart.html", plotly="plotly.json")
    elif engine in ("matplotlib", "plottable", "geo"):
        plt = mpl_setup(spec)
        fig, ax = plt.subplots(figsize=(spec.width/100, spec.height/100), dpi=100)
        if engine == "plottable":
            from plottable import Table, ColumnDefinition
            if len(df) > 40: raise ValueError("Report table supports 40 rows; filter or aggregate explicitly")
            table = df.set_index(x)
            Table(table, ax=ax, column_definitions=[ColumnDefinition(x, title=labels.get(x,x)),ColumnDefinition(y, title=labels.get(y,y), formatter="{:.1%}" if percent else "{:.2f}", textprops={"ha":"right"})])
        elif engine == "geo":
            import geopandas as gpd
            import pydeck as pdk
            lon = spec.extensions.get("longitude", x)
            lat = spec.extensions.get("latitude", y)
            if lon not in df or lat not in df: raise ValueError("Choose longitude and latitude columns")
            if not df[lon].between(-180,180).all() or not df[lat].between(-90,90).all(): raise ValueError("Coordinates outside WGS84 bounds")
            gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[lon],df[lat]), crs="EPSG:4326")
            encoding = spec.extensions.get("color_field")
            ax.set(xlabel="Longitude / 经度", ylabel="Latitude / 纬度")
            rgb = [int(spec.color[i:i+2],16) for i in (1,3,5)]
            data = df.to_dict("records")
            if encoding:
                if encoding not in df: raise ValueError("Color field is not in the analysis result")
                import matplotlib as mpl
                if pd.api.types.is_numeric_dtype(df[encoding]):
                    norm=mpl.colors.Normalize(vmin=float(df[encoding].min()),vmax=float(df[encoding].max()))
                    for row in data: row["_color"]=[int(255*v) for v in mpl.colormaps['viridis'](norm(row[encoding]))[:3]]
                    gdf.plot(ax=ax,column=encoding,cmap='viridis',legend=True,markersize=30)
                else:
                    categories = {v:i for i,v in enumerate(df[encoding].unique())}
                    colors={value:[int(255*v) for v in mpl.colormaps['tab10'](i%10)[:3]] for value,i in categories.items()}
                    for row in data: row["_color"]=colors[row[encoding]]
                    for value in categories:
                        gdf[gdf[encoding]==value].plot(ax=ax,color=tuple(v/255 for v in colors[value]),label=str(value),markersize=30)
                    ax.legend()
            else: gdf.plot(ax=ax,color=spec.color,markersize=30)
            layer = pdk.Layer("ScatterplotLayer", data, get_position=[lon,lat], get_fill_color="_color" if encoding else rgb, get_radius=5000, radius_min_pixels=4, pickable=True)
            deck = pdk.Deck(layers=[layer], initial_view_state=pdk.ViewState(longitude=float(df[lon].mean()), latitude=float(df[lat].mean()), zoom=4), map_style=None, tooltip={"text": "\n".join(f"{c}: {{{c}}}" for c in cols)})
            deck.to_html(str(dest/"chart.html"), offline=True)
            artifacts["html"] = "chart.html"
        else:
            import seaborn as sns
            if spec.kind == "heatmap":
                if len(cols)<3: raise ValueError("Heatmap requires two groups")
                sns.heatmap(df.pivot(index=cols[0],columns=cols[1],values=y), ax=ax, cmap="Blues", annot=len(df)<60)
            elif spec.kind in ("box", "violin"):
                getattr(sns, spec.kind+"plot")(data=df,x=x,y=y,ax=ax,color=spec.color)
            elif spec.kind == "histogram": ax.hist(df[y].dropna(),color=spec.color)
            elif spec.kind == "bar":
                value_field,category_field=(x,y) if horizontal_bar else (y,x)
                numeric=pd.to_numeric(df[value_field],errors="coerce")
                if (df[value_field].notna() & numeric.isna()).any(): raise ValueError("Bar chart requires a numeric value axis / 柱状图的数值轴必须是数字")
                categories=["(missing) / 空值" if pd.isna(v) else str(v) for v in df[category_field]]
                values=numeric.to_numpy(dtype=float,na_value=float("nan"))
                bars=ax.barh(categories,values,color=spec.color,height=.62) if horizontal_bar else ax.bar(categories,values,color=spec.color,width=.62)
                if len(df)<=12:
                    values=["" if pd.isna(v) else (f"{v:.1%}" if percent else f"{v:,.0f}" if abs(v)>=1000 else f"{v:,.2f}".rstrip('0').rstrip('.')) for v in numeric]
                    ax.bar_label(bars,labels=values,padding=6,fontsize=max(10,spec.font_size-2),color=fg)
                    ax.margins(**({"x":.16} if horizontal_bar else {"y":.16}))
            elif spec.kind == "scatter": ax.scatter(df[x],df[y],color=spec.color)
            else: ax.plot(df[x],df[y],color=spec.color)
            ax.set(xlabel=labels.get(x,x),ylabel=labels.get(y,y))
            ax.spines[['top','right']].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_color('#94a3b8')
            ax.set_axisbelow(True)
            if spec.kind in ('bar','line','scatter'): ax.grid(axis='x' if horizontal_bar else 'y',color='#475569' if spec.theme=='dark' else '#e8edf2',linewidth=.7)
            ax.tick_params(axis="both",length=0,pad=8)
            ax.tick_params(axis="x", labelrotation=0 if spec.kind=='bar' and len(df)<=8 else 25)
            if spec.kind=='bar' and long_labels:
                ax.set_xticks(range(len(df)),[textwrap.fill('(missing)' if pd.isna(v) else str(v),14) for v in df[x]],rotation=0)
            if long_labels:
                ax.set_xticks(ax.get_xticks(),[textwrap.fill(label.get_text(),18) for label in ax.get_xticklabels()],rotation=0)
        ax.set_title(textwrap.fill(spec.title,max(20,int(spec.width/(spec.font_size+3)/1.1))), loc="left", fontsize=spec.font_size+3, fontweight="bold", pad=22, color=fg)
        if percent and engine!="plottable":
            from matplotlib.ticker import PercentFormatter
            (ax.xaxis if horizontal_bar else ax.yaxis).set_major_formatter(PercentFormatter(1))
        if spec.theme=="report":
            ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        annotation=textwrap.fill(spec.annotation,max(24,int(spec.width/max(spec.font_size-2,8)/1.05)))
        if annotation: fig.text(.5,.02,annotation,ha="center",fontsize=spec.font_size-2,color=fg)
        bottom=min(.3,max(.06,(annotation.count('\n')+1)*spec.font_size*1.5/spec.height+.03)) if annotation else .03
        fig.tight_layout(rect=(0,bottom,1,.98))
        for fmt in (["png"] if engine=="geo" or preview_only else ["png","svg","pdf"]):
            fig.savefig(dest/f"chart.{fmt}", dpi=100, facecolor=bg)
            artifacts[fmt] = f"chart.{fmt}"
        plt.close(fig)
    elif engine == "altair":
        import altair as alt
        import vl_convert as vlc
        alt.data_transformers.disable_max_rows()
        def encoding_axis(field, horizontal=False):
            numeric=pd.api.types.is_numeric_dtype(df[field])
            temporal=pd.api.types.is_datetime64_any_dtype(df[field])
            kind="quantitative" if numeric else "temporal" if temporal else "nominal"
            options=dict(title=labels.get(field,field),labelColor=fg,labelLimit=400)
            if numeric:
                options["format"]=".1%" if percent and field=="value" else "~s"
            elif not temporal:
                options.update(labelAngle=-20 if horizontal and not long_labels else 0,labelExpr="split(datum.label, '\\n')" if long_labels else "datum.label")
            return kind,alt.Axis(**options)
        xtype,xaxis=encoding_axis(x,True)
        ytype,yaxis=encoding_axis(y)
        base = alt.Chart(df).encode(x=alt.X(field=x,type=xtype,title=labels.get(x,x),sort=None,axis=xaxis), y=alt.Y(field=y,type=ytype,title=labels.get(y,y),sort=None,axis=yaxis),tooltip=cols)
        if spec.kind == "facet":
            if len(cols)<3: raise ValueError("Facet requires two group fields")
            chart = base.mark_bar(color=spec.color).properties(width=max(180,spec.width//3-50),height=spec.height-150).facet(column=cols[1])
        elif spec.kind == "linked":
            brush = alt.selection_interval()
            left = base.mark_point().encode(color=alt.condition(brush,alt.value(spec.color),alt.value("#d4d8e2"))).add_params(brush).properties(width=spec.width//2-80,height=spec.height-140)
            right = base.mark_bar(color=spec.color).transform_filter(brush).properties(width=spec.width//2-80,height=spec.height-140)
            chart = left | right
        else:
            mark = "point" if spec.kind=="scatter" else spec.kind
            chart = getattr(base,"mark_"+mark)(color=spec.color).properties(width=spec.width-150,height=spec.height-140)
        chart = chart.properties(title=alt.Title(spec.title,subtitle=[spec.annotation] if spec.annotation else [],anchor="start",offset=20)).configure(background=bg,font="Microsoft YaHei").configure_axis(labelColor=fg,titleColor=fg,labelFontSize=spec.font_size,titleFontSize=spec.font_size,grid=spec.theme!="report").configure_title(color=fg,fontSize=spec.font_size+4,subtitleColor=fg)
        obj = chart.to_dict(validate=True)
        (dest/"vega.json").write_text(json.dumps(obj,ensure_ascii=False),encoding="utf-8")
        if preview_only:
            chart.save(str(dest/"chart.html"),inline=True)
            return {"html": "chart.html"}
        import xml.etree.ElementTree as ET
        svg=vlc.vegalite_to_svg(obj)
        element=ET.fromstring(svg)
        old_width,old_height=element.get("width"),element.get("height")
        element.set("viewBox",f"0 0 {old_width} {old_height}")
        element.set("width",str(spec.width));element.set("height",str(spec.height))
        wrapper=ET.Element("{http://www.w3.org/2000/svg}svg",{"width":str(spec.width),"height":str(spec.height),"viewBox":f"0 0 {spec.width} {spec.height}"})
        ET.SubElement(wrapper,"{http://www.w3.org/2000/svg}rect",{"width":"100%","height":"100%","fill":bg})
        wrapper.append(element)
        svg=ET.tostring(wrapper,encoding="unicode")
        (dest/"chart.svg").write_text(svg,encoding="utf-8")
        (dest/"chart.png").write_bytes(vlc.svg_to_png(svg))
        (dest/"chart.pdf").write_bytes(vlc.svg_to_pdf(svg))
        artifacts.update(png="chart.png",svg="chart.svg",pdf="chart.pdf")
        chart.save(str(dest/"chart.html"),inline=True)
        artifacts["html"]="chart.html"
    elif engine == "echarts":
        from pyecharts import options as opts
        from pyecharts.charts import Bar, Line, Scatter, Sankey, Tree, Funnel
        init=opts.InitOpts(width=f"{spec.width}px",height=f"{spec.height}px",bg_color=bg)
        if spec.kind in ("sankey","funnel") and (df[y]<0).any(): raise ValueError("Flow/funnel values must be nonnegative / 桑基与漏斗数值不能为负")
        if percent:
            df[y]=df[y]*100
        if spec.kind == "sankey":
            if len(cols)<3: raise ValueError("Sankey needs source, target and value")
            nodes=list(dict.fromkeys(df[cols[0]].astype(str).tolist()+df[cols[1]].astype(str).tolist()))
            chart=Sankey(init_opts=init).add("",[{"name":v} for v in nodes],[{"source":str(r[cols[0]]),"target":str(r[cols[1]]),"value":r[y]} for r in df.to_dict("records")])
        elif spec.kind == "tree":
            chart=Tree(init_opts=init).add("",[{"name":spec.title,"children":[{"name":str(r[x]),"value":r[y]} for r in df.to_dict("records")]}])
        elif spec.kind == "funnel": chart=Funnel(init_opts=init).add("",list(zip(df[x].astype(str),df[y])))
        else:
            cls={"bar":Bar,"line":Line,"scatter":Scatter}[spec.kind]
            chart=cls(init_opts=init).add_xaxis(df[x].astype(str).tolist()).add_yaxis(labels.get(y,y),df[y].tolist(),color=spec.color)
        chart.set_global_opts(title_opts=opts.TitleOpts(title=spec.title,subtitle=spec.annotation,pos_top="3%",pos_left="6%",title_textstyle_opts=opts.TextStyleOpts(color=fg,font_size=spec.font_size+4)),legend_opts=opts.LegendOpts(pos_top="14%",textstyle_opts=opts.TextStyleOpts(color=fg)),xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=0 if long_labels else 20,color=fg)), yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color=fg,formatter="{value}%" if percent else None)),toolbox_opts=opts.ToolboxOpts(is_show=False))
        if spec.kind not in ("sankey","tree","funnel"):
            chart.options["grid"]={"left":"9%","right":"6%","top":"24%","bottom":"15%","containLabel":True}
        if percent:
            chart.set_series_opts(label_opts=opts.LabelOpts(formatter="{c}%"))
        if spec.kind in ("sankey","tree","funnel"):
            for series in chart.options["series"]: series.update(top="24%",bottom="10%")
        # Render options only; never accept model JavaScript or callbacks.
        options=chart.dump_options_with_quotes()
        script=Path(__file__).resolve().parents[2]/"apps/web/public/echarts.min.js"
        if not script.exists(): raise ValueError("Run pnpm install and pnpm --dir apps/web prepare-assets to bundle ECharts")
        js=script.read_text(encoding="utf-8")
        safe_options=options.replace("</", "<\\/")
        html=f'<html><meta charset="utf-8"><body style="margin:0"><div id="chart" style="width:100vw;height:100vh"></div><script>{js}</script><script>const chart=echarts.init(document.getElementById("chart"));chart.setOption({safe_options});window.addEventListener("resize",()=>chart.resize());</script></body></html>'
        (dest/"chart.html").write_text(html,encoding="utf-8")
        if preview_only:
            return {"html": "chart.html"}
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            page=browser.new_page(viewport={"width":spec.width,"height":spec.height},device_scale_factor=1)
            page.goto((dest/"chart.html").resolve().as_uri())
            page.wait_for_function("document.querySelector('canvas') !== null")
            page.wait_for_timeout(1200)
            page.screenshot(path=str(dest/"chart.png"))
            browser.close()
        artifacts.update(html="chart.html",png="chart.png")
    elif engine == "datashader":
        import datashader as ds
        import datashader.transfer_functions as tf
        if x==y: raise ValueError("Density requires two numeric fields")
        ranges=spec.extensions.get("viewport",{})
        canvas=ds.Canvas(plot_width=spec.width-140,plot_height=spec.height-140,x_range=ranges.get("x"),y_range=ranges.get("y"))
        agg=canvas.points(df,x,y)
        img=tf.shade(agg,cmap=["#eff3ff",spec.color],how="log")
        plt=mpl_setup(spec)
        fig,ax=plt.subplots(figsize=(spec.width/100,spec.height/100),dpi=100)
        xr=ranges.get("x") or [float(df[x].min()),float(df[x].max())]
        yr=ranges.get("y") or [float(df[y].min()),float(df[y].max())]
        ax.imshow(tf.set_background(img,bg).to_pil(),extent=[*xr,*yr],aspect="auto",origin="upper")
        ax.set(title=spec.title,xlabel=labels.get(x,x),ylabel=labels.get(y,y))
        fig.text(.5,.02,f"Count per pixel · log color · max {int(agg.max())} · no per-point hover",ha="center",fontsize=10)
        fig.tight_layout(rect=(0,.06,1,.98));fig.savefig(dest/"chart.png",dpi=100,facecolor=bg);plt.close(fig)
        artifacts["png"]="chart.png"
        (dest/"density.json").write_text(json.dumps({"meaning":"count per pixel; logarithmic color; no per-point hover","viewport":ranges,"points_in_view":int(agg.sum()),"max_count":int(agg.max())}),encoding="utf-8")
    (dest/"engine.json").write_text(json.dumps({"engine":engine,"capabilities":REGISTRY[engine]}),encoding="utf-8")
    return artifacts


def configure_export_browser():
    """Playwright uses chrome-headless-shell.exe on Windows, a different layout."""
    import os
    if os.getenv("BROWSER_PATH") and Path(os.environ["BROWSER_PATH"]).is_file():
        return
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser_path = Path(p.chromium.executable_path)
        cache = browser_path.parents[2]
        candidates = [s for s in cache.glob("chromium_headless_shell-*/**/chrome-headless-shell*") if s.is_file() and (s.suffix == ".exe" or s.name == "chrome-headless-shell")]
        executable = next(iter(sorted(candidates, reverse=True)), browser_path)
        if not executable.is_file():
            raise ValueError("图片导出需要浏览器，请运行 .venv/Scripts/python.exe -m playwright install chromium；交互图仍可使用 / Export browser is missing; interactive chart remains available")
        os.environ["BROWSER_PATH"] = str(executable)
