import tkinter as tk
from tkinter import ttk, messagebox
import threading
import itertools
from compare import compare_numbers

# --- 核心算法部分 (复用原逻辑) ---

def generate_candidates(allow_repeat=False):
    if allow_repeat:
        return [f"{i:04d}" for i in range(10000)]
    else:
        perms = itertools.permutations('0123456789', 4)
        return ["".join(p) for p in perms]

def get_feedback_groups(candidates, guess):
    groups = {}
    for scalar in candidates:
        res = compare_numbers(scalar, guess)
        if res not in groups:
            groups[res] = 0
        groups[res] += 1
    return groups

def get_best_guess(candidates):
    # 如果候选集很小，直接猜第一个
    if len(candidates) <= 1:
        return candidates[0]
    
    # 第一步优化
    if len(candidates) > 4900: 
        return "0123"

    best_guess = candidates[0]
    min_worst_case = float('inf')
    
    # 简单的搜索策略：只在候选集中搜索 (一致性猜测)
    # 这样能保证 UI 响应速度
    
    # 为了避免界面卡死过久，如果候选集还是很大，我们可以只搜索前 N 个样本
    # 或者全搜（Python对于几千个循环还是很快的）
    search_space = candidates
    
    for guess in search_space:
        groups = get_feedback_groups(candidates, guess)
        worst_case = max(groups.values())
        
        if worst_case < min_worst_case:
            min_worst_case = worst_case
            best_guess = guess
            
        if min_worst_case == 1:
            return best_guess

    return best_guess

# --- GUI 应用程序 ---

class SolverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("1A2B 助手")
        self.root.geometry("400x500")
        self.root.resizable(False, False)

        # 游戏状态
        self.candidates = []
        self.history = []
        
        self.setup_ui()
        
    def setup_ui(self):
        # 1. 顶部设置区
        self.config_frame = ttk.LabelFrame(self.root, text="设置")
        self.config_frame.pack(fill="x", padx=10, pady=5)
        
        self.repeat_var = tk.BooleanVar(value=False)
        self.chk_repeat = ttk.Checkbutton(self.config_frame, text="允许数字重复", variable=self.repeat_var)
        self.chk_repeat.pack(side="left", padx=10, pady=5)
        
        self.btn_start = ttk.Button(self.config_frame, text="开始新游戏", command=self.start_game)
        self.btn_start.pack(side="right", padx=10, pady=5)

        # 2. 核心操作区
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 推荐猜测显示
        ttk.Label(self.main_frame, text="推荐猜测", font=("Microsoft YaHei", 10)).pack(pady=(10, 0))
        self.lbl_guess = ttk.Label(self.main_frame, text="---", font=("Consolas", 24, "bold"), foreground="#007ACC")
        self.lbl_guess.pack(pady=5)
        
        self.lbl_status = ttk.Label(self.main_frame, text="请点击开始", font=("Microsoft YaHei", 9), foreground="gray")
        self.lbl_status.pack(pady=(0, 15))

        # 输入反馈
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(pady=5)
        
        ttk.Label(input_frame, text="A:").pack(side="left")
        self.spin_a = ttk.Spinbox(input_frame, from_=0, to=4, width=3, font=("Consolas", 12))
        self.spin_a.set(0)
        self.spin_a.pack(side="left", padx=5)
        
        ttk.Label(input_frame, text="B:").pack(side="left")
        self.spin_b = ttk.Spinbox(input_frame, from_=0, to=4, width=3, font=("Consolas", 12))
        self.spin_b.set(0)
        self.spin_b.pack(side="left", padx=5)
        
        self.btn_confirm = ttk.Button(input_frame, text="确认", command=self.process_feedback, state="disabled")
        self.btn_confirm.pack(side="left", padx=15)

        # 3. 历史记录和候选信息
        self.log_frame = ttk.LabelFrame(self.root, text="猜测记录 & 候选")
        self.log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.txt_log = tk.Text(self.log_frame, height=10, state="disabled", font=("Consolas", 9))
        self.txt_log.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 绑定回车键
        self.root.bind('<Return>', lambda event: self.process_feedback())

    def log(self, message):
        self.txt_log.config(state="normal")
        self.txt_log.insert("end", message + "\n")
        self.txt_log.see("end")
        self.txt_log.config(state="disabled")

    def start_game(self):
        self.candidates = generate_candidates(self.repeat_var.get())
        self.history = []
        
        # 重置UI
        self.txt_log.config(state="normal")
        self.txt_log.delete(1.0, "end")
        self.txt_log.config(state="disabled")
        self.spin_a.set(0)
        self.spin_b.set(0)
        
        self.update_guess_ui()
        self.btn_confirm.config(state="normal")
        self.log(f"游戏开始! 初始候选数: {len(self.candidates)}")

    def update_guess_ui(self):
        count = len(self.candidates)
        if count == 0:
            self.lbl_guess.config(text="无解")
            self.lbl_status.config(text="没有符合条件的数字，请检查输入", foreground="red")
            self.btn_confirm.config(state="disabled")
            return
            
        if count == 1:
            self.lbl_guess.config(text=self.candidates[0])
            self.lbl_status.config(text="找到唯一答案！", foreground="green")
            self.log(f"最终答案: {self.candidates[0]}")
            # 这里可以选择不禁用，防止误操作
            return

        self.lbl_status.config(text="正在计算...", foreground="orange")
        self.root.update() # 强制刷新UI显示"正在计算"
        
        # 启动线程或直接运行（对于简单逻辑直接运行即可，复杂的用线程）
        # 为了代码简单，这里直接运行，因为逻辑优化过，速度很快
        best = get_best_guess(self.candidates)
        
        self.curr_guess = best
        self.lbl_guess.config(text=best)
        self.lbl_status.config(text=f"剩余可能: {count}", foreground="black")

    def process_feedback(self):
        if str(self.btn_confirm['state']) == 'disabled':
            return

        try:
            a = int(self.spin_a.get())
            b = int(self.spin_b.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
            return

        if a + b > 4:
            messagebox.showerror("错误", "A + B 不能大于 4")
            return
            
        if a == 4:
            self.lbl_guess.config(text="胜利!")
            self.lbl_status.config(text="恭喜！", foreground="green")
            self.btn_confirm.config(state="disabled")
            self.log(f">> {self.curr_guess} -> 4A0B (完成)")
            return

        # 记录日志
        self.log(f"[{len(self.history)+1}] {self.curr_guess} -> {a}A{b}B")
        
        # 剪枝逻辑
        prev_count = len(self.candidates)
        new_candidates = []
        for cand in self.candidates:
            res = compare_numbers(cand, self.curr_guess)
            if res[0] == a and res[1] == b:
                new_candidates.append(cand)
        
        self.candidates = new_candidates
        diff = prev_count - len(self.candidates)
        # self.log(f"   排除 {diff} 个选项")
        
        self.update_guess_ui()

if __name__ == "__main__":
    root = tk.Tk()
    app = SolverApp(root)
    root.mainloop()
