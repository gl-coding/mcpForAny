# PromptLoader 函数调用示例
# 自动生成的函数调用格式文件

import json
from prompt_loader import PromptLoader

# 创建实例
loader = PromptLoader("prompt")

# 结果存储
results = []


if __name__ == "__main__":
    # 运行所有示例
    for name, func in globals().items():
        if name.startswith('example_'):
            print(f"\n运行示例: {name}")
            result = func()
            results.append(result)
    
    # 将结果保存为JSON文件
    with open("function_calls/results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n所有结果已保存到 function_calls/results.json")
