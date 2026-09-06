# -*- coding: utf-8 -*-
"""球場瀏覽器資料：分區 → 球場 → 類別，含月度序列與年度彙總。
   涵蓋所有具歷史序列的標的（含已停業球場），不限於目前仍有報價者。"""
import json, sys, statistics, collections
sys.path.insert(0,'pipeline')
from common import REGION
from clean import build_series, clean

S = build_series(); clean(S)                    # 同一套清理規則
cons = {(c["course"],c["klass"]): c for c in json.load(open("data/consensus.json",encoding="utf-8"))}
fees = json.load(open("data/green_fees.json",encoding="utf-8"))

def lbl(m): return f"{(m-1)//12}-{(m-1)%12+1:02d}"

def annual(pts):
    """年度彙總：年初、年末、最高、最低、均價、年變動"""
    byy=collections.defaultdict(list)
    for ym,v in pts: byy[int(ym[:4])].append((ym,v))
    rows=[]; prev=None
    for y in sorted(byy):
        d=sorted(byy[y]); vs=[x[1] for x in d]
        r=dict(year=y, jan=d[0][1], dec=d[-1][1], n=len(d),
               lo=min(vs), hi=max(vs), avg=round(statistics.mean(vs),1),
               first_m=d[0][0][5:], last_m=d[-1][0][5:])
        r["yoy"]=round((r["dec"]/prev-1)*100,1) if prev else None
        prev=r["dec"]; rows.append(r)
    return rows

courses=collections.defaultdict(lambda: collections.defaultdict(dict))
meta={}
for (course,klass),s in S.items():
    pts=[(lbl(m),v) for m,v in sorted(s.items())]
    if len(pts)<12: continue
    reg=REGION.get(course,"其他")
    c=cons.get((course,klass))
    courses[reg][course][klass]=dict(
        series={k:round(v,1) for k,v in pts},
        annual=annual(pts),
        first=pts[0][0], last=pts[-1][0], n=len(pts),
        cur=(c or {}).get("mid"), conf=(c or {}).get("confidence"),
        fee=(c or {}).get("transfer_fee"), dues=(c or {}).get("annual_dues"),
        active=pts[-1][0] >= "2026-01",
    )
cur_status={}
for (c,k),v in cons.items():
    if v.get("status"): cur_status.setdefault(c, v["status"])
    if v.get("mid") is not None: cur_status[c]="有報價"
for reg,cs in courses.items():
    for course,ks in cs.items():
        last=max(v["last"] for v in ks.values())
        st=cur_status.get(course)
        meta[course]=dict(region=reg, last=last, active=last>="2026-01",
                          status=st or "無當期報價",
                          gf=fees.get(course), n_class=len(ks))

out=dict(regions={r:sorted(cs) for r,cs in courses.items()},
         data={r:{c:k for c,k in cs.items()} for r,cs in courses.items()},
         meta=meta)
json.dump(out, open("data/courses.json","w",encoding="utf-8"), ensure_ascii=False, separators=(',',':'))
import os
tot=sum(len(k) for cs in courses.values() for k in cs.values())
print(f"courses.json {os.path.getsize('data/courses.json')/1024:.0f} KB")
print(f"區域 {len(courses)} · 球場 {len(meta)} · 標的 {tot}")
for r in sorted(courses):
    act=sum(1 for c in courses[r] if meta[c]['active'])
    print(f"  {r:<8} 球場 {len(courses[r]):>2}（現有報價 {act:>2}，已停 {len(courses[r])-act:>2}）")
print("\n已停止交易但有完整歷史的球場：")
for c,m in sorted(meta.items(), key=lambda x:x[1]['last']):
    if not m['active']: print(f"  {c:<14} {m['region']:<6} 資料至 {m['last']}")
