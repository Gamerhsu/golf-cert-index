# -*- coding: utf-8 -*-
"""TGMI 台灣球證指數：等權重、鏈式連接（chain-linking）
   鏈式連接的理由：涵蓋球場數由民國76年約10檔成長至115年約70檔，
   直接跨期比較會混入成分變動；每期僅比較同時存在於 t-1 與 t 的標的。"""
import json, sys, os, math, statistics, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import canon_course, canon_class

from common import REGION

from clean import build_series, clean
series = build_series()
corrections = clean(series)          # 先修來源錯字，再算指數
print(f"已修正來源錯字 {len(corrections)} 筆")

months=sorted({m for s in series.values() for m in s})
print(f"標的 {len(series)} 檔 · 月份 {len(months)} 期 "
      f"({months[0]//12}/{months[0]%12 or 12} – {months[-1]//12}/{months[-1]%12 or 12})")

def chain(keys, min_overlap=5):
    vals=[]; idx=100.0; used=[]
    for i,m in enumerate(months):
        if i==0: vals.append(idx); used.append(0); continue
        p=months[i-1]
        rel=[series[k][m]/series[k][p] for k in keys
             if m in series[k] and p in series[k] and series[k][p]>0]
        if len(rel)>=min_overlap:
            # 幾何平均：價格指數的標準做法，避免算術平均的向上偏誤
            idx*= math.exp(sum(math.log(x) for x in rel)/len(rel))
        vals.append(idx); used.append(len(rel))
    return vals, used

allkeys=list(series)
main,used = chain(allkeys)

# 分區
sub={}
for reg in sorted(set(REGION.values())):
    ks=[k for k in allkeys if REGION.get(k[0])==reg]
    if len(ks)>=4:
        v,_=chain(ks, min_overlap=3); sub[reg]=v

# 分價格帶（以民國115年最後報價分層）
last={k:max(s.items())[1] for k,s in series.items() if s}
cur={k:v for k,v in last.items() if max(series[k])>=2025*12}
tiers={"千萬級 (≥1000萬)":[k for k,v in cur.items() if v>=1000],
       "百萬級 (100–1000萬)":[k for k,v in cur.items() if 100<=v<1000],
       "百萬以下 (<100萬)":[k for k,v in cur.items() if v<100]}
tier_idx={}
for name,ks in tiers.items():
    if len(ks)>=4:
        v,_=chain(ks,min_overlap=3); tier_idx[name]=v

lbl=[f"{m//12}-{m%12 or 12:02d}" for m in months]
json.dump(dict(months=lbl, main=main, overlap=used, region=sub, tier=tier_idx,
               corrections=corrections,
               tier_members={k:len(v) for k,v in tiers.items()}),
          open("data/index.json","w",encoding="utf-8"), ensure_ascii=False)

# 個別標的序列（供單檔頁）
ser={f"{c}|{k}":{lbl[months.index(m)]:round(v,1) for m,v in sorted(s.items())}
     for (c,k),s in series.items()}
json.dump(ser, open("data/series.json","w",encoding="utf-8"), ensure_ascii=False)

print(f"\nTGMI 基期 {lbl[0]} = 100")
for y in (1987,1990,1993,1997,2001,2003,2008,2010,2016,2020,2023,2025,2026):
    for i,l in enumerate(lbl):
        if l.startswith(f"{y}-01") or (y==2026 and l.startswith("2026-08")):
            print(f"  {l}  指數 {main[i]:>9,.1f}   （當期可比標的 {used[i]:>2} 檔）"); break
pk=max(range(len(main)),key=lambda i:main[i]); tr=min(range(pk,len(main)),key=lambda i:main[i])
print(f"\n  歷史高點 {lbl[pk]}  {main[pk]:,.1f}")
print(f"  其後低點 {lbl[tr]}  {main[tr]:,.1f}   自高點 {(main[tr]/main[pk]-1)*100:+.1f}%")
print(f"  最新     {lbl[-1]}  {main[-1]:,.1f}   自高點 {(main[-1]/main[pk]-1)*100:+.1f}%")
print(f"\n分區指數: {list(sub)}")
print(f"分價格帶: {[(k,len(v)) for k,v in tiers.items()]}")
