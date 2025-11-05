######### 이미지 파일 도트 변환 ################
#8/19 개선 사항버전
# 32/64/128/256 도트 사이즈 선택 가능

import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

# ---------------- 변환 함수 ----------------
def convert_to_dot_with_edges(img, target_size=64):

    # 1️⃣ 이미지 축소
    h, w = img.shape[:2]
    scale = min(target_size / w, target_size / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # 중앙에 패딩
    pad_top = (target_size - new_h) // 2
    pad_bottom = target_size - new_h - pad_top
    pad_left = (target_size - new_w) // 2
    pad_right = target_size - new_w - pad_left
    padded = cv2.copyMakeBorder(resized, pad_top, pad_bottom, pad_left, pad_right,
                                borderType=cv2.BORDER_CONSTANT, value=255) # 배경을 흰색으로

    # 2️⃣ 도트 이미지 (어두운 부분이 1, 밝은 부분이 0)
    _, binary = cv2.threshold(padded, 128, 1, cv2.THRESH_BINARY_INV)

    # 3️⃣ 얇은 선 검출 (Canny) - 원본 해상도에서 실행 후, 도트 이미지와 동일한 비율로 축소/패딩
    # 원본 이미지에 Canny 적용
    original_edges = cv2.Canny(img, 50, 150)

    # Canny 결과를 도트 이미지와 같은 중간 크기로 리사이즈 (비율 유지)
    resized_edges = cv2.resize(original_edges, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    # 도트 이미지와 동일한 여백을 추가하여 최종 정렬
    padded_edges = cv2.copyMakeBorder(resized_edges, pad_top, pad_bottom, pad_left, pad_right,
                                      borderType=cv2.BORDER_CONSTANT, value=0)

    # 리사이즈 및 패딩된 Canny 결과에서 최종 선 추출
    _, edges_bin = cv2.threshold(padded_edges, 1, 1, cv2.THRESH_BINARY)

    # 4️⃣ 합성: 도트와 선을 합칩니다. (1: 점 또는 선)
    final = np.maximum(binary, edges_bin)

    # --- 화면 표시용 이미지 생성 (모두 검은 그림 / 흰 배경으로 통일) ---
    dot_display = (1 - binary) * 255
    edges_display = (1 - edges_bin) * 255
    final_display = (1 - final) * 255

    # Raw data and Display data
    raw_data = (binary, edges_bin, final)
    display_images = (dot_display, edges_display, final_display)

    return raw_data, display_images


# ---------------- Tkinter UI ----------------
class DotConverterApp:
    """
    4단계 비교 UI:
    1) 원본
    2) 도트 변환
    3) 선 이미지
    4) 최종 합친 이미지
    + 각 이미지별 0/1 변환 기능 추가
    + 사이즈 선택 기능 추가
    """
    def __init__(self, root):
        self.root = root
        self.root.title("도트 변환기 (선 유지 + 비교)")

        self.original_img = None
        self.raw_dot = None
        self.raw_edges = None
        self.raw_final = None

        # --- 상단 버튼 및 옵션 영역 ---
        top_frame = tk.Frame(root)
        top_frame.pack(pady=5)

        self.load_btn = tk.Button(top_frame, text="이미지 불러오기", command=self.load_image)
        self.load_btn.pack(side=tk.LEFT, padx=5)

        # --- 사이즈 선택 드롭다운 ---
        tk.Label(top_frame, text="변환 사이즈:").pack(side=tk.LEFT, padx=(10, 2))
        self.size_var = tk.StringVar(root)
        self.size_options = [32, 64, 115, 128, 256]
        self.size_var.set(self.size_options[1]) # 기본값 64
        self.size_menu = tk.OptionMenu(top_frame, self.size_var, *self.size_options)
        self.size_menu.pack(side=tk.LEFT, padx=2)

        self.convert_btn = tk.Button(top_frame, text="변환 실행", command=self.convert_image, state=tk.DISABLED)
        self.convert_btn.pack(side=tk.LEFT, padx=5)

        # --- 이미지 표시 영역 ---
        img_frame = tk.Frame(root, padx=10, pady=10)
        img_frame.pack()

        # 원본 이미지
        original_frame = tk.Frame(img_frame)
        original_frame.grid(row=0, column=0, padx=5, pady=5, sticky=tk.N)
        self.label_original = tk.Label(original_frame, text="원본 이미지", compound=tk.TOP)
        self.label_original.pack()

        # 도트 이미지
        dot_frame = tk.Frame(img_frame)
        dot_frame.grid(row=0, column=1, padx=5, pady=5)
        self.label_dot = tk.Label(dot_frame, text="도트 이미지", compound=tk.TOP)
        self.label_dot.pack()
        self.btn_save_dot = tk.Button(dot_frame, text="0,1 변환", command=self.save_dot_txt, state=tk.DISABLED)
        self.btn_save_dot.pack(pady=5)

        # 선 이미지
        edges_frame = tk.Frame(img_frame)
        edges_frame.grid(row=1, column=0, padx=5, pady=5)
        self.label_edges = tk.Label(edges_frame, text="선 이미지", compound=tk.TOP)
        self.label_edges.pack()
        self.btn_save_edges = tk.Button(edges_frame, text="0,1 변환", command=self.save_edges_txt, state=tk.DISABLED)
        self.btn_save_edges.pack(pady=5)

        # 최종 합성 이미지
        final_frame = tk.Frame(img_frame)
        final_frame.grid(row=1, column=1, padx=5, pady=5)
        self.label_final = tk.Label(final_frame, text="최종 합성", compound=tk.TOP)
        self.label_final.pack()
        self.btn_save_final = tk.Button(final_frame, text="0,1 변환", command=self.save_final_txt, state=tk.DISABLED)
        self.btn_save_final.pack(pady=5)

    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        )
        if not file_path:
            return

        img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            print("이미지를 불러오지 못했습니다.")
            return

        # 알파 채널 제거
        if len(img.shape) == 3 and img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        elif len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        self.original_img = img
        self.show_image(self.original_img, self.label_original, resize_for_display=True)
        self.convert_btn.config(state=tk.NORMAL)
        
        # Clear previous results
        self.raw_dot, self.raw_edges, self.raw_final = None, None, None
        
        # Create empty placeholder for the labels
        placeholder = ImageTk.PhotoImage(Image.new('RGB', (256, 256), 'white'))
        
        self.label_dot.config(image=placeholder)
        self.label_dot.image = placeholder
        self.label_edges.config(image=placeholder)
        self.label_edges.image = placeholder
        self.label_final.config(image=placeholder)
        self.label_final.image = placeholder

        self.btn_save_dot.config(state=tk.DISABLED)
        self.btn_save_edges.config(state=tk.DISABLED)
        self.btn_save_final.config(state=tk.DISABLED)

    def convert_image(self):
        if self.original_img is None:
            return

        try:
            target_size = int(self.size_var.get())
        except (ValueError, TypeError):
            target_size = 64 # 문제가 생기면 기본값 64로 설정
            print(f"경고: 잘못된 크기가 선택되어 기본값 {target_size}로 변환합니다.")

        (self.raw_dot, self.raw_edges, self.raw_final), (dot_img, edges_img, final_img) = convert_to_dot_with_edges(self.original_img, target_size=target_size)

        # 각 이미지 Label에 표시
        self.show_image(dot_img, self.label_dot, resize_for_display=False)
        self.show_image(edges_img, self.label_edges, resize_for_display=False)
        self.show_image(final_img, self.label_final, resize_for_display=False)
        
        # 저장 버튼 활성화
        self.btn_save_dot.config(state=tk.NORMAL)
        self.btn_save_edges.config(state=tk.NORMAL)
        self.btn_save_final.config(state=tk.NORMAL)

    def show_image(self, img, label, resize_for_display=True):
        if img is None:
            return

        if len(img.shape) == 2:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        else:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        img_pil = Image.fromarray(img_rgb)

        # 화면에서 보기 좋게 항상 확대
        if resize_for_display:
            img_pil = img_pil.resize((256, 256), Image.NEAREST)
        else:
            img_pil = img_pil.resize((256, 256), Image.NEAREST)

        img_tk = ImageTk.PhotoImage(img_pil)
        label.config(image=img_tk)
        label.image = img_tk

    def save_data_as_txt(self, data_array, default_filename):
        if data_array is None:
            print("저장할 데이터가 없습니다.")
            return
        
        file_path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        with open(file_path, "w") as f:
            for row in data_array:
                f.write(str(row.tolist()) + ',' + "\n")
        print(f"{file_path} 에 저장되었습니다.")

    def save_dot_txt(self):
        self.save_data_as_txt(self.raw_dot, "dot_image.txt")

    def save_edges_txt(self):
        self.save_data_as_txt(self.raw_edges, "edges_image.txt")

    def save_final_txt(self):
        self.save_data_as_txt(self.raw_final, "final_image.txt")


# ---------------- 실행 ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = DotConverterApp(root)
    root.mainloop()