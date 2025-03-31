import firebase_admin
from firebase_admin import credentials, storage
import time
from datetime import datetime
import os
import subprocess

# 初始化 Firebase Admin SDK
cred = credentials.Certificate("autoprint-e192b-firebase-adminsdk-fbsvc-302c4ca40c.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'autoprint-e192b.firebasestorage.app'
})

# 獲取 storage bucket
bucket = storage.bucket()

def print_file(file_path):
    """使用 airprint 指令列印檔案"""
    try:
        # 先列出可用的印表機
        print("正在查詢可用的印表機...")
        subprocess.run("lpstat -p", shell=True)
        
        # 使用指定的印表機名稱，或使用預設印表機
        printer_name = "您的印表機名稱"  # 請替換成您的印表機名稱
        command = f"lp -d {printer_name} {file_path}"
        
        print(f"執行列印指令: {command}")
        # subprocess.run(command, shell=True, check=True)
        # print(f"檔案已送印: {file_path}")
    except subprocess.CalledProcessError as e:
        print(f"列印失敗: {e}")

def list_files():
    """列出當前 storage 中的所有檔案"""
    files = bucket.list_blobs()
    return {blob.name: blob.updated for blob in files}

def monitor_storage():
    """監控 storage 的變化"""
    print("開始監聽 Firebase Storage...")
    previous_files = list_files()
    
    while True:
        try:
            current_files = list_files()
            
            # 檢查新增的檔案
            for file_name, updated_time in current_files.items():
                if file_name not in previous_files:
                    print(f"偵測到新檔案: {file_name}")
                    print(f"上傳時間: {updated_time}")
                    
                    # 下載新檔案
                    blob = bucket.blob(file_name)
                    download_path = os.path.join("downloads", file_name)
                    os.makedirs(os.path.dirname(download_path), exist_ok=True)
                    blob.download_to_filename(download_path)
                    print(f"檔案已下載至: {download_path}")
                    
                    # 列印檔案
                    print_file(download_path)
            
            previous_files = current_files
            time.sleep(10)  # 每10秒檢查一次
            
        except Exception as e:
            print(f"發生錯誤: {e}")
            time.sleep(10)  # 發生錯誤時等待10秒後重試

if __name__ == "__main__":
    # 創建下載目錄
    os.makedirs("downloads", exist_ok=True)
    monitor_storage()
