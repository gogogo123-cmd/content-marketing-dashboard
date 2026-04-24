#!/usr/bin/env python3
"""Generate the full dashboard HTML with embedded CSV."""
import os, csv

CSV_PATH = os.path.expanduser('~/Downloads/小说_bi实时分计划_自定义聚合数据表1776151765606.csv')
JUXING_PATH = os.path.expanduser('~/Downloads/聚星_助推详情_自定义聚合数据表1776158206942.csv')
CSV_PREV_PATH = os.path.expanduser('~/Downloads/小说_bi实时分计划_自定义聚合数据表1776167665040.csv')
JUXING_PREV_PATH = os.path.expanduser('~/Downloads/聚星_助推详情_自定义聚合数据表1776167577275.csv')
OUT_PATH = os.path.expanduser('~/Downloads/投放数据看板.html')

# 读取主数据列头
with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
    main_hdr = list(csv.reader(f))[0]

# 聚星 → 主数据 字段映射（主数据列名 → 聚星列名）
JX_MAP = {
    '消耗':              '当天消耗金额',
    '曝光数':            '报表今日曝光数',
    '关键行为数':        '报表今日行为数',
    '激活数':            '激活数',
    '激励视频cpm':       '激励视频cpm',
    '人均激励视频数':     '人均激励视频数',
    '激活成本':          '激活成本',
    '修复真实1日roi_规则赔付': '助推的预估roi',
    '预估ltv':             '预估ltv',
}

def merge_juxing(main_csv_path, juxing_csv_path):
    """读取主数据+聚星数据，合并为统一CSV字符串"""
    with open(main_csv_path, 'r', encoding='utf-8-sig') as f:
        main_raw = f.read()
    with open(juxing_csv_path, 'r', encoding='utf-8-sig') as f:
        jx = list(csv.reader(f))
    jx_hdr = jx[0]
    jx_idx = {h: i for i, h in enumerate(jx_hdr)}
    # 同名列直接映射
    jx_map = dict(JX_MAP)
    for col in main_hdr:
        if col in jx_idx and col not in jx_map:
            jx_map[col] = col
    juxing_rows = []
    for row in jx[1:]:
        new_row = [''] * len(main_hdr)
        for col, jx_col in jx_map.items():
            if jx_col in jx_idx:
                new_row[main_hdr.index(col)] = row[jx_idx[jx_col]]
        new_row[main_hdr.index('投放渠道')] = '聚星'
        new_row[main_hdr.index('运营负责人')] = '韩孟伶'
        juxing_rows.append(new_row)
    combined = main_raw.rstrip('\n') + '\n'
    for r in juxing_rows:
        combined += ','.join(r) + '\n'
    return combined

combined_csv = merge_juxing(CSV_PATH, JUXING_PATH)
combined_prev = merge_juxing(CSV_PREV_PATH, JUXING_PREV_PATH)

def esc(s):
    return s.replace(chr(92), chr(92)+chr(92)).replace('`', chr(92)+'`').replace('${', chr(92)+'${')

csv_escaped = esc(combined_csv)
csv_prev_escaped = esc(combined_prev)


HTML_BEFORE = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>内容营销数据看板 (4/3 - 4/9)</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"><\/script>
<style>
:root{--bg:#f5f6fa;--card:#fff;--text:#222;--text2:#666;--border:#e2e5ec;--accent:#4361ee;--accent2:#3a0ca3;--green:#2ec4b6;--red:#e63946;--orange:#f77f00;--purple:#7209b7}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);line-height:1.6}
.container{max-width:1400px;margin:0 auto;padding:20px}
h1{text-align:center;font-size:24px;margin-bottom:6px;color:var(--accent2)}
.subtitle{text-align:center;color:var(--text2);font-size:14px;margin-bottom:24px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:28px}
.card{background:var(--card);border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.06);border:1px solid var(--border)}
.card .label{font-size:12px;color:var(--text2);margin-bottom:4px}
.card .value{font-size:24px;font-weight:700;color:var(--accent)}
.card .value.green{color:var(--green)}
.card .value.orange{color:var(--orange)}
.section{background:var(--card);border-radius:12px;padding:24px;margin-bottom:24px;box-shadow:0 2px 8px rgba(0,0,0,.06);border:1px solid var(--border)}
.section h2{font-size:18px;margin-bottom:16px;color:var(--accent2);border-left:4px solid var(--accent);padding-left:12px}
.section h3{font-size:15px;margin:16px 0 10px;color:var(--text)}
table{width:100%;border-collapse:collapse;font-size:13px;margin-bottom:16px}
th,td{padding:6px 8px;font-size:12px;text-align:right;border-bottom:1px solid var(--border);white-space:nowrap}
th{background:#f0f2f8;color:var(--text2);font-weight:600;position:sticky;top:0;z-index:1}
td:first-child,th:first-child{text-align:left;font-weight:600}
td:nth-child(2),th:nth-child(2){text-align:right}
tr:hover td{background:#f8f9fd}
.table-wrap{margin-bottom:16px;overflow-x:auto;max-width:100%}
.chart-row{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:16px}
.chart-box{position:relative;height:320px}
.person-grid{display:grid;grid-template-columns:1fr;gap:16px}
@media(max-width:900px){.chart-row,.person-grid{grid-template-columns:1fr}}
.loading{text-align:center;padding:60px;font-size:18px;color:var(--text2)}
.totals td{font-weight:700;background:#f0f2f8}
.zero-row td{background:#fff5f5;color:#e63946;font-weight:600}
.tab-bar{display:flex;gap:6px;margin-bottom:20px;flex-wrap:wrap}
.tab-btn{padding:8px 20px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;border:2px solid var(--border);background:var(--card);color:var(--text2);transition:all .2s}
.tab-btn:hover{border-color:var(--accent2);color:var(--accent2)}
.tab-btn.active{background:var(--accent2);color:#fff;border-color:var(--accent2)}
.tab-btn.sub{padding:6px 16px;font-size:13px;border-radius:20px}
.tab-btn.sub:hover{border-color:var(--accent);color:var(--accent)}
.tab-btn.sub.active{background:var(--accent);border-color:var(--accent)}
.tab-row{margin-bottom:16px}
.tab-label{font-size:12px;color:var(--text2);margin-bottom:6px;font-weight:600}
.person-card{background:var(--card);border-radius:12px;padding:20px;border:1px solid var(--border);box-shadow:0 2px 8px rgba(0,0,0,.04);overflow-x:auto}
.person-card h3{margin-top:0}
.mini-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px}
.mini-stat{text-align:center;padding:8px;background:#f8f9fd;border-radius:8px}
.mini-stat .ms-label{font-size:11px;color:var(--text2)}
.mini-stat .ms-val{font-size:16px;font-weight:700;color:var(--accent)}
.tpl-desc{text-align:center;font-size:13px;color:var(--text2);margin-bottom:20px}
.type-badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:700;color:#fff}
.type-kb{background:#4361ee}.type-act{background:#7209b7}.type-pay{background:#e63946}.type-ret{background:#2ec4b6}.type-all{background:#666}
</style>
</head>
<body>
<div class="container">
<h1>内容营销数据看板</h1>
<p class="subtitle">本周：2026/4/3 - 4/9 ｜ 上周：2026/3/27 - 4/2 ｜ 渠道：头条 / 小红书 / 快手 / 聚星</p>
<div id="controls"></div>
<div id="app"><div class="loading">正在加载数据...</div></div>
</div>
<script>
const CSV_DATA = `'''

HTML_AFTER = r'''`;const CSV_DATA_PREV = `''' + csv_prev_escaped + r'''`;

const CHANNELS=['头条','小红书','快手','聚星'],CH_COLORS=['#4361ee','#e63946','#f77f00','#2ec4b6'];
const PERSONS=['韩孟伶','兰兰','崔宇彤','陈畅'],P_COLORS=['#4361ee','#e63946','#f77f00','#7209b7'];
const BID_RANGES=['<15','15-20','20-25','25-30','30-35','35-40','40-50','50-60','60+'];
// 渠道归属负责人
const CH_PERSON={'头条':'韩孟伶','小红书':'兰兰','快手':'崔宇彤','聚星':'韩孟伶'};

// 转化类型配置：标签、颜色、说明
const CONV_TYPES=[
  {key:'all',      label:'全部',   cls:'type-all', desc:'所有转化类型汇总数据'},
  {key:'关键行为',  label:'关键行为', cls:'type-kb', desc:'以关键行为（阅读/任务）为核心转化目标'},
  {key:'激活',      label:'激活',   cls:'type-act', desc:'以激活（下载+首次使用）为核心转化目标'},
  {key:'激活且每日留存', label:'激活且每日留存', cls:'type-ret', desc:'以激活且每日留存为核心转化目标'},
  {key:'付费',      label:'付费',   cls:'type-pay', desc:'以付费转化为核心优化目标'},
  {key:'激活且次留', label:'激活且次留', cls:'type-act', desc:'以激活且次日留存为核心转化目标'}
];

// 模板配置
const TEMPLATES={
  kb:{
    name:'关键行为',
    desc:'以关键行为转化为优化目标，分析转化成本、激活效率及出价分布',
    cards:[
      {l:'总消耗',k:'cost'},
      {l:'总关键行为数',k:'ka',d:0},
      {l:'总激活数',k:'act',d:0},
      {l:'转化成本',k:'convCost'},
      {l:'激活成本',k:'actCost'},
      {l:'平均出价',k:'avgBid'},
      {l:'点击率',k:'clickRate',fmt:'pct'},
      {l:'次留率',k:'retRate',fmt:'pct',color:'green'},
      {l:'付费收入占比',k:'payRevenue',fmt:'pct'},
      {l:'LTV',k:'ltv'},
      {l:'1日ROI赔付',k:'roi1',fmt:'pct'}
    ],
    chTable:['消耗','激活数','关键行为数','转化成本','激活成本','平均出价','点击率','次留率','3日留存','7日留存','付费率','付费收入占比','LTV','人均激励视频','激励视频CPM','1日ROI赔付','3日ROI赔付','7日ROI赔付','在投账户数','新建计划数','在投计划数'],
    chData:['cost','act','ka','convCost','actCost','avgBid','clickRate','retRate','ret3','ret7','payRate','payRevenue','ltv','avgVideoNum','avgVideoCPM','roi1','roi3','roi7','accts','newPlans','plans'],
    chFmt: [2,0,0,2,2,2,'pct','pct','pct','pct','pct','pct',2,2,2,'pct','pct','pct',0,0,0],
    personCh:['消耗','激活','关键行为','转化成本','点击率','次留率','付费率','付费收入占比','LTV','1日ROI','在投账户','新建计划','在投计划'],
    personChData:['cost','act','ka','convCost','clickRate','retRate','payRate','payRevenue','ltv','roi1','accts','newPlans','plans'],
    personChFmt:[2,0,0,2,'pct','pct','pct','pct',2,'pct',0,0,0]
  },
  pay:{
    name:'付费',
    desc:'以付费转化为优化目标，分析付费率、付费成本及LTV/ROI回收情况',
    cards:[
      {l:'总消耗',k:'cost'},
      {l:'总付费用户',k:'payUsers',d:0},
      {l:'当日付费率',k:'payRate',fmt:'pct',color:'green'},
      {l:'付费单次成本',k:'payCost'},
      {l:'7日付费单次成本',k:'payCost7'},
      {l:'付费收入占比',k:'payRevenue',fmt:'pct'},
      {l:'点击率',k:'clickRate',fmt:'pct'},
      {l:'LTV',k:'ltv'},
      {l:'1日ROI赔付',k:'roi1',fmt:'pct'},
      {l:'7日ROI赔付',k:'roi7',fmt:'pct'}
    ],
    chTable:['消耗','付费用户','付费率','付费单次成本','7日付费成本','付费收入占比','点击率','平均出价','次留率','LTV','1日ROI赔付','3日ROI赔付','7日ROI赔付','人均激励视频','激励视频CPM','在投账户数','新建计划数','在投计划数'],
    chData:['cost','payUsers','payRate','payCost','payCost7','payRevenue','clickRate','avgBid','retRate','ltv','roi1','roi3','roi7','avgVideoNum','avgVideoCPM','accts','newPlans','plans'],
    chFmt: [2,0,'pct',2,2,'pct','pct',2,'pct',2,'pct','pct','pct',2,2,0,0,0],
    personCh:['消耗','付费用户','付费率','付费单次成本','7日付费成本','点击率','LTV','1日ROI','3日ROI','7日ROI','在投账户','新建计划','在投计划'],
    personChData:['cost','payUsers','payRate','payCost','payCost7','clickRate','ltv','roi1','roi3','roi7','accts','newPlans','plans'],
    personChFmt:[2,0,'pct',2,2,'pct',2,'pct','pct','pct',0,0,0]
  },
  ret:{
    name:'留存',
    desc:'以用户留存为优化目标，分析次留率、多日留存率及留存成本',
    cards:[
      {l:'总消耗',k:'cost'},
      {l:'总激活数',k:'act',d:0},
      {l:'次留率',k:'retRate',fmt:'pct',color:'green'},
      {l:'3日留存',k:'ret3',fmt:'pct'},
      {l:'7日留存',k:'ret7',fmt:'pct'},
      {l:'14日留存',k:'ret14',fmt:'pct'},
      {l:'次留成本',k:'retCost'},
      {l:'平均使用时长',k:'avgUse',d:2,s:'分钟'},
      {l:'点击率',k:'clickRate',fmt:'pct'},
      {l:'付费收入占比',k:'payRevenue',fmt:'pct'},
      {l:'LTV',k:'ltv'}
    ],
    chTable:['消耗','激活数','次留率','3日留存','7日留存','14日留存','次留成本','平均使用时长','付费率','付费收入占比','点击率','平均出价','LTV','人均激励视频','激励视频CPM','1日ROI赔付','3日ROI赔付','7日ROI赔付','在投账户数','新建计划数','在投计划数'],
    chData:['cost','act','retRate','ret3','ret7','ret14','retCost','avgUse','payRate','payRevenue','clickRate','avgBid','ltv','avgVideoNum','avgVideoCPM','roi1','roi3','roi7','accts','newPlans','plans'],
    chFmt: [2,0,'pct','pct','pct','pct',2,2,'pct','pct','pct',2,2,2,2,'pct','pct','pct',0,0,0],
    personCh:['消耗','激活','次留率','3日留存','7日留存','14日留存','次留成本','平均使用时长','付费率','付费收入占比','点击率','LTV','在投账户','新建计划','在投计划'],
    personChData:['cost','act','retRate','ret3','ret7','ret14','retCost','avgUse','payRate','payRevenue','clickRate','ltv','accts','newPlans','plans'],
    personChFmt:[2,0,'pct','pct','pct','pct',2,2,'pct','pct','pct',2,0,0,0]
  }
};

var currentType='all',currentTpl='kb',currentOS='all',charts={};

// Lightweight CSV parser
function parseCSV(text){
  var lines=[],buf='',inQ=false,row=[],rows=[];
  for(var i=0;i<text.length;i++){
    var c=text[i],n=text[i+1];
    if(inQ){
      if(c=='"'&&n=='"'){buf+='"';i++;}
      else if(c=='"'){inQ=false;}
      else {buf+=c;}
    } else {
      if(c=='"'){inQ=true;}
      else if(c=='\n'||(c=='\r'&&n=='\n')){
        row.push(buf.trim());buf='';
        if(row.length>0&&row.join('')!=='')rows.push(row);
        row=[];if(c=='\r')i++;
      } else if(c==','){row.push(buf.trim());buf='';}
      else {buf+=c;}
    }
  }
  if(buf.trim()||row.length>0)row.push(buf.trim()),rows.push(row);
  var hdrs=rows[0]||[];
  var result=[];
  for(var j=1;j<rows.length;j++){
    var obj={};
    for(var k=0;k<hdrs.length;k++)obj[hdrs[k]]=rows[j][k]||'';
    var app=obj['app名称']||'';
    obj['os']=app.indexOf('-ios')!==-1?'iOS':'安卓';
    result.push(obj);
  }
  return result;
}

function pn(v){if(v==null||v===''||v==='-')return 0;return parseFloat(String(v).replace(/,/g,'').replace(/%/g,'').replace(/\t/g,'').trim())||0}
function fmt(n,d){d=d==null?2:d;return n.toFixed(d)}
function fmtPct(n){return n.toFixed(2)+'%'}
function sumCol(rows,k){return rows.reduce((s,r)=>s+pn(r[k]),0)}
function wavg(rows,vk,wk){let svw=0,sw=0;rows.forEach(r=>{let v=pn(r[vk]),w=pn(r[wk]);svw+=v*w;sw+=w});return sw===0?0:svw/sw}
function groupBy(rows,k){let m={};rows.forEach(r=>{let key=r[k]||'未知';if(!m[key])m[key]=[];m[key].push(r)});return m}
function bidBucket(v){if(v<15)return'<15';if(v<20)return'15-20';if(v<25)return'20-25';if(v<30)return'25-30';if(v<35)return'30-35';if(v<40)return'35-40';if(v<50)return'40-50';if(v<60)return'50-60';return'60+'}

function stats(rows){
  let cost=sumCol(rows,'消耗'),act=sumCol(rows,'激活数'),ka=sumCol(rows,'关键行为数');
  let payRate=wavg(rows,'当日实际付费率','激活数');
  return{cost,act,ka,
    convCost:act===0?0:wavg(rows,'转化成本','激活数'),
    actCost:act===0?0:cost/act,
    avgBid:wavg(rows,'当前平均出价','消耗'),
    retRate:wavg(rows,'次留率','激活数'),
    ret3:wavg(rows,'3日留存率','激活数'),
    ret7:wavg(rows,'7日留存率','激活数'),
    ret14:wavg(rows,'14日留存率','激活数'),
    payRate:payRate,
    payUsers:act*payRate,
    payCost:wavg(rows,'当日实际付费单次成本','激活数'),
    payCost7:wavg(rows,'7日内回传付费单次成本','激活数'),
    payRevenue:wavg(rows,'当日实际付费收入占比','激活数'),
    avgUse:wavg(rows,'当日平均使用时长_分钟','激活数'),
    retCost:wavg(rows,'次日留存成本','激活数'),
    roi1:wavg(rows,'修复真实1日roi_规则赔付','消耗'),
    roi3:wavg(rows,'修复真实3日roi_规则赔付','消耗'),
    roi7:wavg(rows,'修复真实7日roi_规则赔付','消耗'),
    newPlans:sumCol(rows,'新建计划数'),
    accts:new Set(rows.map(function(r){return(r['账户id']||'').trim()}).filter(Boolean)).size,
    plans:rows.length,
    avgVideoNum:wavg(rows,'人均激励视频数','消耗'),
    avgVideoCPM:wavg(rows,'激励视频cpm','消耗'),
    clickRate:wavg(rows,'点击转化率','消耗'),
    ltv:wavg(rows,'预估ltv','消耗')
  };
}

function getVal(s,k,fd){
  var v=s[k]||0;
  if(fd==='pct')return fmtPct(v);
  return fmt(v,fd!=null?fd:2);
}

// 对比模式下的单元格：本周值 + 环比变化
function getValC(cur,prev,k,fd){
  if(!cur)cur={};
  if(!prev)prev={};
  var cv=cur[k]||0;
  var pv=prev[k]||0;
  var cvStr=fd==='pct'?fmtPct(cv):fmt(cv,fd!=null?fd:2);
  var pct=fd==='pct';
  var delta=pv>0?(cv-pv)/pv*100:null;
  if(delta===null)return'<div>'+cvStr+'</div><div style="font-size:10px;color:#999">—</div>';
  var sign=delta>0?'+':'';
  // pct指标：留存率、付费率、ROI 越大越好；成本类指标：越小越好
  var isGood;
  if(pct){
    // 留存/付费率/ROI越高越好；成本越低越好
    var costK=['convCost','actCost','payCost','payCost7','retCost'];
    isGood=costK.indexOf(k)===-1;
  } else {
    isGood=true;
  }
  var color=isGood?(delta>0?'#2ec4b6':'#e63946'):(delta>0?'#e63946':'#2ec4b6');
  return'<div style="font-weight:700">'+cvStr+'</div><div style="font-size:10px;color:'+color+'">'+sign+delta.toFixed(1)+'%</div>';
}

// 带环比变化的汇总卡片
function overviewCardC(cur,prev,k,l,fd,extra){
  if(!cur)cur={};
  if(!prev)prev={};
  var cv=cur[k]||0;
  var pv=prev[k]||0;
  var cvStr=fd==='pct'?fmtPct(cv):fmt(cv,fd!=null?fd:2);
  var pct=fd==='pct';
  var delta=pv>0?(cv-pv)/pv*100:null;
  var changeStr='';
  if(delta!==null){
    var sign=delta>0?'+':'';
    var isGood=!['convCost','actCost','payCost','payCost7','retCost'].some(function(x){return x===k});
    var color=isGood?(delta>0?'#2ec4b6':'#e63946'):(delta>0?'#e63946':'#2ec4b6');
    changeStr='<span style="font-size:13px;font-weight:600;color:'+color+'">'+sign+delta.toFixed(1)+'%</span>';
  }
  var cls=extra?' '+extra:'';
  return'<div class="card"><div class="label">'+l+'</div><div class="value'+cls+'">'+cvStr+(extra?'分钟':'')+'</div>'+(changeStr?'<div style="margin-top:4px">'+changeStr+' vs上周</div>':'')+'</div>';
}

function getRowsByType(rawRows,type){
  var base=type==='all'?rawRows:rawRows.filter(function(r){return r['转化类型']===type});
  if(currentOS==='all')return base;
  var filtered=base.filter(function(r){return r['os']===currentOS;});
  console.log('getRowsByType - type:', type, 'currentOS:', currentOS, 'base.length:', base.length, 'filtered.length:', filtered.length);
  if(filtered.length>0){
    console.log('Sample filtered row os:', filtered[0]['os'], 'app:', filtered[0]['app名称']);
  }
  return filtered;
}

// 渲染转化类型选择器
function renderTypeTabs(){
  var h='<div class="tab-bar">';
  CONV_TYPES.forEach(function(t){
    h+='<div class="tab-btn'+(t.key===currentType?' active':'')+'" data-type="'+t.key+'">';
    h+='<span class="type-badge '+t.cls+'">'+t.label+'</span>';
    h+='</div>';
  });
  h+='</div>';
  return h;
}

// 渲染模板选择器
function renderTplTabs(){
  var h='<div class="tab-bar">';
  Object.keys(TEMPLATES).forEach(function(key){
    var t=TEMPLATES[key];
    h+='<div class="tab-btn sub'+(key===currentTpl?' active':'')+'" data-tpl="'+key+'">'+t.name+'</div>';
  });
  h+='</div>';
  return h;
}

// 渲染OS平台选择器
function renderOsTabs(){
  var osList=['all','安卓','iOS'];
  var osLabels={'all':'全部平台','安卓':'安卓','iOS':'iOS'};
  var h='<div class="tab-label">操作系统</div>';
  h+='<div class="tab-bar" id="osTabs">';
  osList.forEach(function(o){
    h+='<div class="tab-btn'+(currentOS===o?' active':'')+'" data-os="'+o+'">'+osLabels[o]+'</div>';
  });
  h+='</div>';
  return h;
}

// 概览卡片
function overviewCards(s){
  var tpl=TEMPLATES[currentTpl];
  var h='<div class="cards">';
  tpl.cards.forEach(function(c){
    var v=s[c.k]||0;
    var fv=c.fmt==='pct'?fmtPct(v):fmt(v,c.d||2);
    h+='<div class="card"><div class="label">'+c.l+'</div><div class="value'+(c.color?(' '+c.color):'')+'">'+fv+(c.s||'')+'</div></div>';
  });
  h+='</div>';
  return h;
}

// 渠道对比表格（含OS平台拆分，带环比）
function channelTable(rows,t,prevRows,pt,tpl){
  var byCh=groupBy(rows,'投放渠道');
  var prevByCh=prevRows?groupBy(prevRows,'投放渠道'):{};
  var isAllOS=currentOS==='all';
  var emptyS={cost:0,act:0,ka:0,convCost:0,actCost:0,avgBid:0,retRate:0,ret3:0,ret7:0,payRate:0,avgVideoNum:0,avgVideoCPM:0,roi1:0,roi3:0,roi7:0,accts:0,newPlans:0,plans:0,clickRate:0,payRevenue:0,ltv:0};
  var h='<div class="table-wrap"><table>';
  h+='<tr><th>渠道</th>';
  tpl.chTable.forEach(function(col){h+='<th>'+col+'</th>'});
  h+='</tr>';
  CHANNELS.forEach(function(ch,i){
    var chRows=byCh[ch]||[];
    var prevChRows=prevByCh[ch]||[];
    if(isAllOS){
      // 安卓行
      var azRows=chRows.filter(function(r){return r['os']==='安卓'});
      var pAzRows=prevChRows.filter(function(r){return r['os']==='安卓'});
      var csAz=stats(azRows);
      var psAz=pAzRows.length>0?stats(pAzRows):null;
      h+='<tr><td><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:'+CH_COLORS[i]+';margin-right:6px"></span>'+ch+' <span style="color:#2ec4b6;font-size:11px;font-weight:600">安卓</span></td>';
      tpl.chData.forEach(function(k,idx){h+='<td>'+getValC(csAz,psAz,k,tpl.chFmt[idx])+'</td>'});
      h+='</tr>';
      // iOS行（仅头条有）
      var iosRows=chRows.filter(function(r){return r['os']==='iOS'});
      var pIosRows=prevChRows.filter(function(r){return r['os']==='iOS'});
      if(iosRows.length>0){
        var csIos=stats(iosRows);
        var psIos=pIosRows.length>0?stats(pIosRows):null;
        h+='<tr><td><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:'+CH_COLORS[i]+';margin-right:6px;opacity:0.5"></span>'+ch+' <span style="color:#e63946;font-size:11px;font-weight:600">iOS</span></td>';
        tpl.chData.forEach(function(k,idx){h+='<td>'+getValC(csIos,psIos,k,tpl.chFmt[idx])+'</td>'});
        h+='</tr>';
      }
    } else {
      var cs=stats(chRows);
      var ps=prevChRows.length>0?stats(prevChRows):null;
      var osLabel=currentOS==='iOS'?' <span style="color:#e63946;font-size:11px;font-weight:600">iOS</span>':' <span style="color:#2ec4b6;font-size:11px;font-weight:600">安卓</span>';
      h+='<tr><td><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:'+CH_COLORS[i]+';margin-right:6px"></span>'+ch+osLabel+'</td>';
      tpl.chData.forEach(function(k,idx){h+='<td>'+getValC(cs,ps,k,tpl.chFmt[idx])+'</td>'});
      h+='</tr>';
    }
  });
  h+='<tr class="totals"><td>合计</td>';
  tpl.chData.forEach(function(k,idx){h+='<td>'+getValC(t,pt,k,tpl.chFmt[idx])+'</td>'});
  h+='</tr></table></div>';
  return h;
}

// 负责人汇总表格（带环比）
function personSummaryTable(rows,tpl,prevRows){
  var byP=groupBy(rows,'运营负责人');
  var prevByP=prevRows?groupBy(prevRows,'运营负责人'):{};
  var h='<div class="table-wrap"><table>';
  h+='<tr><th>负责人</th>';
  tpl.chData.forEach(function(k,i){h+='<th>'+tpl.chTable[i]+'</th>'});
  h+='</tr>';
  PERSONS.forEach(function(p){h+=personRowC(p,stats(byP[p]||[]),prevByP[p]?stats(prevByP[p]):null,tpl)});
  var pt=prevRows?stats(prevRows):null;
  h+='<tr class="totals">'+personRowC('合计',stats(rows),pt,tpl).slice(4)+'</tr></table></div>';
  return h;
}

function personRowC(label,s,ps,tpl){
  var h='<tr><td>'+label+'</td>';
  tpl.chData.forEach(function(k,idx){h+='<td>'+getValC(s,ps,k,tpl.chFmt[idx])+'</td>'});
  h+='</tr>';return h;
}

function personRow(label,s,tpl){
  var h='<tr><td>'+label+'</td>';
  tpl.chData.forEach(function(k,idx){h+='<td>'+getVal(s,k,tpl.chFmt[idx])+'</td>'});
  h+='</tr>';return h;
}

// 出价分布表
function bidStats(rows){
  var result={};
  BID_RANGES.forEach(function(b){result[b]={accts:new Set(),newPlans:0,plans:0,cost:0,rows:[]}});
  rows.forEach(function(r){
    var bid=pn(r['当前平均出价']);
    if(bid<=0)return;
    var d=result[bidBucket(bid)];
    d.accts.add((r['账户id']||'').trim());
    d.newPlans+=pn(r['新建计划数']);
    d.plans++;d.cost+=pn(r['消耗']);
    d.rows.push(r);
  });
  BID_RANGES.forEach(function(b){
    var d=result[b];
    d.acctCount=d.accts.size;
    d.roi1=d.rows.length?wavg(d.rows,'修复真实1日roi_规则赔付','消耗'):0;
    d.roi3=d.rows.length?wavg(d.rows,'修复真实3日roi_规则赔付','消耗'):0;
    d.roi7=d.rows.length?wavg(d.rows,'修复真实7日roi_规则赔付','消耗'):0;
  });
  return result;
}

function bidTable(bs,tpl){
  var h='<div class="table-wrap"><table style="font-size:12px">';
  h+='<tr><th>出价区间</th>';
  tpl.chTable.forEach(function(col){h+='<th>'+col+'</th>'});
  h+='</tr>';
  var tAccts=new Set(),tNew=0,tPlans=0,tCost=0,tRows=[];
  BID_RANGES.forEach(function(b){
    var d=bs[b];
    if(d.plans>0){
      tNew+=d.newPlans;tPlans+=d.plans;tCost+=d.cost;tRows=tRows.concat(d.rows);
      d.accts.forEach(function(a){tAccts.add(a)});
      var s=stats(d.rows);
      h+='<tr><td>'+b+'</td>';
      tpl.chData.forEach(function(k,idx){h+='<td>'+getVal(s,k,tpl.chFmt[idx])+'</td>'});
      h+='</tr>';
    } else {
      h+='<tr class="zero-row"><td>'+b+'</td><td colspan="'+tpl.chData.length+'" style="text-align:center">— 无数据 —</td></tr>';
    }
  });
  var tS=stats(tRows);
  h+='<tr class="totals"><td>合计</td>';
  tpl.chData.forEach(function(k,idx){h+='<td>'+getVal(tS,k,tpl.chFmt[idx])+'</td>'});
  h+='</tr>';
  h+='</table></div>';
  return h;
}

// 负责人分渠道明细（按渠道子筛选，带环比）
function renderPersonSection(typeRows,prevTypeRows){
  var tpl=TEMPLATES[currentTpl];
  var container=document.getElementById('personContent');
  var h='';

  h+=personSummaryTable(typeRows,tpl,prevTypeRows);

  h+='<div class="person-grid">';
  PERSONS.forEach(function(p,i){
    var pRows=typeRows.filter(function(r){return r['运营负责人']===p});
    var s=stats(pRows);
    h+='<div class="person-card">';
    h+='<h3 style="color:'+P_COLORS[i]+'">'+p+'</h3>';
    h+='<div class="mini-stats" id="miniStats'+i+'">';
    h+='<div class="mini-stat"><div class="ms-label">在投账户数</div><div class="ms-val">'+s.accts+'</div></div>';
    h+='<div class="mini-stat"><div class="ms-label">新建计划数</div><div class="ms-val">'+s.newPlans+'</div></div>';
    h+='<div class="mini-stat"><div class="ms-label">在投计划数</div><div class="ms-val">'+s.plans+'</div></div>';
    h+='</div>';
    // 渠道子筛选
    h+='<div class="tab-label" style="margin-top:8px">按渠道筛选</div>';
    h+='<div class="tab-bar" id="pChTabs'+i+'" style="margin-bottom:10px">';
    h+='<div class="tab-btn sub active" data-pch="全部" data-pi="'+i+'">全部</div>';
    CHANNELS.forEach(function(ch){h+='<div class="tab-btn sub" data-pch="'+ch+'" data-pi="'+i+'">'+ch+'</div>'});
    h+='</div>';
    h+='<div id="pChContent'+i+'"></div>';
    h+='</div>';
  });
  h+='</div>';
  container.innerHTML=h;

  // 渠道子筛选点击
  PERSONS.forEach(function(p,i){
    var pRows=typeRows.filter(function(r){return r['运营负责人']===p});
    var pByCh=groupBy(pRows,'投放渠道');
    document.getElementById('pChTabs'+i).addEventListener('click',function(e){
      var tab=e.target.closest('.tab-btn');
      if(!tab)return;
      document.querySelectorAll('#pChTabs'+i+' .tab-btn').forEach(function(t){t.classList.remove('active')});
      tab.classList.add('active');
      var ch=tab.dataset.pch;
      var rows=ch==='全部'?pRows:(pByCh[ch]||[]);
      var s=stats(rows);
      var tpl=TEMPLATES[currentTpl];
      // 更新mini-stats
      var ms=document.getElementById('miniStats'+i);
      if(ms){ms.innerHTML='<div class="mini-stat"><div class="ms-label">在投账户数</div><div class="ms-val">'+s.accts+'</div></div><div class="mini-stat"><div class="ms-label">新建计划数</div><div class="ms-val">'+s.newPlans+'</div></div><div class="mini-stat"><div class="ms-label">在投计划数</div><div class="ms-val">'+s.plans+'</div></div>';}
      var cont=document.getElementById('pChContent'+i);
      var h2='<div class="table-wrap"><table style="font-size:12px">';
      h2+='<tr><th>渠道</th>';
      tpl.personCh.forEach(function(col){h2+='<th>'+col+'</th>'});
      h2+='</tr>';
      CHANNELS.forEach(function(c){
        var chRows=pByCh[c]||[];
        var azRows=chRows.filter(function(r){return r['os']==='安卓'});
        var iosRows=chRows.filter(function(r){return r['os']==='iOS'});
        if(azRows.length>0){
          var cs=stats(azRows);
          h2+='<tr><td>'+c+' <span style="color:#2ec4b6;font-size:10px">安卓</span></td>';
          tpl.personChData.forEach(function(k,idx){h2+='<td>'+getVal(cs,k,tpl.personChFmt[idx])+'</td>'});
          h2+='</tr>';
        }
        if(iosRows.length>0){
          var cs=stats(iosRows);
          h2+='<tr><td>'+c+' <span style="color:#e63946;font-size:10px">iOS</span></td>';
          tpl.personChData.forEach(function(k,idx){h2+='<td>'+getVal(cs,k,tpl.personChFmt[idx])+'</td>'});
          h2+='</tr>';
        }
      });
      h2+='<tr class="totals"><td>合计</td>';
      tpl.personChData.forEach(function(k,idx){h2+='<td>'+getVal(s,k,tpl.personChFmt[idx])+'</td>'});
      h2+='</tr></table></div>';
      // 出价分布
      h2+='<h3 style="font-size:13px;margin-top:12px">出价分布明细</h3>';
      h2+=bidTable(bidStats(rows),tpl);
      cont.innerHTML=h2;
    });
    // 默认渲染全部
    document.getElementById('pChContent'+i).innerHTML=(function(){
      var s=stats(pRows);
      var tpl=TEMPLATES[currentTpl];
      var h2='<div class="table-wrap"><table style="font-size:12px">';
      h2+='<tr><th>渠道</th>';
      tpl.personCh.forEach(function(col){h2+='<th>'+col+'</th>'});
      h2+='</tr>';
      CHANNELS.forEach(function(c){
        var chRows=pByCh[c]||[];
        var azRows=chRows.filter(function(r){return r['os']==='安卓'});
        var iosRows=chRows.filter(function(r){return r['os']==='iOS'});
        if(azRows.length>0){
          var cs=stats(azRows);
          h2+='<tr><td>'+c+' <span style="color:#2ec4b6;font-size:10px">安卓</span></td>';
          tpl.personChData.forEach(function(k,idx){h2+='<td>'+getVal(cs,k,tpl.personChFmt[idx])+'</td>'});
          h2+='</tr>';
        }
        if(iosRows.length>0){
          var cs=stats(iosRows);
          h2+='<tr><td>'+c+' <span style="color:#e63946;font-size:10px">iOS</span></td>';
          tpl.personChData.forEach(function(k,idx){h2+='<td>'+getVal(cs,k,tpl.personChFmt[idx])+'</td>'});
          h2+='</tr>';
        }
      });
      h2+='<tr class="totals"><td>合计</td>';
      tpl.personChData.forEach(function(k,idx){h2+='<td>'+getVal(s,k,tpl.personChFmt[idx])+'</td>'});
      h2+='</tr></table></div>';
      h2+='<h3 style="font-size:13px;margin-top:12px">出价分布明细</h3>';
      h2+=bidTable(bidStats(pRows),tpl);
      return h2;
    })();
  });
}

// 代理关键词映射
const AGENCIES=[
  {key:'短笛',kw:'短笛',color:'#4361ee'},
  {key:'汇创',kw:'汇创',color:'#e63946'},
  {key:'天擎',kw:'天擎',color:'#f77f00'},
  {key:'民众',kw:'民众',color:'#2ec4b6'},
  {key:'泰格',kw:'泰格',color:'#7209b7'},
  {key:'月象',kw:'月象',color:'#3a0ca3'},
  {key:'蜜橘',kw:'蜜橘',color:'#f4a261'}
];
var currentAgencyCh='全部';

var allRows=[],prevRows=[],byType={},byTypePrev={};

// 代理数据模块
var AG_METRICS=[
  {l:'消耗',k:'cost',fd:2},
  {l:'激活数',k:'act',fd:0},
  {l:'关键行为数',k:'ka',fd:0},
  {l:'转化成本',k:'convCost',fd:2},
  {l:'激活成本',k:'actCost',fd:2},
  {l:'平均出价',k:'avgBid',fd:2},
  {l:'点击率',k:'clickRate',fd:'pct'},
  {l:'次留率',k:'retRate',fd:'pct'},
  {l:'付费率',k:'payRate',fd:'pct'},
  {l:'付费收入占比',k:'payRevenue',fd:'pct'},
  {l:'LTV',k:'ltv',fd:2},
  {l:'人均激励视频',k:'avgVideoNum',fd:2},
  {l:'激励视频CPM',k:'avgVideoCPM',fd:2},
  {l:'1日ROI赔付',k:'roi1',fd:'pct'},
  {l:'3日ROI赔付',k:'roi3',fd:'pct'},
  {l:'7日ROI赔付',k:'roi7',fd:'pct'},
  {l:'在投账户数',k:'accts',fd:0},
  {l:'新建计划数',k:'newPlans',fd:0},
  {l:'在投计划数',k:'plans',fd:0}
];

function renderAgencySection(){
  var h='<div class="section"><h2>代理数据</h2>';
  h+='<div class="tab-label" style="margin-bottom:8px">选择渠道</div>';
  h+='<div class="tab-bar" id="agencyChTabs" style="margin-bottom:14px">';
  h+='<div class="tab-btn sub active" data-agch="全部">全部渠道</div>';
  CHANNELS.forEach(function(ch){h+='<div class="tab-btn sub" data-agch="'+ch+'">'+ch+'</div>'});
  h+='</div>';
  h+='<div id="agencyContent"></div>';
  h+='</div>';
  return h;
}

function renderAgencyData(){
  var baseRows=(currentAgencyCh==='全部'?allRows:allRows.filter(function(r){return r['投放渠道']===currentAgencyCh})).filter(function(r){return currentOS==='all'||r['os']===currentOS;});
  var prevBaseRows=(currentAgencyCh==='全部'?prevRows:prevRows.filter(function(r){return r['投放渠道']===currentAgencyCh})).filter(function(r){return currentOS==='all'||r['os']===currentOS;});
  var agData={},prevAgData={};
  AGENCIES.forEach(function(a){
    agData[a.key]=baseRows.filter(function(r){return(r['账户组备注']||'').indexOf(a.kw)!==-1});
    prevAgData[a.key]=prevBaseRows.filter(function(r){return(r['账户组备注']||'').indexOf(a.kw)!==-1});
  });
  var allAgRows=[];
  AGENCIES.forEach(function(a){allAgRows=allAgRows.concat(agData[a.key])});
  var prevAllAgRows=[];
  AGENCIES.forEach(function(a){prevAllAgRows=prevAllAgRows.concat(prevAgData[a.key])});
  var totalS=stats(allAgRows);
  var prevTotalS=prevAllAgRows.length>0?stats(prevAllAgRows):null;
  var nonAll=CONV_TYPES.filter(function(t){return t.key!=='all'});

  // 汇总卡片（带环比）
  var h='<div class="cards">';
  h+='<div class="card"><div class="label">代理总消耗</div><div class="value">'+fmt(totalS.cost)+'</div>'+(prevTotalS?'<div style="margin-top:4px;font-size:11px;color:#666">上周：'+fmt(prevTotalS.cost)+'</div>':'')+'</div>';
  h+='<div class="card"><div class="label">总激活数</div><div class="value">'+fmt(totalS.act,0)+'</div>'+(prevTotalS?'<div style="margin-top:4px;font-size:11px;color:#666">上周：'+fmt(prevTotalS.act,0)+'</div>':'')+'</div>';
  h+='<div class="card"><div class="label">总关键行为数</div><div class="value">'+fmt(totalS.ka,0)+'</div>'+(prevTotalS?'<div style="margin-top:4px;font-size:11px;color:#666">上周：'+fmt(prevTotalS.ka,0)+'</div>':'')+'</div>';
  h+=overviewCardC(totalS,prevTotalS,'convCost','转化成本');
  h+=overviewCardC(totalS,prevTotalS,'retRate','次留率');
  h+=overviewCardC(totalS,prevTotalS,'payRate','付费率');
  h+=overviewCardC(totalS,prevTotalS,'roi1','1日ROI赔付');
  h+=overviewCardC(totalS,prevTotalS,'roi3','3日ROI赔付');
  h+=overviewCardC(totalS,prevTotalS,'roi7','7日ROI赔付');
  h+='<div class="card"><div class="label">在投账户数</div><div class="value">'+totalS.accts+'</div>'+(prevTotalS?'<div style="margin-top:4px;font-size:11px;color:#666">上周：'+prevTotalS.accts+'</div>':'')+'</div>';
  h+='<div class="card"><div class="label">在投计划数</div><div class="value">'+totalS.plans+'</div>'+(prevTotalS?'<div style="margin-top:4px;font-size:11px;color:#666">上周：'+prevTotalS.plans+'</div>':'')+'</div>';
  h+='</div>';

  // 明细表格
  h+='<div class="table-wrap"><table style="font-size:11px">';
  h+='<tr><th>代理</th><th>转化类型</th>';
  AG_METRICS.forEach(function(m){h+='<th>'+m.l+'</th>'});
  h+='</tr>';

  nonAll.forEach(function(t){
    var anyData=AGENCIES.some(function(a){
      var tRows=agData[a.key].filter(function(r){return r['转化类型']===t.key});
      return tRows.length>0;
    });
    if(!anyData)return;

    h+='<tr style="background:#f0f2f8"><td colspan="2" style="font-weight:700"><span class="type-badge '+t.cls+'">'+t.label+'</span></td>';
    AG_METRICS.forEach(function(){h+='<td style="background:#f0f2f8"></td>'});
    h+='</tr>';

    AGENCIES.forEach(function(a,i){
      var tRows=agData[a.key].filter(function(r){return r['转化类型']===t.key});
      var ptRows=prevAgData[a.key].filter(function(r){return r['转化类型']===t.key});
      if(tRows.length===0)return;
      var s=stats(tRows);
      var ps=ptRows.length>0?stats(ptRows):null;
      h+='<tr>';
      h+='<td style="color:'+a.color+';font-weight:600">'+a.key+'</td>';
      h+='<td style="color:var(--text2)">'+t.label+'</td>';
      AG_METRICS.forEach(function(m){h+='<td>'+getValC(s,ps,m.k,m.fd)+'</td>'});
      h+='</tr>';
    });
  });

  // 合计分隔行
  h+='<tr style="border-top:2px solid var(--accent2);background:#f0f2f8"><td colspan="'+(2+AG_METRICS.length)+'" style="font-weight:700">合计（各代理全部数据）</td></tr>';
  AGENCIES.forEach(function(a){
    var s=stats(agData[a.key]);
    var ps=prevAgData[a.key].length>0?stats(prevAgData[a.key]):null;
    if(s.plans===0&&(!ps||ps.plans===0))return;
    h+='<tr class="totals">';
    h+='<td style="color:'+a.color+';font-weight:600">'+a.key+'</td><td>全部</td>';
    AG_METRICS.forEach(function(m){h+='<td>'+getValC(s,ps,m.k,m.fd)+'</td>'});
    h+='</tr>';
  });

  h+='</table></div>';

  // 图表：各代理消耗对比（本周 vs 上周）
  h+='<div class="chart-row" style="margin-top:16px">';
  h+='<div class="chart-box"><canvas id="agBarChart"></canvas></div>';
  h+='<div class="chart-box"><canvas id="agPieChart"></canvas></div></div>';

  document.getElementById('agencyContent').innerHTML=h;

  if(window._agBar)try{window._agBar.destroy()}catch(e){}
  if(window._agPie)try{window._agPie.destroy()}catch(e){}

  var agLabels=AGENCIES.map(function(a){return a.key});
  var agCosts=AGENCIES.map(function(a){return stats(agData[a.key]).cost});
  var agPrevCosts=AGENCIES.map(function(a){return stats(prevAgData[a.key]).cost});
  var agColors=AGENCIES.map(function(a){return a.color});

  window._agBar=new Chart(document.getElementById('agBarChart'),{
    type:'bar',
    data:{labels:agLabels,datasets:[
      {label:'本周消耗',data:agCosts,backgroundColor:agColors.map(function(c){return c+'cc'})},
      {label:'上周消耗',data:agPrevCosts,backgroundColor:agColors.map(function(c){return c+'66'})}
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{title:{display:true,text:'各代理消耗对比（'+currentAgencyCh+'）'}},scales:{y:{beginAtZero:true}}}
  });
  window._agPie=new Chart(document.getElementById('agPieChart'),{
    type:'pie',
    data:{labels:agLabels,datasets:[{data:agCosts,backgroundColor:agColors}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{title:{display:true,text:'各代理消耗占比（'+currentAgencyCh+'）'}}}
  });
}

function setupAgencyEvents(){
  document.getElementById('agencyChTabs').addEventListener('click',function(e){
    var tab=e.target.closest('.tab-btn');
    if(!tab)return;
    currentAgencyCh=tab.dataset.agch;
    document.querySelectorAll('#agencyChTabs .tab-btn').forEach(function(t){t.classList.remove('active')});
    tab.classList.add('active');
    renderAgencyData();
  });
}

// 转化类型 x 渠道交叉表格
function typeChannelSection(){
  var h='<div class="section"><h2>各转化类型 × 渠道数据明细</h2>';
  h+='<div class="tab-label" style="margin-bottom:10px">选择渠道</div>';
  h+='<div class="tab-bar" id="tcChTabs">';
  h+='<div class="tab-btn sub active" data-tcch="全部">全部渠道</div>';
  CHANNELS.forEach(function(ch,i){h+='<div class="tab-btn sub" data-tcch="'+ch+'" style="border-left-color:'+CH_COLORS[i]+';border-left-width:3px">'+ch+'</div>'});
  h+='</div>';
  h+='<div id="tcContent"></div>';
  h+='</div>';
  return h;
}

function renderTypeChannel(){
  var tpl=TEMPLATES[currentTpl];
  var currentCh='全部';

  function renderTcTable(ch){
    var baseRows=ch==='全部'?allRows:allRows.filter(function(r){return r['投放渠道']===ch});
    var prevBaseRows=ch==='全部'?prevRows:prevRows.filter(function(r){return r['投放渠道']===ch});
    var rows=currentOS==='all'?baseRows:baseRows.filter(function(r){return r['os']===currentOS;});
    var prevRowsCh=currentOS==='all'?prevBaseRows:prevBaseRows.filter(function(r){return r['os']===currentOS;});
    var nonAll=CONV_TYPES.filter(function(t){return t.key!=='all'});
    var isAllOS=currentOS==='all';

    var h='<div class="table-wrap"><table>';
    h+='<tr><th>转化类型</th>';
    tpl.chTable.forEach(function(col){h+='<th>'+col+'</th>'});
    h+='</tr>';
    nonAll.forEach(function(t){
      var tRows=rows.filter(function(r){return r['转化类型']===t.key});
      if(tRows.length===0)return;
      if(isAllOS){
        var azRows=tRows.filter(function(r){return r['os']==='安卓'});
        var iosRows=tRows.filter(function(r){return r['os']==='iOS'});
        if(azRows.length>0){
          var s=stats(azRows);
          var pAz=prevRowsCh.filter(function(r){return r['转化类型']===t.key&&r['os']==='安卓'});
          var ps=pAz.length>0?stats(pAz):null;
          h+='<tr><td><span class="type-badge '+t.cls+'">'+t.label+'</span> <span style="color:#2ec4b6;font-size:11px">安卓</span></td>';
          tpl.chData.forEach(function(k,idx){h+='<td>'+getValC(s,ps,k,tpl.chFmt[idx])+'</td>'});
          h+='</tr>';
        }
        if(iosRows.length>0){
          var s=stats(iosRows);
          var pIos=prevRowsCh.filter(function(r){return r['转化类型']===t.key&&r['os']==='iOS'});
          var ps=pIos.length>0?stats(pIos):null;
          h+='<tr><td><span class="type-badge '+t.cls+'">'+t.label+'</span> <span style="color:#e63946;font-size:11px">iOS</span></td>';
          tpl.chData.forEach(function(k,idx){h+='<td>'+getValC(s,ps,k,tpl.chFmt[idx])+'</td>'});
          h+='</tr>';
        }
      } else {
        var ptRows=prevRowsCh.filter(function(r){return r['转化类型']===t.key});
        var s=stats(tRows);
        var ps=ptRows.length>0?stats(ptRows):null;
        h+='<tr><td><span class="type-badge '+t.cls+'">'+t.label+'</span></td>';
        tpl.chData.forEach(function(k,idx){h+='<td>'+getValC(s,ps,k,tpl.chFmt[idx])+'</td>'});
        h+='</tr>';
      }
    });
    h+='<tr class="totals"><td>合计</td>';
    var totalS=stats(rows);
    var prevTotalS=prevRowsCh.length>0?stats(prevRowsCh):null;
    tpl.chData.forEach(function(k,idx){h+='<td>'+getValC(totalS,prevTotalS,k,tpl.chFmt[idx])+'</td>'});
    h+='</tr></table></div>';

    // 柱状图：本周 vs 上周
    h+='<div class="chart-row" style="margin-top:16px">';
    h+='<div class="chart-box"><canvas id="tcBarChart"></canvas></div>';
    h+='<div class="chart-box"><canvas id="tcPieChart"></canvas></div></div>';

    document.getElementById('tcContent').innerHTML=h;

    if(window._tcChart)try{window._tcChart.destroy()}catch(e){}
    if(window._tcPieChart)try{window._tcPieChart.destroy()}catch(e){}

    // 柱状图：各转化类型消耗对比
    var barLabels=nonAll.map(function(t){return t.label});
    var barData=nonAll.map(function(t){
      var tRows=rows.filter(function(r){return r['转化类型']===t.key});
      return stats(tRows).cost;
    });
    var prevBarData=nonAll.map(function(t){
      var ptRows=prevRowsCh.filter(function(r){return r['转化类型']===t.key});
      return stats(ptRows).cost;
    });
    window._tcChart=new Chart(document.getElementById('tcBarChart'),{
      type:'bar',
      data:{labels:barLabels,datasets:[
        {label:'本周消耗',data:barData,backgroundColor:['#4361ee','#7209b7','#2ec4b6','#e63946','#f77f00'].map(function(c){return c+'cc'})},
        {label:'上周消耗',data:prevBarData,backgroundColor:['#4361ee','#7209b7','#2ec4b6','#e63946','#f77f00'].map(function(c){return c+'66'})}
      ]},
      options:{responsive:true,maintainAspectRatio:false,plugins:{title:{display:true,text:(ch==='全部'?'全部':ch)+'：各转化类型消耗'}},scales:{y:{beginAtZero:true}}}
    });

    // 饼图：本周各转化类型消耗占比
    window._tcPieChart=new Chart(document.getElementById('tcPieChart'),{
      type:'pie',
      data:{labels:barLabels,datasets:[{data:barData,backgroundColor:['#4361ee','#7209b7','#2ec4b6','#e63946','#f77f00']}]},
      options:{responsive:true,maintainAspectRatio:false,plugins:{title:{display:true,text:(ch==='全部'?'全部':ch)+'：转化类型消耗占比'}}}
    });
  }

  document.getElementById('tcChTabs').addEventListener('click',function(e){
    var tab=e.target.closest('.tab-btn');
    if(!tab)return;
    document.querySelectorAll('#tcChTabs .tab-btn').forEach(function(t){t.classList.remove('active')});
    tab.classList.add('active');
    renderTcTable(tab.dataset.tcch);
  });

  renderTcTable('全部');
}

function renderApp(){
  var tpl=TEMPLATES[currentTpl];
  var typeRows=getRowsByType(allRows,currentType);
  var prevTypeRows=getRowsByType(prevRows,currentType);
  console.log('renderApp - currentOS:', currentOS, 'typeRows.length:', typeRows.length, 'prevTypeRows.length:', prevTypeRows.length);

  if(typeRows.length===0){
    document.getElementById('app').innerHTML='<div class="section"><h2>暂无数据</h2><p>当前筛选条件下没有数据</p></div>';
    return;
  }

  var byCh=groupBy(typeRows,'投放渠道');
  var prevByCh=groupBy(prevTypeRows,'投放渠道');
  var t=stats(typeRows);
  var pt=stats(prevTypeRows);
  var h='';

  // 概览卡片（带环比）
  h+='<div class="section"><h2>本周核心指标</h2>';
  var cards=tpl.cards;
  h+='<div class="cards">';
  cards.forEach(function(c){
    var cv=c.k?t[c.k]:0;
    var pv=c.k?pt[c.k]:0;
    h+=overviewCardC(t,pt,c.k,c.l,c.fmt,c.s||'');
  });
  h+='</div></div>';

  // 渠道对比
  h+='<div class="section"><h2>各渠道数据对比</h2>';
  h+=channelTable(typeRows,t,prevTypeRows,pt,tpl);
  h+='<div class="chart-row"><div class="chart-box"><canvas id="chBarChart"></canvas></div><div class="chart-box"><canvas id="chPieChart"></canvas></div></div>';
  h+='</div>';

  // 负责人
  h+='<div class="section"><h2>各运营负责人数据</h2>';
  h+='<div id="personContent"></div>';
  h+='</div>';

  // 转化类型 x 渠道明细
  h+=typeChannelSection();

  // 代理数据
  h+=renderAgencySection();

  document.getElementById('app').innerHTML=h;

  Object.values(charts).forEach(function(c){if(c)try{c.destroy()}catch(e){}});
  charts={};

  renderPersonSection(typeRows,prevTypeRows);
  renderTypeChannel();
  setupAgencyEvents();
  renderAgencyData();

  // 柱状图：本周 vs 上周（按OS拆分）
  var isAllOS=currentOS==='all';
  var barLabels=isAllOS?CHANNELS:CHANNELS;
  var azData=CHANNELS.map(function(ch){return stats((byCh[ch]||[]).filter(function(r){return r['os']==='安卓'})).cost});
  var iosData=CHANNELS.map(function(ch){return stats((byCh[ch]||[]).filter(function(r){return r['os']==='iOS'})).cost});
  var pAzData=CHANNELS.map(function(ch){return stats((prevByCh[ch]||[]).filter(function(r){return r['os']==='安卓'})).cost});
  var pIosData=CHANNELS.map(function(ch){return stats((prevByCh[ch]||[]).filter(function(r){return r['os']==='iOS'})).cost});
  var datasets=isAllOS?[
    {label:'本周安卓',data:azData,backgroundColor:CH_COLORS.map(function(c){return c+'cc'})},
    {label:'本周iOS',data:iosData,backgroundColor:CH_COLORS.map(function(c){return c+'55'})},
    {label:'上周安卓',data:pAzData,backgroundColor:CH_COLORS.map(function(c){return c+'66'})},
    {label:'上周iOS',data:pIosData,backgroundColor:CH_COLORS.map(function(c){return c+'33'})}
  ]:[
    {label:'本周消耗',data:CHANNELS.map(function(ch){return stats(byCh[ch]||[]).cost}),backgroundColor:CH_COLORS.map(function(c){return c+'cc'})},
    {label:'上周消耗',data:CHANNELS.map(function(ch){return stats(prevByCh[ch]||[]).cost}),backgroundColor:CH_COLORS.map(function(c){return c+'66'})}
  ];
  charts.bar=new Chart(document.getElementById('chBarChart'),{
    type:'bar',
    data:{labels:CHANNELS,datasets:datasets},
    options:{responsive:true,maintainAspectRatio:false,plugins:{title:{display:true,text:tpl.name+'：各渠道消耗对比'}},scales:{y:{beginAtZero:true}}}
  });
  var pieData=CHANNELS.map(function(ch){return stats((byCh[ch]||[]).filter(function(r){return currentOS==='all'||r['os']===currentOS})).cost});
  charts.pie=new Chart(document.getElementById('chPieChart'),{
    type:'pie',
    data:{labels:CHANNELS,datasets:[{data:pieData,backgroundColor:CH_COLORS}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{title:{display:true,text:'本周消耗占比'}}}
  });
}

function render(){
  console.log('render called, currentOS:', currentOS);
  var controls=document.getElementById('controls');

  // 只保留OS平台选择器
  var h=renderOsTabs();
  controls.innerHTML=h;

  // OS平台点击
  document.querySelectorAll('[data-os]').forEach(function(el){
    el.addEventListener('click',function(){
      currentOS=this.dataset.os;
      console.log('OS clicked:', currentOS);
      document.querySelectorAll('[data-os]').forEach(function(e){e.classList.remove('active')});
      this.classList.add('active');
      renderApp();
    });
  });

  renderApp();
}

document.addEventListener('DOMContentLoaded',function(){
  try{
    var rows=parseCSV(CSV_DATA);
    var prev=parseCSV(CSV_DATA_PREV);
    if(!rows||rows.length===0){document.getElementById('app').innerHTML='<div class="loading">无数据</div>';return}
    allRows=rows;
    prevRows=prev;
    byType={};byTypePrev={};
    CONV_TYPES.forEach(function(t){
      if(t.key==='all'){byType[t.key]=allRows;byTypePrev[t.key]=prevRows;return;}
      byType[t.key]=allRows.filter(function(r){return r['转化类型']===t.key});
      byTypePrev[t.key]=prevRows.filter(function(r){return r['转化类型']===t.key});
    });
    render();
  }catch(e){document.getElementById('app').innerHTML='<div class="loading">解析失败: '+e.message+'</div>';console.error(e)}
});
<\/script>
</body>
</html>'''

with open(OUT_PATH, 'w', encoding='utf-8') as out:
    full = HTML_BEFORE + csv_escaped + HTML_AFTER
    full = full.replace('<\\/script>', '</script>')
    out.write(full)

print(f"Done! Output: {OUT_PATH}")
print(f"File size: {os.path.getsize(OUT_PATH)/1024:.0f} KB")
