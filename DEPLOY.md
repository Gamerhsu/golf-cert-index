# 部署說明

網站的產物是**單一自含 HTML 檔**（`dist/index.html`，約 1.2 MB），資料以 JSON 內嵌，
沒有後端、沒有資料庫、沒有外部 JS 相依（只有 Google Fonts 一個外部樣式表）。
因此任何靜態主機都能直接放。

```bash
./build.sh          # 抓取 → 解析 → 清理 → 共識 → 指數 → 產出 dist/index.html
```

---

## 選項比較

| 方式 | 適合 | 網址 | 自動更新 | 成本 |
|---|---|---|---|---|
| **Artifact**（目前） | 給少數人看、不想公開 | claude.ai 連結 | 否，需重新發布 | 免費 |
| **Cloudflare Pages** | 公開、要自訂網域 | 自訂網域 | 需接 Git | 免費 |
| **Netlify** | 最快上線 | `*.netlify.app` | 需接 Git | 免費 |
| **GitHub Pages + Actions** | 要每週自動更新 | `*.github.io` | **是，每週一自動** | 免費 |

---

## 一、最快：拖曳上傳（3 分鐘，不需要 Git）

1. `./build.sh`
2. 開 <https://app.netlify.com/drop>（或 Cloudflare Pages 的 *Direct Upload*）
3. 把整個 `dist/` 資料夾拖進去

立刻拿到網址。缺點是每次更新都要重新拖一次。

---

## 二、要自動更新：GitHub Pages + Actions（推薦）

`.github/workflows/build.yml` 已經寫好，每週一早上 06:00（台北時間）自動重新抓取、
重建、部署，並把當次的 `corrections.json` 與 `consensus.json` 留存 90 天作為稽核紀錄。

### 建立步驟

```bash
cd "/Users/gamerhsu/Desktop/AI/高爾夫球證價格變化"
git init && git add -A && git commit -m "球證行情所 v1.3"
gh repo create golf-cert-index --private --source=. --push
```

接著到 GitHub 的 **Settings → Pages → Source** 選 **GitHub Actions**，
然後在 **Actions** 分頁手動跑一次 `每週重建並部署` 確認流程正常。

> 私有 repo 的 GitHub Pages 需要 Pro 方案。若要維持免費，改用 public repo，
> 或改用下面的 Cloudflare Pages。

### 自訂網域

Pages 設定裡填入網域，再到 DNS 加一筆 `CNAME` 指向 `<帳號>.github.io`。

---

## 三、Cloudflare Pages（公開站的最佳選擇）

免費方案就支援私有 repo、自訂網域與無限流量。

1. Cloudflare Dashboard → Workers & Pages → Create → Pages → Connect to Git
2. 建置設定：
   - **Build command**：`./build.sh`
   - **Build output directory**：`dist`
   - **環境變數**：`PYTHON_VERSION = 3.12`
3. 每次 push 自動重建。要定期更新，另外加一個 Cron Trigger 或沿用上面的 GitHub Actions。

---

## 四、繼續用 Artifact

不需要任何設定，`球證行情所.html` 重新發布即可，網址不變。
要給別人看，在 Artifact 頁面右上角的分享選單開啟權限——**預設是私有的**。

---

## 更新頻率與抓取禮節

- **排程設為每週一次**。四個來源的行情表大約每月更新一次，週更已足夠，
  再密集只是徒增對方主機負擔。
- `pipeline/fetch.py` 對每個請求間隔 1.2 秒，並帶可識別的 User-Agent。
- **快取策略**：往年的歷史頁面不再變動，永久快取；
  **當年度與前一年度的歷史頁、以及全部當期報價頁，每次都強制重抓**。
  （這點很重要——早期版本只要檔案存在就跳過，會導致排程永遠讀到舊資料。）
- 悅來的 `robots.txt` 明確 `Allow: /`；其餘三家沒有 `robots.txt`。
  但**服務條款尚未逐一確認**，正式公開前應該先看過，並準備好來源方的下架聯絡窗口。

---

## 上線前的檢查清單

- [ ] 服務條款：四個來源的使用條款是否允許彙整與再呈現
- [ ] 頁尾聲明是否完整（參考行情非成交價、不構成投資建議、不從事仲介）
- [ ] 保證金可退性查證 —— 目前「淨價」指標建立在推斷之上，尚未向球場確認
- [ ] 擊球費的會員價抽取失敗名單（5 座）是否要改以人工補齊
- [ ] 若要公開，建議先加上來源方的意見回饋管道

---

## 檔案結構

```
build.sh                    一鍵重建
pipeline/
  fetch.py                  抓取 48 個頁面並存檔留證
  common.py                 共用規則：別名、類別詞彙、價格/費用/年費解析、區域對照
  parse_history.py          40 年月度行情 → 25,376 筆
  parse_current.py          四來源當期報價
  clean.py                  來源錯字偵測（單月尖峰且回復）
  consensus.py              中位數共識價、極差率、信心等級
  build_index.py            TGMI 指數（等權重、鏈式連接、幾何平均）
  build_courses.py          分區 → 球場 → 類別，含年度彙總
  parse_fees.py             擊球費四格抽取與跨源共識
  build_site_data.py        績效指標與損益兩平
  assemble.py               合併成單一 site.json
site/index.html             頁面模板（含 __DATA__ 佔位符）
data/                       各階段產物（JSON）
dist/index.html             最終產物
```
