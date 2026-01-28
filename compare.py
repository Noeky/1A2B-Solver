def compare_numbers(basic, input_val):
    """
    比较两个四位数字，返回A和B。
    
    参数:
    basic: 目标数字 (可以是字符串或整数)
    input_val: 猜测数字 (可以是字符串或整数)
    
    返回:
    (count_a, count_b): 
        count_a: 数字和位置都对的个数
        count_b: 数字出现但位置不对的个数
    """
    # 确保输入是字符串
    str_basic = str(basic)
    str_input = str(input_val)

    # 简单的验证
    if len(str_basic) != 4 or len(str_input) != 4:
         raise ValueError("输入必须是四位数字")

    count_a = 0
    
    # 用于统计字符频率的字典
    basic_counts = {}
    input_counts = {}
    
    for i in range(4):
        # 统计 A: 位置和字符都相同
        if str_basic[i] == str_input[i]:
            count_a += 1
        
        # 统计 Basic 中的字符出现次数
        char_b = str_basic[i]
        basic_counts[char_b] = basic_counts.get(char_b, 0) + 1
        
        # 统计 Input 中的字符出现次数
        char_i = str_input[i]
        input_counts[char_i] = input_counts.get(char_i, 0) + 1

    # 计算总共匹配的字符数（包含位置对和位置不对）
    # 逻辑：对于每个字符，不仅在 basic 中有，input 中也有，那么重叠的数量就是 min(basic_count, input_count)
    total_matches = 0
    for char in basic_counts:
        if char in input_counts:
            total_matches += min(basic_counts[char], input_counts[char])
            
    # B 的数量 = 总匹配数 - 完全匹配数(A)
    count_b = total_matches - count_a
    
    return count_a, count_b

if __name__ == "__main__":
    # 简单的测试用例
    test_cases = [
        ("1234", "1234"), # 4A0B
        ("1234", "4321"), # 0A4B
        ("1234", "1324"), # 2A2B
        ("1122", "1213"), # 1A2B (pos 0 matches, 1 2 match counts logic)
    ]
    
    for b, i in test_cases:
        a, b_val = compare_numbers(b, i)
        print(f"Basic: {b}, Input: {i} -> {a}A{b_val}B")
