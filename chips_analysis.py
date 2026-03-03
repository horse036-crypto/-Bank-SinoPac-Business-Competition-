import requests
import pandas as pd
import time

def get_chips_data(stock_code, days=5):
    """
    [籌碼分析模組]
    抓取個股最近 N 天的三大法人買賣超 (T86)
    """
    print(f"🕵️‍♀️ 正在追蹤 {stock_code} 的主力籌碼 (近 {days} 天)...")
    
    # 產生最近的日期 (多抓幾天以防遇到假日)
    date_range = pd.date_range(end=pd.Timestamp.now(), periods=days*3).tolist()
    date_range.reverse() # 從最新的日期開始
    
    chips_data = []
    success_count = 0
    
    for date_obj in date_range:
        if success_count >= days: # 抓滿 N 天就收工
            break
            
        date_str = date_obj.strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={date_str}&selectType=ALL&response=json"
        
        try:
            time.sleep(0.3) # 避免打太快
            res = requests.get(url)
            data = res.json()
            
            if data['stat'] == 'OK':
                df_day = pd.DataFrame(data['data'], columns=data['fields'])
                row = df_day[df_day['證券代號'] == stock_code]
                
                if not row.empty:
                    # 處理千分位逗號
                    def to_int(val): return int(val.replace(',', ''))
                    
                    chips_data.append({
                        "日期": date_obj.strftime("%Y-%m-%d"),
                        "外資": to_int(row.iloc[0]['外資自營商買賣超股數']),
                        "投信": to_int(row.iloc[0]['投信買賣超股數']),
                        "自營商": to_int(row.iloc[0]['自營商買賣超股數']),
                        "合計": to_int(row.iloc[0]['三大法人買賣超股數'])
                    })
                    success_count += 1
        except: pass

    if chips_data:
        return pd.DataFrame(chips_data).sort_values('日期')
    else:
        return None