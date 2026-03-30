import os
import sys
import tkinter as tk
from tkinter import filedialog
from PyPDF2 import PdfReader, PdfWriter

def extract_pdf_pages(input_pdf_path, output_pdf_path, start_page, end_page):
    """
    從來源 PDF 中擷取指定範圍的頁面，並另存為新的 PDF 檔案。
    
    參數:
        input_pdf_path (str): 來源 PDF 檔案路徑
        output_pdf_path (str): 輸出的新 PDF 檔案路徑
        start_page (int): 起始頁碼 (以人類閱讀習慣的 1 為起點)
        end_page (int): 結束頁碼 (包含此頁)
    """
    
    # 【防呆機制 1】檢查檔案是否存在
    if not os.path.exists(input_pdf_path):
        print(f"❌ 錯誤：找不到來源檔案 {input_pdf_path}")
        return

    # 【防呆機制 2】檢查頁碼邏輯是否合理
    if start_page < 1 or end_page < start_page:
        print("❌ 錯誤：起始頁碼必須大於等於 1，且結束頁碼必須大於等於起始頁碼。")
        return

    try:
        print(f"開始讀取檔案：{input_pdf_path} ...")
        reader = PdfReader(input_pdf_path)
        total_pages = len(reader.pages)
        print(f"來源 PDF 總頁數：{total_pages} 頁")

        # 【防呆機制 3】檢查指定頁碼是否超出 PDF 總頁數
        if end_page > total_pages:
            print(f"⚠️ 警告：指定的結束頁碼 ({end_page}) 超出總頁數 ({total_pages})。將自動調整至最後一頁。")
            end_page = total_pages

        writer = PdfWriter()

        # 寫入指定範圍的頁面
        # 注意：PyPDF2 的索引是從 0 開始，所以人類的第 1 頁在程式裡是 index 0
        start_index = start_page - 1
        end_index = end_page # 在 Python 的 range 中，結束值不包含，所以剛好對應

        print(f"正在擷取第 {start_page} 頁到第 {end_page} 頁 ...")
        for i in range(start_index, end_index):
            page = reader.pages[i]
            writer.add_page(page)

        # 確保輸出目錄存在
        os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

        # 將擷取出來的頁面存檔
        with open(output_pdf_path, "wb") as output_file:
            writer.write(output_file)

        print(f"✅ 裁切成功！檔案已儲存至：{output_pdf_path}")
        print(f"-> 新檔案共包含 {len(writer.pages)} 頁。")

    except Exception as e:
        print(f"❌ 處理 PDF 時發生未知的錯誤：{e}")

if __name__ == "__main__":
    # 隱藏 tkinter 主視窗
    root = tk.Tk()
    root.withdraw()
    
    print("請選擇來源 PDF 檔案...")
    # 1. 讓使用者透過視窗選擇來源檔案
    INPUT_FILE = filedialog.askopenfilename(
        title="選擇來源 PDF 檔案",
        filetypes=[("PDF Files", "*.pdf")]
    )
    
    if not INPUT_FILE:
        print("❌ 未選擇來源檔案，程式結束。")
        sys.exit()
        
    print(f"已選擇來源檔案：{INPUT_FILE}")
    
    print("請選擇儲存 PDF 的位置與檔名...")
    # 2. 讓使用者透過視窗選擇儲存位置
    OUTPUT_FILE = filedialog.asksaveasfilename(
        title="儲存擷取後的 PDF",
        defaultextension=".pdf",
        filetypes=[("PDF Files", "*.pdf")]
    )
    
    if not OUTPUT_FILE:
        print("❌ 未選擇儲存位置，程式結束。")
        sys.exit()
        
    print(f"將儲存至：{OUTPUT_FILE}")
    
    # 3. 讓使用者在終端機輸入要擷取的頁面範圍
    try:
        START_PAGE = int(input("請輸入起始頁碼 (例如: 10): "))
        END_PAGE = int(input("請輸入結束頁碼 (例如: 20): "))
    except ValueError:
        print("❌ 頁碼輸入錯誤，請輸入整數數字。程式結束。")
        sys.exit()
    
    # 執行擷取任務
    extract_pdf_pages(
        input_pdf_path=INPUT_FILE,
        output_pdf_path=OUTPUT_FILE,
        start_page=START_PAGE,
        end_page=END_PAGE
    )