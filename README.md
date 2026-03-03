# 🏦 BankAI 企業全方位徵信系統 (MVP)

專為銀行法金業務 (ARM/RM) 設計的自動化徵信報告生成工具。本專案旨在解決日常繁瑣的徵信資料收集與報表 Key-in 流程，透過自動化爬蟲與 AI 文件解析技術，大幅提升法金人員的工作效率，並降低人為錯誤風險。

## ✨ 核心功能 (Features)

1. **公開財報一鍵整合 (Automated Data Retrieval)**
   * 串接 `yfinance` API，輸入統編或股票代號即可秒速抓取企業基本資料、市值、最新資產負債表與營收趨勢。
   * 內建「雙層保險備援機制 (Fail-over)」：若遇網路不穩或 API 限制，系統將自動無縫切換至內建模擬數據，確保比賽或向客戶 Demo 時 100% 穩定呈現。

2. **智慧文件解析 (Smart PDF OCR & Parsing)**
   * 整合 `pdfplumber` 技術，自動讀取客戶提供的非結構化 PDF 財報（如掃描檔、財報附註）。
   * 模擬 LLM 自然語言處理，自動摘要財務重點並標記風險關鍵字（如：匯率風險、ESG 合規）。

3. **視覺化風險儀表板 (Visualized Risk Dashboard)**
   * 自動計算關鍵財務指標（營收 YoY、淨利率、負債比、流動比率）。
   * 透過 `Streamlit` 與 `st-aggrid` 提供互動式圖表與自適應表格，打造具備銀行專業感的前端介面。

4. **高風險模型外包架構 (API Integration Ready)**
   * 系統已預留 API 擴充接口，針對高風險之違約機率 (PD) 計算、負責人票信與訴訟紀錄掃描，規劃串接外部專業信評機構 (如 TEJ、JCIC) 進行資料交換，確保銀行合規性與資安標準。

## 🛠️ 技術架構 (Tech Stack)

* **前端展示:** `Streamlit`, `st-aggrid`
* **資料處理:** `Pandas`
* **外部資料源:** `yfinance` (Yahoo Finance API)
* **文件解析:** `pdfplumber`

## 🚀 系統安裝與執行 (Installation & Usage)

### 1. 環境要求 (Prerequisites)
**強烈建議使用 Python 3.11 或 3.12**。
*(⚠️ 警告：目前 Streamlit 尚未完全支援 Python 3.14 測試版，若使用 3.14 可能會導致網頁呈現全白畫面)*

### 2. 建立虛擬環境 (建議)
```bash
python -m venv venv
# Windows 啟動虛擬環境:
.\venv\Scripts\activate
# macOS/Linux 啟動虛擬環境:
source venv/bin/activate

近期仍舊不斷更新內容
