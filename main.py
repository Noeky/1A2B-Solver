import flet as ft
# Copright (c) 一懒众衫小Noeky
import itertools
import threading
import time

# --- 核心逻辑 (保持不变) ---

def compare_numbers(basic, input_val):
    str_basic = str(basic)
    str_input = str(input_val)
    count_a = 0
    basic_counts = {}
    input_counts = {}
    for i in range(4):
        if str_basic[i] == str_input[i]:
            count_a += 1
        basic_counts[str_basic[i]] = basic_counts.get(str_basic[i], 0) + 1
        input_counts[str_input[i]] = input_counts.get(str_input[i], 0) + 1
    total_matches = sum(min(basic_counts.get(c, 0), input_counts.get(c, 0)) for c in basic_counts)
    return count_a, total_matches - count_a

def generate_candidates(allow_repeat=False):
    if allow_repeat:
        return [f"{i:04d}" for i in range(10000)]
    else:
        return ["".join(p) for p in itertools.permutations('0123456789', 4)]

def get_best_guess(candidates):
    if not candidates: return None
    if len(candidates) <= 1: return candidates[0]
    if len(candidates) > 4900: return "0123" # 快速开局
    
    # 为了手机性能，我们只搜索前500个候选项或者全部（如果少于500）
    search_space = candidates if len(candidates) < 500 else candidates[:500]
    
    best_guess = candidates[0]
    min_worst_case = float('inf')
    
    for guess in search_space:
        groups = {}
        for cand in candidates:
            res = compare_numbers(cand, guess)
            groups[res] = groups.get(res, 0) + 1
        
        worst_case = max(groups.values())
        if worst_case < min_worst_case:
            min_worst_case = worst_case
            best_guess = guess
        if min_worst_case == 1: break
            
    return best_guess

# --- Flet UI ---

def main(page: ft.Page):
    page.title = "1A2B 助手"
    page.scroll = "adaptive"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.window_width = 400
    page.window_height = 700

    # 状态变量
    candidates = []
    current_guess = ""
    history = []

    # UI 控件
    txt_guess = ft.Text("---", size=40, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE)
    txt_status = ft.Text("请点击开始", size=14, color=ft.colors.GREY)
    
    # 历史记录列表
    lv_history = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)

    # 输入控件
    dd_a = ft.Dropdown(
        width=80, label="A", 
        options=[ft.dropdown.Option(str(i)) for i in range(5)],
        value="0"
    )
    dd_b = ft.Dropdown(
        width=80, label="B", 
        options=[ft.dropdown.Option(str(i)) for i in range(5)],
        value="0"
    )
    
    def add_log(text, is_success=False):
        color = ft.colors.GREEN if is_success else ft.colors.BLACK
        lv_history.controls.append(ft.Text(text, color=color, size=16))
        lv_history.update()

    def update_guess_display(text, status_text, color=ft.colors.BLUE):
        txt_guess.value = text
        txt_guess.color = color
        txt_status.value = status_text
        page.update()

    def run_solver_thread():
        nonlocal current_guess
        
        count = len(candidates)
        if count == 0:
            update_guess_display("无解", "没有符合条件的数字", ft.colors.RED)
            btn_confirm.disabled = True
            btn_confirm.update()
            return
        
        if count == 1:
            current_guess = candidates[0]
            update_guess_display(current_guess, "唯一确定答案!", ft.colors.GREEN)
            add_log(f"最终答案: {current_guess}", True)
            return

        # 计算中...
        update_guess_display("计算中...", f"剩余可能性: {count}", ft.colors.ORANGE)
        
        # 运行算法
        best = get_best_guess(candidates)
        current_guess = best
        
        update_guess_display(best, f"剩余可能性: {count}", ft.colors.BLUE)
        btn_confirm.disabled = False
        btn_confirm.update()

    def on_confirm_click(e):
        if not current_guess: return
        
        try:
            val_a = int(dd_a.value)
            val_b = int(dd_b.value)
        except:
            return

        if val_a == 4:
            update_guess_display("胜利!", "恭喜你！", ft.colors.GREEN)
            add_log(f"{current_guess} -> 4A0B (完成)", True)
            btn_confirm.disabled = True
            btn_confirm.update()
            return

        if val_a + val_b > 4:
            page.show_snack_bar(ft.SnackBar(content=ft.Text("A + B 不能大于 4")))
            return

        # 记录
        add_log(f"{current_guess} -> {val_a}A{val_b}B")
        
        # 剪枝
        nonlocal candidates
        new_candidates = []
        for cand in candidates:
            res = compare_numbers(cand, current_guess)
            if res[0] == val_a and res[1] == val_b:
                new_candidates.append(cand)
        
        candidates = new_candidates
        
        # 重置输入
        dd_a.value = "0"
        dd_b.value = "0"
        dd_a.update()
        dd_b.update()
        
        # 下一步
        run_solver_thread()

    btn_confirm = ft.ElevatedButton("确认", on_click=on_confirm_click, disabled=True)

    def on_start_click(e):
        nonlocal candidates, history
        candidates = generate_candidates(sw_repeat.value)
        history = []
        lv_history.controls.clear()
        
        dd_a.value = "0"
        dd_b.value = "0"
        
        add_log(f"开始新游戏 (候选数: {len(candidates)})")
        run_solver_thread()
        page.update()

    sw_repeat = ft.Switch(label="允许数字重复", value=False)
    btn_start = ft.ElevatedButton("开始新游戏", on_click=on_start_click, icon=ft.icons.PLAY_ARROW)

    # 布局
    page.add(
        ft.Container(
            content=ft.Column([
                ft.Row([sw_repeat, btn_start], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Column([
                    ft.Text("推荐猜测", size=12),
                    txt_guess,
                    txt_status
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Divider(),
                ft.Row([
                    dd_a, dd_b, btn_confirm
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                ft.Text("历史记录", weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=lv_history,
                    height=300, # 固定高度以允许滚动
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=10,
                )
            ]),
            padding=20
        )
    )

ft.app(target=main)
