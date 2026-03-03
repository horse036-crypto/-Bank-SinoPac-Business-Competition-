import pandas as pd
import io

def generate_excel_report(stock_id, info, df_price, df_ratios, df_chips, score_data, df_mix):
    """
    [銀行級報表產生器 V3.0]
    將所有分析數據 (含 Z-Score, 信用評分, 籌碼, CCC, 產品結構) 打包成 Excel
    """
    output = io.BytesIO()
    
    # 使用 ExcelWriter 寫入多個 Sheet
    # engine='xlsxwriter' 是 pandas 內建支援的引擎
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        
        # ==========================================
        # Sheet 1: 銀行徵信摘要 (Executive Summary)
        # ==========================================
        
        # 準備基本數據
        company_name = info.get('公司名稱', 'N/A')
        industry = info.get('產業別', 'N/A')
        price = df_price.iloc[-1]['收盤價'] if df_price is not None else 0
        
        # 從 score_data 提取信用資訊
        score = score_data.get('總分', 0) if score_data else 0
        grade = score_data.get('評級', 'N/A') if score_data else 'N/A'
        z_score = score_data.get('Z-Score', 0) if score_data else 0
        z_status = score_data.get('Z-Status', 'N/A') if score_data else 'N/A'
        
        # 建立摘要表格
        summary_data = {
            "項目": [
                "股票代號", "公司名稱", "產業別", "最新股價", 
                "銀行內部評分", "信用評級", 
                "破產風險 (Z-Score)", "風險狀態"
            ],
            "數值": [
                stock_id, company_name, industry, price,
                f"{score} 分", grade,
                z_score, z_status
            ]
        }
        
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='徵信摘要', index=False)
        
        # ==========================================
        # Sheet 2: 信用評分細節 (Credit Details)
        # ==========================================
        if score_data and '細項' in score_data:
            df_score = pd.DataFrame(score_data['細項'])
            df_score.to_excel(writer, sheet_name='評分明細', index=False)
            
        # ==========================================
        # Sheet 3: 完整財務數據 (Financials)
        # ==========================================
        if df_ratios is not None:
            # 這裡面已經包含了: 速動比、CCC、FCF、利息保障倍數
            df_ratios.to_excel(writer, sheet_name='財務數據', index=False)

        # ==========================================
        # Sheet 4: 產品營收結構 (Business Mix) [新增]
        # ==========================================
        if df_mix is not None and not df_mix.empty:
            df_mix.to_excel(writer, sheet_name='產品營收比重', index=False)
            
        # ==========================================
        # Sheet 5: 法人籌碼 (Chips)
        # ==========================================
        if df_chips is not None:
            df_chips.to_excel(writer, sheet_name='法人籌碼', index=False)
            
        # ==========================================
        # Sheet 6: 股價歷史 (Price History)
        # ==========================================
        if df_price is not None:
            # 只留最近 60 天就好
            df_price.tail(60).to_excel(writer, sheet_name='股價走勢', index=False)
            
    return output.getvalue()