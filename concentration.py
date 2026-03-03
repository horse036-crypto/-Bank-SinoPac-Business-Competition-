import pdfplumber
import pandas as pd
import re

def extract_concentration_risk(pdf_file, progress_callback=None):
    """
    [財報閱讀器 V2.0]
    針對台灣年報格式優化，進行全書搜索。
    參數:
        pdf_file: 上傳的 PDF 檔案物件
        progress_callback: 用來更新 Streamlit 進度條的函式 (選擇性)
    """
    customers = []
    suppliers = []
    
    # 台灣年報常見的關鍵字
    target_keywords = [
        "主要進貨名單", "主要銷貨名單", 
        "佔全年度進貨", "佔全年度銷貨",
        "進貨金額", "銷貨金額"
    ]
    
    try:
        with pdfplumber.open(pdf_file) as pdf:
            total_pages = len(pdf.pages)
            print(f"📄 開始讀取 PDF，共 {total_pages} 頁...")
            
            # 我們搜尋全部頁面 (注意：頁數多時會跑比較久)
            for i, page in enumerate(pdf.pages):
                
                # 如果有提供進度條函式，就更新它
                if progress_callback:
                    progress_callback(i, total_pages)
                
                # 1. 先抓文字，快速判斷這一頁有沒有我們要的東西
                text = page.extract_text()
                if not text: continue
                
                # 簡單過濾：如果這頁完全沒出現關鍵字，就跳過 (加速用)
                hit = False
                for kw in target_keywords:
                    if kw in text:
                        hit = True
                        break
                if not hit: continue

                # 2. 如果有關鍵字，才開始詳細挖表格
                tables = page.extract_tables()
                
                for table in tables:
                    # 表格清洗與轉換
                    # 將表格第一列合併成字串來檢查標題
                    # 過濾掉 None 值
                    header_row = [str(x).replace('\n', '').replace(' ', '') for x in table[0] if x is not None]
                    header_str = "".join(header_row)
                    
                    # A. 判斷是否為「客戶/銷貨」表格
                    # 特徵：含有「客戶名稱」且含有「佔比」或「金額」
                    if ("客戶名稱" in header_str or "銷貨對象" in header_str) and ("比例" in header_str or "金額" in header_str):
                        print(f"✅ 在第 {i+1} 頁找到客戶名單！")
                        df = _clean_table(table, "Customer")
                        if not df.empty:
                            customers.append(df)
                    
                    # B. 判斷是否為「供應商/進貨」表格
                    elif ("供應商名稱" in header_str or "進貨對象" in header_str) and ("比例" in header_str or "金額" in header_str):
                        print(f"✅ 在第 {i+1} 頁找到供應商名單！")
                        df = _clean_table(table, "Supplier")
                        if not df.empty:
                            suppliers.append(df)

        # 合併搜尋結果
        df_cust = pd.concat(customers).drop_duplicates() if customers else pd.DataFrame()
        df_supp = pd.concat(suppliers).drop_duplicates() if suppliers else pd.DataFrame()
        
        # 再次檢查資料是否乾淨 (有時候會抓到雜訊)
        if not df_cust.empty:
            df_cust = df_cust.sort_values('數值', ascending=False).head(10)
        if not df_supp.empty:
            df_supp = df_supp.sort_values('數值', ascending=False).head(10)

        return df_cust, df_supp

    except Exception as e:
        print(f"❌ PDF 解析錯誤: {e}")
        return None, None

def _clean_table(table, type_name):
    """
    [內部函式] 清洗 PDF 表格數據
    """
    try:
        # 轉成 DataFrame
        # 有時候表格第一列不是標題，是合併儲存格，這裡做個簡單判斷
        # 我們假設含有 "名稱" 的那一列才是標題列
        header_idx = 0
        for idx, row in enumerate(table[:3]): # 檢查前三列
            row_str = "".join([str(x) for x in row if x])
            if "名稱" in row_str or "對象" in row_str:
                header_idx = idx
                break
        
        df = pd.DataFrame(table[header_idx+1:], columns=table[header_idx])
        
        # 尋找關鍵欄位
        name_col = None
        ratio_col = None
        
        for col in df.columns:
            if col is None: continue
            c_name = str(col).replace('\n', '').replace(' ', '')
            
            if "名稱" in c_name or "對象" in c_name:
                name_col = col
            # 優先找 "比例" 或 "%"，其次找 "金額" (如果只有金額，我們後續比較難算佔比，先以佔比為主)
            if "比例" in c_name or "佔" in c_name or "%" in c_name:
                ratio_col = col
        
        if name_col and ratio_col:
            result = df[[name_col, ratio_col]].copy()
            result.columns = ['名稱', '佔比']
            
            # 數據清洗
            # 1. 處理名稱：有時候會包含代號 (例如: "A 公司")
            result['名稱'] = result['名稱'].astype(str).str.strip()
            
            # 2. 處理數值：移除 %, 移除逗號, 轉 float
            result['數值'] = result['佔比'].astype(str).str.replace('%', '', regex=False).str.replace(',', '', regex=False)
            result['數值'] = pd.to_numeric(result['數值'], errors='coerce').fillna(0)
            
            # 3. 過濾無效數據
            result = result[result['數值'] > 0]
            
            # 4. 排除掉 "合計" 或 "Total" 這種匯總行
            result = result[~result['名稱'].str.contains("合計|Total|其他", na=False)]
            
            return result
            
        return pd.DataFrame()
        
    except Exception as e:
        return pd.DataFrame()

# 測試用假資料 (Mock Data)
def get_mock_concentration_data():
    # 這是為了讓 UI 在測試時不至於空白
    df_c = pd.DataFrame([
        {"名稱": "客戶 A (Mock)", "數值": 45.0, "佔比": "45%"},
        {"名稱": "客戶 B (Mock)", "數值": 20.0, "佔比": "20%"},
        {"名稱": "客戶 C (Mock)", "數值": 15.0, "佔比": "15%"},
    ])
    df_s = pd.DataFrame([
        {"名稱": "供應商 X (Mock)", "數值": 30.0, "佔比": "30%"},
        {"名稱": "供應商 Y (Mock)", "數值": 25.0, "佔比": "25%"},
        {"名稱": "供應商 Z (Mock)", "數值": 10.0, "佔比": "10%"},
    ])
    return df_c, df_s