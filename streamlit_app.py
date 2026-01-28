import streamlit as st
import pandas as pd
import sys
import os

# 将当前脚本所在的目录添加到 sys.path，解决在 Streamlit Cloud 子目录部署时的路径问题
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from solver import generate_candidates, get_best_guess
from compare import compare_numbers

# set_page_config 必须是第一个 Streamlit 命令
st.set_page_config(page_title="1A2B 求解器", page_icon="🧩")

def reset_game():
    """重置游戏状态"""
    st.session_state.candidates = generate_candidates(st.session_state.allow_repeat)
    # 用于 minmax 的搜索空间，如果是标准版（不重复），可以全集搜索或者只搜索候选集
    # 这里为了简单和性能，我们传递 candidates 的副本作为 potential_guesses
    # 注意：solver.py 中的 get_best_guess 接受 (candidates, all_possible_guesses)
    # 但在 solver.py 内部逻辑里，如果 candidates 较多，它主要用 search_space = candidates
    st.session_state.all_possible = list(st.session_state.candidates)
    st.session_state.history = []
    st.session_state.game_over = False
    st.session_state.turn = 1
    st.session_state.last_guess = None

st.title("🧩 1A2B (Bulls and Cows) 求解器")
st.markdown("""
这是一个辅助你玩 1A2B 猜数字游戏的 AI助手。
你自己在这个网页之外的地方（比如手机APP、纸上）玩游戏，然后在这里输入 AI 推荐猜测的结果。
""")

# --- 侧边栏配置 ---
with st.sidebar:
    st.header("⚙️ 游戏设置")
    allow_repeat = st.checkbox("允许数字重复?", value=False, key="allow_repeat_checkbox")
    
    # 如果设置改变，重置游戏
    if "allow_repeat" not in st.session_state:
        st.session_state.allow_repeat = allow_repeat
        reset_game()
    elif st.session_state.allow_repeat != allow_repeat:
        st.session_state.allow_repeat = allow_repeat
        reset_game()
    
    if st.button("🔄 重新开始游戏"):
        reset_game()

# --- 初始化状态 ---
if "candidates" not in st.session_state:
    st.session_state.allow_repeat = allow_repeat
    reset_game()

# --- 游戏主逻辑 ---

if st.session_state.game_over:
    if len(st.session_state.candidates) == 1:
        st.success(f"🎉 答案一定是: **{st.session_state.candidates[0]}**")
    else:
        st.error("游戏结束，但在候选集中没有找到答案，可能是之前的反馈有误。")
    
    if st.button("再玩一次"):
        reset_game()
        st.rerun()
else:
    # 显示当前状态
    col1, col2 = st.columns(2)
    with col1:
        st.metric("当前回合", st.session_state.turn)
    with col2:
        st.metric("剩余可能答案", len(st.session_state.candidates))

    # 获取AI推荐
    # 如果是第一步，且是标准模式，直接给出经典开局
    if st.session_state.turn == 1 and not st.session_state.allow_repeat:
        recommended_guess = "0123"
    elif st.session_state.turn == 1 and st.session_state.allow_repeat:
        recommended_guess = "0123" # 也是个不错的开始
    else:
        # 只有当候选集不是特别大时，或者需要计算时才显示 spinner
        with st.spinner('🤔 AI 正在思考最佳策略...'):
             if len(st.session_state.candidates) == 1:
                 recommended_guess = st.session_state.candidates[0]
             else:
                 recommended_guess = get_best_guess(st.session_state.candidates, st.session_state.all_possible)
    
    st.session_state.last_guess = recommended_guess

    st.info(f"AI 推荐猜测: **{recommended_guess}**")

    # 用户输入反馈
    st.write("请输入你在游戏中猜测该数字后得到的结果:")
    
    with st.form(key="feedback_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            feedback_a = st.number_input("A (位置数值都对)", min_value=0, max_value=4, value=0)
        with col_b:
            feedback_b = st.number_input("B (数值对位置不对)", min_value=0, max_value=4, value=0)
            
        submit_btn = st.form_submit_button("提交反馈")

    if submit_btn:
        # 验证输入合法性
        if feedback_a + feedback_b > 4:
            st.error("❌ A + B 不能大于 4")
        elif len(st.session_state.candidates) == 1 and recommended_guess == st.session_state.candidates[0] and feedback_a != 4:
             st.error("❌ 这里有点问题。只剩这一个候选了，但结果不是 4A。请检查之前的反馈。")
        else:
            # 记录历史
            st.session_state.history.append({
                "回合": st.session_state.turn,
                "猜测": recommended_guess,
                "反馈": f"{feedback_a}A{feedback_b}B",
                "剩余可能": len(st.session_state.candidates)
            })
            
            # 胜利检测
            if feedback_a == 4:
                st.balloons()
                st.success(f"🎉 恭喜！答案是 {recommended_guess}。总共用了 {st.session_state.turn} 步。")
                st.session_state.game_over = True
                st.rerun()

            # 过滤候选集
            new_candidates = []
            for cand in st.session_state.candidates:
                # 假设 cand 是答案，用 recommended_guess 去猜，结果应该是多少？
                res = compare_numbers(cand, recommended_guess)
                if res[0] == feedback_a and res[1] == feedback_b:
                    new_candidates.append(cand)
            
            st.session_state.candidates = new_candidates
            st.session_state.turn += 1
            
            if len(st.session_state.candidates) == 0:
                 st.session_state.game_over = True
                 st.error("🤯 哎呀，没有符合条件的数字了！之前的某个反馈可能输错了。")
            
            st.rerun()

# --- 显示历史 ---
if st.session_state.history:
    st.markdown("### 📜 猜测历史")
    df_history = pd.DataFrame(st.session_state.history)
    st.table(df_history)

# --- 调试信息 (可选，当候选集很少时显示) ---
if 0 < len(st.session_state.candidates) <= 10 and not st.session_state.game_over:
    st.markdown("### 🔍 剩余的嫌疑数字")
    st.write(st.session_state.candidates)
