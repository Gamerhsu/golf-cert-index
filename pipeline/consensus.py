# -*- coding: utf-8 -*-
"""規則 9：共識價取中位數；計算極差率與信心等級"""
import json, statistics, collections

q=json.load(open("data/current_quotes.json",encoding="utf-8"))
by=collections.defaultdict(list)
for r in q: by[(r["course"], r["klass"])].append(r)

out=[]
for (course,klass),rs in by.items():
    priced=[r for r in rs if r["low"] is not None]
    mids=[(r["low"]+r["high"])/2 for r in priced]
    rec=dict(course=course, klass=klass,
             region=next((r["region"] for r in rs if r["region"]), None),
             n_sources=len(mids),
             quotes={r["source"]:dict(low=r["low"],high=r["high"],status=r["status"],
                                      raw=r["raw"],date=r["quote_date"]) for r in rs})
    # 費用同樣取多源共識（規則 8）
    fees=[r["transfer_fee"] for r in rs if r["transfer_fee"] is not None]
    dues=[r["annual_dues"] for r in rs if r["annual_dues"] is not None]
    deps=[r["deposit"] for r in rs if r["deposit"] is not None]
    rec["transfer_fee"]=statistics.median(fees) if fees else None
    rec["transfer_fee_spread"]=(max(fees)-min(fees))/statistics.median(fees)*100 if fees and statistics.median(fees) else 0
    rec["annual_dues"]=statistics.median(dues) if dues else None
    rec["deposit"]=statistics.median(deps) if deps else None
    if mids:
        mid=statistics.median(mids)
        disp=(max(mids)-min(mids))/(sum(mids)/len(mids))*100 if len(mids)>1 else 0.0
        rec.update(mid=round(mid,1), dispersion=round(disp,2),
                   lo=min(mids), hi=max(mids))
        n=len(mids)
        rec["confidence"] = "A" if (n>=3 and disp<=2) else "B" if (n>=3 and disp<=5) else "C" if n>=2 else "—"
        rec["net_price"]=round(mid-(rec["deposit"] or 0),1)
        rec["all_in"]=round(mid+(rec["transfer_fee"] or 0),1)
        rec["fee_rate"]=round((rec["transfer_fee"] or 0)/mid*100,1) if mid else None
        rec["status"]=None
    else:
        st=[r["status"] for r in rs if r["status"]]
        rec.update(mid=None, dispersion=None, confidence="—",
                   status=collections.Counter(st).most_common(1)[0][0] if st else "無報價")
    out.append(rec)

out.sort(key=lambda r:-(r["mid"] or -1))
json.dump(out, open("data/consensus.json","w",encoding="utf-8"), ensure_ascii=False, indent=0)

priced=[r for r in out if r["mid"]]
multi=[r for r in priced if r["n_sources"]>=2]
d=[r["dispersion"] for r in multi]
print(f"共識標的 {len(out)} 檔（有價 {len(priced)}，多源 {len(multi)}）")
print(f"極差率  中位={statistics.median(d):.2f}%  平均={statistics.mean(d):.2f}%")
print(f"  ≤2%（A級） {sum(1 for x in multi if x['confidence']=='A'):>3} 檔")
print(f"  2–5%（B級） {sum(1 for x in multi if x['confidence']=='B'):>3} 檔")
print(f"  >5% 或單源（C級） {sum(1 for x in priced if x['confidence']=='C'):>3} 檔")
print("\n極差率最大的 8 檔（需人工複核）:")
for r in sorted(multi,key=lambda r:-r["dispersion"])[:8]:
    qs=" / ".join(f"{s}:{(v['low']+v['high'])/2:g}" for s,v in r["quotes"].items() if v['low'] is not None)
    print(f"  {r['course']}·{r['klass']:<6} 極差{r['dispersion']:>5.1f}%  共識{r['mid']:>7.1f}  [{qs}]")
print("\n對照手動查核（東方/美麗華/台北團體）:")
for r in out:
    if (r['course'],r['klass']) in [('東方','個人'),('東方','眷屬'),('美麗華','個人'),('台北','團體'),('翡翠','個人')]:
        print(f"  {r['course']}·{r['klass']:<5} 共識{r['mid']}  極差{r['dispersion']}%  過戶費{r['transfer_fee']}萬  費率{r['fee_rate']}%  {r['confidence']}級")
