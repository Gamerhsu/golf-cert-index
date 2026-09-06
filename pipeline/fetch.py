# -*- coding: utf-8 -*-
"""抓取原始頁面並存檔留證（每個來源獨立、失敗不影響其他）"""
import os, time, urllib.request, ssl

CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
UA = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 GolfCertResearch/0.1"}
BASE = os.path.dirname(os.path.abspath(__file__))

def get(url, path, delay=1.2, force=False):
    """force=True 時忽略快取。當期報價與『當年度』歷史頁每次都必須重抓，
       否則週更排程只會一直讀到舊檔。往年歷史頁不再變動，可永久快取。"""
    if not force and os.path.exists(path) and os.path.getsize(path) > 2000:
        return "cached"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40, context=CTX) as r:
        data = r.read()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path,"wb").write(data)
    time.sleep(delay)
    return f"{len(data)}B"

# 悅來歷年行情：民國76–115，41 個年度頁
HIST_IDS = {
 47:115,44:114,43:113,42:112,41:111,40:110,39:109,33:108,32:107,38:106,37:105,
 31:104,34:103,28:102,27:101,1:100,2:99,3:98,4:97,5:96,6:95,7:94,8:93,9:92,
 10:91,11:90,12:89,13:88,14:87,15:86,16:85,17:84,18:83,19:82,20:81,21:80,
 22:79,23:78,24:77,25:76,
}
CURRENT = {
 "ylgolf_latest":  "https://ylgolf.com.tw/market/latest/",
 "ylgolf_charge":  "https://ylgolf.com.tw/market/charge/",
 "godao_latest":   "http://golf888.com.tw/latest.aspx",
 "godao_charge":   "http://golf888.com.tw/charge.aspx",
 "huifeng_latest": "https://hfgolfservice.com/index.php/Membership/membership",
 "huifeng_charge": "https://hfgolfservice.com/index.php/Fieldcost/fieldcost",
 "golf168_latest": "http://www.golf168.com.tw/new_page_2.htm",
 "golf168_charge": "http://www.golf168.com.tw/new_page_10.htm",
}

if __name__ == "__main__":
    import datetime
    CUR_ROC = datetime.date.today().year - 1911
    ok=fail=skip=0
    for sid, roc in sorted(HIST_IDS.items(), key=lambda x:-x[1]):
        p = os.path.join(BASE,"raw","history",f"roc{roc}.html")
        # 當年度與前一年度的頁面仍會更新，必須重抓
        force = roc >= CUR_ROC - 1
        try:
            r=get(f'https://ylgolf.com.tw/market/history/?id={sid}', p, force=force)
            if r=="cached": skip+=1
            else: print(f"  hist {roc:>3} -> {r}{' (force)' if force else ''}"); ok+=1
        except Exception as e: print(f"  hist {roc:>3} FAIL {e}"); fail+=1
    for name,url in CURRENT.items():
        p = os.path.join(BASE,"raw","current",f"{name}.html")
        try: print(f"  cur {name:<16} -> {get(url,p,force=True)}"); ok+=1
        except Exception as e: print(f"  cur {name:<16} FAIL {e}"); fail+=1
    print(f"\n完成 抓取={ok} 快取={skip} 失敗={fail}")
    if fail and ok==0:
        raise SystemExit("所有來源皆抓取失敗，中止建置")
