# -*- coding: utf-8 -*-
"""建置前的哨兵檢查。
   自動更新最危險的失敗模式不是「抓不到」——那會報錯；
   而是來源改版後解析器只抓到一半，網站照樣產出，只是資料悄悄變少。
   因此對關鍵數量設下限，低於門檻就讓建置失敗，寧可停在舊版也不要發布壞資料。"""
import json, sys

FLOOR = {
    "history_quotes": 24000,   # 實測 25,376
    "current_rows":     280,   # 實測 312
    "consensus":         85,   # 實測 93
    "priced":            70,   # 實測 77
    "series":            95,   # 實測 110
    "fee_courses":       55,   # 實測 64
    "index_months":     460,   # 實測 475
}

def check():
    bad=[]
    def cmp(k, got):
        f=FLOOR[k]
        ok = got>=f
        print(f"  {'✓' if ok else '✗'} {k:<16} {got:>7,}  (下限 {f:,})")
        if not ok: bad.append(f"{k}={got} < {f}")

    cmp("history_quotes", len(json.load(open("data/history_quotes.json",encoding="utf-8"))))
    cmp("current_rows",   len(json.load(open("data/current_quotes.json",encoding="utf-8"))))
    cons=json.load(open("data/consensus.json",encoding="utf-8"))
    cmp("consensus", len(cons))
    cmp("priced",    sum(1 for c in cons if c.get("mid") is not None))
    cmp("series",    len(json.load(open("data/series.json",encoding="utf-8"))))
    fees=json.load(open("data/green_fees.json",encoding="utf-8"))
    cmp("fee_courses", len(fees))
    idx=json.load(open("data/index.json",encoding="utf-8"))
    cmp("index_months", len(idx["months"]))

    # 每家來源都必須有貢獻，否則代表某一家已經改版
    q=json.load(open("data/current_quotes.json",encoding="utf-8"))
    per={}
    for r in q: per[r["source"]]=per.get(r["source"],0)+1
    for s in ("huifeng","godao","ylgolf","golf168"):
        n=per.get(s,0); ok=n>=50
        print(f"  {'✓' if ok else '✗'} 來源 {s:<10} {n:>7} 列  (下限 50)")
        if not ok: bad.append(f"來源 {s} 只解析到 {n} 列，可能已改版")

    # 指數不得出現不合理的單月跳動（解析錯誤的典型徵兆）
    v=idx["main"]
    jumps=[(idx["months"][i], v[i]/v[i-1]-1) for i in range(1,len(v))
           if v[i-1]>0 and abs(v[i]/v[i-1]-1)>0.25]
    print(f"  {'✓' if not jumps else '✗'} 指數單月跳動 >25%  {len(jumps)} 筆")
    if jumps: bad.append(f"指數異常跳動：{jumps[:3]}")
    return bad

if __name__=="__main__":
    print("哨兵檢查：")
    bad=check()
    if bad:
        print("\n建置中止 —— 資料量或來源解析異常：")
        for b in bad: print("   ·",b)
        sys.exit(1)
    print("\n全部通過。")
