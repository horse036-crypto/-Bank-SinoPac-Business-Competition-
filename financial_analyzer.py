import requests
import pandas as pd
import streamlit as st

class FinancialAnalyzer:
    def __init__(self):
        self.base_url = "https://openapi.twse.com.tw/v1"
        # 專屬於官方財報的 10 個 API
        self.fin_endpoints = {
            "資產負債表彙總": "/opendata/t187ap03_L",
            "綜合損益表彙總": "/opendata/t187ap02_L",
            "現金流量表彙總": "/opendata/t187ap04_L",
            "營收產銷量值彙總": "/opendata/t187ap05_L",
            "個別財務報告彙總": "/opendata/t187ap11_L",
            "財務比率分析彙總": "/opendata/t187ap14_L",
            "資本額及股利彙總": "/opendata/t187ap16_L",
            "負擔背書保證彙總": "/opendata/t187ap22_L",
            "資金貸與他人彙總": "/opendata/t187ap24_L",
            "內部人持股彙總": "/opendata/t187ap30_L"
        }

    @st.cache_data(ttl=3600)
    def get_data(_self, category):
        endpoint = _self.fin_endpoints.get(category)
        if not endpoint: return pd.DataFrame()
        try:
            url = f"{_self.base_url}{endpoint}"
            # 增加 timeout 到 15 秒，因為財報資料量較大
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                df = pd.DataFrame(res.json())
                # 這裡做一個簡單的資料清洗：移除欄位名稱中的換行符號
                df.columns = [c.replace('\n', '') for c in df.columns]
                return df
        except Exception as e:
            print(f"API 連線異常 ({category}): {e}")
        return pd.DataFrame()

    def filter_by_stock(self, df, stock_code):
        """強化的自動偵測篩選器"""
        if df is not None and not df.empty:
            # 優先搜尋代號欄位
            id_cols = ['公司代號', '公司編號', '出表公司代號', '證券代號', '公司代碼', '公司代號/編號']
            target_col = next((c for c in df.columns if c in id_cols), None)
            
            # 如果找不到精確欄位，找包含 '公司' 且包含 '代' 的欄位
            if not target_col:
                target_col = next((c for c in df.columns if '公司' in c and '代' in c), None)

            if target_col:
                # 轉成字串並去除空白，確保 2330 == "2330 "
                return df[df[target_col].astype(str).str.strip() == str(stock_code).strip()]
        return pd.DataFrame()

    def get_balance_sheet_metrics(self, stock_code):
        """專門針對資產負債表 (t187ap03_L) 提取關鍵數據"""
        df = self.get_data("資產負債表彙總")
        target = self.filter_by_stock(df, stock_code)
        
        if not target.empty:
            # 提取範例：你可以根據實際 API 欄位微調這些 Key
            metrics = {
                "資產總計": target.get('資產總額', target.get('資產總計', ['N/A'])).values[0],
                "負債總計": target.get('負債總額', target.get('負債總計', ['N/A'])).values[0],
                "權益總計": target.get('權益總額', target.get('權益總計', ['N/A'])).values[0]
            }
            return metrics
        return None