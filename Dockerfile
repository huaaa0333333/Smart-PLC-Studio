# 使用輕量級的 Python 3.10 作為基底
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 將套件清單複製進容器並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 將專案的所有程式碼複製進容器
COPY . .

# 曝露 Streamlit 預設的 8501 Port
EXPOSE 8501

# 容器啟動時執行的指令 (對應我們重構後的 ui.py)
CMD ["streamlit", "run", "ui.py", "--server.port=8501", "--server.address=0.0.0.0"]