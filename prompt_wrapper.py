import inspect
from functools import wraps
from sanic import Sanic
from sanic.response import json
import json as json_module
import argparse
from test_runner import TestRunner

# 创建 Sanic 应用实例
app = Sanic("PromptWrapperServer")

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
        self._setup_routes()
    
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
    
    def _setup_routes(self):
        """设置 Sanic 路由"""
        # MCP 路由已经在 _expose_methods 中设置了公共方法
        
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

def run_tests():
    """运行测试用例"""
    print("\n开始运行测试用例...")
    runner = TestRunner()
    test_cases = runner.load_test_cases("test_cases.json")
    results = runner.run_all_tests(test_cases)
    runner.print_summary(results)

def start_server():
    """启动 MCP 服务器"""
    from prompt_loader import PromptLoader
    
    # 创建包装器实例
    wrapper = PromptWrapper(PromptLoader, "prompt")
    
    # 启动 MCP 服务器
    print("\n启动 MCP 服务器...")
    print("服务器地址: http://0.0.0.0:8000")
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
    app.run(host="0.0.0.0", port=8000, single_process=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PromptWrapper 服务器和测试运行器")
    parser.add_argument("--mode", choices=["server", "test"], default="server",
                      help="运行模式：server（启动服务器）或 test（运行测试）")
    
    args = parser.parse_args()
    
    if args.mode == "test":
        run_tests()
    else:
        start_server() 