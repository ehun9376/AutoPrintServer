import firebase_admin
from firebase_admin import credentials, storage
import time
from datetime import datetime
import os
import subprocess
from PIL import Image
import matplotlib.pyplot as plt

def process_image(input_path, output_path):
    """處理圖片，調整為 6.8cm × 9.5cm"""
    try:
        # 目標紙張大小（毫米）
        paper_width = 73   # 7.3cm
        paper_height = 100  # 10cm
        
        # 目標圖片大小（毫米）
        image_width = 68   # 6.8cm
        image_height = 95  # 9.5cm
        
        # 計算邊距（居中）
        margin_width = (paper_width - image_width) / 2   # 約 0.25cm
        margin_height = (paper_height - image_height) / 2  # 約 0.25cm
        
        # 轉換為像素（使用 300 DPI 以獲得高品質輸出）
        dpi = 300
        pixels_per_mm = dpi / 25.4  # 1英寸 = 25.4mm
        
        # 計算像素尺寸
        target_width = int(image_width * pixels_per_mm)   # 圖片目標寬度（像素）
        target_height = int(image_height * pixels_per_mm)  # 圖片目標高度（像素）
        paper_width_px = int(paper_width * pixels_per_mm)  # 紙張寬度（像素）
        paper_height_px = int(paper_height * pixels_per_mm)  # 紙張高度（像素）
        
        # 處理圖片
        with Image.open(input_path) as img:
            # 確保圖片為 RGB 模式
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 計算縮放比例（保持原始圖片比例）
            img_ratio = img.width / img.height
            target_ratio = target_width / target_height
            
            if img_ratio > target_ratio:
                # 圖片較寬，以寬度為基準
                new_width = target_width
                new_height = int(target_width / img_ratio)
            else:
                # 圖片較高，以高度為基準
                new_height = target_height
                new_width = int(target_height * img_ratio)
            
            # 調整圖片大小
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 創建新的白色背景圖片（完整紙張大小）
            new_img = Image.new('RGB', (paper_width_px, paper_height_px), 'white')
            
            # 計算居中位置
            x = (paper_width_px - new_width) // 2
            y = (paper_height_px - new_height) // 2
            
            # 將調整後的圖片貼到白色背景上
            new_img.paste(resized_img, (x, y))
            
            print(f"原始圖片尺寸: {img.width}x{img.height} 像素")
            print(f"調整後尺寸: {new_width}x{new_height} 像素")
            print(f"目標圖片尺寸: {image_width}x{image_height} 毫米 ({target_width}x{target_height} 像素)")
            print(f"紙張尺寸: {paper_width}x{paper_height} 毫米 ({paper_width_px}x{paper_height_px} 像素)")
            print(f"邊距: 寬 {margin_width:.1f}mm, 高 {margin_height:.1f}mm")
            
            # 保存處理後的圖片
            new_img.save(output_path, quality=95, dpi=(dpi, dpi))
            
        print(f"圖片處理完成：{output_path}")
        return True
        
    except Exception as e:
        print(f"圖片處理過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def preview_image(image_path):
    """使用 matplotlib 顯示圖片預覽"""
    try:
        # 開啟圖片
        img = Image.open(image_path)
        
        # 顯示圖片
        plt.imshow(img)
        plt.axis('off')  # 隱藏座標軸
        plt.title("圖片預覽")
        plt.show()
        
    except Exception as e:
        print(f"預覽圖片時發生錯誤: {e}")

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
        
        # 預覽圖片（不阻塞）
        preview_image(processed_path)
        
        print("正在查詢可用的印表機...")
        result = subprocess.run("lpstat -p", shell=True, capture_output=True, text=True)
        if result.stdout:
            print("可用的印表機列表：")
            print(result.stdout)
        else:
            print("警告：未找到任何印表機")
            
        printer_name = "EPSON_L3550_Series"  # 請替換成您的印表機名稱
        
        # 設定列印參數
        command = (f"lp -d {printer_name} "
                  f"-o media=Custom.73x100mm "  # 7.3cm x 10cm
                  f"-o ColorModel=RGB "
                  f"-o print-color-mode=color "
                  f"-o MediaType=photographic-glossy "
                  f"-o cupsPrintQuality=High "
                  f"-o fit-to-page "
                  f"-o resolution=1200dpi "  # 使用高解析度
                  f"{processed_path}")
        
        print(f"執行列印指令: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        # 刪除臨時文件
        try:
            os.remove(processed_path)
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
    cred = credentials.Certificate("autoprint-e192b-firebase-adminsdk-fbsvc-302c4ca40c.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'autoprint-e192b.firebasestorage.app'
    })

    # 獲取 storage bucket
    bucket = storage.bucket()
    
    # 創建下載目錄
    os.makedirs("downloads", exist_ok=True)
    monitor_storage()
