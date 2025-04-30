# mcpForAny

## 项目简介

本项目旨在实现一个**高效的Prompt/配置文本管理与变量替换系统**，适用于批量管理、复用、嵌套引用大量prompt、配置、文案等文本资源的场景。通过`PromptLoader`类，可以自动遍历指定目录下的所有文件，解析特定格式的键值对，支持变量引用、递归替换、循环检测，并可导出有效/无效项，极大提升Prompt工程化和自动化管理能力。

---

## 目录结构

```
.
├── prompt_loader.py      # 主逻辑代码，核心类PromptLoader
├── prompt/              # 存放所有prompt/配置文件的目录（可自定义）
│   ├── first/
│   │   ├── tt
│   │   └── cc.aa
│   └── test/
│       ├── vars
│       ├── vars.txt
│       ├── bb
│       └── circular
├── README.md            # 项目说明文档
├── output.txt           # 示例输出
├── invalid_output.txt   # 示例无效项输出
├── config.json          # 其他配置
└── method_info.json     # 其他信息
```

---

## 文件格式说明

每个文件可包含多个键值对，格式如下：

```
#key1
value1

#key2
value2，支持变量引用：{{some.path.key1}}
```

- `#key`：键名，必须独占一行，且以#开头。
- `value`：键值，可以为任意文本，支持用`{{变量名}}`引用其他键的值。
- 变量名支持"路径.键名"格式，路径为相对于`prompt`目录的相对路径（用`.`分隔）。

### 示例

**prompt/test/vars**
```
#var1
这是一个测试变量

#var2
引用了var1的值: {{test.vars.var1}}

#var3
引用了不存在的变量: {{nonexist}}
```

**prompt/test/circular**
```
#self_ref
这是一个循环引用测试: {{test.circular.self_ref}}

#mutual_ref1
引用了mutual_ref2: {{test.circular.mutual_ref2}}

#mutual_ref2
引用了mutual_ref1: {{test.circular.mutual_ref1}}
```

---

## 核心功能与逻辑

### 1. 目录遍历与文件解析

- 初始化时递归遍历指定目录（如`prompt`），处理所有文件。
- 每个文件中，按`#key\nvalue`格式提取所有键值对。
- 键名会自动加上相对路径前缀，形成全局唯一key（如`test.vars.var1`）。

### 2. 变量递归替换

- 支持在value中用`{{变量名}}`引用其他键的值，支持多级递归替换。
- 自动检测并记录未定义变量和循环引用，分别存入`invalid_items`。

### 3. 有效/无效项区分

- 替换成功的项存入`valid_items`，有问题的项（如变量未定义或循环引用）存入`invalid_items`。

### 4. 数据导出

- 可将所有有效/无效的键值对导出为文件，格式同输入（`#key\nvalue`）。

### 5. 单项写入与自动刷新

- 支持通过`write_key_value`方法，按key写入/更新指定文件的键值对，并自动重新处理变量替换。

### 6. 查询接口

- 提供`get_value`、`get_all_items`、`get_invalid_items`方法，便于查询和调试。

---

## 典型用法

```python
from prompt_loader import PromptLoader

# 1. 初始化加载
loader = PromptLoader("prompt")

# 2. 查询某个key的值
value = loader.get_value("test.vars.var2")
print(value)  # 输出: 引用了var1的值: 这是一个测试变量

# 3. 写入/更新某个key
loader.write_key_value("test.vars.new_var", "新变量内容 {{test.vars.var1}}")

# 4. 导出所有数据
loader.dump("all_valid.txt", "all_invalid.txt")

# 5. 重新加载其他目录
success = loader.load_directory("other_prompt_dir")
if success:
    print("新目录加载成功")
```

---

## 注意事项

- 文件路径中不能包含`.`字符，否则会报错。
- 变量引用需使用全路径（如`test.vars.var1`），否则可能找不到。
- 支持循环引用和未定义变量检测，相关项会被归为无效项。
- 支持多级目录和多文件管理，适合大规模prompt/配置工程化。

---

## 适用场景

- Prompt工程化、自动化管理、批量生成
- 配置/文案/模板的批量管理与复用
- 需要变量嵌套、递归替换的文本资源管理

---

如需进一步定制或扩展功能，请参考`prompt_loader.py`源码或联系开发者。
