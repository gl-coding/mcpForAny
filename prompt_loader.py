import os
import re
import json
import argparse
from prompt_wrapper import Testable, PromptWrapper

class PromptLoader(Testable):
    def __init__(self, directory):
        """初始化PromptLoader
        
        Args:
            directory (str): 要遍历的目录路径
        """
        self.key_value_store = {}
        self.valid_items = {}  # 存储有效的键值对
        self.invalid_items = {}  # 存储无效的键值对
        self.base_directory = directory  # 保存基础目录路径
        if os.path.exists(directory):
            print(f"开始处理目录: {directory}")
            self._traverse_directory(directory)
            # 初始化后立即处理变量替换
            self._process_variables()
        else:
            print(f"目录 {directory} 不存在")

    def _parse_key_value_pairs(self, content):
        """解析文件内容中的键值对"""
        # 使用正则表达式匹配 #key \n value 格式
        pattern = r'#(\w+)\s*\n([^#]+)'
        matches = re.findall(pattern, content, re.DOTALL)
        return matches

    def _validate_path(self, file_path):
        """检查文件路径是否有效"""
        if '.' in file_path:
            raise ValueError(f"文件路径 {file_path} 中不能包含.字符")

    def _process_file(self, file_path, base_dir):
        """处理单个文件"""
        try:
            # 检查文件路径
            self._validate_path(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                pairs = self._parse_key_value_pairs(content)
                if pairs:
                    # 获取相对于base_dir的路径，并将路径分隔符替换为.
                    rel_path = os.path.relpath(file_path, base_dir).replace('/', '.')
                    print(f"\n文件: {file_path}")
                    for key, value in pairs:
                        # 在键名前面添加相对路径作为前缀，使用.作为分隔符
                        prefixed_key = f"{rel_path}.{key}"
                        # 将键值对存储到字典中
                        self.key_value_store[prefixed_key] = value.strip()
                        print(f"键: {prefixed_key}")
                        print(f"值: {value.strip()}")
                        print("-" * 40)
        except ValueError as e:
            print(f"错误: {str(e)}")
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {str(e)}")

    def _traverse_directory(self, directory):
        """遍历目录及其子目录"""
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                self._process_file(file_path, directory)

    def _process_variables(self):
        """处理值中的变量替换"""
        # 用于存储未找到的变量
        missing_vars = set()
        # 用于存储循环引用
        circular_refs = set()
        # 用于记录变量替换过程中的引用链
        ref_chain = []
        
        def replace_variables(key, value):
            """替换值中的变量引用
            
            Args:
                key (str): 当前处理的键
                value (str): 要处理的值
                
            Returns:
                tuple: (处理后的值, 是否有效)
            """
            # 检查是否已经在引用链中
            if key in ref_chain:
                # 发现循环引用
                cycle = ref_chain[ref_chain.index(key):] + [key]
                circular_refs.add(tuple(cycle))
                # 返回原始值，标记为无效
                return value, False
                
            ref_chain.append(key)
            
            # 查找所有变量引用
            variables = re.findall(r'{{([\w.]+)}}', value)
            if variables:
                new_value = value
                is_valid = True
                for var in variables:
                    if var in self.key_value_store:
                        # 递归处理变量引用
                        var_value, var_valid = replace_variables(var, self.key_value_store[var])
                        if not var_valid:
                            is_valid = False
                        # 替换变量
                        new_value = new_value.replace(f"{{{{{var}}}}}", var_value)
                    else:
                        missing_vars.add(var)
                        is_valid = False
                value = new_value
                ref_chain.pop()
                return value, is_valid
                
            ref_chain.pop()
            return value, True
        
        # 处理所有键值对
        for key, value in list(self.key_value_store.items()):
            ref_chain.clear()
            new_value, is_valid = replace_variables(key, value)
            if is_valid:
                self.valid_items[key] = new_value
            else:
                self.invalid_items[key] = new_value
        
        # 打印未找到的变量
        if missing_vars:
            print("\n警告: 以下变量未找到对应的值:")
            for var in sorted(missing_vars):
                print(f"- {var}")
                
        # 打印循环引用
        if circular_refs:
            print("\n警告: 检测到循环引用:")
            for cycle in sorted(circular_refs):
                cycle_str = " -> ".join(cycle)
                print(f"- 循环引用链: {cycle_str}")

    def get_value(self, key):
        """通过键名查询对应的值
        
        Args:
            key (str): 要查询的键名
            
        Returns:
            str: 如果找到对应的值则返回该值，否则返回None
        """
        return self.valid_items.get(key)

    def get_all_items(self):
        """返回所有有效的键值对
        
        Returns:
            dict: 包含所有有效键值对的字典
        """
        return self.valid_items.copy()

    def get_invalid_items(self):
        """返回所有无效的键值对
        
        Returns:
            dict: 包含所有无效键值对的字典
        """
        return self.invalid_items.copy()

    def dump(self, output_file, invalid_output_file=None):
        """将键值对以#key \n value的格式写入文件
        
        Args:
            output_file (str): 输出文件路径
            invalid_output_file (str, optional): 无效键值对的输出文件路径
            
        Returns:
            bool: 写入是否成功
        """
        try:
            # 写入有效的键值对
            with open(output_file, 'w', encoding='utf-8') as f:
                for key, value in self.valid_items.items():
                    f.write(f"#{key}\n{value}\n\n")
            print(f"成功将有效键值对写入文件: {output_file}")
            
            # 如果有无效的键值对，写入到另一个文件
            if self.invalid_items and invalid_output_file:
                with open(invalid_output_file, 'w', encoding='utf-8') as f:
                    f.write("# 以下键值对包含无效的变量引用或循环引用:\n\n")
                    for key, value in self.invalid_items.items():
                        f.write(f"#{key}\n{value}\n\n")
                print(f"成功将无效键值对写入文件: {invalid_output_file}")
            
            return True
            
        except Exception as e:
            print(f"写入文件时出错: {str(e)}")
            return False

    def write_key_value(self, key, value):
        """根据键名找到对应文件并写入键值对
        
        Args:
            key (str): 要写入的键名
            value (str): 要写入的值
            
        Returns:
            bool: 写入是否成功
        """
        try:
            # 解析键名，获取文件路径和键名
            parts = key.split('.')
            if len(parts) < 2:
                raise ValueError(f"无效的键名格式: {key}")
                
            # 最后一个部分是键名，其余部分是文件路径
            file_key = parts[-1]
            file_path_parts = parts[:-1]
            
            # 构建完整的文件路径
            file_path = os.path.join(self.base_directory, *file_path_parts)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 读取现有内容（如果文件存在）
            existing_content = ""
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            
            # 将内容分割成键值对
            pairs = []
            if existing_content.strip():
                # 使用正则表达式匹配所有键值对
                matches = re.finditer(r'#(\w+)\s*\n([^#]+)', existing_content)
                for match in matches:
                    k = match.group(1)
                    v = match.group(2).strip()
                    if k != file_key:  # 保留非当前键的所有键值对
                        pairs.append((k, v))
            
            # 添加或更新当前键值对
            pairs.append((file_key, value))
            
            # 重新格式化所有键值对
            new_content = ""
            for i, (k, v) in enumerate(pairs):
                if i > 0:  # 如果不是第一个键值对，添加一个空行
                    new_content += "\n"
                new_content += f"#{k}\n{v}\n"
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"成功将键值对写入文件: {file_path}")
            
            # 更新键值对存储
            self.key_value_store[key] = value
            # 重新处理变量替换
            self._process_variables()
            
            return True
            
        except Exception as e:
            print(f"写入键值对时出错: {str(e)}")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PromptLoader 测试运行器")
    parser.add_argument("--mode", choices=["test", "server"], default="test",
                      help="运行模式：test（运行测试）或 server（启动服务器）")
    parser.add_argument("--dir", default="prompt",
                      help="要处理的目录路径")
    parser.add_argument("--test-file", default="test_cases.json",
                      help="测试用例文件路径")
    
    args = parser.parse_args()
    
    # 创建 PromptLoader 实例
    loader = PromptLoader(args.dir)
    
    if args.mode == "test":
        # 运行测试
        loader.run_tests(args.test_file)
    else:
        # 启动服务器
        from prompt_wrapper import PromptWrapper
        PromptWrapper.start_server(PromptLoader, args.dir)
