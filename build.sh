#!/usr/bin/env bash
# 完整重建：抓取 → 解析 → 清理 → 共識 → 指數 → 組頁面
# 產物：dist/index.html（單一自含檔案，無外部相依，可直接丟任何靜態主機）
set -euo pipefail
cd "$(dirname "$0")"

echo "[1/7] 抓取原始頁面（已存在者略過）"
python3 pipeline/fetch.py

echo "[2/7] 解析歷史行情"
python3 pipeline/parse_history.py | head -1

echo "[3/7] 解析當期四來源"
python3 pipeline/parse_current.py | tail -1

echo "[4/7] 共識價與信心等級"
python3 pipeline/consensus.py | head -3

echo "[5/7] 指數 · 球場 · 擊球費"
python3 pipeline/build_index.py  | tail -3
python3 pipeline/build_courses.py | head -2
python3 pipeline/parse_fees.py    | tail -1
python3 pipeline/build_site_data.py | head -1
python3 pipeline/assemble.py

echo "[6/7] 哨兵檢查"
python3 pipeline/sanity.py

echo "[7/7] 產生 dist/index.html"
mkdir -p dist
python3 - <<'PY'
tpl = open("site/index.html", encoding="utf-8").read()
data = open("data/site.json", encoding="utf-8").read().replace("</", "<\\/")
open("dist/index.html", "w", encoding="utf-8").write(tpl.replace("__DATA__", data))
import os
print(f"    dist/index.html  {os.path.getsize('dist/index.html')/1024/1024:.2f} MB")
PY
echo "完成。"
