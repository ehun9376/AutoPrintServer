import firebase_admin
from firebase_admin import credentials, storage
import time
from datetime import datetime
import os
import subprocess
from PIL import Image

def process_image(input_path, output_path):
    
    try:
        dpi = 300
        width_inch = 4
        height_inch = 6
        target_width = int(width_inch * dpi)
        target_height = int(height_inch * dpi)
        with Image.open(input_path) as img:
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, 'white')
                background.paste(img, mask=img.split()[3])
                img = background
            # 計算縮放比例，保留全部內容
            img_ratio = img.width / img.height
            target_ratio = target_width / target_height
            if img_ratio > target_ratio:
                # 圖片較寬，以高度為基準縮放
                new_height = target_height
                new_width = int(img_ratio * new_height)
            else:
                # 圖片較高，以寬度為基準縮放
                new_width = target_width
                new_height = int(new_width / img_ratio)
            resized_img = img.resize((new_width, new_height), Image.LANCZOS)
            # 建立白色背景
            new_img = Image.new('RGB', (target_width, target_height), 'white')
            # 計算貼圖位置（置中）
            x = (target_width - new_width) // 2
            y = (target_height - new_height) // 2
            new_img.paste(resized_img, (x, y))
            new_img.save(output_path, dpi=(dpi, dpi))
            final_output_path = os.path.join("completed", output_path)
            os.makedirs(os.path.dirname(final_output_path), exist_ok=True)
            os.rename(output_path, final_output_path)
            os.remove(input_path)
            print(f"圖片處理完成：{final_output_path}")
        return True
        
    except Exception as e:
        print(f"圖片處理過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_file(file_path):
    """使用 airprint 指令列印檔案"""
    try:
        if not os.path.exists(file_path):
            print(f"錯誤：檔案不存在 - {file_path}")
            return False
            
        # 創建臨時文件用於處理後的圖片
        processed_path = f"{file_path}_processed.jpg"
        # 處理圖片
        if not process_image(file_path, processed_path):
            print("圖片處理失敗")
            return False
        # 取得最終檔案路徑（completed/）
        final_output_path = os.path.join("completed", processed_path)
        try:
            preview_img = Image.open(final_output_path)
            preview_img.show(title="列印預覽（處理後）")
            print("已顯示處理後預覽，請確認後繼續...")
        except Exception as e:
            print(f"顯示處理後預覽時發生錯誤: {e}")

        print("正在查詢可用的印表機...")
        result = subprocess.run("lpstat -p", shell=True, capture_output=True, text=True)
        if result.stdout:
            print("可用的印表機列表：")
            print(result.stdout)
        else:
            print("警告：未找到任何印表機")

            #TODO: - 接新的印表機
        printer_name = "EPSON_L3550_Series"
        # 設定列印參數
        command = (f"lp -d {printer_name} "
                  f"-o cupsPrintQuality=High "
                  f"-o fit-to-page "
                  f"{final_output_path}")
        print(f"執行列印指令: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        # 刪除臨時文件（已移動到 completed/）
        try:
            os.remove(final_output_path)
        except:
            pass
        if result.returncode == 0:
            print(f"列印成功！")
            print(f"列印工作詳情: {result.stdout}")
            return True
        else:
            print(f"列印失敗！錯誤訊息: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"列印過程發生錯誤: {e}")
        print(f"錯誤詳情: {e.stderr}")
        return False
    except Exception as e:
        print(f"發生未預期的錯誤: {e}")
        return False

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
                    if print_file(download_path):
                        print("檔案處理完成：成功下載並列印")
                    else:
                        print("檔案處理失敗：列印過程出現問題")
            
            previous_files = current_files
            time.sleep(10)  # 每10秒檢查一次
            
        except Exception as e:
            print(f"發生錯誤: {e}")
            time.sleep(10)  # 發生錯誤時等待10秒後重試

if __name__ == "__main__":
    # 初始化 Firebase Admin SDK
    cred = credentials.Certificate("autoprint-e192b-038b6a5219dc.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'autoprint-e192b.firebasestorage.app'
    })

    # 獲取 storage bucket
    bucket = storage.bucket()
    
    # 創建下載目錄
    os.makedirs("downloads", exist_ok=True)
    monitor_storage()
