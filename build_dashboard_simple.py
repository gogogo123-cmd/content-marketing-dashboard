#!/usr/bin/env python3
"""生成多周数据看板 - 支持周次选择和环比"""
import os
import csv
import glob
import re

PROJECT_DIR = os.path.expanduser('~/Downloads/内容营销数据看板')
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
OUT_PATH = os.path.join(PROJECT_DIR, '内容营销数据看板.html')

# 读取主数据列头（从第一个CSV文件）
def get_main_header():
    files = glob.glob(os.path.join(DATA_DIR, '*.csv'))
    if files:
        with open(files[0], 'r', encoding='utf-8-sig') as f:
            return list(csv.reader(f))[0]
    return []

main_hdr = get_main_header()

def get_all_weeks():
    """获取所有周数据文件，按日期排序"""
    files = glob.glob(os.path.join(DATA_DIR, '*.csv'))
    weeks = []
    for f in files:
        basename = os.path.basename(f)
        match = re.match(r'(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})\.csv', basename)
        if match:
            start_date = match.group(1)
            end_date = match.group(2)
            weeks.append({
                'start': start_date,
                'end': end_date,
                'path': f,
                'label': f"{start_date.replace('-', '/')} - {end_date.replace('-', '/')}"
            })
    weeks.sort(key=lambda x: x['start'])
    return weeks

def read_csv_escaped(path):
    """读取CSV并转义为JS字符串"""
    with open(path, 'r', encoding='utf-8-sig') as f:
        raw = f.read()
    return raw.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')

# 获取所有周数据
weeks = get_all_weeks()
if not weeks:
    print("错误: data文件夹中没有找到数据文件")
    print(f"请确保 {DATA_DIR} 文件夹中有格式为 YYYY-MM-DD_YYYY-MM-DD.csv 的文件")
    exit(1)

print(f"找到 {len(weeks)} 周数据:")
for w in weeks:
    print(f"  - {w['label']}")

# 生成周数据的JS数组
weeks_js = "const WEEKS_DATA = [\n"
for i, w in enumerate(weeks):
    csv_data = read_csv_escaped(w['path'])
    weeks_js += f"  {{start:'{w['start']}',end:'{w['end']}',label:'{w['label']}',data:`{csv_data}`}}"
    if i < len(weeks) - 1:
        weeks_js += ","
    weeks_js += "\n"
weeks_js += "];\n"
weeks_js += "var currentWeekIndex = WEEKS_DATA.length - 1;\n"

# 现在直接从/tmp/build_dashboard.py读取并生成
exec(open('/tmp/build_dashboard.py').read().replace(
    "CSV_PATH = os.path.expanduser('~/Downloads/小说_bi实时分计划_自定义聚合数据表1776151765606.csv')",
    f"CSV_PATH = '{weeks[-1]['path']}'"
).replace(
    "CSV_PREV_PATH = os.path.expanduser('~/Downloads/小说_bi实时分计划_自定义聚合数据表1776167665040.csv')",
    f"CSV_PREV_PATH = '{weeks[-2]['path'] if len(weeks) > 1 else weeks[-1]['path']}'"
).replace(
    "OUT_PATH = os.path.expanduser('~/Downloads/投放数据看板.html')",
    f"OUT_PATH = '{OUT_PATH}'"
))

print(f"\n✓ 看板生成完成: {OUT_PATH}")
print(f"✓ 文件大小: {os.path.getsize(OUT_PATH)/1024:.0f} KB")
print(f"✓ 包含 {len(weeks)} 周数据")
