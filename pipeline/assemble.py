# -*- coding: utf-8 -*-
"""把各階段產物合併成單一 site.json"""
import json, sys
sys.path.insert(0,'pipeline'); from common import REGION

p    = json.load(open("data/site.json",  encoding="utf-8"))
p["courses"] = json.load(open("data/courses.json", encoding="utf-8"))
fees = json.load(open("data/green_fees.json", encoding="utf-8"))
cons = json.load(open("data/consensus.json",  encoding="utf-8"))

best={}
for c in cons:
    if c.get("mid") is None: continue
    if c["course"] not in best or c["mid"] < best[c["course"]]["mid"]: best[c["course"]]=c
rows=[]
for course,f in fees.items():
    r=dict(course=course, region=REGION.get(course,"其他"),
           mwd=f.get("member_wd"), mwe=f.get("member_we"),
           gwd=f.get("guest_wd"),  gwe=f.get("guest_we"),
           n=f.get("n_sources"), flag=f.get("fee_flag"), spread_gwe=f.get("guest_we_spread"))
    r["gap_wd"]=(r["gwd"]-r["mwd"]) if r["gwd"] and r["mwd"] else None
    r["gap_we"]=(r["gwe"]-r["mwe"]) if r["gwe"] and r["mwe"] else None
    b=best.get(course)
    if b: r.update(cert=b["mid"], cert_klass=b["klass"])
    rows.append(r)
p["fees"]=sorted(rows, key=lambda r:(r["region"], r["course"]))
json.dump(p, open("data/site.json","w",encoding="utf-8"), ensure_ascii=False, separators=(',',':'))
print(f"    site.json 已合併：標的 {len(p['items'])} · 球場 {len(p['fees'])}")
