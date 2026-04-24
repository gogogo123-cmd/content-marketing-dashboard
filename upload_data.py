#!/usr/bin/env python3
"""数据上传脚本 - 每周更新数据"""
import os
import sys
import shutil
from datetime import datetime

PROJECT_DIR = os.path.expanduser('~/Downloads/内容营销数据看板')
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
BACKUP_DIR = os.path.join(PROJECT_DIR, 'backups')
DASHBOARD_PATH = os.path.join(PROJECT_DIR, '内容营销数据看板.html')

def main():
    if len(sys.argv) < 4:
        print("用法: python3 upload_data.py <主数据CSV> <聚星数据CSV> <开始日期> <结束日期>")
        print("示例: python3 upload_data.py ~/Downloads/小说_xxx.csv ~/Downloads/聚星_xxx.csv 2026-04-10 2026-04-16")
        sys.exit(1)

    main_csv = os.path.expanduser(sys.argv[1])
    juxing_csv = os.path.expanduser(sys.argv[2])
    start_date = sys.argv[3]  # 格式: 2026-04-10
    end_date = sys.argv[4]    # 格式: 2026-04-16

    if not os.path.exists(main_csv):
        print(f"错误: 主数据文件不存在 {main_csv}")
        sys.exit(1)

    # 1. 备份当前看板
    if os.path.exists(DASHBOARD_PATH):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(BACKUP_DIR, f'看板_{timestamp}.html')
        shutil.copy2(DASHBOARD_PATH, backup_path)
        print(f"✓ 已备份当前看板到: {backup_path}")

    # 2. 复制数据到data文件夹
    week_filename = f"{start_date}_{end_date}.csv"
    main_dest = os.path.join(DATA_DIR, week_filename)
    juxing_dest = os.path.join(DATA_DIR, f"{start_date}_{end_date}_juxing.csv")

    shutil.copy2(main_csv, main_dest)
    print(f"✓ 已保存主数据: {main_dest}")

    if os.path.exists(juxing_csv):
        shutil.copy2(juxing_csv, juxing_dest)
        print(f"✓ 已保存聚星数据: {juxing_dest}")

    # 3. 重新生成看板
    print("✓ 正在生成新看板...")
    os.system(f'cd {PROJECT_DIR} && python3 build_dashboard.py')

    print(f"\n✓ 完成！新看板已生成: {DASHBOARD_PATH}")

if __name__ == '__main__':
    main()
