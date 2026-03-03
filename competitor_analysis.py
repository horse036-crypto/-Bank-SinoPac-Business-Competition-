import requests
import pandas as pd
import streamlit as st

# ==========================================
# 1. 抓取大盤個股數據 (只抓數據，不抓名稱)
# ==========================================
@st.cache_data(ttl=3600)
def get_market_stats():
    """
    從證交所抓取：本益比、殖利率、股價淨值比
    API: BWIBBU_ALL
    """
    url = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL"
    try:
        res = requests.get(url, verify=False)
        data = res.json()
        df = pd.DataFrame(data)
        
        # 【修正點】
        # 1. 這裡只重新命名數據欄位
        # 2. 我們故意不抓 'Name'，避免跟產業表的 '公司名稱' 衝突
        df = df.rename(columns={
            'Code': '證券代號',
            'PEratio': '本益比',
            'DividendYield': '殖利率(%)',
            'PBratio': '股價淨值比'
        })
        
        # 只保留我們需要的數據欄位
        keep_cols = ['證券代號', '本益比', '殖利率(%)', '股價淨值比']
        # 防呆：確保這些欄位真的存在 (避免 API 改版導致報錯)
        available_cols = [c for c in keep_cols if c in df.columns]
        df = df[available_cols]

        # 資料清洗：將 "-" 轉為 0，並轉成數字格式
        for col in ['本益比', '殖利率(%)', '股價淨值比']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace('-', '0'), errors='coerce')
            
        return df
    except Exception as e:
        print(f"同業資料抓取失敗: {e}")
        return pd.DataFrame()

# ==========================================
# 2. 抓取產業分類表 (名稱以此為準)
# ==========================================
@st.cache_data(ttl=86400)
def get_industry_map():
    """
    抓取「股票代號」對應「產業別」
    API: T187AP03_L
    """
    url = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
    try:
        res = requests.get(url, verify=False)
        data = res.json()
        df = pd.DataFrame(data)
        
        # 這裡有我們要的 '公司名稱'
        return df[['公司代號', '公司名稱', '產業別']]
    except:
        return pd.DataFrame()

# ==========================================
# 3. 核心功能：產生同業比較表
# ==========================================
def get_peers_comparison(target_code, target_industry):
    """
    輸入：目標股票代號、產業
    輸出：該產業的同業比較表 (DataFrame)
    """
    # 1. 取得數據
    df_stats = get_market_stats()    # 有：證券代號, 本益比...
    df_industry = get_industry_map() # 有：公司代號, 公司名稱, 產業別
    
    if df_stats.empty or df_industry.empty:
        return None

    # 2. 合併資料
    # 使用 inner join，這樣合併後就會有：
    # [證券代號, 本益比..., 公司名稱, 產業別]
    # 因為 df_stats 裡沒有 '公司名稱'，所以不會產生 _x, _y 的衝突
    df_merged = pd.merge(
        df_stats, 
        df_industry, 
        left_on='證券代號', 
        right_on='公司代號', 
        how='inner'
    )
    
    # 3. 篩選同產業
    df_peers = df_merged[df_merged['產業別'] == target_industry].copy()
    
    if df_peers.empty:
        return None

    # 4. 確保目標股票在裡面 (防呆)
    if target_code not in df_peers['證券代號'].values:
        # 有時候目標股票可能因為本益比是負的被證交所標記異常，或者資料沒對上
        # 我們嘗試從 df_merged 裡硬抓出來補進去
        target_row = df_merged[df_merged['證券代號'] == target_code]
        if not target_row.empty:
            df_peers = pd.concat([df_peers, target_row])
        else:
            return None # 真的找不到這支股票

    # 5. 排序與取樣
    # 過濾異常值 (本益比太高或太低的) 讓圖表好看一點
    df_clean = df_peers[(df_peers['本益比'] > 0) & (df_peers['本益比'] < 200)].sort_values('本益比')
    
    # 如果過濾後目標股票不見了，把它救回來
    if target_code not in df_clean['證券代號'].values:
        target_row = df_peers[df_peers['證券代號'] == target_code]
        df_clean = pd.concat([df_clean, target_row])

    # 重新排序
    df_clean = df_clean.sort_values('本益比').reset_index(drop=True)
    
    # 取出目標股票附近的同業 (前後各 4 名)
    try:
        idx_list = df_clean.index[df_clean['證券代號'] == target_code].tolist()
        if idx_list:
            target_idx = idx_list[0]
            start = max(0, target_idx - 4)
            end = min(len(df_clean), target_idx + 5)
            final_df = df_clean.iloc[start:end]
        else:
            final_df = df_clean.head(9)
    except:
        final_df = df_clean.head(9)

    return final_df[['證券代號', '公司名稱', '本益比', '殖利率(%)', '股價淨值比']]