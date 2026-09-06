# -*- coding: utf-8 -*-
"""組合網站資料：共識價 + 歷史序列 + 績效 + 擊球費 + 損益兩平"""
import json, math, statistics, sys
sys.path.insert(0,'pipeline')

cons=json.load(open("data/consensus.json",encoding="utf-8"))
ser=json.load(open("data/series.json",encoding="utf-8"))
idx=json.load(open("data/index.json",encoding="utf-8"))
fees=json.load(open("data/green_fees.json",encoding="utf-8"))

def perf(pts):
    """pts = [(ym, value)] 已排序"""
    if len(pts)<13: return {}
    v=[p[1] for p in pts]; m=[p[0] for p in pts]
    out={}
    def look(back):
        if len(v)<=back: return None
        a,b=v[-1-back],v[-1]
        return ((b/a)**(12/back)-1)*100 if a>0 else None
    out["cagr_1y"]=look(12); out["cagr_5y"]=look(60); out["cagr_10y"]=look(120)
    n=len(v)-1
    out["cagr_all"]=((v[-1]/v[0])**(12/n)-1)*100 if v[0]>0 and n>0 else None
    out["since"]=m[0]; out["months"]=len(v)
    peak=-1e9; mdd=0; pi=0; pair=None
    for i,x in enumerate(v):
        if x>peak: peak=x; pi=i
        if peak>0 and x/peak-1<mdd: mdd=x/peak-1; pair=(m[pi],m[i])
    out["mdd"]=mdd*100; out["mdd_span"]=pair
    r=[math.log(v[i]/v[i-1]) for i in range(1,len(v)) if v[i-1]>0 and v[i]>0]
    out["vol"]=statistics.pstdev(r)*math.sqrt(12)*100 if len(r)>2 else None
    ath=max(range(len(v)),key=lambda i:v[i])
    out["ath"]=v[ath]; out["ath_ym"]=m[ath]; out["from_ath"]=(v[-1]/v[ath]-1)*100
    return out

items=[]
for c in cons:
    key=f"{c['course']}|{c['klass']}"
    s=ser.get(key,{})
    pts=sorted(s.items())
    rec=dict(c); rec["series"]={k:v for k,v in pts}
    rec.update(perf(pts))
    f=fees.get(c["course"])
    if f:
        rec["fee"]=f
        gw, gd = f.get("gap_we"), f.get("gap_wd")
        if c.get("mid") and (gw or gd):
            allin=(c["mid"]+(c.get("transfer_fee") or 0))*10000
            carry=allin*0.025+(c.get("annual_dues") or 0)
            rec["annual_carry"]=round(carry)
            if gw: rec["be_rounds_we"]=round(carry/gw,1)
            if gd: rec["be_rounds_wd"]=round(carry/gd,1)
    items.append(rec)

# 排行：近一年漲幅
rank=[i for i in items if i.get("cagr_1y") is not None and i.get("mid")]
rank.sort(key=lambda x:-x["cagr_1y"])

payload=dict(
  generated="2026-09-06",
  index=idx,
  items=items,
  corrections=json.load(open("data/corrections.json",encoding="utf-8")),
  stats=dict(
    n_items=len(items),
    n_priced=sum(1 for i in items if i.get("mid")),
    n_series=len(ser),
    n_quotes=25376,
    n_fee_courses=sum(1 for v in fees.values() if v.get("gap_we")),
  ))
json.dump(payload, open("data/site.json","w",encoding="utf-8"), ensure_ascii=False, separators=(',',':'))
import os
print(f"site.json  {os.path.getsize('data/site.json')/1024:.0f} KB   標的 {len(items)}")
print("\n近一年漲幅前 8：")
for i in rank[:8]:
    print(f"  {i['course']}·{i['klass']:<6} {i['mid']:>7.0f}萬  1年 {i['cagr_1y']:+6.1f}%  "
          f"5年 {(i.get('cagr_5y') or 0):+6.1f}%  最大回撤 {i.get('mdd',0):>6.1f}%")
print("\n近一年跌幅前 5：")
for i in rank[-5:]:
    print(f"  {i['course']}·{i['klass']:<6} {i['mid']:>7.0f}萬  1年 {i['cagr_1y']:+6.1f}%")
be=[i for i in items if i.get("be_rounds_we")]
print(f"\n可算損益兩平的標的 {len(be)} 檔，門檻最低的 6 檔（最容易靠打球回本）：")
for i in sorted(be,key=lambda x:x["be_rounds_we"])[:6]:
    print(f"  {i['course']}·{i['klass']:<6} 全假日每年 {i['be_rounds_we']:>6.1f} 場打平  "
          f"(投入 {i['all_in']:.0f}萬, 假日價差 {i['fee']['gap_we']} 元)")
print("門檻最高的 4 檔：")
for i in sorted(be,key=lambda x:-x["be_rounds_we"])[:4]:
    print(f"  {i['course']}·{i['klass']:<6} 全假日每年 {i['be_rounds_we']:>6.1f} 場打平  (投入 {i['all_in']:.0f}萬)")
