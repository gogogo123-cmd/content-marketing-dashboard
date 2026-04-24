#!/usr/bin/env python3
"""生成多周数据看板 - 支持周次选择和环比"""
import re
import glob
import os
import csv

PROJECT_DIR = os.path.expanduser('~/Downloads/内容营销数据看板')
DATA_DIR = os.path.join(PROJECT_DIR, 'data')

def esc(s):
    return s.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')

# 读取主数据列头
def get_main_header():
    files = glob.glob(os.path.join(DATA_DIR, '*.csv'))
    for f in files:
        if '_juxing' not in f:
            with open(f, 'r', encoding='utf-8-sig') as fp:
                return list(csv.reader(fp))[0]
    return []

main_hdr = get_main_header()

# 聚星字段映射
JX_MAP = {
    '消耗': '当天消耗金额',
    '曝光数': '报表今日曝光数',
    '激活数': '激活数',
    '激励视频cpm': '激励视频cpm',
    '人均激励视频数': '人均激励视频数',
    '激活成本': '激活成本',
    '修复真实1日roi_规则赔付': '助推的预估roi',
    '预估ltv': '预估ltv',
}

def merge_juxing(main_csv_path, juxing_csv_path):
    """合并主数据和聚星数据"""
    # 读取当前文件的列头（而不是使用全局的 main_hdr）
    with open(main_csv_path, 'r', encoding='utf-8-sig') as f:
        main_raw = f.read()
        f.seek(0)
        current_hdr = list(csv.reader(f))[0]

    try:
        with open(juxing_csv_path, 'r', encoding='utf-8-sig') as f:
            jx = list(csv.reader(f))
        jx_hdr = jx[0]
        jx_idx = {h: i for i, h in enumerate(jx_hdr)}
        jx_map = dict(JX_MAP)
        for col in current_hdr:
            if col in jx_idx and col not in jx_map:
                jx_map[col] = col
        juxing_rows = []
        for row in jx[1:]:
            new_row = [''] * len(current_hdr)
            for col, jx_col in jx_map.items():
                if jx_col in jx_idx and col in current_hdr:
                    new_row[current_hdr.index(col)] = row[jx_idx[jx_col]]
            new_row[current_hdr.index('投放渠道')] = '聚星'
            new_row[current_hdr.index('运营负责人')] = '韩孟伶'
            juxing_rows.append(new_row)
        combined = main_raw.rstrip('\n') + '\n'
        for r in juxing_rows:
            combined += ','.join(r) + '\n'
        print(f"✓ 已合并 {len(juxing_rows)} 行聚星数据")
        return combined
    except Exception as e:
        print(f"⚠ 合并聚星数据失败: {e}")
        import traceback
        traceback.print_exc()
        return main_raw

# 1. 读取项目内模板
TEMPLATE_PATH = os.path.join(PROJECT_DIR, 'template.html')
with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
    html = f.read()

# 2. 读取所有周数据
files = glob.glob(os.path.join(DATA_DIR, '*.csv'))
weeks = []
for f in files:
    if '_juxing' in f or '_素材' in f or '_基建' in f:
        continue
    basename = os.path.basename(f)
    match = re.match(r'(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})\.csv', basename)
    if match:
        start_date = match.group(1)
        end_date = match.group(2)
        juxing_path = os.path.join(DATA_DIR, f'{start_date}_{end_date}_juxing.csv')
        juxing_exists = os.path.exists(juxing_path)
        combined = merge_juxing(f, juxing_path if juxing_exists else None)

        # 读取素材和基建数据
        material_path = os.path.join(DATA_DIR, f'{start_date}_{end_date}_素材.csv')
        infra_path = os.path.join(DATA_DIR, f'{start_date}_{end_date}_基建.csv')
        material_data = ''
        infra_data = ''

        if os.path.exists(material_path):
            with open(material_path, 'r', encoding='utf-8-sig') as mf:
                material_data = esc(mf.read())

        if os.path.exists(infra_path):
            with open(infra_path, 'r', encoding='utf-8-sig') as inf:
                infra_data = esc(inf.read())

        week_obj = {
            'start': start_date,
            'end': end_date,
            'label': f"{start_date.replace('-', '/')} - {end_date.replace('-', '/')}",
            'data': esc(combined)
        }

        if material_data:
            week_obj['materialData'] = material_data
        if infra_data:
            week_obj['infraData'] = infra_data

        weeks.append(week_obj)

weeks.sort(key=lambda x: x['start'])
print(f"找到 {len(weeks)} 周数据:")
for w in weeks:
    print(f"  - {w['label']}")

# 3. 生成WEEKS_DATA
weeks_js = "const WEEKS_DATA = [\n"
for i, w in enumerate(weeks):
    weeks_js += f"  {{start:'{w['start']}',end:'{w['end']}',label:'{w['label']}',data:`{w['data']}`"
    if 'materialData' in w and w['materialData']:
        weeks_js += f",materialData:`{w['materialData']}`"
    if 'infraData' in w and w['infraData']:
        weeks_js += f",infraData:`{w['infraData']}`"
    weeks_js += "}"
    if i < len(weeks) - 1:
        weeks_js += ","
    weeks_js += "\n"
weeks_js += "];\nvar currentWeekIndex = WEEKS_DATA.length - 1;\n"

# 5. 添加周选择器样式
html = html.replace(
    '.type-all{background:#666}',
    '.type-all{background:#666}\n.week-selector{background:var(--card);border-radius:12px;padding:16px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,.06);border:1px solid var(--border)}\n.week-selector .label{font-size:13px;color:var(--text2);margin-bottom:8px;font-weight:600}\n.week-buttons{display:flex;gap:8px;flex-wrap:wrap}\n.week-btn{padding:8px 16px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;border:2px solid var(--border);background:var(--card);color:var(--text2);transition:all .2s}\n.week-btn:hover{border-color:var(--accent);color:var(--accent)}\n.week-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}',
    1
)

# 6. 添加周选择器HTML
html = html.replace(
    '<div id="controls"></div>',
    '<div class="week-selector"><div class="label">选择周次</div><div class="week-buttons" id="weekButtons"></div></div>\n<div id="controls"></div>',
    1
)

# 7. 替换模板中的WEEKS_DATA
html = re.sub(
    r'const WEEKS_DATA = \[.*?\];',
    weeks_js.rstrip('\n'),
    html,
    count=1,
    flags=re.DOTALL
)

# 8. 删除CSV_DATA和CSV_DATA_PREV定义
html = re.sub(r'const CSV_DATA = `[^`]*`;', '', html, count=1)
html = re.sub(r'const CSV_DATA_PREV = `[^`]*`;', '', html, count=1)

# 9. 替换DOMContentLoaded
orig_dom = """document.addEventListener('DOMContentLoaded',function(){
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
});"""

# 从localStorage加载上传的数据
upload_merge_js = """// 合并localStorage中的上传数据到WEEKS_DATA
function mergeUploadedWeeks(){
  try{
    var uploaded=JSON.parse(localStorage.getItem('content_mkt_uploaded_weeks')||'[]');
    uploaded.forEach(function(w){
      var exists=WEEKS_DATA.some(function(d){return d.start===w.start&&d.end===w.end});
      if(!exists){
        WEEKS_DATA.push({start:w.start,end:w.end,label:w.start.replace(/-/g,'/')+' - '+w.end.replace(/-/g,'/'),data:w.data,uploaded:true});
      }
    });
    WEEKS_DATA.sort(function(a,b){return a.start.localeCompare(b.start)});
  }catch(e){console.log('mergeUploadedWeeks error:',e)}
}
function renderWeekButtons(){
  mergeUploadedWeeks();
  var h='';
  WEEKS_DATA.forEach(function(w,i){
    var tag=w.uploaded?' <span style="font-size:10px;color:#f77f00">↑</span>':'';
    h+='<div class="week-btn'+(i===currentWeekIndex?' active':'')+'" data-week-idx="'+i+'">'+w.label+tag+'</div>';
  });
  document.getElementById('weekButtons').innerHTML=h;
  document.querySelectorAll('.week-btn').forEach(function(btn){
    btn.addEventListener('click',function(){
      currentWeekIndex=parseInt(this.dataset.weekIdx);
      document.querySelectorAll('.week-btn').forEach(function(b){b.classList.remove('active')});
      this.classList.add('active');
      loadWeekData();
    });
  });
}
function loadWeekData(){
  var week=WEEKS_DATA[currentWeekIndex];
  if(!week)return;
  allRows=parseCSV(week.data);
  prevRows=currentWeekIndex>0?parseCSV(WEEKS_DATA[currentWeekIndex-1].data):[];
  byType={};byTypePrev={};
  CONV_TYPES.forEach(function(t){
    if(t.key==='all'){byType[t.key]=allRows;byTypePrev[t.key]=prevRows;return;}
    byType[t.key]=allRows.filter(function(r){return r['转化类型']===t.key});
    byTypePrev[t.key]=prevRows.filter(function(r){return r['转化类型']===t.key});
  });
  render();
}
document.addEventListener('DOMContentLoaded',function(){
  renderWeekButtons();
  try{
    loadWeekData();
  }catch(e){document.getElementById('app').innerHTML='<div class="loading">解析失败: '+e.message+'</div>';console.error(e)}
});"""

html = html.replace(orig_dom, upload_merge_js)

# 10. 修复script结束标签
html = html.replace('<\\/script>', '</script>')

# 11. 写文件
OUT_PATH = os.path.join(PROJECT_DIR, '内容营销数据看板.html')
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n✓ 看板生成完成: {OUT_PATH}")
print(f"✓ 文件大小: {os.path.getsize(OUT_PATH)/1024:.0f} KB")
print(f"✓ 包含 {len(weeks)} 周数据")
