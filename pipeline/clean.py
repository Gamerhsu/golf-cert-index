# -*- coding: utf-8 -*-
"""規則 9 延伸：來源錯字偵測。
   單月尖峰且次月立即回復（一上一下、方向相反、幅度皆 >30%）判定為來源打字錯誤，
   以前後月幾何平均取代，並完整記錄修正紀錄供稽核。"""
import json, sys, math, collections
sys.path.insert(0,'pipeline'); from common import canon_course, canon_class

def build_series(path="data/history_quotes.json"):
    h=json.load(open(path,encoding="utf-8"))
    S=collections.defaultdict(dict)
    for r in h:
        if r["low"] is None: continue
        k=canon_class(r["klass"])
        if k in ("團體","團體平日"): continue
        S[(canon_course(r["course"]),k)][(r["roc"]+1911)*12+r["month"]]=(r["low"]+r["high"])/2
    return S

def clean(S, thr=0.30):
    log=[]
    for key,s in S.items():
        ms=sorted(s)
        for i in range(1,len(ms)-1):
            a,b,c = ms[i-1],ms[i],ms[i+1]
            if b-a!=1 or c-b!=1: continue
            if s[a]<=0 or s[b]<=0 or s[c]<=0: continue
            r1=math.log(s[b]/s[a]); r2=math.log(s[c]/s[b])
            if abs(r1)>thr and abs(r2)>thr and r1*r2<0:
                new=round(math.sqrt(s[a]*s[c]),1)
                log.append(dict(course=key[0], klass=key[1],
                                ym=f"{(b-1)//12}-{(b-1)%12+1:02d}",
                                was=s[b], now=new, prev=s[a], next=s[c]))
                s[b]=new
    return log

if __name__=="__main__":
    S=build_series(); log=clean(S)
    json.dump(log, open("data/corrections.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"偵測並修正來源錯字 {len(log)} 筆：")
    for c in log:
        print(f"  {c['course']}·{c['klass']:<7}{c['ym']}  {c['was']:>7.1f} → {c['now']:>7.1f}   "
              f"（前後月 {c['prev']:g} / {c['next']:g}）")
