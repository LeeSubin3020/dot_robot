############################# frame 방식에서 canvas 방식으로 이미지 버튼을 개선 해서 리소스 문제를 해결한 버전 + 텍스트 파일 불러오기  ##################################
import time
import rclpy
import DR_init
import tkinter as tk
from tkinter import filedialog
import ast
import threading
import queue

# ======================
# 설정
# ======================
ROBOT_ID = "dsr01"
ROBOT_MODEL = "m0609"
VELOCITY, ACC = 100, 100
MATRIX_SIZE = 256 # 64x64 빈 배열 요청에 따라 크기를 64로 설정
ON, OFF = 1, 0

dot_64x64 = [

]


DR_init.__dsr__id = ROBOT_ID
DR_init.__dsr__model = ROBOT_MODEL

# 명령 큐
command_queue = queue.Queue()


class DotMatrixGUI:
    def __init__(self, master, initial_matrix=None):
        self.master = master
        master.title(f"{MATRIX_SIZE}x{MATRIX_SIZE} Dot Matrix")
        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=1)

        self.matrix = [[0 for _ in range(MATRIX_SIZE)] for _ in range(MATRIX_SIZE)]
        self.rects = [[None for _ in range(MATRIX_SIZE)] for _ in range(MATRIX_SIZE)]

        # --- 스크롤바와 캔버스를 담을 프레임 ---
        canvas_frame = tk.Frame(master)
        canvas_frame.grid(row=0, column=0, sticky="nsew")
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # --- Canvas 설정 ---
        self.cell_size = 7
        canvas_width = MATRIX_SIZE * self.cell_size
        canvas_height = MATRIX_SIZE * self.cell_size
        
        self.canvas = tk.Canvas(canvas_frame, width=canvas_width, height=canvas_height, bg="white", highlightthickness=0)
        
        # --- 스크롤바 생성 및 연결 ---
        v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # 캔버스에 격자무늬 사각형 그리기
        for r in range(MATRIX_SIZE):
            for c in range(MATRIX_SIZE):
                x1, y1 = c * self.cell_size, r * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                self.rects[r][c] = self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="#d0d0d0")
        
        # 스크롤 영역 설정
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        # 이벤트 바인딩
        self.canvas.bind("<Button-1>", self.handle_mouse_event)
        self.canvas.bind("<B1-Motion>", self.handle_mouse_event)

        # --- 버튼들을 담을 프레임 ---
        button_frame = tk.Frame(master)
        button_frame.grid(row=1, column=0, pady=5)

        self.load_button = tk.Button(button_frame, text="Load from File", command=self.load_from_file)
        self.load_button.pack(side=tk.LEFT, padx=5)
        
        self.send_button = tk.Button(button_frame, text="Send", command=self.send_matrix)
        self.send_button.pack(side=tk.LEFT, padx=5)

        if initial_matrix:
            self.load_matrix(initial_matrix)

    def load_from_file(self):
        filepath = filedialog.askopenfilename(
            title="Open Dot Matrix File",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r') as f:
                content = f.read().strip()
                # 마지막에 쉼표(,)가 있으면 문법 오류를 유발할 수 있으므로 제거
                if content.endswith(','):
                    content = content[:-1]
                
                # 전체 내용을 대괄호로 감싸서 완전한 리스트 문자열로 만듦
                matrix_string = f"[{content}]"
            
            new_matrix = ast.literal_eval(matrix_string)
            
            # 기본적인 행렬 검증
            if (isinstance(new_matrix, list) and 
                len(new_matrix) == MATRIX_SIZE and 
                all(isinstance(row, list) and len(row) == MATRIX_SIZE for row in new_matrix)):
                self.load_matrix(new_matrix)
            else:
                print(f"Error: The data in the file is not a valid {MATRIX_SIZE}x{MATRIX_SIZE} matrix.")
        except (ValueError, SyntaxError, TypeError) as e:
            print(f"Error parsing file content: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


    def load_matrix(self, matrix_to_load):
        if not (isinstance(matrix_to_load, list) and len(matrix_to_load) == MATRIX_SIZE and
                all(isinstance(row, list) and len(row) == MATRIX_SIZE for row in matrix_to_load)):
            print(f"Warning: Initial matrix is empty or dimensions do not match {MATRIX_SIZE}x{MATRIX_SIZE}. Skipping load.")
            return

        for r in range(MATRIX_SIZE):
            for c in range(MATRIX_SIZE):
                self.matrix[r][c] = matrix_to_load[r][c]
                color = "black" if self.matrix[r][c] == 1 else "white"
                self.canvas.itemconfig(self.rects[r][c], fill=color)

    def toggle_dot(self, r, c):
        if not (0 <= r < MATRIX_SIZE and 0 <= c < MATRIX_SIZE):
            return

        if self.matrix[r][c] == 0:
            self.matrix[r][c] = 1
            self.canvas.itemconfig(self.rects[r][c], fill="black")
        else:
            self.matrix[r][c] = 0
            self.canvas.itemconfig(self.rects[r][c], fill="white")

    def handle_mouse_event(self, event):
        # 캔버스 좌표를 그리드 좌표로 변환
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        c = int(canvas_x // self.cell_size)
        r = int(canvas_y // self.cell_size)
        
        self.toggle_dot(r, c)

    def send_matrix(self):
        print("Sending matrix to robot:")
        for row in self.matrix:
            print(row)
        command_queue.put(self.matrix)


def draw_matrix(matrix, dsr_robot_module, dsr_common_module):
    """Function to control the robot to draw the given matrix."""
    movej = dsr_robot_module.movej
    movel = dsr_robot_module.movel
    DR_MV_MOD_REL = dsr_robot_module.DR_MV_MOD_REL
    posj = dsr_common_module.posj

    home = posj(0., 0., 90., 0., 90., 0.)

    # --- 고정된 드로잉 영역 설정 ---
    drawing_start_x = 275.0
    drawing_end_x = 462.0
    start_y = 6.31
    start_z = 125.8
    start_ori = [100.0, 180.0, 12.0]

    # --- 설정에 따른 변수 자동 계산 ---
    drawing_width = drawing_end_x - drawing_start_x
    cell_spacing = drawing_width / (MATRIX_SIZE - 1)
    #cell_spacing = 1.5
    print(f"Calculated cell spacing to fit the area: {cell_spacing:.4f} mm")

    # --- 이동 위치 계산 ---
    start_pos = [drawing_start_x, start_y, start_z] + start_ori
    # 드로잉 준비 위치 (시작점보다 Z축으로 20mm 위)
    ready_pos = start_pos.copy()
    ready_pos[2] += 20.0
    
    # 이동 간격 정의
    delta_x = [cell_spacing, 0., 0., 0., 0., 0.]
    delta_y = [0., cell_spacing, 0., 0., 0., 0.]
    delta_z = [-1.3, 0., -3.1, 0., 0., 0.]
    delta_z_up = [1.3, 0., 3.1, 0., 0., 0.]

    # --- 로봇 이동 시작 ---
    # 1. 안전한 홈 포지션으로 이동
    movej(home, vel=100, acc=100)
    # 2. 그림을 그릴 준비 위치로 이동 (관절 이동)
    movej(ready_pos, vel=VELOCITY, acc=ACC)
    # 3. 실제 드로잉 시작 위치로 선형 이동
    movel(start_pos, vel=VELOCITY, acc=ACC)

    for i in range(MATRIX_SIZE):
        a = 0
        # 현재 행의 마지막 1 위치 찾기
        try:
            last_one_index = max(idx for idx, val in enumerate(matrix[i]) if val == 1)
        except ValueError:
            last_one_index = -1

        if last_one_index == -1:
            # 1이 없으면 다음 행으로 이동
            movel(delta_y, vel=VELOCITY, acc=ACC, mod=DR_MV_MOD_REL)
            continue

        for j in range(last_one_index + 1):
            if matrix[i][j] == 1:
                movel(delta_z, vel=VELOCITY, acc=ACC, mod=DR_MV_MOD_REL)
                time.sleep(0.05)
                movel(delta_z_up, vel=VELOCITY, acc=ACC, mod=DR_MV_MOD_REL)
                time.sleep(0.05)

            if j == last_one_index:
                # 행의 마지막 도달 시, 다음 행으로 이동 및 X축 원위치 복귀
                movel([a, cell_spacing, 0., 0., 0., 0.], vel=VELOCITY, acc=ACC, mod=DR_MV_MOD_REL)
            else:
                # 다음 점으로 이동
                a -= cell_spacing
                movel(delta_x, vel=VELOCITY, acc=ACC, mod=DR_MV_MOD_REL)

    # 그리기가 끝나면 다시 준비 위치로 후퇴
    movej(ready_pos, vel=VELOCITY, acc=ACC)
    # 홈으로 복귀
    movej(home, vel=100, acc=95)
    print("Drawing finished.")


def ros_control_loop(node, dsr_robot, dsr_common):
    """ROS2 spin + 큐에서 명령 읽어서 실행"""
    while rclpy.ok():
        try:
            matrix = command_queue.get_nowait()
            draw_matrix(matrix, dsr_robot, dsr_common)
        except queue.Empty:
            pass
        rclpy.spin_once(node, timeout_sec=0.05)


def main(args=None):
    rclpy.init(args=args)
    node = rclpy.create_node("rokey_move", namespace=ROBOT_ID)
    DR_init.__dsr__node = node

    try:
        import DSR_ROBOT2 as dsr_robot
        import DR_common2 as dsr_common
    except ImportError as e:
        print(f"Error importing DSR modules: {e}")
        rclpy.shutdown()
        return

    # 툴 세팅 및 그리퍼 함수를 draw_matrix에서 여기로 이동
    dsr_robot.set_tool("Tool Weight_2FG")
    dsr_robot.set_tcp("2FG_TCP")


    # ROS 제어 스레드 시작
    ros_thread = threading.Thread(
        target=ros_control_loop, args=(node, dsr_robot, dsr_common), daemon=True
    )
    ros_thread.start()

    # Tkinter GUI 실행
    root = tk.Tk()
    DotMatrixGUI(root, initial_matrix=dot_64x64)
    root.mainloop()

    rclpy.shutdown()


if __name__ == "__main__":
    main()