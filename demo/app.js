// A standalone rule-based sample, independent of the API and worker.
const messages = {
  zh: {
    eyebrow:'无需安装 · 无需密钥 · 浏览器内计算',headline:'先确认口径，再看见答案。',intro:'用一份合成销售数据，体验从业务问题到可追溯图表的完整过程。',notice:'这是规则模式互动体验，不调用 AI。完整版本支持 Excel/CSV 导入、自然语言多轮讨论和图表版本回溯。',
    step1:'01 / 选择样例',dataTitle:'季度销售与转化',dataDescription:'固定合成数据：4 个地区、3 个月。金额单位为元；访问次数与成交数用于演示比例口径。',rows:'条记录',regions:'个地区',missing:'个缺失值',viewData:'查看原始样例',step2:'02 / 确认分析口径',questionTitle:'你想了解什么？',questionLabel:'选择一个业务问题',salesQuestion:'各地区销售额是多少？',conversionQuestion:'各地区转化率是多少？',planTitle:'执行前的分析方案',ratioLabel:'比例计算方式',totalRatio:'总体：成交数之和 ÷ 访问次数之和',meanRatio:'简单平均：各月转化率的平均值',validation:'校验：字段存在 · 数值有效 · 分母非零 · 无缺失值。保留全部记录，不抽样。',generate:'确认口径，生成图表 →',fullVersion:'想分析自己的表格或自由输入问题？使用完整本地工作台。',install:'查看完整版本安装步骤 ↗',step3:'03 / 查看、调整与下载',resultTitle:'分析结果',emptyTitle:'你的第一张图，从明确口径开始',emptyDescription:'在左侧选择问题，确认分析方案后生成。所有数字都由这 12 条样例记录计算。',chartTitle:'图表标题',sortLabel:'数值排序',descending:'从高到低',ascending:'从低到高',colorLabel:'图表颜色',purple:'紫色',blue:'蓝色',apply:'应用修改',undo:'撤销修改',downloadSvg:'下载图表 SVG',downloadCsv:'下载计算结果 CSV',reproduce:'下载可复现 JSON',computedData:'查看计算明细',feature1:'数字来自数据',feature1text:'每个柱形都能回到原始记录和聚合规则。没有预填结果，也没有编造指标。',feature2:'口径由你确认',feature2text:'总体转化率与简单平均可能不同。切换计算方式，直接观察差异。',feature3:'结果可以带走',feature3text:'下载图表、结果或包含样例与方案的 JSON。完整工作台还支持更多引擎和历史版本。',footer:'样例数据仅用于演示。计算在当前浏览器完成，不上传数据。',star:'有帮助？在 GitHub 收藏项目 ⭐',waiting:'等待确认',ready:'已生成 · 规则模式',salesTitle:'各地区季度销售额',conversionTitle:'各地区转化率',salesPlan:'按地区分组；销售额求和；按数值降序。金额单位：元。',totalPlan:'按地区分组；成交数求和 ÷ 访问次数求和；分母加权。',meanPlan:'按地区分组；先计算各月成交数 ÷ 访问次数，再等权平均。',calculated:'已计算 12 条记录 · 未抽样 · ',salesDefinition:'销售额 = 各月销售额之和',totalDefinition:'总体转化率 = Σ成交数 / Σ访问次数',meanDefinition:'简单平均转化率 = mean(各月成交数 / 访问次数)',edited:'修改已应用，计算口径保持不变。',undone:'已恢复上一个图表样式。',downloaded:'下载已开始。',region:'地区',value:'计算值',month:'月份',sales:'销售额',visits:'访问次数',orders:'成交数',unit:'元',regionsList:['华东','华北','华南','西部']
  },
  en: {
    eyebrow:'NO INSTALLATION · NO API KEY · IN-BROWSER COMPUTATION',headline:'Define the metric. See the answer.',intro:'Explore the journey from a business question to a traceable chart with a synthetic sales dataset.',notice:'This interactive sample uses rules, not AI. The full workbench supports Excel/CSV imports, natural-language discussion and chart revision history.',
    step1:'01 / EXPLORE THE SAMPLE',dataTitle:'Quarterly sales & conversion',dataDescription:'Synthetic data: four regions, three months. Sales are in CNY; visits and orders demonstrate ratio definitions.',rows:'records',regions:'regions',missing:'missing values',viewData:'View source records',step2:'02 / CONFIRM THE DEFINITION',questionTitle:'What would you like to know?',questionLabel:'Choose a business question',salesQuestion:'What are total sales by region?',conversionQuestion:'What is conversion by region?',planTitle:'Plan before execution',ratioLabel:'Ratio definition',totalRatio:'Overall: sum(orders) / sum(visits)',meanRatio:'Simple mean: average monthly conversion',validation:'Validated: fields exist, numbers are valid, denominators are nonzero, no missing values. All records retained; no sampling.',generate:'Confirm & generate chart →',fullVersion:'Want to use your own spreadsheet or ask an open-ended question? Run the full local workbench.',install:'Install the full version ↗',step3:'03 / EXPLORE, REFINE & DOWNLOAD',resultTitle:'Analysis result',emptyTitle:'A useful chart starts with a clear definition',emptyDescription:'Choose a question and confirm the plan. Every number is computed from these 12 sample records.',chartTitle:'Chart title',sortLabel:'Value order',descending:'Highest first',ascending:'Lowest first',colorLabel:'Chart color',purple:'Purple',blue:'Blue',apply:'Apply changes',undo:'Undo changes',downloadSvg:'Download SVG chart',downloadCsv:'Download result CSV',reproduce:'Download reproducible JSON',computedData:'View computed values',feature1:'Numbers from data',feature1text:'Trace every bar to source records and aggregation rules. No hard-coded answers or invented metrics.',feature2:'Definitions you approve',feature2text:'Overall conversion and a simple average can differ. Switch definitions to explore the difference.',feature3:'Results you can keep',feature3text:'Download the chart, computed data or a JSON bundle containing the sample and plan. The full workbench adds more engines and revision history.',footer:'Synthetic demonstration only. Computation stays in your browser; no data is uploaded.',star:'Useful? Star the project on GitHub ⭐',waiting:'Awaiting confirmation',ready:'Generated · rule mode',salesTitle:'Quarterly sales by region',conversionTitle:'Conversion by region',salesPlan:'Group by region; sum sales; sort descending. Unit: CNY.',totalPlan:'Group by region; sum orders / sum visits; weighted by denominator.',meanPlan:'Group by region; calculate orders / visits for each month, then average with equal weights.',calculated:'12 records computed · No sampling · ',salesDefinition:'Sales = sum of monthly sales',totalDefinition:'Overall conversion = Σorders / Σvisits',meanDefinition:'Simple mean conversion = mean(monthly orders / visits)',edited:'Style changes applied. The calculation definition is unchanged.',undone:'Previous chart style restored.',downloaded:'Download started.',region:'Region',value:'Computed value',month:'Month',sales:'Sales',visits:'Visits',orders:'Orders',unit:'CNY',regionsList:['East','North','South','West']
  }
};
const source = [
  [0,'2026-01',12000,1000,100],[0,'2026-02',18000,3000,150],[0,'2026-03',15000,2000,200],
  [1,'2026-01',9000,800,80],[1,'2026-02',11000,1200,180],[1,'2026-03',13000,2000,140],
  [2,'2026-01',17000,1500,120],[2,'2026-02',21000,2500,300],[2,'2026-03',19000,1000,150],
  [3,'2026-01',6000,400,40],[3,'2026-02',8000,800,40],[3,'2026-03',7000,1200,180]
].map(([region,month,sales,visits,orders])=>({region,month,sales,visits,orders}));
const $ = id=>document.getElementById(id);
let language = new URLSearchParams(location.search).get('lang') === 'en' ? 'en' : 'zh';
let state = null;
const history = [];
const m = ()=>messages[language];
function compute(metric, ratio) {
  return [0,1,2,3].map(region=>{
    const records=source.filter(row=>row.region===region);
    const sum=key=>records.reduce((total,row)=>total+row[key],0);
    if (records.some(row=>row.visits<=0 || !Number.isFinite(row.sales))) throw Error('Invalid sample data');
    const value=metric==='sales' ? sum('sales') : ratio==='total' ? sum('orders')/sum('visits') : records.reduce((total,row)=>total+row.orders/row.visits,0)/records.length;
    return {region,value};
  });
}
function escapeXml(value) {return String(value).replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[char]));}
function format(value) {return state?.metric==='conversion' ? (value*100).toFixed(2)+'%' : value.toLocaleString(language==='zh'?'zh-CN':'en-US');}
function plan() {
  const conversion=$('question').value==='conversion';
  $('ratio').hidden=$('ratioLabel').hidden=!conversion;
  $('plan').textContent=!conversion?m().salesPlan:$('ratio').value==='total'?m().totalPlan:m().meanPlan;
}
function table(id, headings, rows) {
  const target=$(id); target.replaceChildren();
  const header=document.createElement('tr');
  headings.forEach(text=>{const cell=document.createElement('th');cell.scope='col';cell.textContent=text;header.append(cell);});target.append(header);
  rows.forEach(row=>{const tr=document.createElement('tr');row.forEach(text=>{const cell=document.createElement('td');cell.textContent=text;tr.append(cell);});target.append(tr);});
}
function sortedResults() {return compute(state.metric,state.ratio).sort((a,b)=>state.sort==='asc'?a.value-b.value:b.value-a.value);}
function draw() {
  if(!state) return;
  const rows=sortedResults(), max=Math.max(...rows.map(row=>row.value)), e=escapeXml;
  const lines=rows.map((row,index)=>{
    const y=100+index*62,w=row.value/max*400;
    return `<text x="24" y="${y+22}" fill="#746e86" font-size="14">${e(m().regionsList[row.region])}</text><rect x="100" y="${y}" width="${w}" height="34" rx="5" fill="${state.color}"><title>${e(m().regionsList[row.region]+': '+format(row.value))}</title></rect><text x="${110+w}" y="${y+22}" fill="#27233b" font-size="14">${e(format(row.value))}</text>`;
  }).join('');
  $('chart').innerHTML=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 380" aria-labelledby="chart-title chart-description"><title id="chart-title">${e(state.title)}</title><desc id="chart-description">${e(rows.map(row=>m().regionsList[row.region]+': '+format(row.value)).join('; '))}</desc><rect width="660" height="380" rx="12" fill="#faf9fd"/><g font-family="Segoe UI, Microsoft YaHei, sans-serif"><text x="24" y="40" font-size="20" font-weight="600" fill="#27233b">${e(state.title)}</text><text x="24" y="65" font-size="11" fill="#746e86">${e(state.metric==='sales'?m().unit:state.ratio==='total'?m().totalRatio:m().meanRatio)}</text>${lines}<text x="24" y="362" fill="#746e86" font-size="10">IntentLens · Synthetic sample · 12 records</text></g></svg>`;
  $('chart').setAttribute('aria-label',state.title);
  $('calculation').textContent=m().calculated+(state.metric==='sales'?m().salesDefinition:state.ratio==='total'?m().totalDefinition:m().meanDefinition);
  table('computed',[m().region,m().value],rows.map(row=>[m().regionsList[row.region],format(row.value)]));
  $('title').value=state.title;$('sort').value=state.sort;$('color').value=state.color;
  $('output').hidden=false;$('empty').hidden=true;$('status').textContent=m().ready;$('undo').disabled=!history.length;
}
function translate() {
  document.documentElement.lang=language==='zh'?'zh-CN':'en';
  document.querySelectorAll('[data-i]').forEach(element=>element.textContent=m()[element.dataset.i]);
  $('language').textContent=language==='zh'?'English':'中文';
  $('status').textContent=state?m().ready:m().waiting;
  table('source',[m().region,m().month,m().sales,m().visits,m().orders],source.map(row=>[m().regionsList[row.region],row.month,row.sales,row.visits,row.orders]));
  plan();draw();
}
$('question').addEventListener('change',plan);$('ratio').addEventListener('change',plan);
$('generate').addEventListener('click',()=>{
  state={metric:$('question').value,ratio:$('ratio').value,title:$('question').value==='sales'?m().salesTitle:m().conversionTitle,sort:'desc',color:'#7463d7'};
  history.length=0;$('feedback').textContent='';draw();
});
$('apply').addEventListener('click',()=>{
  const title=$('title').value.trim(); if(!title){$('title').focus();return;}
  history.push({...state});state={...state,title,sort:$('sort').value,color:$('color').value};draw();$('feedback').textContent=m().edited;
});
$('undo').addEventListener('click',()=>{if(history.length){state=history.pop();draw();$('feedback').textContent=m().undone;}});
$('language').addEventListener('click',()=>{
  const old=m();language=language==='zh'?'en':'zh';
  if(state){if(state.title===old.salesTitle)state.title=m().salesTitle;else if(state.title===old.conversionTitle)state.title=m().conversionTitle;}
  history.length=0;$('feedback').textContent='';translate();
});
function download(name,type,contents){
  const url=URL.createObjectURL(new Blob([contents],{type}));const link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);$('feedback').textContent=m().downloaded;
}
$('svg').addEventListener('click',()=>download('intentlens-sample.svg','image/svg+xml;charset=utf-8',new XMLSerializer().serializeToString($('chart').firstElementChild)));
$('csv').addEventListener('click',()=>download('intentlens-result.csv','text/csv;charset=utf-8','\uFEFFregion,value\n'+sortedResults().map(row=>m().regionsList[row.region]+','+row.value).join('\n')));
$('reproduce').addEventListener('click',()=>download('intentlens-reproduce.json','application/json',JSON.stringify({version:1,mode:'rule',synthetic:true,regionLabels:messages.en.regionsList,source,plan:{groupBy:'region',metric:state.metric,aggregation:state.metric==='sales'?'sum':state.ratio==='total'?'ratio_total':'ratio_mean',missing:'error',sort:state.sort},chart:{title:state.title,color:state.color},result:sortedResults()},null,2)));
translate();
