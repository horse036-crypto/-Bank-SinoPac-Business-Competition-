import requests
import pandas as pd
import re
import urllib.parse

# ══════════════════════════════════════════════
# 常數設定
# ══════════════════════════════════════════════
NEWSAPI_URL = "https://newsapi.org/v2/everything"

# ══════════════════════════════════════════════
# 核心工具函式
# ══════════════════════════════════════════════

def clean_company_name(name: str) -> str:
    """ [名稱清洗] 移除贅字，提高 NewsAPI 搜尋命中率 """
    if not name:
        return ""
    for s in ["股份有限公司", "有限公司", "（股）公司", "(股)公司", "-KY", "*"]:
        name = name.replace(s, "")
    return name.strip()

# ══════════════════════════════════════════════
# 主搜尋函式 (修正參數標頭)
# ══════════════════════════════════════════════

def search_news_api(company_name, target_word=None, page_size=20, api_key=None):
    """
    [新聞雷達 V14.1] 
    利用 NewsAPI 進行廣域搜尋，並統計目標單字出現次數
    修正：確保 api_key 參數可以被正確接收
    """
    # 1. 確保搜尋關鍵字乾淨
    target_company = clean_company_name(company_name)
    
    # 2. 如果沒指定統計單字，預設統計公司名稱
    count_target = target_word if target_word else target_company

    # 3. 使用傳入的 api_key，如果沒傳入則視為錯誤
    if not api_key:
        print("❌ 錯誤：未提供 NewsAPI Key")
        return []

    params = {
        "q": target_company,
        "language": "zh",
        "pageSize": page_size,
        "apiKey": api_key
    }

    results = []
    try:
        # 4. 發送請求至 NewsAPI
        r = requests.get(NEWSAPI_URL, params=params, timeout=10)
        data = r.json()
        articles = data.get("articles", [])
        
        for a in articles:
            title = a.get("title", "")
            desc = a.get("description", "") or ""
            url = a.get("url", "#")
            
            # 5. 關鍵字統計邏輯
            count = len(re.findall(count_target, title + desc))
            
            results.append({
                "標題": title,
                "來源": a.get("source", {}).get("name", "媒體"),
                "日期": a.get("publishedAt", ""),
                "連結": url,
                "顯示內容": desc,
                "關鍵字計數": count,
                "目標單字": count_target
            })
            
    except Exception as e:
        print(f"NewsAPI 連線錯誤: {e}")
        
    # 依據關鍵字出現次數排序
    if results:
        results = sorted(results, key=lambda x: x['關鍵字計數'], reverse=True)
        
    return results