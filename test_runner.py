import json
import requests
from typing import Any, Dict, List

class TestRunner:
    """测试运行器，用于执行测试用例"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """初始化测试运行器
        
        Args:
            base_url (str): MCP 服务器的基础 URL
        """
        self.base_url = base_url
        self.mcp_url = f"{base_url}/mcp"
    
    def load_test_cases(self, file_path: str) -> List[Dict[str, Any]]:
        """加载测试用例
        
        Args:
            file_path (str): 测试用例文件路径
            
        Returns:
            List[Dict[str, Any]]: 测试用例列表
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('test_cases', [])
    
    def run_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个测试用例
        
        Args:
            test_case (Dict[str, Any]): 测试用例
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        # 准备请求数据
        request_data = {
            "method": test_case["method"],
            "args": test_case["args"],
            "kwargs": test_case["kwargs"]
        }
        
        # 发送请求
        response = requests.post(self.mcp_url, json=request_data)
        result = response.json()
        
        # 检查结果
        success = result["success"]
        actual = result.get("result")
        expected = test_case["expected"]
        
        # 比较结果
        passed = actual == expected
        
        return {
            "name": test_case["name"],
            "method": test_case["method"],
            "args": test_case["args"],
            "kwargs": test_case["kwargs"],
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "error": None if success else result.get("error")
        }
    
    def run_all_tests(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """运行所有测试用例
        
        Args:
            test_cases (List[Dict[str, Any]]): 测试用例列表
            
        Returns:
            List[Dict[str, Any]]: 测试结果列表
        """
        results = []
        for test_case in test_cases:
            result = self.run_test_case(test_case)
            results.append(result)
            
            # 打印测试结果
            print(f"\n测试: {result['name']}")
            print(f"方法: {result['method']}")
            print(f"参数: args={result['args']}, kwargs={result['kwargs']}")
            print(f"预期: {result['expected']}")
            print(f"实际: {result['actual']}")
            print(f"状态: {'通过' if result['passed'] else '失败'}")
            if result['error']:
                print(f"错误: {result['error']}")
            print("-" * 40)
        
        return results
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """打印测试摘要
        
        Args:
            results (List[Dict[str, Any]]): 测试结果列表
        """
        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        failed = total - passed
        
        print("\n测试摘要:")
        print(f"总测试数: {total}")
        print(f"通过数: {passed}")
        print(f"失败数: {failed}")
        print(f"通过率: {passed/total*100:.2f}%")

if __name__ == "__main__":
    # 创建测试运行器
    runner = TestRunner()
    
    # 加载测试用例
    test_cases = runner.load_test_cases("test_cases.json")
    
    # 运行测试
    results = runner.run_all_tests(test_cases)
    
    # 打印摘要
    runner.print_summary(results) 