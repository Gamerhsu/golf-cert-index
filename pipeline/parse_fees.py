# -*- coding: utf-8 -*-
"""擊球費抽取：來賓平/假日取自表格數值列，會員平/假日多藏在備註文字，需另行抽取。
   四源各自抽取後取中位數；覆蓋率與分歧一併輸出。"""
import re, os, sys, json, statistics, collections
sys.path.insert(0,'pipeline'); from common import cells_of, canon_course

BASE="pipeline/raw/current"
def nums(s):
    return [float(x) for x in re.findall(r'\d{3,5}', (s or '').replace(',',''))]

def member_from_text(t):
    """從備註抽『會員平日1750﹑假日1950』這類寫法"""
    t=(t or '').replace(',','')
    wd=we=None
    m=re.search(r'會員[^。\n]{0,6}?平日\s*(\d{3,5})', t)
    if m: wd=float(m.group(1))
    m=re.search(r'會員[^。\n]{0,6}?假日\s*(\d{3,5})', t)
    if m: we=float(m.group(1))
    if we is None:
        m=re.search(r'平日\s*(\d{3,5})\s*[﹑、,，]\s*假日\s*(\d{3,5})', t)
        if m: wd,we=float(m.group(1)),float(m.group(2))
    return wd,we

def generic(fn, enc, guest_slots=(0,1)):
    src=open(f"{BASE}/{fn}","rb").read().decode(enc,errors="replace")
    rows=[cells_of(r) for r in re.findall(r'(?is)<tr\b[^>]*>(.*?)</tr>', src)]
    out={}
    for i,c in enumerate(rows):
        if not c or '平日' not in ' '.join(c) or '假日' not in ' '.join(c): continue
        name=c[0]
        if not name or '球' in name[:2] and '場' in name[:3]: continue
        name=re.sub(r'\s*\d[\d\-#\s]{6,}.*$','',name).strip()
        if not name or len(name)>14: continue
        vals=[]; note=''
        for j in (i+1,i+2):
            if j<len(rows):
                jc=rows[j]
                if jc and ('備註' in jc[0] or '優惠' in jc[0]): note=' '.join(jc)
                else: vals += nums(' '.join(jc))
        if len(vals)<2: continue
        mwd,mwe = member_from_text(note)
        # 表頭列自身也可能含會員價（單一數字欄）
        hdr_single=[x for x in c if re.fullmatch(r'\d{3,5}元?', x or '')]
        if mwd is None and hdr_single: mwd=float(re.sub(r'\D','',hdr_single[0]))
        out[canon_course(name)] = dict(guest_wd=vals[guest_slots[0]], guest_we=vals[guest_slots[1]],
                                       member_wd=mwd, member_we=mwe, note=note[:220])
    return out

def golf168():
    src=open(f"{BASE}/golf168_charge.html","rb").read().decode("big5",errors="replace")
    rows=[cells_of(r) for r in re.findall(r'(?is)<tr\b[^>]*>(.*?)</tr>', src)]
    out={}
    for c in rows:
        if len(c)<7: continue
        if not re.match(r'^[一-鿿（()\s]{2,14}$', c[0] or ''): continue
        if not re.fullmatch(r'\d{1,2}', (c[1] or '').strip()): continue
        g=nums(c[3])+nums(c[4])
        if len(g)<2: continue
        mwd,mwe=member_from_text(c[5])
        if mwd is None:
            mn=nums(c[5])
            if len(mn)>=2: mwd,mwe=mn[0],mn[1]
            elif len(mn)==1: mwd=mn[0]
        out[canon_course(re.sub(r'\s','',c[0]))]=dict(guest_wd=g[0],guest_we=g[1],
                                                      member_wd=mwd,member_we=mwe,note=(c[5] or '')[:120])
    return out

srcs={"ylgolf":generic("ylgolf_charge.html","utf-8"),
      "huifeng":generic("huifeng_charge.html","utf-8"),
      "godao":generic("godao_charge.html","utf-8"),
      "golf168":golf168()}
for k,v in srcs.items(): print(f"{k:<9} 抽出 {len(v):>3} 座球場")

merged={}
for sid,d in srcs.items():
    for course,rec in d.items():
        m=merged.setdefault(course, dict(guest_wd=[],guest_we=[],member_wd=[],member_we=[],srcs=[]))
        for f in ("guest_wd","guest_we","member_wd","member_we"):
            if rec[f]: m[f].append(rec[f])
        m["srcs"].append(sid)
final={}
for c,m in merged.items():
    r={}
    for f in ("guest_wd","guest_we","member_wd","member_we"):
        v=[x for x in m[f] if 300<x<20000]
        r[f]=round(statistics.median(v)) if v else None
        r[f+"_n"]=len(v)
        r[f+"_spread"]=round((max(v)-min(v))/statistics.median(v)*100,1) if len(v)>1 else 0.0
    r["n_sources"]=len(set(m["srcs"]))
    # 驗證：會員價必須低於來賓價，否則判定為抽取失敗（多半誤抓到桿弟費或保證金欄）
    r["fee_flag"]=None
    for a,b in (("member_wd","guest_wd"),("member_we","guest_we")):
        if r[a] and r[b] and r[a] >= r[b]:
            r[a]=None; r["fee_flag"]="會員價抽取失敗，已剔除"
    if r["guest_we"] and r["member_we"]: r["gap_we"]=r["guest_we"]-r["member_we"]
    if r["guest_wd"] and r["member_wd"]: r["gap_wd"]=r["guest_wd"]-r["member_wd"]
    final[c]=r
json.dump(final, open("data/green_fees.json","w",encoding="utf-8"), ensure_ascii=False, indent=0)

full=[c for c,r in final.items() if r.get("gap_we") is not None and r.get("gap_wd") is not None]
print(f"\n合計 {len(final)} 座；四格齊全（可算價差）{len(full)} 座")
sp=[r["guest_we_spread"] for r in final.values() if r["guest_we_spread"]>0]
print(f"來賓假日價 跨源極差率 中位 {statistics.median(sp):.1f}%（球證報價為 3.0%，擊球費分歧明顯較大）")
bad=[c for c,r in final.items() if r.get("fee_flag")]
print(f"抽取失敗已剔除會員價：{len(bad)} 座 {bad}")
print("\n假日價差最大的 10 座：")
for c in sorted(full,key=lambda c:-final[c]["gap_we"])[:10]:
    r=final[c]; print(f"  {c:<14} 會員 {r['member_we']:>5} / 來賓 {r['guest_we']:>5}  價差 {r['gap_we']:>5} 元")
print("\n價差最小的 6 座（買證省不到錢）：")
for c in sorted(full,key=lambda c:final[c]["gap_we"])[:6]:
    r=final[c]; print(f"  {c:<14} 會員 {r['member_we']:>5} / 來賓 {r['guest_we']:>5}  價差 {r['gap_we']:>5} 元")
