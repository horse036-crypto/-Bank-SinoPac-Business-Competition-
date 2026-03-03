import yfinance as yf
import pandas as pd

# ==========================================
# 您的客製化業界標準 (Benchmark)
# ==========================================
BENCHMARKS = {
    "毛利率": {"中位數": 43.50, "偏低注意": 34.84, "高風險": 26.75},
    "營業利益率": {"中位數": 8.43, "偏低注意": 5.67, "高風險": 3.18},
    "淨利率": {"中位數": 6.56, "偏低注意": 3.80, "高風險": 0.43},
    "流動比率": {"中位數": 121, "偏低注意": 91, "高風險": 61},
    "負債比率": {"中位數": 52, "偏高注意": 62.7, "高風險": 73.3},
    # [新增] 銀行核貸關鍵指標
    "利息保障倍數": {"中位數": 5, "偏低注意": 2.5, "高風險": 1.5} 
}

# --- 輔助函式 1: 產生文字解讀 ---
def check_benchmark(name, value, criteria, higher_is_better=True):
    if higher_is_better:
        if value < criteria["高風險"]: return f"🔴 **【標準】{name}高風險**：僅 {value} (低於高風險線 {criteria['高風險']})。"
        elif value < criteria["偏低注意"]: return f"🟠 **【標準】{name}偏低**：僅 {value} (低於注意線 {criteria['偏低注意']})。"
        elif value >= criteria["中位數"]: return f"🟢 **【標準】{name}優異**：達 {value} (優於中位數 {criteria['中位數']})。"
        else: return f"⚪ **【標準】{name}尚可**：{value} (介於注意線與中位數之間)。"
    else:
        if value > criteria["高風險"]: return f"🔴 **【標準】{name}高風險**：高達 {value} (超過高風險線 {criteria['高風險']})。"
        elif value > criteria["偏高注意"]: return f"🟠 **【標準】{name}偏高**：達 {value} (超過注意線 {criteria['偏高注意']})。"
        elif value <= criteria["中位數"]: return f"🟢 **【標準】{name}安全**：僅 {value} (優於中位數 {criteria['中位數']})。"
        else: return f"⚪ **【標準】{name}尚可**：{value} (介於中位數與警戒線之間)。"

# --- 輔助函式 2: 計算得分 ---
def get_score_and_comment(value, criteria, higher_is_better=True):
    score = 0
    comment = ""
    if higher_is_better:
        if value < criteria["高風險"]: score = 0; comment = "危險"
        elif value < criteria["偏低注意"]: score = 10; comment = "注意"
        elif value >= criteria["中位數"]: score = 20; comment = "優良"
        else: score = 15; comment = "普通"
    else:
        if value > criteria["高風險"]: score = 0; comment = "危險"
        elif value > criteria["偏高注意"]: score = 10; comment = "注意"
        elif value <= criteria["中位數"]: score = 20; comment = "優良"
        else: score = 15; comment = "普通"
    return score, comment

# --- 主程式 ---
def get_comprehensive_analysis(stock_code):
    """
    [財報分析模組 V6.0 - 銀行核貸完全版]
    新增：利息保障倍數 (Interest Coverage Ratio)
    """
    ticker = yf.Ticker(f"{stock_code}.TW")
    try:
        fin = ticker.financials
        bs = ticker.balance_sheet
        cf = ticker.cashflow
        
        try:
            info = ticker.info
            market_cap = info.get('marketCap', 0)
        except: market_cap = 0

        if fin.empty or bs.empty: return None, [], None

        data_list = []
        insights = []
        years = fin.columns[:3]
        
        for date in years:
            year_str = str(date.year)
            
            # Helper function
            def get_val(df, key): return df.loc[key, date] if key in df.index else 0
            
            # 1. 抓取數據
            rev = get_val(fin, 'Total Revenue')
            net_income = get_val(fin, 'Net Income')
            op_income = get_val(fin, 'Operating Income')
            cost = get_val(fin, 'Cost Of Revenue')
            ebit = get_val(fin, 'EBIT') if 'EBIT' in fin.index else op_income
            
            # [新增] 利息費用 (有些財報會寫 Interest Expense，有些在 Net Interest Income 裡)
            interest_expense = abs(get_val(fin, 'Interest Expense'))
            if interest_expense == 0:
                # 嘗試另一種欄位名稱
                interest_expense = abs(get_val(fin, 'Interest Expense Non Operating'))
            
            total_assets = get_val(bs, 'Total Assets')
            total_liab = get_val(bs, 'Total Liabilities Net Minority Interest')
            curr_assets = get_val(bs, 'Current Assets')
            curr_liab = get_val(bs, 'Current Liabilities')
            stockholder_equity = get_val(bs, 'Stockholders Equity')
            retained_earnings = get_val(bs, 'Retained Earnings')
            inventory = get_val(bs, 'Inventory')
            
            ocf = get_val(cf, 'Operating Cash Flow')
            capex = abs(get_val(cf, 'Capital Expenditure'))
            
            # 2. 計算公式
            gross_margin = ((rev - cost) / rev * 100) if rev else 0
            op_margin = op_income / rev * 100 if rev else 0
            net_margin = net_income / rev * 100 if rev else 0
            roe = net_income / stockholder_equity * 100 if stockholder_equity else 0
            curr_ratio = curr_assets / curr_liab * 100 if curr_liab else 0
            debt_ratio = total_liab / total_assets * 100 if total_assets else 0
            quality_ratio = ocf / net_income * 100 if net_income else 0
            
            # 進階指標
            fcf = ocf - capex
            asset_turnover = rev / total_assets if total_assets else 0
            leverage = total_assets / stockholder_equity if stockholder_equity else 1
            working_capital = curr_assets - curr_liab
            
            # 速動比
            quick_assets = curr_assets - inventory
            quick_ratio = quick_assets / curr_liab * 100 if curr_liab else 0
            
            # CCC (簡化版)
            receivables = get_val(bs, 'Net Receivables')
            payables = get_val(bs, 'Accounts Payable')
            dso = (receivables / rev) * 365 if rev else 0
            dio = (inventory / cost) * 365 if cost else 0
            dpo = (payables / cost) * 365 if cost else 0
            ccc = dso + dio - dpo
            
            # [新增] 利息保障倍數 = EBIT / 利息費用
            if interest_expense > 0:
                interest_coverage = ebit / interest_expense
            else:
                interest_coverage = 999 # 代表無利息壓力，極好
                
            # Z-Score
            z_score = 0
            if total_assets > 0 and total_liab > 0:
                A = working_capital / total_assets
                B = retained_earnings / total_assets
                C = ebit / total_assets
                D = market_cap / total_liab if market_cap > 0 else 0
                E = rev / total_assets
                z_score = 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E

            # 3. 存入表格
            data_list.append({
                "期間": f"{year_str}",
                "毛利率 (%)": round(gross_margin, 2),
                "營業利益率 (%)": round(op_margin, 2),
                "淨利率 (%)": round(net_margin, 2),
                "ROE (%)": round(roe, 2),
                "流動比率 (%)": round(curr_ratio, 2),
                "負債比率 (%)": round(debt_ratio, 2),
                "速動比率 (%)": round(quick_ratio, 2),
                "利息保障倍數 (倍)": round(interest_coverage, 2), # 新增
                "Z-Score": round(z_score, 2),
                "自由現金流 (億)": round(fcf / 100000000, 2),
                "現金週轉循環 (天)": round(ccc, 1),
                "應收帳款天數 (DSO)": round(dso, 1),
                "存貨週轉天數 (DIO)": round(dio, 1),
                "應付帳款天數 (DPO)": round(dpo, 1),
                "資產周轉率 (次)": round(asset_turnover, 2),
                "權益乘數 (倍)": round(leverage, 2),
                "資料來源": f"https://tw.stock.yahoo.com/quote/{stock_code}.TW/financials"
            })

        df_result = pd.DataFrame(data_list)
        score_details = {} 
        
        # 4. 產生解讀與評分
        if len(data_list) >= 1:
            latest = data_list[0]
            
            # 趨勢分析
            if len(data_list) >= 2:
                prev = data_list[1]
                diff_gross = latest['毛利率 (%)'] - prev['毛利率 (%)']
                if diff_gross > 1: insights.append(f"📈 **【趨勢】毛利率改善**：+{diff_gross:.2f}%")
                elif diff_gross < -1: insights.append(f"📉 **【趨勢】毛利率衰退**：{diff_gross:.2f}%")

            # 業界標準解讀
            insights.append(check_benchmark("毛利率", latest['毛利率 (%)'], BENCHMARKS["毛利率"], True))
            insights.append(check_benchmark("負債比率", latest['負債比率 (%)'], BENCHMARKS["負債比率"], False))
            # [新增] 利息保障倍數解讀
            if latest['利息保障倍數 (倍)'] == 999:
                 insights.append("🟢 **【標準】償債能力極強**：幾乎無利息支出。")
            else:
                 insights.append(check_benchmark("利息保障倍數", latest['利息保障倍數 (倍)'], BENCHMARKS["利息保障倍數"], True))

            # 信用評分計算 (加入利息保障倍數作為加分項)
            s1, c1 = get_score_and_comment(latest['毛利率 (%)'], BENCHMARKS["毛利率"], True)
            s2, c2 = get_score_and_comment(latest['營業利益率 (%)'], BENCHMARKS["營業利益率"], True)
            s3, c3 = get_score_and_comment(latest['淨利率 (%)'], BENCHMARKS["淨利率"], True)
            s4, c4 = get_score_and_comment(latest['流動比率 (%)'], BENCHMARKS["流動比率"], True)
            s5, c5 = get_score_and_comment(latest['負債比率 (%)'], BENCHMARKS["負債比率"], False)
            
            # [調整] 總分計算邏輯：如果利息保障倍數太差，直接扣分
            total_score = s1 + s2 + s3 + s4 + s5
            icr = latest['利息保障倍數 (倍)']
            icr_comment = "正常"
            icr_score = 0
            
            if icr < 2: 
                total_score -= 10 # 懲罰性扣分
                icr_comment = "🔴 危險 (扣10分)"
                icr_score = -10
            elif icr >= 5 or icr == 999:
                total_score += 5 # 獎勵性加分 (最多加到100)
                if total_score > 100: total_score = 100
                icr_comment = "🟢 優異 (加5分)"
                icr_score = 5

            if total_score >= 90: grade = "AAA (極優)"
            elif total_score >= 80: grade = "AA (優異)"
            elif total_score >= 70: grade = "A (良好)"
            elif total_score >= 60: grade = "B (尚可)"
            else: grade = "C (高風險)"

            z = latest['Z-Score']
            if z > 2.99: z_status = "安全區 (Safe)"
            elif z > 1.81: z_status = "灰色警示 (Grey)"
            else: z_status = "破產高險 (Distress)"

            score_details = {
                "總分": total_score,
                "評級": grade,
                "Z-Score": z,
                "Z-Status": z_status,
                "細項": [
                    {"項目": "毛利率", "數值": latest['毛利率 (%)'], "評語": c1, "得分": s1},
                    {"項目": "營業利益率", "數值": latest['營業利益率 (%)'], "評語": c2, "得分": s2},
                    {"項目": "淨利率", "數值": latest['淨利率 (%)'], "評語": c3, "得分": s3},
                    {"項目": "流動比率", "數值": latest['流動比率 (%)'], "評語": c4, "得分": s4},
                    {"項目": "負債比率", "數值": latest['負債比率 (%)'], "評語": c5, "得分": s5},
                    {"項目": "利息保障倍數", "數值": latest['利息保障倍數 (倍)'], "評語": icr_comment, "得分": icr_score},
                ]
            }

        return df_result, insights, score_details
        
    except Exception as e:
        print(f"Analysis Error: {e}")
        return None, [], None