import itertools
from compare import compare_numbers
import sys
import time

def generate_candidates(allow_repeat=False):
    """
    生成所有可能的四位数字候选列表。
    """
    if allow_repeat:
        return [f"{i:04d}" for i in range(10000)]
    else:
        # 使用 itertools.permutations 生成无重复数字
        perms = itertools.permutations('0123456789', 4)
        return ["".join(p) for p in perms]

def get_feedback_groups(candidates, guess):
    """
    计算如果猜 guess，候选集会被分成哪些 (A, B) 组，每组有多少个。
    返回: 字典 {(A, B): count}
    """
    groups = {}
    for scalar in candidates:
        # scalar 是潜在的答案
        # compare_numbers(basic, input) -> basic是答案, input是猜测
        res = compare_numbers(scalar, guess)
        if res not in groups:
            groups[res] = 0
        groups[res] += 1
    return groups

def get_best_guess(candidates, all_possible_guesses):
    """
    使用 Minimax 策略寻找最优解。
    目标：最小化最大可能剩余的候选集数量。
    为了速度，我们通常只在 candidates 中搜索猜测（一致性猜测），
    或者如果 candidates 很少，我们可以搜索全集。
    """
    # 如果候选集很小，直接猜第一个
    if len(candidates) <= 2:
        return candidates[0]
        
    start_time = time.time()
    
    best_guess = None
    min_worst_case = float('inf')
    
    # 策略优化：
    # 如果候选集太多 (>1000)，计算量太大。
    # 我们先只从候选集中找，这样比较快（一致性猜测）。
    # 如果候选集较小，我们可以尝试搜索更多的空间（如果需要更优）。
    # 这里为了响应速度，默认使用 "从剩余候选者中猜测" 的策略。
    # 也可以在第一步硬编码一个好的初始猜测（如 0123 或 1234）。
    
    search_space = candidates 
    
    # 如果是第一步（全集），直接返回一个已知较优解以节省时间
    if len(candidates) > 4900: # 5040 is standard no-repeat count
        # 对于标准的不重复 1A2B，0123 是一个很好的开局
        # 对于可重复，0123 也是不错的
        return "0123"

    for guess in search_space:
        groups = get_feedback_groups(candidates, guess)
        
        # 这种猜测下的最坏情况（剩下的候选集最大是多少）
        worst_case = max(groups.values())
        
        if worst_case < min_worst_case:
            min_worst_case = worst_case
            best_guess = guess
            
        # 如果找到一个能保证下次只剩1个或0个的（这不太可能，但在小集合里可能），直接返回
        if min_worst_case == 1:
            return best_guess

    return best_guess

def main():
    print("--- 1A2B 求解器 ---")
    print("请输入游戏模式:")
    mode = input("是否允许数字重复? (y/n) [默认 n]: ").strip().lower()
    allow_repeat = mode == 'y'
    
    candidates = generate_candidates(allow_repeat)
    all_possible_guesses = list(candidates) # 备份一份完整的空间
    
    print(f"初始候选数: {len(candidates)}")
    
    steps = 0
    while True:
        steps += 1
        print(f"\n--- 第 {steps} 步 ---")
        
        if len(candidates) == 0:
            print("错误：没有符合条件的数字了！请检查输入是否正确。")
            break
        
        if len(candidates) == 1:
            print(f"唯一剩下的可能答案是: {candidates[0]}")
            break
            
        print("正在计算最优猜测...")
        guess = get_best_guess(candidates, all_possible_guesses)
        print(f"推荐猜测: {guess}")
        
        while True:
            try:
                feedback = input(f"请输入 '{guess}' 的结果 (例如 1 2 代表 1A2B): ").strip()
                if not feedback: continue
                parts = feedback.replace('A', ' ').replace('B', ' ').split()
                if len(parts) != 2:
                    print("格式错误。请输入两个数字，用空格分隔。")
                    continue
                a = int(parts[0])
                b = int(parts[1])
                if a == 4:
                    print(f"恭喜！答案是 {guess}。总共用了 {steps} 步。")
                    return
                break
            except ValueError:
                print("无效输入，请输入数字。")

        # 剪枝
        new_candidates = []
        for cand in candidates:
            # 这里的 cand 是潜在的 Secret
            # 如果 Secret 是 cand，我们猜 guess，结果应该是 (a, b)
            # 如果算出来的结果不是 (a, b)，那 cand 就不可能是 Secret
            res = compare_numbers(cand, guess)
            if res[0] == a and res[1] == b:
                new_candidates.append(cand)
        
        print(f"排除后剩余可能: {len(candidates)} -> {len(new_candidates)}")
        candidates = new_candidates
        
        if len(candidates) <= 10:
            print(f"剩余的候选者: {candidates}")

if __name__ == "__main__":
    main()
