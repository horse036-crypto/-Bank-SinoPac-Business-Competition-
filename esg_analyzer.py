import requests
import pandas as pd
import streamlit as st

class ESGAnalyzer:
    def __init__(self):
        self.base_url = "https://openapi.twse.com.tw/v1"
        self.endpoints = {
            "溫室氣體": "/opendata/t187ap46_L_1",
            "能源管理": "/opendata/t187ap46_L_2",
            "廢棄物管理": "/opendata/t187ap46_L_3",
            "員工薪資": "/opendata/t187ap46_L_5",
            "職安訓練": "/opendata/t187ap46_L_4",
            "產品安全": "/opendata/t187ap46_L_13",
            "董事會多元": "/opendata/t187ap46_L_6",
            "法規遵循": "/opendata/t187ap46_L_8",
            "委員會設置": "/opendata/t187ap46_L_9",
            "供應鏈管理": "/opendata/t187ap46_L_11"
        }

    @st.cache_data(ttl=3600)
    def get_raw_data(_self, category):
        endpoint = _self.endpoints.get(category)
        url = f"{_self.base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return pd.DataFrame(data)
                else:
                    # 這裡是重點：如果 API 回傳空的，代表這項指標目前證交所沒資料
                    return "EMPTY_API" 
            return None
        except:
            return None

    def filter_by_stock(self, df, stock_code):
        if isinstance(df, str) and df == "EMPTY_API":
            return "EMPTY_API"
        
        if df is not None and not df.empty:
            # 所有的比對都要轉成字串，並去掉空格
            stock_str = str(stock_code).strip()
            
            # 證交所 API 的常見代號欄位名稱
            id_cols = ['公司代號', '公司編號', '出表公司代號', '證券代號', '公司代碼']
            
            # 找到現有的欄位
            actual_col = next((c for c in df.columns if c in id_cols), None)
            
            if actual_col:
                # 執行篩選
                filtered = df[df[actual_col].astype(str).str.strip() == stock_str]
                if filtered.empty:
                    # 如果篩選完是空的，我們回傳一小段原始資料來 debug
                    return {"debug": True, "columns": df.columns.tolist(), "sample": df.head(3)}
                return filtered
        return pd.DataFrame()