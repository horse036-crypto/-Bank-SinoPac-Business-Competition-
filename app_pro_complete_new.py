import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import time
import urllib3
from datetime import datetime
import io
import financial_analyzer as fa # 新增這行，導入新模組
# 匯入所有自定義模組
import company_info as ci
import financial_data as fd
import news_analyzer as news
# 在 app.py 頂部加入
import news_analyzer as news # 確保模組名稱對應
import chips_analysis as chips
import competitor_analysis as ca
import product_mix as pm
import concentration as conc
from module_rag import FinancialRAG
import report_generator as rg
# 1. 在檔案頂部的 import 區新增這一行
import esg_analyzer as esg  # 這是我們剛才寫的 ESG 模組
import sbom_generator as sbom  # 匯入新模組
# 忽略 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 頁面設定
# ==========================================
st.set_page_config(
    page_title="智慧財務分析系統 Pro Complete",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS 樣式
st.markdown("""
<style>
    /* 主標題樣式 */
    .main-header {
        font-size: 2.8rem;
        font-weight: bold;
        text-align: center;
        padding: 25px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    
    /* 副標題 */
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 30px;
    }
    
    /* 卡片容器 */
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 10px 0;
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    /* 評分顯示 */
    .score-display {
        text-align: center;
        font-size: 3.5rem;
        font-weight: bold;
        padding: 40px;
        border-radius: 20px;
        margin: 20px 0;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    
    /* 資訊框 */
    .info-box {
        background-color: #e3f2fd;
        padding: 18px;
        border-left: 5px solid #2196F3;
        border-radius: 8px;
        margin: 12px 0;
    }
    
    .warning-box {
        background-color: #fff3e0;
        padding: 18px;
        border-left: 5px solid #ff9800;
        border-radius: 8px;
        margin: 12px 0;
    }
    
    .success-box {
        background-color: #e8f5e9;
        padding: 18px;
        border-left: 5px solid #4caf50;
        border-radius: 8px;
        margin: 12px 0;
    }
    
    .danger-box {
        background-color: #ffebee;
        padding: 18px;
        border-left: 5px solid #f44336;
        border-radius: 8px;
        margin: 12px 0;
    }
    
    /* Tab 樣式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        background-color: white;
        border-radius: 8px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* 按鈕樣式 */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* 進度條 */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 輔助函數
# ==========================================
@st.cache_data(ttl=3600)
def fetch_stock_history(stock_code):
    """抓取股價歷史資料"""
    all_data = []
    date_list = pd.date_range(end=pd.Timestamp.now(), periods=6, freq='MS')
    
    for date_item in date_list:
        date_str = date_item.strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date_str}&stockNo={stock_code}"
        
        try:
            res = requests.get(url, verify=False, timeout=10)
            data = res.json()
            
            if data['stat'] == 'OK':
                df = pd.DataFrame(data['data'], columns=data['fields'])
                df['日期'] = df['日期'].apply(lambda x: str(int(x.split('/')[0]) + 1911) + '-' + x.split('/')[1] + '-' + x.split('/')[2])
                
                for col in ['收盤價', '開盤價', '最高價', '最低價', '成交股數']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce')
                
                all_data.append(df)
            time.sleep(0.5)
        except:
            pass
    
    return pd.concat(all_data, ignore_index=True) if all_data else None

def create_gauge_chart(value, title, max_value=100):
    """創建儀表板圖表"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 20}},
        delta = {'reference': max_value * 0.7},
        gauge = {
            'axis': {'range': [None, max_value]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, max_value*0.6], 'color': "#ffcccc"},
                {'range': [max_value*0.6, max_value*0.8], 'color': "#fff4cc"},
                {'range': [max_value*0.8, max_value], 'color': "#ccffcc"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_value * 0.9
            }
        }
    ))
    
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
    return fig


# ============================================================
# 📄 Markdown 完整報告產生器 — 涵蓋全部模組輸出
# ============================================================
def _build_markdown_report(
    stock_id, company_name, info,
    df_price, df_ratios, insights, score_data,
    df_chips, df_mix,
) -> bytes:
    """
    整合所有模組 (company_info / financial_data / chips_analysis /
    competitor_analysis / product_mix / news_analyzer / esg_analyzer /
    financial_analyzer / concentration / module_rag) 的輸出，
    產生一份完整的 Markdown 報告。
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    L = []   # 所有行最後 join

    def h(level, text):      L.append(f"{'#'*level} {text}\n")
    def hr():                L.append("---\n")
    def br():                L.append("")
    def row(*cells):         L.append("| " + " | ".join(str(c) for c in cells) + " |")
    def thead(*cols):
        row(*cols)
        L.append("|" + "|".join(["---"] * len(cols)) + "|")
    def quote(text, emoji="ℹ️"):  L.append(f"> {emoji} {text}")
    def para(text):          L.append(str(text))

    # ── 封面 ──────────────────────────────────────────────────
    L.append(f"# 📊 {company_name}（{stock_id}）完整財務分析報告")
    br()
    L.append(f"> **產生時間：** {now}")
    L.append(f">")
    L.append(f"> **資料來源：** TWSE Open API · Yahoo Finance · FinMind · Google News · HiStock · ESG OpenAPI")
    br()
    hr()

    # ── 目錄 ──────────────────────────────────────────────────
    h(2, "📋 目錄")
    toc = [
        "1. 公司基本資訊 (company_info)",
        "2. 股價走勢統計 (TWSE STOCK_DAY)",
        "3. 財務健康評分 (financial_data)",
        "4. 財務指標明細 17+ 項 (financial_data)",
        "5. AI 財務洞察 (financial_data)",
        "6. 法人籌碼動向 (chips_analysis)",
        "7. 產品營收結構 (product_mix)",
        "8. 同業估值比較 (competitor_analysis)",
        "9. ESG 永續數據 (esg_analyzer)",
        "10. 官方財報彙總 (financial_analyzer)",
        "11. 新聞雷達摘要 (news_analyzer)",
    ]
    for t in toc:
        L.append(f"- {t}")
    br()
    hr()

    # ══════════════════════════════════════════════════════════
    # 1. 公司基本資訊 (完整輸出版)
    # ══════════════════════════════════════════════════════════
    h(2, "1. 🏢 公司基本資訊")
    para(f"*資料來源：`company_info.py` → 證交所官方數據 + Yahoo Finance*")
    br()
    
    if info:
        # --- 第一部分：核心經營資料表格 ---
        h(3, "📊 經營核心數據")
        # 定義核心展示順序，其餘欄位會自動加在後面
        core_keys = ["公司名稱", "股票代碼", "產業別", "董事長", "總經理", "發言人", "成立日期", "上市日期", "實收資本額"]
        
        thead("項目", "內容")
        # 先輸出核心欄位
        for k in core_keys:
            if k in info and info[k]:
                row(k, str(info[k]).replace("|", "｜"))
        
        # 輸出其餘所有不屬於「簡介」與「聯絡資訊」的欄位（確保不遺漏任何隱藏資訊）
        contact_keys = ["總機電話", "傳真號碼", "電子郵件", "公司地址", "公司網址", "網址"]
        skip_keys = set(core_keys) | set(contact_keys) | {"公司簡介", "公司簡介(EN)", "主要業務"}
        
        for k, v in info.items():
            if k not in skip_keys and v:
                row(k, str(v).replace("|", "｜"))
        br()

        # --- 第二部分：聯絡資訊 ---
        h(3, "📞 聯絡資訊")
        thead("聯絡項目", "詳細內容")
        for k in contact_keys:
            val = info.get(k)
            if not val: # 嘗試不同 key 名稱
                val = info.get("網址") if k == "公司網址" else "N/A"
            row(k, str(val))
        br()

        # --- 第三部分：完整公司簡介 (取消截斷) ---
        if info.get("公司簡介"):
            h(3, "📖 公司簡介 (完整內容)")
            # 使用 blockquote 格式，並移除 500 字限制
            content = info['公司簡介'].replace('\n', '\n> ')
            para(f"> {content}")
        br()

        # --- 第四部分：主要業務 ---
        if info.get("主要業務"):
            h(3, "🛠️ 主要業務範圍")
            para(info["主要業務"])
        br()

    else:
        quote("無法取得公司基本資訊，請檢查網路連線或代碼。抽樣 API 可能暫時無回應。", "⚠️")
        br()
    
    hr()

    # ══════════════════════════════════════════════════════════
    # 2. 📈 股價走勢統計 (完整深度分析版)
    # ══════════════════════════════════════════════════════════
    h(2, "2. 📈 股價走勢深度統計")
    para("*資料來源：TWSE STOCK_DAY API（近 6 個月日 K 數據彙整分析）*")
    br()

    if df_price is not None and not df_price.empty:
        # --- 數據準備 ---
        lp  = df_price.iloc[-1]
        pp  = df_price.iloc[-2] if len(df_price) > 1 else lp
        
        # 價格與漲跌
        curr_price = lp["收盤價"]
        chg = curr_price - pp["收盤價"]
        pct = chg / pp["收盤價"] * 100 if pp["收盤價"] else 0
        
        # 區間統計
        hi  = df_price["最高價"].max()
        lo  = df_price["最低價"].min()
        hi_date = df_price.loc[df_price["最高價"].idxmax(), "日期"]
        lo_date = df_price.loc[df_price["最低價"].idxmin(), "日期"]
        avg_price = df_price["收盤價"].mean()
        
        # 成交量統計
        avg_vol = df_price["成交股數"].mean()
        curr_vol = lp["成交股數"]
        vol_ratio = (curr_vol / avg_vol) if avg_vol else 0

        # --- A. 統計摘要表格 ---
        h(3, "📊 行情統計摘要")
        thead("指標項目", "數值", "備註")
        row("最新收盤價", f"**{curr_price:.2f} 元**", f"今日漲跌：{chg:+.2f} ({pct:+.2f}%)")
        row("近6月最高價", f"{hi:.2f} 元", f"出現日期：{hi_date}")
        row("近6月最低價", f"{lo:.2f} 元", f"出現日期：{lo_date}")
        row("近6月均價", f"{avg_price:.2f} 元", f"目前股價位於均價 {'之上' if curr_price > avg_price else '之下'}")
        row("今日成交量", f"{int(curr_vol):,}", f"量能為均量之 {vol_ratio:.2f} 倍")
        row("資料區間", f"{df_price['日期'].iloc[0]}", f"至 {df_price['日期'].iloc[-1]}")
        br()

        # --- B. 波段漲跌分析 ---
        h(3, "📐 區間波段分析")
        from_low = (curr_price / lo - 1) * 100 if lo else 0
        from_high = (curr_price / hi - 1) * 100 if hi else 0
        
        thead("分析維度", "百分比", "解讀")
        row("距區間最低點漲幅", f"{from_low:+.2f}%", "自低點反彈強度")
        row("距區間最高點回落", f"{from_high:+.2f}%", "自高點修正幅度")
        row("振幅 (High/Low)", f"{(hi/lo-1)*100:.2f}%", "近半年股價波動率")
        br()

        # --- C. 近 15 日每日明細 (含量能分析) ---
        h(3, "📅 近 15 日交易明細")
        thead("日期", "開盤", "最高", "最低", "收盤", "漲跌", "成交張數", "量能狀況")
        
        recent = df_price.tail(15).copy()
        for i in range(len(recent)):
            r = recent.iloc[i]
            # 漲跌判斷
            if i > 0:
                prev_c = recent.iloc[i-1]["收盤價"]
                dir_emoji = "🔴 ↑" if r["收盤價"] > prev_c else ("🟢 ↓" if r["收盤價"] < prev_c else "⚪ —")
                diff = r["收盤價"] - prev_c
            else:
                dir_emoji = "—"
                diff = 0
            
            # 量能狀況 (張數 = 股數/1000)
            vol_k = int(r["成交股數"]) / 1000
            vol_status = "🔥 爆量" if r["成交股數"] > avg_vol * 1.5 else ("❄️ 縮量" if r["成交股數"] < avg_vol * 0.5 else "穩定")
            
            row(
                r["日期"],
                f"{r['開盤價']:.2f}",
                f"{r['最高價']:.2f}",
                f"{r['最低價']:.2f}",
                f"**{r['收盤價']:.2f}**",
                f"{dir_emoji} ({diff:+.2f})",
                f"{vol_k:,.0f} 張",
                vol_status
            )
        br()
        
        # --- D. 簡易趨勢判斷 ---
        h(3, "💡 技術面觀察簡評")
        if curr_price > hi * 0.95:
            quote("股價目前處於近半年**高檔強勢區**，需注意追高風險。", "🚀")
        elif curr_price < lo * 1.05:
            quote("股價目前處於近半年**低檔支撐區**，可觀察止跌訊號。", "⚓")
        else:
            quote("股價目前處於**區間震盪整理**階段。", "⚖️")

    else:
        para("_股價資料無法取得，請確認股票代號是否正確或 TWSE API 狀態。_")
        br()
    
    hr()
    # ══════════════════════════════════════════════════════════
    # 3. 🏆 財務健康評分 (專業徵信深度版)
    # ══════════════════════════════════════════════════════════
    h(2, "3. 🏆 財務健康綜合評鑑")
    para("*資料來源：`financial_data.py` 整合 Yahoo Finance 財報數據與業界標準 (Benchmark)*")
    br()

    if score_data:
        score  = score_data.get("總分", 0)
        grade  = score_data.get("評級", "N/A")
        z      = score_data.get("Z-Score", 0)
        zstat  = score_data.get("Z-Status", "N/A")

        # --- A. 綜合評等摘要 (Code Block 視覺化) ---
        filled = min(10, round(score / 10))
        if score >= 80:
            bar, lvl, emoji = "🟩" * filled + "⬜" * (10 - filled), "【優異】", "🌟"
        elif score >= 60:
            bar, lvl, emoji = "🟨" * filled + "⬜" * (10 - filled), "【尚可】", "⚖️"
        else:
            bar, lvl, emoji = "🟥" * filled + "⬜" * (10 - filled), "【高風險】", "⚠️"

        L.append("```text")
        L.append(f"┌──────────────────────────────────────────────────────────┐")
        L.append(f"  財務健康總分：{score:3d} / 100   狀態：{lvl} {emoji}")
        L.append(f"  進度條顯示：[{bar}]")
        L.append(f"  銀行信用評級：{grade}")
        L.append(f"  破產風險指標：Z-Score {z:.2f} ({zstat})")
        L.append(f"└──────────────────────────────────────────────────────────┘")
        L.append("```")
        br()

        # --- B. 財務強弱勢雷達觀察 ---
        h(3, "🎯 財務構面強弱勢分析")
        items = score_data.get("細項", [])
        if items:
            thead("評鑑構面", "表現等級", "關鍵評語")
            for item in items:
                s = item["得分"]
                if s >= 15:   strength = "💎 強勢"
                elif s >= 10: strength = "✅ 穩健"
                elif s >= 5:  strength = "🟠 偏弱"
                else:         strength = "🚨 劣勢"
                row(item["項目"], strength, item["評語"])
        br()

        # --- C. 杜邦分析關鍵指標 (ROE 拆解) ---
        # 假設 df_ratios 存在於 context 中
        if df_ratios is not None and not df_ratios.empty:
            h(3, "🧬 獲利品質杜邦拆解 (DuPont Analysis)")
            latest = df_ratios.iloc[0]
            roe = latest.get("ROE (%)", 0)
            
            # 獲利能力、營運效率、財務槓桿
            margin = latest.get("淨利率 (%)", 0)
            asset_turn = latest.get("資產周轉率 (次)", 0)
            leverage = latest.get("權益乘數 (倍)", 1)
            
            para(f"最新年度 **ROE 為 {roe:.2f}%**，其結構拆解如下：")
            thead("分析環節", "指標數值", "財務意義")
            row("獲利能力 (淨利率)", f"{margin:.2f}%", "產品競爭力與成本控管")
            row("營運效率 (資產周轉)", f"{asset_turn:.2f} 次", "資產利用效率與銷貨速度")
            row("財務槓桿 (權益乘數)", f"{leverage:.2f} 倍", "負債運用程度與財務壓力")
            br()

        # --- D. Altman Z-Score 深度解讀 ---
        h(3, "⚡ Altman Z-Score 破產風險警示")
        if z > 2.99:
            quote(f"**安全區 (Safe Zone)：** Z-Score = {z:.2f}。該公司財務結構極其穩健，短期內無任何破產風險。", "✅")
        elif z > 1.81:
            quote(f"**灰色地帶 (Grey Zone)：** Z-Score = {z:.2f}。財務狀況尚可，但存在潛在波動風險，建議列入持續觀察名單。", "⚠️")
        else:
            quote(f"**破產高風險區 (Distress Zone)：** Z-Score = {z:.2f}。指標低於 1.81 警戒線，顯示財務壓力巨大，需嚴防營運資金斷鏈風險。", "🚨")

    else:
        quote("目前無法獲取該公司的財務評分數據，可能原因為財報資料揭露不完整（如新上市或控股公司）。", "ℹ️")
    
    br()
    hr()

    # ══════════════════════════════════════════════════════════
    # 4. 💰 財務指標明細 (含成長率與趨勢分析)
    # ══════════════════════════════════════════════════════════
    h(2, "4. 💰 財務指標明細 (17+ 項深度分析)")
    para("*資料來源：`financial_data.py` → 整合 Yahoo Finance 近三年財報數據*")
    br()

    if df_ratios is not None and not df_ratios.empty:
        # 輔助函數：計算與前一期的增減並回傳帶有箭頭的字串
        def get_trend_str(current, idx, col_name, df):
            if idx + 1 < len(df):
                prev = df.iloc[idx + 1][col_name]
                if pd.isna(current) or pd.isna(prev) or prev == 0: return f"{current:.2f}"
                diff = current - prev
                # 判斷指標性質：有些是越低越好（如負債比、天數）
                low_is_better = any(x in col_name for x in ["負債", "天數", "DSO", "DIO", "DPO", "循環"])
                
                if diff > 0:
                    emoji = "📈" if not low_is_better else "⚠️"
                    return f"{current:.2f} (`+{diff:.2f}` {emoji})"
                elif diff < 0:
                    emoji = "📉" if not low_is_better else "✅"
                    return f"{current:.2f} (`{diff:.2f}` {emoji})"
            return f"{current:.2f}"

        # --- A. 獲利能力分析 ---
        h(3, "📊 獲利能力 (Profitability)")
        profit_cols = ["期間", "毛利率 (%)", "營業利益率 (%)", "淨利率 (%)", "ROE (%)"]
        avail = [c for c in profit_cols if c in df_ratios.columns]
        thead(*avail)
        for i, r in df_ratios.iterrows():
            row_data = [r["期間"]]
            for col in avail[1:]:
                row_data.append(get_trend_str(r[col], i, col, df_ratios))
            row(*row_data)
        br()

        # --- B. 成長能力分析 (若資料庫有提供) ---
        growth_cols = ["營收成長率 (%)", "營業利益成長率 (%)", "淨利成長率 (%)", "每股盈餘 (EPS)"]
        avail_growth = [c for c in growth_cols if c in df_ratios.columns]
        if avail_growth:
            h(3, "🚀 成長能力 (Growth)")
            thead("期間", *avail_growth)
            for i, r in df_ratios.iterrows():
                row(r["期間"], *[f"{r.get(c, 0):.2f}" for c in avail_growth])
            br()

        # --- C. 償債與槓桿能力 ---
        h(3, "🛡️ 償債與槓桿 (Solvency)")
        debt_cols = ["期間", "流動比率 (%)", "速動比率 (%)", "負債比率 (%)", "利息保障倍數 (倍)"]
        avail = [c for c in debt_cols if c in df_ratios.columns]
        thead(*avail)
        for i, r in df_ratios.iterrows():
            row_data = [r["期間"]]
            for col in avail[1:]:
                row_data.append(get_trend_str(r[col], i, col, df_ratios))
            row(*row_data)
        br()

        # --- D. 營運效率與現金流 ---
        h(3, "💵 營運效率與現金流 (Efficiency)")
        cash_cols = ["期間", "應收帳款天數 (DSO)", "存貨週轉天數 (DIO)", "現金週轉循環 (天)", "自由現金流 (億)"]
        avail = [c for c in cash_cols if c in df_ratios.columns]
        thead(*avail)
        for i, r in df_ratios.iterrows():
            row_data = [r["期間"]]
            for col in avail[1:]:
                row_data.append(get_trend_str(r[col], i, col, df_ratios))
            row(*row_data)
        br()

        # --- E. Z-Score 趨勢分析 ---
        if "Z-Score" in df_ratios.columns:
            h(3, "⚡ Altman Z-Score 破產風險趨勢")
            thead("期間", "Z-Score 指數", "變動趨勢", "風險等級")
            for i, r in df_ratios.iterrows():
                z_val = r.get("Z-Score", 0)
                z_lv = "✅ 安全區" if z_val > 2.99 else ("⚠️ 灰色區" if z_val > 1.81 else "🚨 危險區")
                
                # 計算變動箭頭
                trend_emoji = "—"
                if i + 1 < len(df_ratios):
                    prev_z = df_ratios.iloc[i+1]["Z-Score"]
                    trend_emoji = "↗️ 改善" if z_val > prev_z else "↘️ 惡化"
                
                row(r["期間"], f"**{z_val:.2f}**", trend_emoji, z_lv)
            br()
            quote("註：Z-Score > 2.99 為財務健全；1.81 ~ 2.99 為灰色地帶；< 1.81 為高風險。", "💡")
    else:
        para("_目前無法獲取該公司的詳細財務指標明細資料。_")
    
    br()
    hr()

    # ══════════════════════════════════════════════════════════
    # 5. 🔍 AI 財務洞察 (診斷式深度分析版)
    # ══════════════════════════════════════════════════════════
    h(2, "5. 🔍 AI 財務診斷洞察")
    para("*分析模型：基於 `financial_data.py` 邏輯與業界中位數 (Benchmark) 之偏差分析*")
    br()

    if insights:
        # --- A. 診斷摘要 (分組顯示) ---
        # 將原始 insights 依照關鍵字分類，讓報告更有條理
        categories = {
            "獲利品質": [],
            "財務結構": [],
            "營運效率": [],
            "其他觀察": []
        }

        for insight in insights:
            if any(x in insight for x in ["毛利", "淨利", "ROE", "盈餘"]):
                categories["獲利品質"].append(insight)
            elif any(x in insight for x in ["負債", "流動", "速動", "利息保障"]):
                categories["財務結構"].append(insight)
            elif any(x in insight for x in ["天數", "周轉", "CCC", "循環"]):
                categories["營運效率"].append(insight)
            else:
                categories["其他觀察"].append(insight)

        for cat, items in categories.items():
            if items:
                h(3, f"📌 {cat}")
                for item in items:
                    # 轉換原始 Emoji 為更專業的 Markdown 標記
                    emoji = "✅" if "🟢" in item else ("🚨" if "🔴" in item else ("⚠️" if "🟠" in item else "ℹ️"))
                    # 清洗文字
                    clean = item.replace("**", "").replace("🟢","").replace("🟠","").replace("🔴","").replace("⚪","").strip()
                    quote(clean, emoji)
                br()
    else:
        para("_目前無特定異常洞察資料。_")
        br()

    # --- B. 關鍵指標 vs. 業界標準對照表 ---
    h(3, "📏 關鍵指標與業界標準 (Benchmark) 對照")
    para("下表呈現公司最新數據與產業中位數之差異，協助判斷位階：")
    
    # 建立 Benchmark 對照邏輯
    bench_map = {
        "毛利率 (%)":      {"val": 43.50, "alert": 34.84, "risk": 26.75, "dir": "H"},
        "營業利益率 (%)":  {"val": 8.43,  "alert": 5.67,  "risk": 3.18,  "dir": "H"},
        "淨利率 (%)":      {"val": 6.56,  "alert": 3.80,  "risk": 0.43,  "dir": "H"},
        "流動比率 (%)":    {"val": 121.0, "alert": 91.0,  "risk": 61.0,  "dir": "H"},
        "負債比率 (%)":    {"val": 52.0,  "alert": 62.7,  "risk": 73.3,  "dir": "L"},
        "利息保障倍數 (倍)":{"val": 5.0,   "alert": 2.5,   "risk": 1.5,   "dir": "H"}
    }

    thead("監控指標", "公司數值", "業界中位數", "位階評估", "目標方向")
    
    if df_ratios is not None and not df_ratios.empty:
        latest = df_ratios.iloc[0]
        for label, b in bench_map.items():
            actual = latest.get(label)
            if actual is not None:
                # 判定評估等級
                if b["dir"] == "H": # 越高越好
                    status = "💎 優於標竿" if actual >= b["val"] else ("🟠 低於均值" if actual >= b["alert"] else "🚨 警訊")
                else: # 越低越好
                    status = "💎 優於標竿" if actual <= b["val"] else ("🟠 高於均值" if actual <= b["alert"] else "🚨 警訊")
                
                target = "↑ 越高越好" if b["dir"] == "H" else "↓ 越低越好"
                row(label, f"**{actual:.2f}**", f"{b['val']}", status, target)
    br()

    # --- C. 投資建議總結 ---
    h(3, "💡 綜合風險評估與建議")
    # 簡易邏輯判斷
    pos_count = sum(1 for i in insights if "🟢" in i)
    neg_count = sum(1 for i in insights if "🔴" in i)
    
    if neg_count >= 2:
        quote("該公司目前在財務安全或獲利能力上存在多項**紅燈警訊**。建議優先關注其營運資金是否足以支應短期債務，並審慎評估其獲利衰退之原因。", "🚨")
    elif pos_count >= 3:
        quote("該公司整體財務體質**表現強韌**，多項關鍵指標均領先產業平均。在獲利品質穩健的前提下，可進一步觀察其市場份額與未來成長動能。", "✅")
    else:
        quote("該公司財務狀況尚屬中性，雖無立即性風險，但亦缺乏明顯的成長爆發力。建議追蹤其下一季度的毛利變化與成本控管成效。", "⚖️")

    br()
    hr()

    # ══════════════════════════════════════════════════════════
    # 6. 🎯 法人籌碼動向 (趨勢與共識分析版)
    # ══════════════════════════════════════════════════════════
    h(2, "6. 🎯 法人籌碼趨勢分析")
    para("*資料來源：`chips_analysis.py` → TWSE T86 三大法人日買賣超彙整*")
    br()

    if df_chips is not None and not df_chips.empty:
        # --- 數據預處理 ---
        t_for = df_chips["外資"].sum()
        t_trs = df_chips["投信"].sum()
        t_dlr = df_chips["自營商"].sum()
        t_all = df_chips["合計"].sum()

        # 計算連續買賣天數 (最新日期往回推)
        def get_consecutive_days(series):
            count = 0
            is_buying = series.iloc[0] > 0
            for val in series:
                if (val > 0) == is_buying and val != 0:
                    count += 1
                else:
                    break
            return count, ("買超" if is_buying else "賣超")

        for_days, for_dir = get_consecutive_days(df_chips["外資"])
        trs_days, trs_dir = get_consecutive_days(df_chips["投信"])

        # --- A. 籌碼多空總覽 (專業框線版) ---
        L.append("```text")
        L.append(f"┌─────────────────── 區間籌碼統計 ───────────────────┐")
        L.append(f"  外資累計：{t_for:10,d} 張  ({for_dir}連持續 {for_days} 天)")
        L.append(f"  投信累計：{t_trs:10,d} 張  ({trs_dir}連持續 {trs_days} 天)")
        L.append(f"  自營累計：{t_dlr:10,d} 張")
        L.append(f"  ──────────────────────────────────────────────────")
        L.append(f"  三大法人合計：{t_all:10,d} 張 ({'多頭佔優' if t_all > 0 else '空頭佔優'})")
        L.append(f"└────────────────────────────────────────────────────┘")
        L.append("```")
        br()

        # --- B. 法人多空共識判斷 ---
        h(3, "🤝 法人多空共識")
        # 判斷是否聯手 (買超前二大法人方向是否一致)
        recent_for = df_chips["外資"].iloc[0]
        recent_trs = df_chips["投信"].iloc[0]
        
        if recent_for > 0 and recent_trs > 0:
            quote("**法人多頭共識：** 外資與投信今日聯手買進，籌碼面極為強勢。", "🚀")
        elif recent_for < 0 and recent_trs < 0:
            quote("**法人空頭共識：** 外資與投信同步站回賣方，需嚴防股價回檔。", "🚨")
        elif abs(recent_trs) > abs(recent_for) and recent_trs > 0:
            quote("**投信主導：** 儘管外資動向不明，但內資投信積極護盤或布局，具備內資盤特徵。", "🏛️")
        else:
            quote("目前法人看法分歧，股價可能維持區間震盪，靜待主力表態。", "⚖️")
        br()

        # --- C. 每日明細 (含趨勢箭頭) ---
        h(3, "📅 近期法人交易明細")
        thead("日期", "外資", "投信", "自營商", "合計", "當日盤勢")
        
        for _, r in df_chips.iterrows():
            # 視覺化小圖標
            def get_icon(v):
                if v > 1000: return "🔥" # 大買
                if v > 0:    return "📈" # 小買
                if v < -1000: return "💀" # 大賣
                if v < 0:    return "📉" # 小賣
                return "⚪"

            row(
                r["日期"],
                f"{int(r['外資']):,}",
                f"{int(r['投信']):,}",
                f"{int(r['自營商']):,}",
                f"**{int(r['合計']):,}**",
                f"{get_icon(r['合計'])}"
            )
        br()
        
        # --- D. 籌碼強度分析 ---
        h(3, "💡 籌碼強度觀察")
        main_player = max([(abs(t_for),"外資"),(abs(t_trs),"投信"),(abs(t_dlr),"自營商")], key=lambda x: x[0])
        strength_desc = "大量" if abs(t_all) > 5000 else ("中量" if abs(t_all) > 1000 else "小量")
        
        quote(f"目前市場主要影響力來自 **{main_player[1]}**，整體籌碼力道屬於 **{strength_desc}**。建議追蹤 {main_player[1]} 的連買/連賣是否中斷，作為轉折參考。", "🔍")

    else:
        para("_暫無法人籌碼資料，可能原因：該股成交量極低或非證交所當日公告標的。_")
    
    br()
    hr()

    # ══════════════════════════════════════════════════════════
    # 7. 📦 產品營收結構 (營收多元化與風險分析版)
    # ══════════════════════════════════════════════════════════
    h(2, "7. 📦 產品營收結構與多元化分析")
    para("*資料來源：`product_mix.py` → 透過 HiStock 爬取最新年度/季度產品比重數據*")
    br()

    if df_mix is not None and not df_mix.empty:
        # --- 數據計算 ---
        # HHI 指數：數值平方和，反映市場集中度 (0-10000)
        hhi = (df_mix["數值"] ** 2).sum()
        top1_name = df_mix.iloc[0]["產品項目"]
        top1_val = df_mix.iloc[0]["數值"]
        top3_val = df_mix.head(3)["數值"].sum()
        
        # --- A. 產品比重排行 (視覺化增強) ---
        h(3, "📊 產品營收權重排行")
        thead("排名", "主要產品/業務項目", "營收佔比", "權重視覺化", "戰略地位")
        
        for rank, (_, r) in enumerate(df_mix.iterrows(), 1):
            val = r.get("數值", 0)
            # 建立動態長條圖
            bar_len = int(val / 4) # 以 25 字元代表 100%
            bar_vis = "█" * bar_len + "░" * (25 - bar_len)
            
            # 賦予戰略標籤
            if rank == 1 and val > 50:    status = "核心支柱 (Core)"
            elif rank <= 3 and val > 15:  status = "重要營收來源"
            elif val > 5:                 status = "成長動能/利基"
            else:                         status = "長尾/附屬業務"
            
            row(
                f"#{rank}", 
                f"**{r.get('產品項目','')}**", 
                f"{val:.1f}%", 
                f"`{bar_vis}`", 
                status
            )
        br()

        # --- B. 營收集中度風險診斷 ---
        h(3, "🎯 營收集中度與風險診斷")
        
        # 集中度分級邏輯
        if hhi > 4000:
            hhi_lv, hhi_msg = "🚨 極度集中", "營收過於仰賴單一產品，具備高度經營風險。"
        elif hhi > 2500:
            hhi_lv, hhi_msg = "⚠️ 高度集中", "產品線較單一，易受產業週期或單一市場波動影響。"
        elif hhi > 1500:
            hhi_lv, hhi_msg = "⚖️ 適中", "具備初步多元化，具備一定程度抗風險能力。"
        else:
            hhi_lv, hhi_msg = "✅ 優異分散", "產品組合極為多元，經營穩健度高。"

        thead("評估指標", "量化數值", "風險等級", "診斷說明")
        row("HHI 集中度指數", f"{hhi:.0f}", hhi_lv, hhi_msg)
        row("前三大產品合計", f"{top3_val:.1f}%", "注意" if top3_val > 80 else "正常", "反映業務核心化程度")
        row("最大支柱佔比", f"{top1_val:.1f}%", "警戒" if top1_val > 60 else "穩定", f"核心項目：{top1_name}")
        row("總產品線數量", str(len(df_mix)), "多元化參考", "支撐營收穩定性的廣度")
        br()

        # --- C. 商業戰略觀察 ---
        h(3, "💡 商業組合戰略觀察")
        if top1_val > 70:
            quote(f"該公司屬於**單一核心驅動型**。優點是規模經濟顯著且專注度高，但缺點是缺乏第二成長曲線，需關注「{top1_name}」的市場壽命與技術迭代風險。", "🚩")
        elif len(df_mix) > 5 and top1_val < 30:
            quote("該公司具備**平衡型產品矩陣**。多項業務並進，單一產品的衰退不至於動搖整體業績，具備較強的抗壓性與轉型彈性。", "🛡️")
        else:
            quote(f"該公司營收結構清晰，以「{top1_name}」為領頭羊並搭配輔助業務。建議追蹤前三大項目是否具備技術關聯性或綜效。", "🔍")

    else:
        quote("無法解析該公司的產品結構。可能原因：公司業務性質單一（如純控股或特定服務）或尚未揭露明細數據。", "ℹ️")
    
    br()
    hr()

   # ══════════════════════════════════════════════════════════
    # 8. ⚖️ 同業估值比較 (產業位階與定價分析版)
    # ══════════════════════════════════════════════════════════
    h(2, "8. ⚖️ 同業估值比較分析")
    para("*資料來源：`competitor_analysis.py` → 證交所 BWIBBU (本益比、殖利率、股價淨值比) 日報數據*")
    br()
    
    industry = info.get("產業別", "") if info else ""
    if industry:
        para(f"**當前比對產業：** `{industry}`")
        br()
        try:
            import competitor_analysis as ca
            # 取得同業資料
            df_peers = ca.get_peers_comparison(stock_id, industry)
            
            if df_peers is not None and not df_peers.empty:
                # 找出本股所在行
                target_row = df_peers[df_peers["證券代號"] == stock_id]
                peers_count = len(df_peers)
                
                # --- A. 產業排名位階 (新增分析) ---
                if not target_row.empty:
                    h(3, "🏆 產業競爭力位階")
                    # 計算排名 (處理 PE/PB 越低越好, Yield 越高越好)
                    pe_rank = df_peers["本益比"].rank(ascending=True).loc[target_row.index[0]]
                    pb_rank = df_peers["股價淨值比"].rank(ascending=True).loc[target_row.index[0]]
                    yield_rank = df_peers["殖利率(%)"].rank(ascending=False).loc[target_row.index[0]]
                    
                    thead("評比指標", "本股數值", "產業排名", "百分位數 (PCTL)", "評價")
                    def get_rank_lv(rank, total):
                        pctl = (rank / total) * 100
                        if pctl <= 25: return f"P{pctl:.0f} (頂尖)", "💎"
                        if pctl <= 50: return f"P{pctl:.0f} (前段)", "✅"
                        return f"P{pctl:.0f} (後段)", "⚠️"
                    
                    p_v, p_e = get_rank_lv(pe_rank, peers_count)
                    row("本益比 (PE)", f"{target_row.iloc[0]['本益比']:.2f}", f"{int(pe_rank)} / {peers_count}", p_v, p_e)
                    
                    y_v, y_e = get_rank_lv(yield_rank, peers_count)
                    row("殖利率 (%)", f"{target_row.iloc[0]['殖利率(%)']:.2f}%", f"{int(yield_rank)} / {peers_count}", y_v, y_e)
                    
                    b_v, b_e = get_rank_lv(pb_rank, peers_count)
                    row("股價淨值比 (PB)", f"{target_row.iloc[0]['股價淨值比']:.2f}", f"{int(pb_rank)} / {peers_count}", b_v, b_e)
                    br()

                # --- B. 同業詳細清單 (依本益比排序) ---
                h(3, f"📊 {industry} 同業估值清單 (n={peers_count})")
                thead("證券代號", "公司名稱", "本益比", "殖利率(%)", "股價淨值比", "市場標籤")
                
                # 排序並顯示前 15 名 (避免表格過長)
                display_peers = df_peers.sort_values("本益比").head(15)
                for _, r in display_peers.iterrows():
                    is_target = "⭐ **本股**" if r["證券代號"] == stock_id else ""
                    # 標註特別便宜或特別高息的股票
                    tag = "🔥 低估" if r["本益比"] < 10 and r["本益比"] > 0 else ("💰 高息" if r["殖利率(%)"] > 5 else "")
                    
                    row(
                        r.get("證券代號",""),
                        r.get("公司名稱",""),
                        f"{r.get('本益比',0):.2f}",
                        f"{r.get('殖利率(%)',0):.2f}%",
                        f"{r.get('股價淨值比',0):.2f}",
                        f"{is_target} {tag}".strip()
                    )
                if peers_count > 15:
                    para(f"*...其餘 {peers_count - 15} 家公司未在此列出。*")
                br()

                # --- C. 本股 vs 產業中位數 (比平均值更抗離群值) ---
                if not target_row.empty:
                    h(3, "⚖️ 價值診斷：本股 vs 產業中位數")
                    # 使用中位數 (Median) 避免極端值干擾 (例如 PE=1000 的公司)
                    metrics = {
                        "本益比": {"label": "本益比 (倍)", "better": "lower"},
                        "殖利率(%)": {"label": "殖利率 (%)", "better": "higher"},
                        "股價淨值比": {"label": "股價淨值比", "better": "lower"}
                    }
                    
                    thead("分析指標", "本股數值", "產業中位數", "偏離度", "市場評價")
                    for m, cfg in metrics.items():
                        my_val = target_row.iloc[0][m]
                        median_val = df_peers[m].median()
                        diff_pct = (my_val / median_val - 1) * 100 if median_val else 0
                        
                        if cfg["better"] == "lower":
                            assess = "✅ 相對便宜" if my_val < median_val else "⚠️ 相對偏貴"
                        else:
                            assess = "✅ 優於同業" if my_val > median_val else "⚠️ 低於平均"
                            
                        row(cfg["label"], f"**{my_val:.2f}**", f"{median_val:.2f}", f"{diff_pct:+.1f}%", assess)
                    br()
                    
                    # --- D. 綜合估值定論 ---
                    h(3, "💡 估值分析結論")
                    my_pe = target_row.iloc[0]["本益比"]
                    med_pe = df_peers["本益比"].median()
                    
                    if my_pe < med_pe * 0.8 and my_pe > 0:
                        quote(f"該公司目前本益比僅 **{my_pe:.2f}**，低於產業中位數約 {((1-my_pe/med_pe)*100):.0f}%，屬於**價值低估**狀態，具備安全邊際。", "💎")
                    elif my_pe > med_pe * 1.5:
                        quote(f"該公司本益比 **{my_pe:.2f}** 遠高於同業平均，市場給予較高溢價，需觀察其成長動能是否能支撐高估值。", "🚀")
                    else:
                        quote("目前估值與產業平均水平相當，股價反映合理基本面，建議配合籌碼面觀察進場時機。", "⚖️")
            else:
                para("_目前無法取得同業比較數據，可能是該產業樣本數不足。_")
        except Exception as e:
            para(f"⚠️ **同業分析模組執行失敗：** `{e}`")
    else:
        para("_無法取得公司產業類別，跳過同業比較分析。_")
    
    br()
    hr()

    # ══════════════════════════════════════════════════════════
    # 9. 🌿 ESG 永續數據 (ESG 深度診斷版)
    # ══════════════════════════════════════════════════════════
    h(2, "9. 🌿 ESG 永續經營指標")
    para("*資料來源：`esg_analyzer.py` → 臺灣證券交易所 (TWSE) OpenAPI 永續發展路徑圖系列數據*")
    br()

    try:
        import esg_analyzer as esg_mod
        analyzer = esg_mod.ESGAnalyzer()
        esg_found = False
        
        # 準備摘要數據容器
        highlights = []

        # --- A. 數據擷取與分類處理 ---
        # 為了更專業，我們將數據分為「環境(E)」、「社會(S)」、「治理(G)」三大塊
        # 這裡會遍歷 API 提供的所有端點並嘗試過濾該股票
        for category, endpoint in analyzer.endpoints.items():
            df_raw = analyzer.get_raw_data(category)
            result = analyzer.filter_by_stock(df_raw, stock_id)

            if isinstance(result, pd.DataFrame) and not result.empty:
                esg_found = True
                h(3, f"🔍 {category}")
                
                # --- 關鍵數據提取 (用於最後的摘要卡片) ---
                # 1. 薪資指標
                if "薪資" in category:
                    salary_col = next((c for c in ["本年度平均員工薪資費用","平均薪資費用","平均薪資"] if c in result.columns), None)
                    if salary_col:
                        val = result[salary_col].values[0]
                        try:
                            f_val = float(str(val).replace(",",""))
                            highlights.append(f"💰 **平均薪資**：{f_val:,.0f} 仟元")
                        except: pass
                
                # 2. 女性主管比例/董事比例
                female_col = next((c for c in ["女性董事席次", "女性主管比例", "女性主管人數"] if c in result.columns), None)
                if female_col:
                    val = result[female_col].values[0]
                    highlights.append(f"👩‍💼 **性別多樣性 ({female_col})**：{val}")

                # --- 數據表格輸出 ---
                cols = list(result.columns)
                thead(*cols)
                for _, r in result.iterrows():
                    # 對數值進行格式化（千分位）
                    formatted_row = []
                    for c in cols:
                        val = r.get(c, "")
                        try: # 嘗試轉為數字格式化
                            if isinstance(val, (int, float, str)) and str(val).replace(".","").isdigit():
                                formatted_row.append(f"{float(val):,.0f}" if float(val) > 1000 else str(val))
                            else:
                                formatted_row.append(str(val))
                        except:
                            formatted_row.append(str(val))
                    row(*formatted_row)
                br()

                # --- 針對特定類別的自動化診斷 ---
                if "薪資" in category and salary_col:
                    val = float(str(result[salary_col].values[0]).replace(",",""))
                    if val > 1500:
                        quote(f"該公司平均薪資達 {val:,.0f} 仟元，具備極強的人才吸引力與競爭優勢。", "✅")
                    elif val < 600:
                        quote(f"該公司平均薪資偏低 ({val:,.0f} 仟元)，需關注其基層員工流動率風險。", "⚠️")
                
                if "溫室氣體" in category:
                    quote("已啟動溫室氣體盤查，顯示公司正積極應對氣候變遷與淨零排放政策。", "🌱")

            # 處理 API 為空或無資料的情況
            elif isinstance(result, str) and result == "EMPTY_API":
                # 靜默處理或記錄
                pass

        # --- B. ESG 亮點摘要框 ---
        if esg_found and highlights:
            h(3, "📊 企業永續亮點摘要")
            L.append("```text")
            L.append(f"┌──────────────── ESG 關鍵數據速覽 ────────────────┐")
            for h_item in highlights:
                # 移除 Markdown 加粗以便在文本框顯示
                clean_h = h_item.replace("**", "")
                L.append(f"  {clean_h}")
            L.append(f"└──────────────────────────────────────────────────┘")
            L.append("```")
            br()

        if not esg_found:
            br()
            quote(f"股票代號 {stock_id} 目前在證交所 ESG 資料庫中尚無揭露資訊。這通常發生在：\n1. 該公司尚未達到法令規定的強制揭露規模。\n2. 該年度資料尚未完成上傳申報。", "ℹ️")

    except Exception as e:
        para(f"⚠️ **ESG 模組執行異常：** `{e}`")
    
    br()
    hr()

    # ══════════════════════════════════════════════════════════
    # 10. 📈 官方財報彙總 (審核級深度摘要版)
    # ══════════════════════════════════════════════════════════
    h(2, "10. 🏛️ 證交所官方財報全指標")
    para("*資料來源：`financial_analyzer.py` → 臺灣證券交易所 (TWSE) OpenAPI t187ap 系列 (含資產負債、損益、現金流量等 10 項指標)*")
    br()

    try:
        import financial_analyzer as fa_mod
        fin_anal = fa_mod.FinancialAnalyzer()
        fin_found = False

        # --- A. 核心財務摘要大字卡 ---
        # 預先抓取資產負債表進行核心指標計算
        df_bs_raw = fin_anal.get_data("資產負債表彙總")
        df_bs = fin_anal.filter_by_stock(df_bs_raw, stock_id)
        
        if not df_bs.empty:
            latest_bs = df_bs.iloc[0]
            def _clean(v): return float(str(v).replace(",","").strip()) if not pd.isna(v) and str(v).strip() != "" else 0
            
            # 自動偵測欄位名稱 (適應 API 變動)
            a_col = next((c for c in ["資產總額","資產總計"] if c in df_bs.columns), None)
            l_col = next((c for c in ["負債總額","負債總計"] if c in df_bs.columns), None)
            e_col = next((c for c in ["權益總額","權益總計","股東權益總額"] if c in df_bs.columns), None)
            
            if a_col and l_col:
                ta = _clean(latest_bs[a_col])
                tl = _clean(latest_bs[l_col])
                te = _clean(latest_bs[e_col]) if e_col else (ta - tl)
                dr = (tl / ta * 100) if ta else 0
                
                L.append("```text")
                L.append(f"┌────────────────── 官方財報核心規模速覽 ──────────────────┐")
                L.append(f"  報告期間：{latest_bs.get('出表日期', latest_bs.get('年度', 'N/A'))}")
                L.append(f"  總 資 產：{ta:15,.0f} (單位：仟元)")
                L.append(f"  總 負 債：{tl:15,.0f} (單位：仟元)")
                L.append(f"  股東權益：{te:15,.0f} (單位：仟元)")
                L.append(f"  負債比率：{dr:14.2f}%  [{'⚠️ 偏高' if dr > 65 else '✅ 穩健'}]")
                L.append(f"└──────────────────────────────────────────────────────────┘")
                L.append("```")
                br()

        # --- B. 各項財報明細分頁輸出 ---
        for category in fin_anal.fin_endpoints.keys():
            df_raw = fin_anal.get_data(category)
            target_fin = fin_anal.filter_by_stock(df_raw, stock_id)

            if not target_fin.empty:
                fin_found = True
                h(3, f"📊 {category}")
                
                # 選取前 10 個核心欄位避免 Markdown 表格過寬
                cols = list(target_fin.columns)
                display_cols = cols[:10] if len(cols) > 10 else cols
                
                thead(*display_cols)
                for _, r in target_fin.iterrows():
                    # 數值千分位處理
                    formatted_row = []
                    for c in display_cols:
                        val = r.get(c, "")
                        if isinstance(val, (int, float)) or (isinstance(val, str) and val.replace(".","").replace(",","").isdigit()):
                            try:
                                formatted_row.append(f"{float(str(val).replace(',','')):,.0f}")
                            except:
                                formatted_row.append(str(val))
                        else:
                            formatted_row.append(str(val))
                    row(*formatted_row)
                
                if len(cols) > 10:
                    para(f"*注：僅列出前 10 項核心欄位，其餘 {len(cols)-10} 項欄位請參閱 Excel 完整報表。*")
                br()

                # --- 智慧型監控洞察 ---
                if "損益" in category:
                    rev_col = next((c for c in ["營業收入合計","營業收入"] if c in target_fin.columns), None)
                    if rev_col and _clean(target_fin.iloc[0][rev_col]) < 0:
                        quote("偵測到單季營收異常值，請確認是否為會計準則調整或季節性因素。", "🚨")
            else:
                # 僅在開發調試時顯示，正式報告保持整潔
                pass

        if not fin_found:
            quote(f"目前證交所官方 API 尚未更新 {stock_id} 的最新年度財務彙總數據。", "ℹ️")

    except Exception as e:
        para(f"⚠️ **官方財報分析模組異常：** `{str(e)}`")
    
    br()
    hr()

    # ══════════════════════════════════════════════════════════
    # 11. 📰 新聞雷達摘要 (NewsAPI 強化版)
    # ══════════════════════════════════════════════════════════
    h(2, "11. 📰 新聞雷達摘要")
    para("*資料來源：`news_analyzer.py` → NewsAPI 全球新聞檢索*")
    br()
    
    try:
        import news_analyzer as news_mod
        # 取得清洗後的核心公司名稱
        search_name = news_mod.clean_company_name(company_name)
        
        # 這裡建議設定一個預設統計單字，例如「獲利」或「成長」
        target_word = "獲利" 
        h(3, f"📊 關鍵字分析：{search_name}")
        para(f"本節針對關鍵字「**{target_word}**」在新聞中的出現頻率進行統計分析。")
        br()

        # 呼叫與網頁端一致的 search_news_api 函數
        # 注意：此處需傳入您的 NewsAPI Key
        api_news = news_mod.search_news_api(
            company_name=search_name, 
            target_word=target_word,
            api_key="api" # 建議從 st.secrets 或變數傳入
        )

        if api_news:
            for i, n in enumerate(api_news, 1):
                count = n.get("關鍵字計數", 0)
                title = n.get("標題", "無標題")
                
                # 標題標註出現次數
                h(4, f"{i}. 【關鍵字出現 {count} 次】 {title}")
                
                thead("項目", "內容")
                row("日期", n.get("日期", "")[:10]) # 僅取日期部分
                row("來源", n.get("來源", "媒體"))
                row("連結", f"[點擊閱讀原文]({n.get('連結', '#')})")
                br()
                
                # 輸出新聞摘要 (描述內容)
                desc = n.get("顯示內容", "")
                if desc:
                    para(f"**新聞摘要：**")
                    para(f"> {desc}")
                else:
                    para("> (此新聞暫無可用摘要內容)")
                br()
        else:
            quote(f"目前查無「{search_name}」相關的新聞報導。", "ℹ️")
            br()
            
    except Exception as e:
        para(f"⚠️ **新聞資料彙整失敗：** `{str(e)}`")
        br()
    
    hr()

    # ── 頁尾 ──────────────────────────────────────────────────
    br()
    L.append(f"*本報告由「智慧財務分析系統 Pro Complete」自動產生 ｜ {now}*")
    br()
    L.append("*⚠ 本報告資料僅供參考，不構成任何投資建議。投資前請審慎評估自身風險承受能力。*")

    return "\n".join(L).encode("utf-8")


# ==========================================
# 側邊欄
# ==========================================
with st.sidebar:
    st.markdown("## 🎯 系統控制台")
    
    # Logo 或圖示
    st.markdown("---")
    
    # 股票代號輸入
    stock_id = st.text_input(
        "📈 股票代號",
        value="2753",
        help="請輸入台股代號（例如：2330）",
        key="stock_input"
    )
    
    st.markdown("---")
    
    # API 密鑰設定
    st.markdown("### 🔑 AI 引擎設定")
    with st.expander("設定 API 密鑰", expanded=False):
        google_api_key = st.text_input(
            "Google Gemini API Key",
            value="Google Gemini API Key",
            type="password",
            help="用於 PDF 文件分析"
        )
        
        if google_api_key:
            st.success("✅ Google API 已連接")
    
    st.markdown("---")
    
    # 功能選單
    st.markdown("### 📋 顯示模組")
    show_overview = st.checkbox("📊 公司概覽", value=True)
    show_financial = st.checkbox("💰 財務分析", value=True)
    show_financial = st.checkbox("📈 官方財報彙總", value=True)   # 新增：證交所 10 項 API 分頁
    show_chips = st.checkbox("🎯 籌碼分析", value=True)
    show_competitors = st.checkbox("⚖️ 同業比較", value=True)
    show_product = st.checkbox("📦 產品結構", value=True)
    show_news = st.checkbox("📰 新聞雷達", value=True)
    show_esg = st.checkbox("🌿 ESG 永續數據", value=True) # <-- 新增這行
    show_pdf = st.checkbox("🤖 PDF 對話", value=True)
    show_concentration = st.checkbox("🔍 集中度分析", value=False)
    show_sbom = st.sidebar.checkbox("🛡️ 顯示系統 SBOM", value=False)
    st.markdown("---")
    
    # 系統資訊
    st.markdown("### ℹ️ 系統資訊")
    st.caption(f"版本：Complete v3.0")
    st.caption(f"更新：{datetime.now().strftime('%Y-%m-%d')}")
    st.caption("Python 3.12 完全兼容")
    
    st.markdown("---")
    
    # 快速操作
    if st.button("🔄 重新整理數據", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")

    # 自動儲存設定
    st.markdown("### 💾 自動儲存設定")
    auto_save = st.checkbox("🚀 載入完成後自動儲存 Markdown", value=True)
    output_folder = st.text_input(
        "📁 儲存資料夾路徑",
        value="./reports",
        help="伺服器上的絕對或相對路徑，例如：./reports 或 /home/user/分析報告"
    )
    if output_folder:
        st.caption(f"📂 將儲存至：`{output_folder}/`")

# ==========================================
# 主頁面標題
# ==========================================
st.markdown('<h1 class="main-header">📊 智慧財務分析系統 Pro Complete</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-header">當前分析：<b style="color:#667eea;">{stock_id}</b> | 系統時間：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>', unsafe_allow_html=True)

# ==========================================
# 主內容區域
# ==========================================
if stock_id:
    # 數據載入進度
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    with st.spinner('🔄 正在載入數據...'):
        # 階段 1: 基本資訊
        status_text.text('載入基本資訊...')
        progress_bar.progress(10)
        info = ci.get_company_basic_info(stock_id)
        company_name = info.get('公司名稱', stock_id)
        
        # 階段 2: 財務數據
        status_text.text('分析財務數據...')
        progress_bar.progress(30)
        df_ratios, insights, score_data = fd.get_comprehensive_analysis(stock_id)
        
        # 階段 3: 股價數據
        status_text.text('抓取股價資料...')
        progress_bar.progress(50)
        df_price = fetch_stock_history(stock_id)
        
        # 階段 4: 籌碼數據
        status_text.text('追蹤法人籌碼...')
        progress_bar.progress(65)
        df_chips = chips.get_chips_data(stock_id, days=10)
        
        # 階段 5: 產品結構
        status_text.text('分析產品結構...')
        progress_bar.progress(80)
        df_mix = pm.get_revenue_mix(stock_id)
        
        # 階段 6: 完成
        status_text.text('數據載入完成！')
        progress_bar.progress(100)
        time.sleep(0.5)
    
    # 清除進度顯示
    progress_bar.empty()
    status_text.empty()

    # ==========================================
    # 自動儲存 Markdown 到指定資料夾
    # ==========================================
    if auto_save and score_data:
        try:
            import os
            # 建立資料夾（若不存在）
            os.makedirs(output_folder, exist_ok=True)

            # 產生報告內容
            md_bytes = _build_markdown_report(
                stock_id=stock_id,
                company_name=company_name,
                info=info,
                df_price=df_price,
                df_ratios=df_ratios,
                insights=insights,
                score_data=score_data,
                df_chips=df_chips,
                df_mix=df_mix,
            )

            # 儲存檔案（用時間戳記避免覆蓋）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_filename = f"{stock_id}_{company_name}_{timestamp}.md"
            save_path = os.path.join(output_folder, save_filename)

            with open(save_path, "wb") as f:
                f.write(md_bytes)

            # 記錄到 session state，讓頁面顯示儲存成功訊息
            st.session_state["last_save_path"] = save_path
            st.session_state["last_save_name"] = save_filename

        except Exception as e:
            st.session_state["last_save_error"] = str(e)

    # 顯示自動儲存結果（在頁面最上方）
    if "last_save_path" in st.session_state:
        st.success(
            f"✅ Markdown 報告已自動儲存至：`{st.session_state['last_save_path']}`",
            icon="💾"
        )
        # 只顯示一次後清除
        del st.session_state["last_save_path"]
    if "last_save_error" in st.session_state:
        st.warning(
            f"⚠️ 自動儲存失敗：{st.session_state['last_save_error']}（請確認路徑是否有寫入權限）",
            icon="⚠️"
        )
        del st.session_state["last_save_error"]
    
    # ==========================================
    # Tab 導航系統
    # ==========================================
    tab_list = []
    if show_overview: tab_list.append("📊 公司概覽")
    if show_financial: tab_list.append("💰 財務分析")      # 原有的分析邏輯
    if show_financial: tab_list.append("📈 官方財報彙總")   # 新增：證交所 10 項 API 分頁
    if show_chips: tab_list.append("🎯 籌碼分析")
    if show_competitors: tab_list.append("⚖️ 同業比較")
    if show_product: tab_list.append("📦 產品結構")
    if show_news: tab_list.append("📰 新聞雷達")
    if show_esg: tab_list.append("🌿 ESG 數據") # <-- 新增這行
    if show_pdf: tab_list.append("🤖 PDF 對話")
    if show_concentration: tab_list.append("🔍 集中度分析")
    


    if tab_list:
        tabs = st.tabs(tab_list)
        tab_idx = 0
        
        # ==========================================
        # Tab 1: 公司概覽
        # ==========================================
        if show_overview:
            with tabs[tab_idx]:
                st.markdown("### 🏢 公司基本資訊")
                
                if info and '公司名稱' in info:
                    # 核心指標卡片
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("公司名稱", info.get('公司名稱', 'N/A'))
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("產業別", info.get('產業別', 'N/A'))
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("董事長", info.get('董事長', 'N/A'))
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col4:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("總經理", info.get('總經理', 'N/A'))
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # 股價走勢圖
                    if df_price is not None and not df_price.empty:
                        st.markdown("### 📈 股價走勢與成交量")
                        
                        # 創建子圖
                        fig = make_subplots(
                            rows=2, cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.03,
                            row_heights=[0.7, 0.3],
                            subplot_titles=('股價K線圖', '成交量')
                        )
                        
                        # K線圖
                        fig.add_trace(go.Candlestick(
                            x=df_price['日期'],
                            open=df_price['開盤價'],
                            high=df_price['最高價'],
                            low=df_price['最低價'],
                            close=df_price['收盤價'],
                            name='K線'
                        ), row=1, col=1)
                        
                        # 成交量
                        colors = ['red' if df_price.iloc[i]['收盤價'] >= df_price.iloc[i]['開盤價'] 
                                 else 'green' for i in range(len(df_price))]
                        
                        fig.add_trace(go.Bar(
                            x=df_price['日期'],
                            y=df_price['成交股數'],
                            name='成交量',
                            marker_color=colors
                        ), row=2, col=1)
                        
                        fig.update_layout(
                            title=f'{stock_id} {company_name} - 近6個月走勢',
                            xaxis_title='日期',
                            yaxis_title='股價 (元)',
                            height=700,
                            hovermode='x unified',
                            xaxis_rangeslider_visible=False
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 股價統計
                        col1, col2, col3, col4, col5 = st.columns(5)
                        latest_price = df_price.iloc[-1]['收盤價']
                        price_change = latest_price - df_price.iloc[-2]['收盤價'] if len(df_price) > 1 else 0
                        price_change_pct = (price_change / df_price.iloc[-2]['收盤價'] * 100) if len(df_price) > 1 else 0
                        
                        col1.metric("最新股價", f"${latest_price:.2f}", f"{price_change:+.2f} ({price_change_pct:+.2f}%)")
                        col2.metric("最高價", f"${df_price['最高價'].max():.2f}")
                        col3.metric("最低價", f"${df_price['最低價'].min():.2f}")
                        col4.metric("平均價", f"${df_price['收盤價'].mean():.2f}")
                        col5.metric("平均成交量", f"{df_price['成交股數'].mean()/1000:.0f}K")
                    
                    st.markdown("---")
                    
                    # 詳細資訊
                    with st.expander("📋 查看完整公司資訊", expanded=False):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 👥 經營團隊")
                            st.write(f"**董事長**：{info.get('董事長', 'N/A')}")
                            st.write(f"**總經理**：{info.get('總經理', 'N/A')}")
                            st.write(f"**發言人**：{info.get('發言人', 'N/A')}")
                            st.write(f"**代理發言人**：{info.get('代理發言人', 'N/A')}")
                            
                            st.markdown("#### 📞 聯絡資訊")
                            st.write(f"**電話**：{info.get('總機電話', 'N/A')}")
                            st.write(f"**傳真**：{info.get('傳真號碼', 'N/A')}")
                            st.write(f"**信箱**：{info.get('電子郵件', 'N/A')}")
                            st.write(f"**地址**：{info.get('公司地址', 'N/A')}")
                        
                        with col2:
                            st.markdown("#### 💼 公司資訊")
                            st.write(f"**成立日期**：{info.get('成立日期', 'N/A')}")
                            st.write(f"**上市日期**：{info.get('上市日期', 'N/A')}")
                            st.write(f"**統一編號**：{info.get('統一編號', 'N/A')}")
                            st.write(f"**實收資本額**：{info.get('實收資本額', 'N/A')}")
                            st.write(f"**已發行股數**：{info.get('已發行股數', 'N/A')}")
                            st.write(f"**股務代理**：{info.get('股務代理', 'N/A')}")
                            
                            st.markdown("#### 📝 公司簡介")
                            st.info(info.get('公司簡介', '無簡介'))
                else:
                    st.error(f"❌ 找不到股票代號 {stock_id} 的資料")
            
            tab_idx += 1
        
        # ==========================================
        # Tab 2: 財務分析
        # ==========================================
        if show_financial:
            with tabs[tab_idx]:
                st.markdown("### 💰 財務健康度全面分析")
                
                if score_data and df_ratios is not None:
                    # 評分儀表板區域
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        score = score_data['總分']
                        grade = score_data['評級']
                        
                        if score >= 80:
                            score_color = "#4caf50"
                            status_emoji = "🟢"
                        elif score >= 60:
                            score_color = "#ff9800"
                            status_emoji = "🟡"
                        else:
                            score_color = "#f44336"
                            status_emoji = "🔴"
                        
                        st.markdown(f"""
                        <div class="score-display" style="background: linear-gradient(135deg, {score_color}20, {score_color}40); border: 3px solid {score_color};">
                            <div style="font-size: 2rem;">{status_emoji}</div>
                            <div style="color: {score_color};">{score}</div>
                            <div style="font-size: 1.3rem; color: #666; margin-top: 10px;">評級：{grade}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        # Z-Score 儀表
                        z_score = score_data.get('Z-Score', 0)
                        fig_z = create_gauge_chart(z_score, "Altman Z-Score", max_value=5)
                        st.plotly_chart(fig_z, use_container_width=True)
                        
                        z_status = score_data.get('Z-Status', 'N/A')
                        if z_score > 2.99:
                            st.success(f"✅ {z_status}")
                        elif z_score > 1.81:
                            st.warning(f"⚠️ {z_status}")
                        else:
                            st.error(f"❌ {z_status}")
                    
                    with col3:
                        # ROE 儀表
                        if not df_ratios.empty:
                            roe = df_ratios.iloc[0]['ROE (%)']
                            fig_roe = create_gauge_chart(roe, "ROE (%)", max_value=30)
                            st.plotly_chart(fig_roe, use_container_width=True)
                            
                            if roe > 15:
                                st.success("✅ 股東權益報酬率優異")
                            elif roe > 8:
                                st.info("ℹ️ 股東權益報酬率一般")
                            else:
                                st.warning("⚠️ 股東權益報酬率偏低")
                    
                    st.markdown("---")
                    
                    # 財務指標卡片
                    st.markdown("#### 📊 關鍵財務指標")
                    
                    if not df_ratios.empty:
                        latest = df_ratios.iloc[0]
                        
                        # 第一排指標
                        col1, col2, col3, col4, col5 = st.columns(5)
                        
                        with col1:
                            val = latest['毛利率 (%)']
                            delta = None
                            if len(df_ratios) > 1:
                                delta = val - df_ratios.iloc[1]['毛利率 (%)']
                            st.metric("毛利率", f"{val:.2f}%", f"{delta:+.2f}%" if delta else None)
                        
                        with col2:
                            val = latest['營業利益率 (%)']
                            delta = None
                            if len(df_ratios) > 1:
                                delta = val - df_ratios.iloc[1]['營業利益率 (%)']
                            st.metric("營業利益率", f"{val:.2f}%", f"{delta:+.2f}%" if delta else None)
                        
                        with col3:
                            val = latest['淨利率 (%)']
                            delta = None
                            if len(df_ratios) > 1:
                                delta = val - df_ratios.iloc[1]['淨利率 (%)']
                            st.metric("淨利率", f"{val:.2f}%", f"{delta:+.2f}%" if delta else None)
                        
                        with col4:
                            st.metric("流動比率", f"{latest['流動比率 (%)']:.2f}%")
                        
                        with col5:
                            st.metric("負債比率", f"{latest['負債比率 (%)']:.2f}%")
                        
                        # 第二排指標
                        col1, col2, col3, col4, col5 = st.columns(5)
                        
                        with col1:
                            st.metric("速動比率", f"{latest['速動比率 (%)']:.2f}%")
                        
                        with col2:
                            st.metric("利息保障", f"{latest['利息保障倍數 (倍)']:.2f}倍")
                        
                        with col3:
                            st.metric("自由現金流", f"{latest['自由現金流 (億)']:.2f}億")
                        
                        with col4:
                            st.metric("資產周轉率", f"{latest['資產周轉率 (次)']:.2f}次")
                        
                        with col5:
                            st.metric("CCC", f"{latest['現金週轉循環 (天)']:.1f}天")
                    
                    st.markdown("---")
                    
                    # 評分細項與趨勢
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.markdown("##### 📊 評分細項分析")
                        
                        if '細項' in score_data:
                            score_df = pd.DataFrame(score_data['細項'])
                            
                            fig = px.bar(
                                score_df,
                                y='項目',
                                x='得分',
                                text='評語',
                                orientation='h',
                                color='得分',
                                color_continuous_scale=['red', 'yellow', 'green'],
                                range_color=[-10, 20]
                            )
                            
                            fig.update_layout(
                                height=400,
                                xaxis_title="得分",
                                yaxis_title="",
                                showlegend=False
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.markdown("##### 📈 財務趨勢洞察")
                        
                        if insights:
                            for insight in insights:
                                if "🟢" in insight or "優異" in insight or "改善" in insight:
                                    st.markdown(f'<div class="success-box">{insight}</div>', unsafe_allow_html=True)
                                elif "🔴" in insight or "高風險" in insight or "危險" in insight:
                                    st.markdown(f'<div class="danger-box">{insight}</div>', unsafe_allow_html=True)
                                elif "🟠" in insight or "偏低" in insight or "偏高" in insight:
                                    st.markdown(f'<div class="warning-box">{insight}</div>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div class="info-box">{insight}</div>', unsafe_allow_html=True)
                    
                    # 完整財報數據
                    with st.expander("📊 查看完整財報數據", expanded=False):
                        st.dataframe(df_ratios, use_container_width=True, hide_index=True)
                
                else:
                    st.error("❌ 無法獲取財務數據")
            
            tab_idx += 1
      # ==========================================
        # Tab: 官方財報彙總 (獨立模組強化版)
        # ==========================================
        if show_financial:
            with tabs[tab_idx]:
                st.markdown("### 📈 證交所官方財務報告全指標")
                st.caption(f"🚀 正在針對股票代號：{stock_id} 檢索 10 項官方財報數據...")
                
                # 初始化財報分析器
                import financial_analyzer as fa
                fin_anal = fa.FinancialAnalyzer() 
                
                for category in fin_anal.fin_endpoints.keys():
                    with st.expander(f"📊 財報細節：{category}", expanded=False):
                        with st.spinner(f'正在載入 {category}...'):
                            df_raw = fin_anal.get_data(category)
                            target_fin = fin_anal.filter_by_stock(df_raw, stock_id)
                        
                        if not target_fin.empty:
                            # --- [核心強化] 針對「資產負債表彙總」顯示指標卡片 ---
                            if category == "資產負債表彙總":
                                try:
                                    # 1. 取得最新一筆資料
                                    latest = target_fin.iloc[0]
                                    
                                    # 2. 定義關鍵欄位 (自動適應不同 API 命名)
                                    a_col = next((c for c in ['資產總額', '資產總計'] if c in target_fin.columns), None)
                                    l_col = next((c for c in ['負債總額', '負債總計'] if c in target_fin.columns), None)
                                    e_col = next((c for c in ['權益總額', '權益總計', '股東權益總額'] if c in target_fin.columns), None)
                                    
                                    if a_col and l_col:
                                        # 3. 數字清洗 (移除逗號並轉為數字)
                                        def clean_num(val):
                                            if pd.isna(val): return 0
                                            return float(str(val).replace(',', '').strip())

                                        total_assets = clean_num(latest[a_col])
                                        total_debt = clean_num(latest[l_col])
                                        debt_ratio = (total_debt / total_assets * 100) if total_assets != 0 else 0
                                        
                                        # 4. 顯示漂亮卡片
                                        c1, c2, c3 = st.columns(3)
                                        with c1:
                                            st.metric("總資產 (單位同表)", f"{total_assets:,.0f}")
                                        with c2:
                                            st.metric("總負債 (單位同表)", f"{total_debt:,.0f}")
                                        with c3:
                                            st.metric("負債比率", f"{debt_ratio:.2f}%", delta_color="inverse")
                                        
                                        st.divider()
                                except Exception as e:
                                    st.caption(f"指標計算中... (詳細請看下方表格)")

                            # 顯示完整表格
                            st.markdown(f"**{category} 原始數據清單：**")
                            st.dataframe(target_fin, use_container_width=True, hide_index=True)
                            st.success(f"✅ {category} 加載完成")
                        else:
                            st.info(f"💡 目前「{category}」尚無該公司公開數據。")
                
                st.divider()
                st.caption("數據來源：臺灣證券交易所 OpenAPI")

            tab_idx += 1
        # ==========================================
        # Tab 3: 籌碼分析
        # ==========================================
        if show_chips:
            with tabs[tab_idx]:
                st.markdown("### 🎯 三大法人籌碼動向")
                
                if df_chips is not None and not df_chips.empty:
                    # 籌碼統計
                    col1, col2, col3, col4 = st.columns(4)
                    
                    total_foreign = df_chips['外資'].sum()
                    total_trust = df_chips['投信'].sum()
                    total_dealer = df_chips['自營商'].sum()
                    total_all = df_chips['合計'].sum()
                    
                    col1.metric("外資買賣超", f"{total_foreign:,}張", 
                               "買超" if total_foreign > 0 else "賣超")
                    col2.metric("投信買賣超", f"{total_trust:,}張",
                               "買超" if total_trust > 0 else "賣超")
                    col3.metric("自營商買賣超", f"{total_dealer:,}張",
                               "買超" if total_dealer > 0 else "賣超")
                    col4.metric("三大法人合計", f"{total_all:,}張",
                               "買超" if total_all > 0 else "賣超")
                    
                    st.markdown("---")
                    
                    # 籌碼走勢圖
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=df_chips['日期'],
                        y=df_chips['外資'],
                        name='外資',
                        mode='lines+markers',
                        line=dict(color='#2196F3', width=3)
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=df_chips['日期'],
                        y=df_chips['投信'],
                        name='投信',
                        mode='lines+markers',
                        line=dict(color='#4CAF50', width=3)
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=df_chips['日期'],
                        y=df_chips['自營商'],
                        name='自營商',
                        mode='lines+markers',
                        line=dict(color='#FF9800', width=3)
                    ))
                    
                    fig.update_layout(
                        title=f'{stock_id} 三大法人籌碼變化',
                        xaxis_title='日期',
                        yaxis_title='買賣超 (張)',
                        height=500,
                        hovermode='x unified'
                    )
                    
                    fig.add_hline(y=0, line_dash="dash", line_color="gray")
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 籌碼表格
                    with st.expander("📋 查看詳細籌碼數據", expanded=False):
                        st.dataframe(df_chips, use_container_width=True, hide_index=True)
                    
                    # 籌碼解讀
                    st.markdown("#### 💡 籌碼解讀")
                    
                    if total_all > 0:
                        st.markdown('<div class="success-box">✅ 三大法人近期呈現<b>買超</b>態勢，籌碼面偏多</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="warning-box">⚠️ 三大法人近期呈現<b>賣超</b>態勢，籌碼面偏空</div>', unsafe_allow_html=True)
                    
                    if abs(total_foreign) == max(abs(total_foreign), abs(total_trust), abs(total_dealer)):
                        st.info(f"🔍 外資是主要交易力量，累計{total_foreign:+,}張")
                
                else:
                    st.warning("⚠️ 無法獲取籌碼數據")
            
            tab_idx += 1
        
        # ==========================================
        # Tab 4: 同業比較
        # ==========================================
        if show_competitors:
            with tabs[tab_idx]:
                st.markdown("### ⚖️ 同業估值比較")
                
                industry = info.get('產業別', '')
                
                if industry:
                    st.caption(f"產業分類：**{industry}**")
                    
                    with st.spinner('正在比較同業資料...'):
                        df_peers = ca.get_peers_comparison(stock_id, industry)
                    
                    if df_peers is not None and not df_peers.empty:
                        # 比較圖表
                        tab1, tab2, tab3 = st.tabs(["📊 本益比比較", "💰 殖利率比較", "📈 股價淨值比"])
                        
                        with tab1:
                            st.markdown("##### 本益比 (PE Ratio) 比較")
                            st.caption("本益比越低，相對越便宜")
                            
                            fig = px.bar(
                                df_peers.sort_values('本益比'),
                                x='公司名稱',
                                y='本益比',
                                text='本益比',
                                color='證券代號',
                                color_discrete_map={stock_id: '#667eea'},
                                color_discrete_sequence=['#cccccc']
                            )
                            
                            fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                            fig.update_layout(
                                height=500,
                                showlegend=False,
                                xaxis_tickangle=-45
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with tab2:
                            st.markdown("##### 殖利率 (Dividend Yield) 比較")
                            st.caption("殖利率越高，配息越優渥")
                            
                            fig = px.bar(
                                df_peers.sort_values('殖利率(%)', ascending=False),
                                x='公司名稱',
                                y='殖利率(%)',
                                text='殖利率(%)',
                                color='證券代號',
                                color_discrete_map={stock_id: '#764ba2'},
                                color_discrete_sequence=['#cccccc']
                            )
                            
                            fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                            fig.update_layout(
                                height=500,
                                showlegend=False,
                                xaxis_tickangle=-45
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with tab3:
                            st.markdown("##### 股價淨值比 (PB Ratio) 比較")
                            st.caption("股價淨值比反映市場對公司資產的評價")
                            
                            fig = px.bar(
                                df_peers.sort_values('股價淨值比'),
                                x='公司名稱',
                                y='股價淨值比',
                                text='股價淨值比',
                                color='證券代號',
                                color_discrete_map={stock_id: '#4CAF50'},
                                color_discrete_sequence=['#cccccc']
                            )
                            
                            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                            fig.update_layout(
                                height=500,
                                showlegend=False,
                                xaxis_tickangle=-45
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # 同業數據表格
                        with st.expander("📋 查看完整同業數據", expanded=False):
                            st.dataframe(df_peers, use_container_width=True, hide_index=True)
                    
                    else:
                        st.info("該產業資料不足或無同業可比較")
                
                else:
                    st.warning("無法識別產業類別")
            
            tab_idx += 1
        
        # ==========================================
        # Tab 5: 產品結構
        # ==========================================
        if show_product:
            with tabs[tab_idx]:
                st.markdown("### 📦 產品營收結構分析")
                
                if df_mix is not None and not df_mix.empty:
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # 甜甜圈圖
                        fig = px.pie(
                            df_mix,
                            values='數值',
                            names='產品項目',
                            title=f'{company_name} 營收來源分布',
                            hole=0.5
                        )
                        
                        fig.update_traces(
                            textposition='inside',
                            textinfo='percent+label',
                            textfont_size=12
                        )
                        
                        fig.update_layout(height=500)
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.markdown("#### 📊 營收佔比排行")
                        
                        for idx, row in df_mix.head(10).iterrows():
                            pct = row['數值']
                            if pct > 30:
                                color = "success"
                            elif pct > 15:
                                color = "info"
                            else:
                                color = "secondary"
                            
                            st.markdown(f"""
                            <div style="margin: 10px 0;">
                                <b>{row['產品項目']}</b>
                                <div style="background-color: #f0f0f0; border-radius: 10px; height: 25px; position: relative;">
                                    <div style="background: linear-gradient(90deg, #667eea, #764ba2); width: {pct}%; height: 100%; border-radius: 10px;"></div>
                                    <span style="position: absolute; right: 10px; top: 2px; color: #333; font-weight: bold;">{pct:.1f}%</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # 集中度分析
                    st.markdown("#### 🎯 營收集中度評估")
                    
                    top3_ratio = df_mix.head(3)['數值'].sum()
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("前三大產品佔比", f"{top3_ratio:.1f}%")
                    col2.metric("產品線數量", len(df_mix))
                    col3.metric("赫芬達爾指數", f"{(df_mix['數值']**2).sum():.0f}")
                    
                    if top3_ratio > 70:
                        st.markdown('<div class="warning-box">⚠️ 營收高度集中於少數產品，存在風險集中度</div>', unsafe_allow_html=True)
                    elif top3_ratio > 50:
                        st.markdown('<div class="info-box">ℹ️ 營收較為集中，建議關注主力產品動態</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="success-box">✅ 營收來源分散，風險相對平衡</div>', unsafe_allow_html=True)
                    
                    # 詳細表格
                    with st.expander("📋 查看完整產品數據", expanded=False):
                        st.dataframe(df_mix, use_container_width=True, hide_index=True)
                
                else:
                    st.warning("⚠️ 無法獲取產品結構數據")
                    st.info("💡 提示：部分公司可能未公開詳細產品營收結構")
            
            tab_idx += 1
        # ==========================================
        # Tab: ESG 數據分析 (偵錯強化完整版)
        # ==========================================
        if show_esg:
            with tabs[tab_idx]:
                st.markdown("### 🌿 企業永續 (ESG) 全指標監控")
                st.caption(f"🚀 正在針對股票代號：{stock_id} 檢索 10 項 ESG 指標...")

                import esg_analyzer as esg
                analyzer = esg.ESGAnalyzer()

                # 使用單一迴圈跑完所有端點
                for category in analyzer.endpoints.keys():
                    with st.expander(f"🔍 查看：{category}", expanded=False):
                        with st.spinner(f'正在調取 {category} 資料...'):
                            # 抓取資料並透過強化版過濾器進行判斷
                            df_raw = analyzer.get_raw_data(category)
                            target_esg = analyzer.filter_by_stock(df_raw, stock_id)

                        # --- 判斷邏輯開始 ---
                        # 情況 1: API 完全沒給資料 (可能是證交所伺服器端該年度空值)
                        if isinstance(target_esg, str) and target_esg == "EMPTY_API":
                            st.warning(f"⚠️ 證交所 {category} API 目前伺服器端無資料回傳。")
                        
                        # 情況 2: 有資料但過濾失敗 (這會顯示 API 內的實際欄位讓你核對)
                        elif isinstance(target_esg, dict) and target_esg.get("debug"):
                            st.error(f"❌ 找不到代號 {stock_id}，但 API 裡有其他公司資料。")
                            st.write(f"該 API 實際使用的欄位：`{target_esg['columns']}`")
                            st.write("資料範例 (前三筆)：")
                            st.dataframe(target_esg["sample"], use_container_width=True)
                        
                        # 情況 3: 成功過濾出該公司的資料
                        elif isinstance(target_esg, pd.DataFrame) and not target_esg.empty:
                            # 如果是薪資類，額外顯示大字卡
                            if "薪資" in category:
                                possible_salary_cols = ['本年度平均員工薪資費用', '平均薪資費用', '平均薪資']
                                salary_col = next((c for c in possible_salary_cols if c in target_esg.columns), None)
                                if salary_col:
                                    avg_val = target_esg[salary_col].values[0]
                                    st.metric("平均員工薪資", f"{float(avg_val):,.0f} 仟元")
                            
                            st.dataframe(target_esg, use_container_width=True, hide_index=True)
                            st.success(f"✅ {category} 數據載入成功")
                        
                        # 情況 4: 其他未預期狀況
                        else:
                            st.info(f"💡 目前「{category}」項目尚無公開數據。")

                st.divider()
                st.caption("數據來源：臺灣證券交易所 OpenAPI")

            tab_idx += 1
        # ==========================================
        # Tab: 新聞雷達 (NewsAPI 關鍵字統計版)
        # ==========================================
        if show_news:
            with tabs[tab_idx]:
                # 1. 取得清洗後的核心公司名稱 (例如: 台積電)
                target_company = news.clean_company_name(company_name)
                
                st.markdown(f"### 📰 新聞雷達 — {target_company}")
                
                # 2. 控制列：輸入要統計的目標單字
                c1, c2 = st.columns([2, 2])
                with c1:
                    target_word = st.text_input("📊 要統計的目標單字", value="獲利", help="統計此單字在標題與摘要中出現的次數")
                with c2:
                    page_size = st.slider("抓取篇數", 5, 50, 20)

                st.divider()

                # 3. 執行 NewsAPI 搜尋
                # 請確保你的 news_analyzer.py 中已有 search_news_api 函式
                # 這裡會依據你輸入的股票代號自動轉換的公司名來搜尋
                with st.spinner(f"正在廣域搜尋 {target_company} 相關新聞..."):
                    api_news = news.search_news_api(
                        company_name=target_company, 
                        target_word=target_word,
                        api_key="NewsAPI" # 建議填入你的金鑰
                    )

                if not api_news:
                    st.warning(f"❌ 找不到與「{target_company}」相關的新聞")
                else:
                    st.success(f"✅ 成功抓取 {len(api_news)} 篇相關新聞")
                    
                    # 4. 顯示新聞與統計結果
                    for i, n in enumerate(api_news, 1):
                        title = n.get("標題", "無標題")
                        desc = n.get("顯示內容", "")
                        url = n.get("連結", "#")
                        count = n.get("關鍵字計數", 0)
                        source = n.get("來源", "媒體")
                        date_str = n.get("日期", "")[:10] # 僅取日期部分

                        # 利用關鍵字出現次數作為標題開頭
                        with st.expander(f"[{count}次] {title}"):
                            st.markdown(f"**📅 發布日期：** {date_str} | **📡 來源：** {source}")
                            st.write(f"**摘要：** {desc}")
                            st.write(f"關鍵字「**{target_word}**」在此文出現次數：`{count}`")
                            st.markdown(f"[🔗 閱讀原文]({url})")
                            
                            # 簡單的情緒視覺化提示
                            if count > 0:
                                st.toast(f"發現關鍵字：{target_word}", icon="🔍")

                st.divider()
                st.caption(f"數據來源：NewsAPI (搜尋對象：{target_company})")

            tab_idx += 1
        # ==========================================
        # Tab 7: PDF 智能對話
        # ==========================================
        if show_pdf:
            with tabs[tab_idx]:
                st.markdown("### 🤖 PDF 文件智能解析與對話")
                
                if google_api_key:
                    # 初始化 RAG 系統
                    if 'rag_system' not in st.session_state:
                        with st.spinner('初始化 AI 引擎...'):
                            st.session_state.rag_system = FinancialRAG(google_api_key=google_api_key)
                    
                    rag = st.session_state.rag_system
                    
                    # 文件上傳區
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        uploaded_file = st.file_uploader(
                            "📂 上傳 PDF 文件",
                            type=['pdf'],
                            help="支援：年報、季報、財報、研究報告等",
                            key="pdf_uploader"
                        )
                    
                    with col2:
                        st.markdown("#### 💡 功能說明")
                        st.markdown("""
                        - 智能文件解析
                        - 自然語言問答
                        - 精準引用來源
                        - 支援中英文
                        """)
                    
                    if uploaded_file is not None:
                        # 檢查是否需要重新上傳
                        if 'active_file_name' not in st.session_state or st.session_state.active_file_name != uploaded_file.name:
                            progress = st.progress(0)
                            status = st.empty()
                            
                            status.text('📄 正在上傳文件...')
                            progress.progress(30)
                            
                            # 保存臨時文件
                            temp_path = f"temp_{uploaded_file.name}"
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            status.text('🔍 AI 正在解析文件內容...')
                            progress.progress(60)
                            
                            # 上傳到 Gemini
                            msg = rag.ingest_pdf(temp_path, uploaded_file.name)
                            
                            progress.progress(100)
                            status.empty()
                            progress.empty()
                            
                            st.session_state.active_file_name = uploaded_file.name
                            st.success(msg)
                        
                        st.markdown("---")
                        
                        # 對話界面
                        st.markdown("#### 💬 智能對話助手")
                        
                        # 初始化對話歷史
                        if 'chat_history' not in st.session_state:
                            st.session_state.chat_history = []
                        
                        # 對話容器
                        chat_container = st.container()
                        
                        with chat_container:
                            # 顯示歷史對話
                            for chat in st.session_state.chat_history:
                                with st.chat_message("user"):
                                    st.write(chat['question'])
                                with st.chat_message("assistant"):
                                    st.write(chat['answer'])
                                    if chat.get('sources'):
                                        with st.expander("📚 參考來源"):
                                            for src in chat['sources']:
                                                st.caption(src)
                        
                        # 問題輸入
                        user_question = st.chat_input("輸入您的問題...", key="pdf_chat_input")
                        
                        if user_question:
                            # 顯示用戶問題
                            with chat_container:
                                with st.chat_message("user"):
                                    st.write(user_question)
                                
                                # 獲取 AI 回答
                                with st.chat_message("assistant"):
                                    with st.spinner("🤔 AI 分析中..."):
                                        answer, sources = rag.query(user_question)
                                        st.write(answer)
                                        
                                        if sources:
                                            with st.expander("📚 參考來源"):
                                                for src in sources:
                                                    st.caption(src)
                            
                            # 保存對話歷史
                            st.session_state.chat_history.append({
                                'question': user_question,
                                'answer': answer,
                                'sources': sources
                            })
                            
                            st.rerun()
                        
                        # 操作按鈕
                        col1, col2, col3 = st.columns([1, 1, 2])
                        
                        with col1:
                            if st.button("🗑️ 清除對話", use_container_width=True):
                                st.session_state.chat_history = []
                                st.rerun()
                        
                        with col2:
                            if st.button("📥 匯出對話", use_container_width=True):
                                # 匯出對話記錄
                                chat_text = ""
                                for chat in st.session_state.chat_history:
                                    chat_text += f"Q: {chat['question']}\n\nA: {chat['answer']}\n\n---\n\n"
                                
                                st.download_button(
                                    label="下載對話記錄",
                                    data=chat_text,
                                    file_name=f"對話記錄_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                    mime="text/plain"
                                )
                    
                    else:
                        # 未上傳文件的提示
                        st.info("👆 請上傳 PDF 文件開始智能對話")
                        
                        # 示例問題
                        st.markdown("#### 📝 問題示例")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("""
                            **基本查詢**
                            - 公司的營收是多少？
                            - 主要產品有哪些？
                            - 董事長是誰？
                            - 公司在哪裡設立？
                            """)
                        
                        with col2:
                            st.markdown("""
                            **深度分析**
                            - 前五大客戶是誰？
                            - 研發費用佔營收比例？
                            - 公司面臨的主要風險？
                            - 未來發展策略是什麼？
                            """)
                
                else:
                    st.warning("⚠️ 請在側邊欄設定 Google API Key 以啟用此功能")
                    
                    with st.expander("如何取得 API Key？", expanded=True):
                        st.markdown("""
                        1. 前往 [Google AI Studio](https://makersuite.google.com/app/apikey)
                        2. 登入 Google 帳號
                        3. 點擊「Create API Key」
                        4. 複製 API Key
                        5. 在側邊欄「AI 引擎設定」中貼上
                        """)
            
            tab_idx += 1
        
        # ==========================================
        # Tab 8: 集中度分析 (選用)
        # ==========================================
        if show_concentration:
            with tabs[tab_idx]:
                st.markdown("### 🔍 客戶與供應商集中度分析")
                
                st.info("💡 請上傳公司年報 PDF 以分析客戶與供應商集中度")
                
                conc_file = st.file_uploader(
                    "📂 上傳年報 PDF",
                    type=['pdf'],
                    key="conc_uploader"
                )
                
                if conc_file is not None:
                    if st.button("🔍 開始分析", use_container_width=True):
                        progress = st.progress(0)
                        status = st.empty()
                        
                        def update_progress(current, total):
                            pct = int((current / total) * 100)
                            progress.progress(pct)
                            status.text(f'正在分析第 {current}/{total} 頁...')
                        
                        df_customers, df_suppliers = conc.extract_concentration_risk(
                            conc_file,
                            progress_callback=update_progress
                        )
                        
                        progress.empty()
                        status.empty()
                        
                        if df_customers is not None or df_suppliers is not None:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### 👥 主要客戶")
                                
                                if df_customers is not None and not df_customers.empty:
                                    # 圓餅圖
                                    fig = px.pie(
                                        df_customers.head(10),
                                        values='數值',
                                        names='名稱',
                                        title='客戶集中度分布'
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                    
                                    # 數據表
                                    st.dataframe(df_customers, use_container_width=True, hide_index=True)
                                    
                                    # 分析
                                    top5 = df_customers.head(5)['數值'].sum()
                                    if top5 > 50:
                                        st.warning(f"⚠️ 前五大客戶佔比 {top5:.1f}%，集中度偏高")
                                    else:
                                        st.success(f"✅ 前五大客戶佔比 {top5:.1f}%，集中度合理")
                                else:
                                    st.info("未找到客戶資料")
                            
                            with col2:
                                st.markdown("#### 🏭 主要供應商")
                                
                                if df_suppliers is not None and not df_suppliers.empty:
                                    # 圓餅圖
                                    fig = px.pie(
                                        df_suppliers.head(10),
                                        values='數值',
                                        names='名稱',
                                        title='供應商集中度分布'
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                    
                                    # 數據表
                                    st.dataframe(df_suppliers, use_container_width=True, hide_index=True)
                                    
                                    # 分析
                                    top5 = df_suppliers.head(5)['數值'].sum()
                                    if top5 > 50:
                                        st.warning(f"⚠️ 前五大供應商佔比 {top5:.1f}%，集中度偏高")
                                    else:
                                        st.success(f"✅ 前五大供應商佔比 {top5:.1f}%，集中度合理")
                                else:
                                    st.info("未找到供應商資料")
                        
                        else:
                            st.error("❌ 未能從 PDF 中提取集中度資料")
                            st.info("請確認上傳的是完整的公司年報")
    # 在 Tab 內容區
    if show_sbom:
        with tabs[tab_idx]:
            st.markdown("### 🛡️ 軟體物料清單 (Software Bill of Materials)")
            st.caption("確保財務分析系統使用的所有第三方套件均受監控與合規。")
        
            gen = sbom.SBOMGenerator()
            df_sbom = gen.get_system_inventory()
        
            #顯示統計
            st.metric("監控組件總數", len(df_sbom))
            st.dataframe(df_sbom, use_container_width=True, hide_index=True)
        
            # 下載按鈕
            st.download_button(
                "📥 下載系統標準 BOM (JSON)",
                data=df_sbom.to_json(orient='records'),
                file_name=f"SBOM_{stock_id}.json",
                mime="application/json"
            )
        tab_idx += 1

    # ==========================================
    # 底部：下載完整報告
    # ==========================================
    st.markdown("---")
    
    if score_data:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("### 📥 匯出完整分析報告")

            # ── Excel 報告 ──────────────────────────
            with st.spinner('正在產生 Excel 報告...'):
                excel_data = rg.generate_excel_report(
                    stock_id, info, df_price, df_ratios,
                    df_chips, score_data, df_mix
                )
            file_name_xlsx = f"{stock_id}_{company_name}_完整分析報告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            st.download_button(
                label="📊 下載 Excel 完整報告",
                data=excel_data,
                file_name=file_name_xlsx,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.caption("報告包含：徵信摘要、評分明細、財務數據、籌碼分析、產品結構、股價走勢")

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Markdown 完整報告 ────────────────────
            with st.spinner('正在產生 Markdown 報告...'):
                md_data = _build_markdown_report(
                    stock_id=stock_id,
                    company_name=company_name,
                    info=info,
                    df_price=df_price,
                    df_ratios=df_ratios,
                    insights=insights,
                    score_data=score_data,
                    df_chips=df_chips,
                    df_mix=df_mix,
                )
            file_name_md = f"{stock_id}_{company_name}_完整分析報告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            st.download_button(
                label="📄 一鍵下載 Markdown 完整分析報告",
                data=md_data,
                file_name=file_name_md,
                mime="text/markdown",
                use_container_width=True
            )
            st.caption("涵蓋所有模組：公司資訊 · 股價 · 財務評分 · 17+指標 · AI洞察 · 籌碼 · 同業 · 產品結構 · ESG · 新聞")

else:
    # 歡迎頁面
    st.markdown("""
    <div style="text-align: center; padding: 80px 20px;">
        <h2 style="color: #667eea; font-size: 2.5rem; margin-bottom: 20px;">
            歡迎使用智慧財務分析系統 Pro Complete
        </h2>
        <p style="font-size: 1.3rem; color: #666; margin-bottom: 40px;">
            全方位股票分析工具 | AI 驅動 | 專業級報告
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 功能介紹卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #667eea;">📊 公司概覽</h3>
            <p>完整基本資訊<br>股價走勢分析<br>K線圖視覺化</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #667eea;">💰 財務分析</h3>
            <p>信用評分系統<br>Z-Score 風險<br>17+ 財務指標</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #667eea;">🎯 籌碼追蹤</h3>
            <p>三大法人動向<br>買賣超統計<br>籌碼趨勢圖</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #667eea;">🤖 AI 對話</h3>
            <p>PDF 智能解析<br>自然語言問答<br>深度文件分析</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #764ba2;">⚖️ 同業比較</h3>
            <p>本益比排名<br>殖利率比較<br>估值分析</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #764ba2;">📦 產品結構</h3>
            <p>營收比重<br>集中度評估<br>產品組合</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #764ba2;">📰 新聞雷達</h3>
            <p>正負面追蹤<br>即時更新<br>智能過濾</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #764ba2;">📥 報告輸出</h3>
            <p>Excel 完整報告<br>多工作表<br>一鍵下載</p>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 頁腳
# ==========================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 30px;">
    <p style="font-size: 1.1rem; margin-bottom: 10px;">
        <b>智慧財務分析系統 Pro Complete v3.0</b>
    </p>
    <p style="font-size: 0.95rem; color: #888;">
        Powered by Streamlit, Plotly, Google Gemini AI
    </p>
    <p style="font-size: 0.9rem; color: #999; margin-top: 15px;">
        ⚠️ 投資有風險，本系統僅供參考，不構成投資建議
    </p>
</div>
""", unsafe_allow_html=True)
