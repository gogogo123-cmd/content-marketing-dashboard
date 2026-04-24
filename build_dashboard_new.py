#!/usr/bin/env python3
"""生成多周数据看板 - 支持周次选择和环比"""
import os
import csv
import glob
import re

PROJECT_DIR = os.path.expanduser('~/Downloads/内容营销数据看板')
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
OUT_PATH = os.path.join(PROJECT_DIR, '内容营销数据看板.html')
TEMPLATE_PATH = '/tmp/build_dashboard.py'

# 聚星数据映射
JX_MAP = {
    '消耗': '当天消耗金额',
    '曝光数': '报表今日曝光数',
    '关键行为数': '报表今日行为数',
    '激活数': '激活数',
    '激励视频cpm': '激励视频cpm',
    '人均激励视频数': '人均激励视频数',
    '激活成本': '激活成本',
    '修复真实1日roi_规则赔付': '助推的预估roi',
    '预估ltv': '预估ltv',
}

def get_all_weeks():
    files = glob.glob(os.path.join(DATA_DIR, '*.csv'))
    weeks = {}
    # 第一遍：只处理投放主数据CSV，建立周条目
    for f in files:
        basename = os.path.basename(f)
        match = re.match(r'(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})\.csv', basename)
        if match:
            key = (match.group(1), match.group(2))
            if key not in weeks:
                weeks[key] = {'start': match.group(1), 'end': match.group(2), 'path': f,
                              'label': f"{match.group(1).replace('-', '/')} - {match.group(2).replace('-', '/')}",
                              'material_path': None, 'infra_path': None}
    # 第二遍：附加素材/基建CSV到已有周
    for f in files:
        basename = os.path.basename(f)
        match2 = re.match(r'(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})_素材\.csv', basename)
        if match2:
            key = (match2.group(1), match2.group(2))
            if key in weeks:
                weeks[key]['material_path'] = f
            else:
                # 无对应投放数据的周，也创建条目（仅素材分析可用）
                weeks[key] = {'start': match2.group(1), 'end': match2.group(2), 'path': None,
                              'label': f"{match2.group(1).replace('-', '/')} - {match2.group(2).replace('-', '/')}",
                              'material_path': f, 'infra_path': None}
        match3 = re.match(r'(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})_基建\.csv', basename)
        if match3:
            key = (match3.group(1), match3.group(2))
            if key in weeks:
                weeks[key]['infra_path'] = f
            elif key in weeks:
                pass
            else:
                weeks[key] = {'start': match3.group(1), 'end': match3.group(2), 'path': None,
                              'label': f"{match3.group(1).replace('-', '/')} - {match3.group(2).replace('-', '/')}",
                              'material_path': None, 'infra_path': f}
    result = list(weeks.values())
    result.sort(key=lambda x: x['start'])
    return result

def esc_csv(s):
    return s.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')

# 读取模板
with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
    template = f.read()

# === 提取模板的两个部分 ===
# 模板结构:
#   Line 64:  HTML_BEFORE = r'''<!DOCTYPE html>...
#   Line 253: const CSV_DATA = `'''          ← JS template literal opening
#   Line 255: HTML_AFTER = r'''`;const CSV_DATA_PREV = `''' + csv_prev_escaped + r'''`;
#   Line 257: const CHANNELS=[...            ← JS code continues
#   Line 1886: </html>'''                    ← end of last raw string
#
# 我们需要:
#   Part A: HTML从<!DOCTYPE>到<script>\n (不含CSV_DATA赋值)
#   Part B: 从const CHANNELS=到</html> (JS代码+HTML结尾)

# Part A: 找到 HTML_BEFORE 内容，截取到 <script>\n
idx_before_start = template.find("HTML_BEFORE = r'''") + len("HTML_BEFORE = r'''")
idx_script_tag = template.find("<script>\n", idx_before_start)
html_part_a = template[idx_before_start:idx_script_tag + len("<script>\n")]

# Part B: 找到 const CSV_DATA = 的位置（我们要在这之前插入密码验证JS）
idx_csv_data = template.find("const CSV_DATA = `'''", idx_script_tag)
# 提取密码验证JS（从<script>后到CSV_DATA之前）
password_js = template[idx_script_tag + len("<script>\n"):idx_csv_data]
# 找到 const CHANNELS= 到 </html>
idx_channels = template.find("\nconst CHANNELS=", idx_csv_data)
if idx_channels == -1:
    idx_channels = template.find("\n\nconst CHANNELS=", idx_csv_data)
# 找到最后的 </html>
idx_html_end = template.rfind("</html>")
js_rest = template[idx_channels:idx_html_end + len("</html>")]

# 直接从模板中的 merge_juxing 函数来读取数据
def merge_juxing_raw(main_csv_path, juxing_csv_path, main_hdr):
    with open(main_csv_path, 'r', encoding='utf-8-sig') as f:
        main_raw = f.read()
    with open(juxing_csv_path, 'r', encoding='utf-8-sig') as f:
        jx = list(csv.reader(f))
    jx_hdr = jx[0]
    jx_idx = {h: i for i, h in enumerate(jx_hdr)}
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

# 读取CSV文件
weeks = get_all_weeks()
if not weeks:
    print("错误: data文件夹中没有找到数据文件"); exit(1)

print(f"找到 {len(weeks)} 周数据:")
for w in weeks:
    print(f"  - {w['label']}")

# 读取表头
first_with_path = next((w for w in weeks if w['path']), None)
if not first_with_path:
    print("警告: 没有找到投放数据CSV，仅处理素材/基建数据")
    main_hdr = []
else:
    with open(first_with_path['path'], 'r', encoding='utf-8-sig') as f:
        main_hdr = list(csv.reader(f))[0]

# 生成每周的合并数据
weeks_data = []
for w in weeks:
    # 投放数据
    if w['path']:
        juxing_path = w['path'].replace('.csv', '_juxing.csv')
        if os.path.exists(juxing_path):
            combined = merge_juxing_raw(w['path'], juxing_path, main_hdr)
        else:
            with open(w['path'], 'r', encoding='utf-8-sig') as f:
                combined = f.read()
    else:
        combined = ''
    # 素材数据
    mat_data = ''
    if w.get('material_path') and os.path.exists(w['material_path']):
        with open(w['material_path'], 'r', encoding='utf-8-sig') as f:
            mat_data = f.read()
    # 基建数据
    infra_data = ''
    if w.get('infra_path') and os.path.exists(w['infra_path']):
        with open(w['infra_path'], 'r', encoding='utf-8-sig') as f:
            infra_data = f.read()
    weeks_data.append({
        'start': w['start'],
        'end': w['end'],
        'label': w['label'],
        'data': esc_csv(combined),
        'materialData': esc_csv(mat_data),
        'infraData': esc_csv(infra_data),
    })

# 3. 生成周数据JS代码
weeks_js = "const WEEKS_DATA = [\n"
for i, w in enumerate(weeks_data):
    weeks_js += f"  {{start:'{w['start']}',end:'{w['end']}',label:'{w['label']}',data:`{w['data']}`,materialData:`{w['materialData']}`,infraData:`{w['infraData']}`}}"
    if i < len(weeks_data) - 1:
        weeks_js += ","
    weeks_js += "\n"
weeks_js += "];\n"

# 默认选中最新一周有投放数据的周次
last_delivery_idx = len(weeks_data) - 1
for i in range(len(weeks_data) - 1, -1, -1):
    if weeks_data[i]['data']:
        last_delivery_idx = i
        break
weeks_js += f"var currentWeekIndex = {last_delivery_idx};\n"

# 4. 构建 html_before（添加周选择器样式和HTML）
html_before_final = html_part_a

# 添加周选择器CSS
week_css = '''
.week-selector{background:var(--card);border-radius:12px;padding:16px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,.06);border:1px solid var(--border)}
.week-selector .label{font-size:13px;color:var(--text2);margin-bottom:8px;font-weight:600}
.week-buttons{display:flex;gap:8px;flex-wrap:wrap}
.week-btn{padding:8px 16px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;border:2px solid var(--border);background:var(--card);color:var(--text2);transition:all .2s}
.week-btn:hover{border-color:var(--accent);color:var(--accent)}
.week-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
'''

# 插入CSS（在 </style> 之前）
html_before_final = html_before_final.replace('</style>', week_css + '</style>')

# 添加周选择器HTML（投放数据页，含上传按钮）
html_before_final = html_before_final.replace(
    '<div id="controls"></div>',
    '''<div class="week-selector" id="deliveryWeekSelector">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
<div class="label" style="margin-bottom:0">选择周次</div>
<button class="upl-btn" onclick="openUploadModal()" style="font-size:13px;padding:5px 12px;border-radius:8px;border:2px solid var(--border);background:var(--card);cursor:pointer;color:var(--text2);font-weight:600">+ 上传投放数据</button>
</div>
<div class="week-buttons" id="weekButtons"></div>
</div>
<div id="controls"></div>'''
)

# 添加素材分析页独立周选择器（含上传按钮）
html_before_final = html_before_final.replace(
    '<div id="materialApp"',
    '''<div class="week-selector" id="matWeekSelector" style="display:none">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
<div class="label" style="margin-bottom:0">选择周次</div>
<button class="upl-btn" onclick="openMatUploadModal()" style="font-size:13px;padding:5px 12px;border-radius:8px;border:2px solid var(--border);background:var(--card);cursor:pointer;color:var(--text2);font-weight:600">+ 上传素材数据</button>
</div>
<div class="week-buttons" id="matWeekButtons"></div>
</div>
<div id="materialApp"'''
)

# 5. 构建 html_after
# 密码验证JS + weeks_js + CSV_DATA赋值 + JS代码(从const CHANNELS=开始) + </html>
html_after_final = password_js + weeks_js + "const CSV_DATA = WEEKS_DATA[currentWeekIndex].data;\nconst CSV_DATA_PREV = currentWeekIndex > 0 ? WEEKS_DATA[currentWeekIndex-1].data : '';\n"

# 7. 添加周选择器JS函数（在 DOMContentLoaded 之前）
week_js = '''
function updateSubtitle(){
  var el=document.getElementById('dashSubtitle');
  if(!el)return;
  var w=WEEKS_DATA[currentWeekIndex];
  var prev=currentWeekIndex>0?WEEKS_DATA[currentWeekIndex-1]:null;
  var txt='本周：'+w.label;
  if(prev)txt+=' ｜ 上周：'+prev.label;
  txt+=' ｜ 渠道：头条 / 小红书 / 快手 / 聚星';
  el.textContent=txt;
  document.title='内容营销数据看板（'+w.label+'）';
}

function renderWeekButtons(){
  var container = document.getElementById('weekButtons');
  if(!container)return;
  var h = '';
  WEEKS_DATA.forEach(function(w, i){
    var active = i === currentWeekIndex ? ' active' : '';
    h += '<div class="week-btn' + active + '" data-week-idx="' + i + '">' + w.label + '</div>';
  });
  container.innerHTML = h;
  document.querySelectorAll('.week-btn').forEach(function(btn){
    btn.addEventListener('click', function(){
      currentWeekIndex = parseInt(this.dataset.weekIdx);
      document.querySelectorAll('.week-btn').forEach(function(b){b.classList.remove('active')});
      this.classList.add('active');
      loadWeekData();
    });
  });
}

function loadWeekData(){
  updateSubtitle();
  var rows = parseCSV(WEEKS_DATA[currentWeekIndex].data);
  var prev = currentWeekIndex > 0 ? parseCSV(WEEKS_DATA[currentWeekIndex - 1].data) : [];
  if(!rows || rows.length === 0){
    document.getElementById('app').innerHTML = '<div class="loading">无数据</div>';
  } else {
    allRows = rows;
    prevRows = prev;
    byType = {};
    byTypePrev = {};
    CONV_TYPES.forEach(function(t){
      if(t.key === 'all'){
        byType[t.key] = allRows;
        byTypePrev[t.key] = prevRows;
        return;
      }
      byType[t.key] = allRows.filter(function(r){return r['转化类型'] === t.key});
      byTypePrev[t.key] = prevRows.filter(function(r){return r['转化类型'] === t.key});
    });
    render();
  }
}

'''

# 6. 在 DOMContentLoaded 之前插入周选择器JS
html_after_final += js_rest.replace(
    "document.addEventListener('DOMContentLoaded',function(){",
    week_js + "document.addEventListener('DOMContentLoaded',function(){\n  renderWeekButtons();\n  updateSubtitle();\n  initMatWeekIndex();\n  renderMatWeekButtons();\n  initPageTabs();\n  initSidebar();"
)

# 7. 合并生成最终HTML
final_html = html_before_final + html_after_final

# 写入文件
with open(OUT_PATH, 'w', encoding='utf-8') as out:
    out.write(final_html.replace('<\\/script>', '</script>'))

size = os.path.getsize(OUT_PATH) / 1024
print(f"\n✓ 看板生成完成: {OUT_PATH}")
print(f"✓ 文件大小: {size:.0f} KB")
print(f"✓ 包含 {len(weeks)} 周数据")
