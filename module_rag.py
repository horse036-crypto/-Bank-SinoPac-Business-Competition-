import os
import time
import google.generativeai as genai

class FinancialRAG:
    def __init__(self, google_api_key=None, llama_cloud_api_key=None):
        """ 
        初始化 Gemini 原生引擎 
        已徹底移除 LlamaIndex 與 ChromaDB 以避開 v1beta 404 衝突
        """
        if google_api_key:
            genai.configure(api_key=google_api_key)
        
        # 使用支援 1M+ Context 的 1.5 Flash，能一次讀完 2024 八方資料包
        try:
            # 移除 models/ 前綴，直接使用穩定版名稱
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            print("✅ RAG 系統：已連結至 Gemini 原生穩定版引擎")
        except Exception as e:
            print(f"❌ 模型初始化失敗: {e}")

        self.active_file = None

    def ingest_pdf(self, file_path, doc_id):
        """ 透過 Google File API 直接解析八方資料包 """
        try:
            print(f"📄 正在將檔案上傳至 Google AI：{file_path}")
            # 1. 直接上傳檔案至 Google 雲端
            uploaded_file = genai.upload_file(path=file_path, display_name=doc_id)
            
            # 2. 等待 Google 完成 OCR 與文件內容處理
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(3)
                uploaded_file = genai.get_file(uploaded_file.name)
            
            if uploaded_file.state.name == "FAILED":
                return "❌ Google 檔案處理失敗，請檢查網路或 API 權限"
                
            self.active_file = uploaded_file
            return f"✅ 「{doc_id}」解析完畢！AI 已讀完 2024 營運亮點與基本資料。"
        except Exception as e:
            return f"❌ 上傳或解析失敗: {str(e)}"

    def query(self, question):
        """ 全文件深度問答 """
        if not self.active_file:
            return "❌ 請先上傳檔案，AI 才能進行解讀。", []
        
        try:
            # 針對您的八方資料包（基本資料、登記資訊、經營團隊聲明）優化 Prompt
            prompt = f"""
            你現在是一位專業的證券分析師。請根據提供的「八方資料包」PDF 內容回答問題。
            
            文件背景說明：
            - 包含基本資料（如統編 70760460）、登記與聯絡資訊。
            - 包含 2024 年營運亮點（如合併營收 80.28 億元）。
            - 包含董事會成員經歷與經營團隊聲明。
            
            回答規範：
            1. 若涉及財務數字（如營收、店數），請務必精確。
            2. 若涉及經營決策，請參考「經營團隊聲明」章節。
            3. 如果文件中找不到相關資訊，請回答「文件中未提及此項細節」。
            
            提問內容：{question}
            """
            
            # 直接將檔案與 Prompt 餵給 Gemini
            response = self.model.generate_content([self.active_file, prompt])
            
            # 原生版無需切片，直接回傳來源標籤
            return response.text, ["(資料來源：八方資料包_merged.pdf 全文件感官理解)"]
            
        except Exception as e:
            return f"❌ 詢問過程中發生錯誤: {str(e)}", []