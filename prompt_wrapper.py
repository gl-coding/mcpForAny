import inspect
from functools import wraps
from sanic import Sanic
from sanic.response import json
import json as json_module
import argparse
import requests
from typing import Any, Dict, List

class ServerConfig:
    """服务器配置类"""
    
    # 默认配置
    HOST = "0.0.0.0"
    _PORT = 8000  # 使用私有变量存储端口
    
    @classmethod
    def get_port(cls) -> int:
        """获取当前端口号
        
        Returns:
            int: 当前端口号
        """
        return cls._PORT
    
    @classmethod
    def set_port(cls, port: int):
        """设置端口号
        
        Args:
            port (int): 要设置的端口号
        """
        if not isinstance(port, int):
            raise TypeError("端口号必须是整数")
        if port < 1 or port > 65535:
            raise ValueError("端口号必须在 1-65535 之间")
        cls._PORT = port
    
    @classmethod
    def get_server_url(cls) -> str:
        """获取服务器URL
        
        Returns:
            str: 服务器完整URL
        """
        return f"http://{cls.HOST}:{cls._PORT}"
    
    @classmethod
    def get_mcp_url(cls) -> str:
        """获取MCP接口URL
        
        Returns:
            str: MCP接口完整URL
        """
        return f"{cls.get_server_url()}/mcp"
    
    @classmethod
    def get_methods_url(cls) -> str:
        """获取methods接口URL
        
        Returns:
            str: methods接口完整URL
        """
        return f"{cls.get_server_url()}/methods"

class Testable:
    """可测试类的基类，提供测试功能"""
    
    def run_tests(self, test_cases_file="test_cases.json"):
        """运行测试用例
        
        Args:
            test_cases_file (str): 测试用例文件路径
        """
        print("\n开始运行测试用例...")
        
        # 加载测试用例
        with open(test_cases_file, 'r', encoding='utf-8') as f:
            data = json_module.load(f)
            test_cases = data.get('test_cases', [])
        
        # 运行测试
        results = []
        for test_case in test_cases:
            # 准备测试数据
            method_name = test_case["method"]
            args = test_case["args"]
            kwargs = test_case["kwargs"]
            expected = test_case["expected"]
            
            # 获取方法
            method = getattr(self, method_name)
            
            # 调用方法
            try:
                result = method(*args, **kwargs)
                passed = result == expected
                error = None
            except Exception as e:
                result = None
                passed = False
                error = str(e)
            
            # 记录结果
            test_result = {
                "name": test_case["name"],
                "method": method_name,
                "args": args,
                "kwargs": kwargs,
                "expected": expected,
                "actual": result,
                "passed": passed,
                "error": error
            }
            results.append(test_result)
            
            # 打印测试结果
            print(f"\n测试: {test_result['name']}")
            print(f"方法: {method_name}")
            print(f"参数: args={args}, kwargs={kwargs}")
            print(f"预期: {expected}")
            print(f"实际: {result}")
            print(f"状态: {'通过' if passed else '失败'}")
            if error:
                print(f"错误: {error}")
            print("-" * 40)
        
        # 打印摘要
        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        failed = total - passed
        
        print("\n测试摘要:")
        print(f"总测试数: {total}")
        print(f"通过数: {passed}")
        print(f"失败数: {failed}")
        print(f"通过率: {passed/total*100:.2f}%")

class TestRunner:
    """测试运行器，用于执行测试用例"""
    
    def __init__(self, base_url: str = ServerConfig.get_server_url()):
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
            data = json_module.load(f)
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

    def call_method(self, args_dict: Dict[str, Any]) -> Dict[str, Any]:
        """通用函数调用
        
        Args:
            args_dict (Dict[str, Any]): 函数参数
            
        Returns:
            Dict[str, Any]: 函数结果
        """
        # 准备请求数据
        request_data = {
            "method": args_dict["method"],
            "args": args_dict["args"],
            "kwargs": args_dict["kwargs"]
        }
        
        # 发送请求
        response = requests.post(self.mcp_url, json=request_data)
        result = response.json()
        
        # 检查结果
        success = result["success"]
        actual = result.get("result")

        return {
            "name": args_dict["name"],
            "method": args_dict["method"],
            "args": args_dict["args"],
            "kwargs": args_dict["kwargs"],
            "actual": actual,
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

class PromptWrapper:
    """PromptLoader的包装器类，通过反射机制暴露和调用被包装类的方法"""
    
    def __init__(self, wrapped_class, *args, **kwargs):
        """初始化包装器
        
        Args:
            wrapped_class: 要包装的类
            *args: 传递给被包装类构造函数的参数
            **kwargs: 传递给被包装类构造函数的关键字参数
        """
        self._wrapped_instance = wrapped_class(*args, **kwargs)
        self._expose_methods()
    
    def _expose_methods(self):
        """通过反射暴露被包装类的公共方法"""
        self._public_methods = {}
        # 获取被包装实例的所有方法
        for name, method in inspect.getmembers(self._wrapped_instance, inspect.ismethod):
            # 只暴露公共方法（不以_开头的方法）
            if not name.startswith('_'):
                # 直接将方法添加到公共方法字典中
                self._public_methods[name] = method
                # 同时也添加到实例属性中
                setattr(self, name, method)
    
    def __getattr__(self, name):
        """当访问不存在的属性时，尝试从被包装实例获取"""
        return getattr(self._wrapped_instance, name)
    
    def __setattr__(self, name, value):
        """设置属性时，如果属性名以_开头，则设置到包装器实例，否则设置到被包装实例"""
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            setattr(self._wrapped_instance, name, value)
    
    def setup_routes(self, app):
        """设置 Sanic 路由
        
        Args:
            app: Sanic 应用实例
        """
        # 添加 MCP 路由
        @app.route("/mcp", methods=["POST"])
        async def handle_mcp(request):
            try:
                # 解析 MCP 请求
                data = request.json
                method_name = data.get("method")
                args = data.get("args", [])
                kwargs = data.get("kwargs", {})
                
                # 检查方法是否存在
                if method_name not in self._public_methods:
                    return json({
                        "success": False,
                        "error": f"Method {method_name} not found"
                    })
                
                # 调用方法
                method = self._public_methods[method_name]
                result = method(*args, **kwargs)
                
                # 返回结果
                return json({
                    "success": True,
                    "result": result
                })
                
            except Exception as e:
                return json({
                    "success": False,
                    "error": str(e)
                })
        
        # 添加方法列表路由
        @app.route("/methods", methods=["GET"])
        async def list_methods(request):
            methods_info = []
            for name, method in self._public_methods.items():
                # 获取方法签名
                sig = inspect.signature(method)
                params = []
                for param in sig.parameters.values():
                    param_info = {
                        "name": param.name,
                        "kind": str(param.kind),
                        "default": str(param.default) if param.default != inspect.Parameter.empty else None
                    }
                    params.append(param_info)
                
                methods_info.append({
                    "name": name,
                    "parameters": params,
                    "doc": method.__doc__
                })
            
            return json({
                "success": True,
                "methods": methods_info
            })

    @classmethod
    def run_tests(cls):
        """运行测试用例"""
        print("\n开始运行测试用例...")
        runner = TestRunner()
        test_cases = runner.load_test_cases("test_cases.json")
        results = runner.run_all_tests(test_cases)
        runner.print_summary(results)

    @classmethod
    def start_server(cls, wrapped_class, *args, **kwargs):
        """启动 MCP 服务器
        
        Args:
            wrapped_class: 要包装的类
            *args: 传递给被包装类构造函数的参数
            **kwargs: 传递给被包装类构造函数的关键字参数
        """
        # 创建 Sanic 应用实例
        app = Sanic("PromptWrapperServer")
        
        # 创建包装器实例
        wrapper = cls(wrapped_class, *args, **kwargs)
        
        # 设置路由
        wrapper.setup_routes(app)
        
        # 启动 MCP 服务器
        print("\n启动 MCP 服务器...")
        print(f"服务器地址: {ServerConfig.get_server_url()}")
        print("\n可用的 API 端点:")
        print("1. GET /methods - 获取所有可用方法的信息")
        print("2. POST /mcp - 调用方法")
        print("\nPOST /mcp 请求示例:")
        print('''
        {
            "method": "get_value",
            "args": ["test.vars.var1"],
            "kwargs": {}
        }
        ''')
        
        # 启动服务器
        app.run(host=ServerConfig.HOST, port=ServerConfig.get_port(), single_process=True)

    @classmethod
    def generate_config(cls, test_file: str = "test_cases.json", output_file: str = "config.json", server_url: str = ServerConfig.get_server_url()):
        """读取测试用例文件，提取可调用的函数并生成配置文件
        
        Args:
            test_file (str): 测试用例文件路径
            output_file (str): 输出配置文件路径
            server_url (str): 服务器地址
        """
        print("\n开始生成配置文件...")
        
        try:
            # 读取测试用例文件
            with open(test_file, 'r', encoding='utf-8') as f:
                data = json_module.load(f)
                test_cases = data.get('test_cases', [])
            
            # 提取所有方法名和参数信息
            methods_info = {}
            for test_case in test_cases:
                method = test_case.get("method")
                if method:
                    if method not in methods_info:
                        methods_info[method] = {
                            "args": test_case.get("args", []),
                            "kwargs": test_case.get("kwargs", {}),
                            "description": f"方法 {method} 的测试用例"
                        }
            
            # 创建配置文件内容
            config = {
                "server": {
                    "url": server_url,
                    "mcp_endpoint": f"{server_url}/mcp",
                    "methods_endpoint": f"{server_url}/methods"
                },
                "methods": {
                    method: info for method, info in sorted(methods_info.items())
                },
                "description": "可用的方法列表及其参数信息，从测试用例中提取"
            }
            
            # 写入配置文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json_module.dump(config, f, ensure_ascii=False, indent=4)
            
            print(f"成功生成配置文件: {output_file}")
            print(f"服务器地址: {server_url}")
            print(f"共提取 {len(methods_info)} 个方法")
            print("方法列表及其参数:")
            for method, info in sorted(methods_info.items()):
                print(f"\n方法: {method}")
                print(f"位置参数: {info['args']}")
                print(f"关键字参数: {info['kwargs']}")
                
        except Exception as e:
            print(f"生成配置文件时出错: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PromptWrapper 服务器和测试运行器")
    parser.add_argument("--mode", choices=["server", "test", "generate_config"], default="server",
                      help="运行模式：server（启动服务器）或 test（运行测试）或 generate_config（生成配置文件）")
    parser.add_argument("--test-file", default="test_cases.json",
                      help="测试用例文件路径")
    parser.add_argument("--output-file", default="config.json",
                      help="输出配置文件路径")
    parser.add_argument("--server-url", default=ServerConfig.get_server_url(),
                      help="服务器地址")
    parser.add_argument("--port", type=int, default=ServerConfig.get_port(),
                      help="服务器端口号")
    
    args = parser.parse_args()
    
    # 设置端口
    if args.port != ServerConfig.get_port():
        ServerConfig.set_port(args.port)
    
    if args.mode == "test":
        PromptWrapper.run_tests()
    elif args.mode == "generate_config":
        PromptWrapper.generate_config(args.test_file, args.output_file, ServerConfig.get_server_url())
    else:
        from prompt_loader import PromptLoader
        PromptWrapper.start_server(PromptLoader, "prompt") 
