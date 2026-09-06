# -*- coding: utf-8 -*-
"""解析悅來歷年行情 → 月度長格式。處理 rowspan、狀態值、區間值、保證金標記。"""
import os, re, json, html, glob

BASE = os.path.dirname(os.path.abspath(__file__))
MONTHS = ["一月","二月","三月","四月","五月","六月","七月","八月","九月","十月","十一月","十二月"]

STATUS_WORDS = ["暫停過戶","停止過戶","停止交易","停止營業","暫停營業","結束營業","詢價","暫停","停售","未上市"]

def cells_of(row_html):
    out=[]
    for m in re.finditer(r'(?is)<t[dh]\b[^>]*>(.*?)</t[dh]>', row_html):
        c = re.sub(r'(?is)<(script|style).*?</\1>',' ', m.group(1))
        c = re.sub(r'(?i)<br\s*/?>', ' ', c)
        c = re.sub(r'<[^>]+>',' ', c)
        c = html.unescape(c)
        c = c.replace('　',' ').replace('\xa0',' ')
        c = re.sub(r'\s+',' ', c).strip()
        out.append(c)
    return out

def parse_value(raw):
    """回傳 (low, high, deposit, status, raw)"""
    s = (raw or "").strip()
    if s in ("","-","－","—","–"): return (None,None,None,None,s)
    for w in STATUS_WORDS:
        if w in s: return (None,None,None,w,s)
    dep = None
    m = re.search(r'[\(（]\s*([\d.]+)\s*保\s*[\)）]', s)
    if m:
        dep = float(m.group(1)); s = s[:m.start()] + s[m.end():]
    s2 = s.replace('，',',').replace('、',',')
    nums = re.findall(r'\d+(?:\.\d+)?', s2)
    if not nums: return (None,None,dep,None,raw)
    vals = [float(n) for n in nums]
    if re.search(r'\d\s*[-~－〜]\s*\d', s2) and len(vals)>=2:
        return (min(vals[:2]), max(vals[:2]), dep, None, raw)
    if len(vals)>1:   # 「880、900」列舉多價
        return (min(vals), max(vals), dep, None, raw)
    return (vals[0], vals[0], dep, None, raw)

def parse_year(path, roc):
    src = open(path, encoding='utf-8', errors='replace').read()
    recs=[]
    for tm in re.finditer(r'(?is)<table\b[^>]*>(.*?)</table>', src):
        tbl = tm.group(1)
        rows = re.findall(r'(?is)<tr\b[^>]*>(.*?)</tr>', tbl)
        if not rows: continue
        # 找標頭：含「一月」與「十二月」
        hdr_i = None
        for i,r in enumerate(rows[:6]):
            c = cells_of(r)
            if "一月" in c and "十二月" in c: hdr_i = i; break
        if hdr_i is None: continue
        hdr = cells_of(rows[hdr_i])
        mcols = [hdr.index(m) for m in MONTHS]
        base = min(mcols)                      # 月份起始欄
        course = None
        for r in rows[hdr_i+1:]:
            c = cells_of(r)
            if len(c) < 12: continue
            if base == 2 and len(c) >= 14:
                course, klass, vals = c[0], c[1], c[2:14]
            elif base == 2 and len(c) == 13:   # 球場 rowspan 續行
                klass, vals = c[0], c[1:13]
            elif base == 1 and len(c) >= 13:
                course, klass, vals = c[0], "", c[1:13]
            else:
                continue
            course = (course or "").strip()
            if not course or course in ("球場","類別"): continue
            if len(vals) != 12: continue
            for mi,v in enumerate(vals):
                lo,hi,dep,st,raw = parse_value(v)
                if lo is None and st is None: continue
                recs.append(dict(course=course, klass=klass.strip() or "個人",
                                 roc=roc, month=mi+1, low=lo, high=hi,
                                 deposit=dep, status=st, raw=raw))
    return recs

if __name__ == "__main__":
    allrecs=[]; per={}
    for p in sorted(glob.glob(os.path.join(BASE,"raw","history","roc*.html"))):
        roc = int(re.search(r'roc(\d+)', p).group(1))
        r = parse_year(p, roc); allrecs += r; per[roc]=len(r)
    os.makedirs(os.path.join(BASE,"..","data"), exist_ok=True)
    out = os.path.join(BASE,"..","data","history_quotes.json")
    json.dump(allrecs, open(out,"w",encoding='utf-8'), ensure_ascii=False)
    print(f"總筆數 {len(allrecs):,}  年度 {len(per)}")
    for roc in sorted(per): print(f"  民國{roc:>3} ({roc+1911}) : {per[roc]:>5} 筆")
