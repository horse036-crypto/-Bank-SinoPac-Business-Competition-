import requests
import pandas as pd
from bs4 import BeautifulSoup

def get_revenue_mix(stock_code):
    """
    [V3 終極手排版爬蟲]
    不依賴 pd.read_html，改用 BeautifulSoup 手動解析 HTML。
    目標網站：HiStock (嗨投資)
    """
    url = f"https://histock.tw/stock/{stock_code}/%E7%87%9F%E6%94%B6%E6%AF%94%E9%87%8D"
    
    # 偽裝成真人瀏覽器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        print(f"🕵️‍♀️ [V3] 正在手動解析 {stock_code} 的營收結構...")
        res = requests.get(url, headers=headers, timeout=10)
        
        if res.status_code == 200:
            # 使用 html.parser (Python 內建，不需要 lxml)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 1. 找到所有的表格
            tables = soup.find_all('table')
            target_table = None
            
            # 2. 尋找含有 "產品項目" 和 "比重" 的表格
            for table in tables:
                headers_text = [th.get_text(strip=True) for th in table.find_all('th')]
                if '產品項目' in headers_text and '比重' in headers_text:
                    target_table = table
                    break
            
            if target_table:
                # 3. 手動提取每一列 (tr) 的數據
                rows = []
                # 跳過第一列 (標題列)
                for tr in target_table.find_all('tr')[1:]:
                    cols = tr.find_all('td')
                    if len(cols) >= 2:
                        # 提取文字
                        product_name = cols[0].get_text(strip=True)
                        ratio_str = cols[1].get_text(strip=True)
                        
                        rows.append({
                            '產品項目': product_name,
                            '比重': ratio_str
                        })
                
                # 4. 轉成 DataFrame
                df = pd.DataFrame(rows)
                
                if not df.empty:
                    # 數據清洗：移除 % 並轉成數字
                    df['數值'] = df['比重'].astype(str).str.replace('%', '', regex=False)
                    df['數值'] = pd.to_numeric(df['數值'], errors='coerce').fillna(0)
                    
                    # 過濾有效數據並排序
                    df_clean = df[df['數值'] > 0].sort_values('數值', ascending=False)
                    
                    print(f"✅ 成功抓取！(項目數: {len(df_clean)})")
                    return df_clean
                else:
                    print("⚠️ 表格是空的")
                    return None
            else:
                print("⚠️ 找不到目標表格 (結構可能已變更)")
                return None
        else:
            print(f"❌ 網站連線失敗 (Status: {res.status_code})")
            return None
            
    except Exception as e:
        print(f"❌ 發生未預期的錯誤: {e}")
        return None

# 自我測試區
if __name__ == "__main__":
    df = get_revenue_mix("2330")
    if df is not None:
        print("測試成功！資料預覽：")
        print(df.head())
    else:
        print("測試失敗。")