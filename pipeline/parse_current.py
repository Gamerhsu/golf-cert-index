# -*- coding: utf-8 -*-
"""解析四來源當期行情表（通用 rowspan 攤平 + 區域偵測）"""
import os, re, json, html, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cells_of, parse_price, parse_fee, parse_dues, canon_course, canon_class

BASE = os.path.dirname(os.path.abspath(__file__))

SOURCES = {
 "huifeng": dict(name="惠豐高爾夫", file="huifeng_latest.html", enc="utf-8",
                 date="2026-08-17", url="https://hfgolfservice.com/index.php/Membership/membership"),
 "godao":   dict(name="公道國際",   file="godao_latest.html",   enc="utf-8",
                 date="2026-08-19", url="http://golf888.com.tw/latest.aspx"),
 "ylgolf":  dict(name="悅來高爾夫", file="ylgolf_latest.html",  enc="utf-8",
                 date="2026-08-26", url="https://ylgolf.com.tw/market/latest/"),
 "golf168": dict(name="golf168",   file="golf168_latest.html", enc="big5",
                 date=None,  # 規則 1：未標示日期 → 僅供交叉驗證，不進主序列
                 url="http://www.golf168.com.tw/new_page_2.htm"),
}

REGIONS = [("台北","台北新北"),("新北","台北新北"),("林口","台北新北"),
           ("桃園","桃園"),("花東","花東"),("宜蘭","花東"),
           ("新竹","竹苗"),("苗栗","竹苗"),
           ("台中","中彰投"),("彰化","中彰投"),("南投","中彰投"),
           ("嘉義","嘉南高屏"),("台南","嘉南高屏"),("高雄","嘉南高屏"),("屏東","嘉南高屏")]

def region_of(text):
    hits=[r for k,r in REGIONS if k in text]
    return hits[0] if hits else None

def parse_source(sid):
    cfg=SOURCES[sid]
    raw=open(os.path.join(BASE,"raw","current",cfg["file"]),"rb").read()
    src=raw.decode(cfg["enc"], errors="replace")
    plain=re.sub(r'<[^>]+>',' ', src)
    recs=[]
    for tm in re.finditer(r'(?is)<table\b[^>]*>(.*?)</table>', src):
        tbl=tm.group(1)
        rows=re.findall(r'(?is)<tr\b[^>]*>(.*?)</tr>', tbl)
        hdr_i=None
        for i,r in enumerate(rows[:4]):
            c="".join(cells_of(r))
            if "參考行情" in c and ("過戶" in c or "類別" in c or "會員別" in c):
                hdr_i=i; break
        if hdr_i is None: continue
        # 區域：往前找最近的區域字樣
        before=re.sub(r'<[^>]+>',' ', src[:tm.start()])
        region=None
        for seg in reversed(re.findall(r'[^\s]{2,40}地區|台北市[^\s]{0,20}', before)[-6:]):
            region=region_of(seg)
            if region: break
        course=None
        for r in rows[hdr_i+1:]:
            c=cells_of(r)
            c=[x for x in c]
            if len(c)<3: continue
            if "參考行情" in "".join(c) or c[0] in ("球場","球 場"): continue
            if len(c)>=5 and not c[0].startswith("●"):
                cand_course, klass, price, fee, dues = c[0],c[1],c[2],c[3],c[4]
                if cand_course: course=cand_course
            elif len(c)==4:
                klass, price, fee, dues = c[0],c[1],c[2],c[3]
            elif len(c)==3:
                klass, price, fee = c[0],c[1],c[2]; dues=""
            else: continue
            if not course or course.startswith("●"): continue
            if not klass or klass in ("類別","會員別"): continue
            lo,hi,dep,st = parse_price(price)
            if lo is None and st is None: continue
            recs.append(dict(source=sid, source_name=cfg["name"], quote_date=cfg["date"],
                             region=region,
                             course=canon_course(course), course_raw=course,
                             klass=canon_class(klass), klass_raw=klass,
                             low=lo, high=hi, deposit=dep, status=st,
                             transfer_fee=parse_fee(fee), annual_dues=parse_dues(dues),
                             raw=price))
    return recs

if __name__=="__main__":
    allr=[]
    for sid in SOURCES:
        r=parse_source(sid); allr+=r
        prices=[x for x in r if x["low"] is not None]
        print(f"{SOURCES[sid]['name']:<10} 共 {len(r):>3} 列（有價 {len(prices):>3}，狀態 {len(r)-len(prices):>2}）"
              f"  日期={SOURCES[sid]['date'] or '未標示 → 僅交叉驗證'}")
    json.dump(allr, open("data/current_quotes.json","w",encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"\n合計 {len(allr)} 列 → data/current_quotes.json")
