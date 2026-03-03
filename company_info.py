import requests
import pandas as pd
import yfinance as yf
from deep_translator import GoogleTranslator

def get_company_basic_info(stock_code):
    """
    [基本資料模組]
    整合 證交所 Open Data + Yahoo Finance
    回傳：包含詳細公司資訊的 Dictionary
    """
    # 1. 抓取證交所詳細清單 (API: t187ap03_L)
    url = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
    basic_info = {}
    
    try:
        # 這裡不使用 verify=False，若報錯在主程式處理
        res = requests.get(url, verify=False) 
        df = pd.DataFrame(res.json())
        
        # 篩選這家公司
        company = df[df['公司代號'] == stock_code]
        
        if not company.empty:
            row = company.iloc[0]
            # 將證交所的欄位一一填入
            basic_info['公司名稱'] = row.get('公司名稱', '')
            basic_info['產業別'] = row.get('產業別', '')
            basic_info['董事長'] = row.get('董事長', '')
            basic_info['總經理'] = row.get('總經理', '')
            basic_info['發言人'] = row.get('發言人', '')
            basic_info['代理發言人'] = row.get('代理發言人', '')
            basic_info['成立日期'] = row.get('成立日期', '')
            basic_info['上市日期'] = row.get('上市日期', '')
            basic_info['統一編號'] = row.get('營利事業統一編號', '')
            basic_info['總機電話'] = row.get('電話', '')
            basic_info['傳真號碼'] = row.get('傳真', '')
            basic_info['電子郵件'] = row.get('電子郵件信箱', '')
            basic_info['公司網址'] = row.get('網址', '')
            basic_info['公司地址'] = row.get('住址', '')
            basic_info['股務代理'] = row.get('股票過戶機構', '') 
            
            # 處理數字格式 (加千分位逗號)
            try:
                cap = float(row.get('實收資本額', 0))
                basic_info['實收資本額'] = f"{int(cap):,}"
            except: basic_info['實收資本額'] = row.get('實收資本額', '')

            try:
                shares = float(row.get('已發行普通股數', 0))
                basic_info['已發行股數'] = f"{int(shares):,}"
            except: basic_info['已發行股數'] = row.get('已發行普通股數', '')

    except Exception as e:
        print(f"證交所資料抓取失敗: {e}")

    # 2. 抓取 Yahoo Finance (補充簡介與英文名)
    try:
        ticker = yf.Ticker(f"{stock_code}.TW")
        yf_info = ticker.info
        
        # 如果證交所沒抓到，嘗試用 Yahoo 補
        if '公司名稱' not in basic_info:
            basic_info['公司名稱'] = yf_info.get('longName', stock_code)
            basic_info['產業別'] = yf_info.get('sector', 'N/A')
            basic_info['公司網址'] = yf_info.get('website', '')
            basic_info['公司地址'] = yf_info.get('address1', '')

        # 抓取英文簡介並翻譯
        summary = yf_info.get('longBusinessSummary', '暫無詳細描述')
        if summary != '暫無詳細描述' and len(summary) > 10:
            try:
                # 限制字數翻譯
                summary_zh = GoogleTranslator(source='auto', target='zh-TW').translate(summary[:4000])
                basic_info['公司簡介'] = summary_zh
            except:
                basic_info['公司簡介'] = summary # 翻譯失敗顯示原文
        else:
            basic_info['公司簡介'] = "暫無詳細描述"
            
    except Exception as e:
        print(f"Yahoo 資料抓取失敗: {e}")
        if '公司簡介' not in basic_info: basic_info['公司簡介'] = "無法取得簡介"

    return basic_info