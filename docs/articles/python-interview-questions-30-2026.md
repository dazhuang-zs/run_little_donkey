# Python面试题（30题）- 2026年版

> 适用于：初级（10题）、中级（12题）、高级（8题）
> 每题含答案和解析，覆盖Python核心知识点和高频考点

---

## 初级（1-10题）

### Q1: Python中的list和tuple有什么区别？

**答案：**
- list是可变的（mutable），创建后可以修改、添加、删除元素
- tuple是不可变的（immutable），创建后不能修改
- list用方括号 `[]`，tuple用圆括号 `()`
- tuple比list更轻量，性能稍好

**代码示例：**
```python
# list
my_list = [1, 2, 3]
my_list.append(4)  # ✅ 可以修改
print(my_list)  # [1, 2, 3, 4]

# tuple
my_tuple = (1, 2, 3)
my_tuple.append(4)  # ❌ AttributeError: 'tuple' object has no attribute 'append'
```

**实际应用场景：**
- 用tuple存储不需要修改的数据（如配置项、坐标），更安全且性能更好
- 用list存储需要动态修改的数据（如用户列表、日志）

---

### Q2: Python中的深拷贝和浅拷贝有什么区别？

**答案：**
- **浅拷贝（shallow copy）**：只拷贝对象的第一层，嵌套对象仍是引用
- **深拷贝（deep copy）**：递归拷贝所有层级，原对象和拷贝对象完全独立

**代码示例：**
```python
import copy

original = [[1, 2, 3], [4, 5, 6]]

# 浅拷贝
shallow = copy.copy(original)
shallow[0][0] = 999
print(original)  # [[999, 2, 3], [4, 5, 6]]  ← 原对象被修改了！

# 深拷贝
deep = copy.deepcopy(original)
deep[0][0] = 888
print(original)  # [[999, 2, 3], [4, 5, 6]]  ← 原对象未被修改
```

**实际应用场景：**
- 浅拷贝适合嵌套层级浅或不可变对象的场景
- 深拷贝适合复杂嵌套结构（如多维数组、嵌套dict）

---

### Q3: Python中的*args和**kwargs是什么？

**答案：**
- `*args`：接收任意数量的位置参数，打包成tuple
- `**kwargs`：接收任意数量的关键字参数，打包成dict

**代码示例：**
```python
def demo(*args, **kwargs):
    print(f"args: {args}")
    print(f"kwargs: {kwargs}")

demo(1, 2, 3, name="Alice", age=30)
# 输出：
# args: (1, 2, 3)
# kwargs: {'name': 'Alice', 'age': 30}
```

**实际应用场景：**
- 写装饰器、包装函数时常用
- 继承父类方法时保留灵活性（`super().__init__(*args, **kwargs)`）

---

### Q4: Python中如何管理内存？

**答案：**
- Python使用**引用计数（reference counting）**为主的垃圾回收机制
- 每个对象有一个引用计数器，当计数器归零时，对象被回收
- 循环引用问题由**分代回收（generational GC）**解决
- 使用 `gc` 模块可以手动控制垃圾回收

**代码示例：**
```python
import sys
import gc

a = [1, 2, 3]
print(sys.getrefcount(a))  # 引用计数

# 手动触发垃圾回收
gc.collect()
```

**实际应用场景：**
- 处理大文件、大数据时注意及时释放引用（`del` 或重新赋值为 `None`）
- 避免循环引用（如双向链表、父子对象互相引用）

---

### Q5: Python中的GIL是什么？有什么影响？

**答案：**
- **GIL（Global Interpreter Lock）**：全局解释器锁，同一时刻只有一个线程可以执行Python字节码
- **影响**：CPU密集型任务无法利用多核CPU，多线程反而更慢
- **解决方案**：
  - IO密集型任务：使用 `threading`（IO等待时会释放GIL）
  - CPU密集型任务：使用 `multiprocessing`（多进程，每个进程有独立的GIL）

**实际应用场景：**
- Web爬虫、文件读写等IO密集型任务 → 用多线程
- 数据处理、机器学习训练等CPU密集型任务 → 用多进程

---

### Q6: Python中的装饰器是什么？写一个示例。

**答案：**
- 装饰器是接受函数作为参数并返回新函数的高阶函数
- 用于在不修改原函数代码的情况下添加功能（如日志、计时、权限校验）

**代码示例：**
```python
import time

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} 执行时间: {end - start:.4f}秒")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(1)
    return "完成"

slow_function()  # 输出: slow_function 执行时间: 1.0012秒
```

**实际应用场景：**
- 记录函数执行时间
- Flask/Django的路由装饰器（`@app.route('/')`）
- 权限校验装饰器

---

### Q7: Python中的生成器（generator）是什么？和迭代器有什么区别？

**答案：**
- **生成器**：使用 `yield` 关键字的函数，按需生成值，节省内存
- **迭代器**：实现了 `__iter__()` 和 `__next__()` 方法的对象
- **区别**：生成器是迭代器的一种，但更简洁（不需要手动实现 `__iter__()` 和 `__next__()`）

**代码示例：**
```python
# 生成器函数
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

# 使用
for num in fibonacci(10):
    print(num, end=" ")  # 0 1 1 2 3 5 8 13 21 34
```

**实际应用场景：**
- 处理大文件（逐行读取，而不是一次性读入内存）
- 生成大量数据（如百万级数据集）

---

### Q8: Python中的with语句是什么？如何实现？

**答案：**
- `with` 语句用于资源管理（如文件、数据库连接），确保资源被正确释放
- 实现原理：上下文管理器（实现了 `__enter__()` 和 `__exit__()` 方法）

**代码示例：**
```python
# 传统方式
file = open("test.txt", "r")
try:
    content = file.read()
finally:
    file.close()

# with语句（推荐）
with open("test.txt", "r") as file:
    content = file.read()
# 自动关闭文件，即使发生异常
```

**自定义上下文管理器：**
```python
class MyContext:
    def __enter__(self):
        print("进入上下文")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("退出上下文")
        return False  # 不吞掉异常

with MyContext():
    print("正在处理...")
```

---

### Q9: Python中的lambda函数是什么？有什么限制？

**答案：**
- `lambda` 是匿名函数，用于定义简单的单行函数
- **限制**：
  - 只能写一个表达式，不能包含多条语句
  - 不能包含 `if-elif-else`（但可以用三元表达式 `x if condition else y`）
  - 不能包含 `try-except`、`import` 等语句

**代码示例：**
```python
# 合法
square = lambda x: x ** 2
print(square(5))  # 25

# 不合法（会报SyntaxError）
# lambda x: if x > 0: return x else: return -x

# 可以用三元表达式替代
abs_value = lambda x: x if x > 0 else -x
```

**实际应用场景：**
- 作为高阶函数的参数（如 `sorted()`、`map()`、`filter()`）
- 简单的回调函数

---

### Q10: Python中的is和==有什么区别？

**答案：**
- `==`：比较值是否相等（调用 `__eq__()` 方法）
- `is`：比较身份标识是否相同（即是否是同一个对象，比较 `id()`）

**代码示例：**
```python
a = [1, 2, 3]
b = [1, 2, 3]

print(a == b)  # True（值相等）
print(a is b)  # False（不是同一个对象）

c = a
print(a is c)  # True（c和a指向同一个对象）
```

**特殊情况：**
```python
# 小整数缓存（-5 到 256）
x = 100
y = 100
print(x is y)  # True（同一个对象）

# 大整数不缓存
x = 100000
y = 100000
print(x is y)  # False（不同对象，但值相等）
print(x == y)  # True
```

---

## 中级（11-22题）

### Q11: Python中的元类（metaclass）是什么？

**答案：**
- 元类是"创建类的类"，控制类的创建行为
- 类的定义过程：遇到 `class` 语句时，Python会用元类创建这个类对象
- 默认元类是 `type`

**代码示例：**
```python
# 用元类自动添加方法
class MyMeta(type):
    def __new__(cls, name, bases, attrs):
        # 自动添加一个hello方法
        attrs['hello'] = lambda self: f"Hello from {name}"
        return super().__new__(cls, name, bases, attrs)

class MyClass(metaclass=MyMeta):
    pass

obj = MyClass()
print(obj.hello())  # Hello from MyClass
```

**实际应用场景：**
- ORM框架（如Django ORM）用元类将类属性转换为数据库字段
- 注册模式（自动注册所有子类）

---

### Q12: Python中的描述符（descriptor）是什么？

**答案：**
- 描述符是实现了 `__get__()`、`__set__()` 或 `__delete__()` 方法的对象
- 用于控制属性访问（get、set、delete）

**代码示例：**
```python
class PositiveNumber:
    def __init__(self):
        self.value = 0
    
    def __get__(self, instance, owner):
        return self.value
    
    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError("必须是正数")
        self.value = value

class Product:
    price = PositiveNumber()

p = Product()
p.price = 100  # ✅
p.price = -50  # ❌ ValueError: 必须是正数
```

**实际应用场景：**
- 属性校验（如Django模型的字段验证）
- 计算属性（lazy loading）

---

### Q13: Python中的协程（coroutine）和async/await是什么？

**答案：**
- **协程**：可以暂停和恢复的函数，用于异步编程
- `async def` 定义协程函数，`await` 暂停协程直到等待的操作完成

**代码示例：**
```python
import asyncio

async def fetch_data(url):
    print(f"开始请求 {url}")
    await asyncio.sleep(1)  # 模拟IO等待
    print(f"完成请求 {url}")
    return f"数据来自 {url}"

async def main():
    # 并发执行
    results = await asyncio.gather(
        fetch_data("https://api.example.com/1"),
        fetch_data("https://api.example.com/2"),
        fetch_data("https://api.example.com/3")
    )
    print(results)

asyncio.run(main())
```

**实际应用场景：**
- 高并发网络请求（如爬虫、API调用）
- 异步Web框架（如FastAPI、aiohttp）

---

### Q14: Python中的多线程和多进程如何选择？

**答案：**
- **多线程（`threading`）**：
  - 适合IO密集型任务（网络请求、文件读写）
  - 受GIL限制，CPU密集型任务无法并行
- **多进程（`multiprocessing`）**：
  - 适合CPU密集型任务（数据处理、计算）
  - 每个进程独立GIL，可以真正并行

**代码示例：**
```python
import concurrent.futures
import time

# IO密集型任务 → 用多线程
def fetch_url(url):
    time.sleep(1)  # 模拟网络请求
    return f"数据来自 {url}"

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(fetch_url, [
        "https://api.example.com/1",
        "https://api.example.com/2",
        "https://api.example.com/3"
    ]))
```

---

### Q15: Python中的__init__()和__new__()有什么区别？

**答案：**
- `__new__()`：静态方法，创建对象时调用，返回实例
- `__init__()`：实例方法，初始化对象时调用，不返回任何值
- 执行顺序：先 `__new__()` 创建对象，再 `__init__()` 初始化

**代码示例：**
```python
class Singleton:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, value):
        self.value = value

a = Singleton(10)
b = Singleton(20)
print(a is b)  # True（同一个对象）
print(a.value)  # 20（后初始化的会覆盖）
```

**实际应用场景：**
- 单例模式
- 不可变对象的创建（如自定义tuple）

---

### Q16: Python中的@property装饰器是什么？

**答案：**
- `@property` 将方法转换为属性访问
- 用于实现getter、setter、deleter，控制属性访问

**代码示例：**
```python
class Temperature:
    def __init__(self, celsius):
        self._celsius = celsius
    
    @property
    def fahrenheit(self):
        return self._celsius * 9/5 + 32
    
    @fahrenheit.setter
    def fahrenheit(self, value):
        self._celsius = (value - 32) * 5/9

temp = Temperature(25)
print(temp.fahrenheit)  # 77.0（像属性一样访问）
temp.fahrenheit = 100
print(temp._celsius)  # 37.777...
```

**实际应用场景：**
- 将方法伪装成属性，更直观
- 属性校验和转换

---

### Q17: Python中的闭包（closure）是什么？

**答案：**
- 闭包是内层函数引用了外层函数的变量，即使外层函数已执行完毕，内层函数仍能访问那些变量

**代码示例：**
```python
def outer(x):
    def inner(y):
        return x + y  # 引用了外层函数的x
    return inner

add_10 = outer(10)
print(add_10(5))  # 15
print(add_10(20))  # 30
```

**实际应用场景：**
- 工厂函数（动态生成函数）
- 装饰器的实现基础

---

### Q18: Python中的模块和包有什么区别？

**答案：**
- **模块（module）**：单个 `.py` 文件
- **包（package）**：包含多个模块的目录，必须包含 `__init__.py` 文件（Python 3.3+可选，但建议保留）

**代码示例：**
```
my_package/
    __init__.py
    module1.py
    module2.py
    subpackage/
        __init__.py
        module3.py
```

**导入方式：**
```python
import my_package.module1
from my_package import module2
from my_package.subpackage import module3
```

**实际应用场景：**
- 组织大型项目代码
- 避免命名冲突

---

### Q19: Python中的异常处理最佳实践？

**答案：**
- 只捕获预期的异常，不要用 `except Exception:` 捕获所有异常
- 异常处理的粒度要小，不要包裹大段代码
- 使用 `finally` 确保资源释放
- 自定义异常类提供更清晰的错误信息

**代码示例：**
```python
class InsufficientFundsError(Exception):
    pass

def withdraw(balance, amount):
    if amount > balance:
        raise InsufficientFundsError("余额不足")
    return balance - amount

try:
    result = withdraw(100, 150)
except InsufficientFundsError as e:
    print(f"错误: {e}")
finally:
    print("交易结束")
```

---

### Q20: Python中的列表推导式和生成器表达式有什么区别？

**答案：**
- **列表推导式**：`[x for x in iterable]`，立即生成完整列表，占用内存
- **生成器表达式**：`(x for x in iterable)`，按需生成，节省内存

**代码示例：**
```python
# 列表推导式
squares_list = [x**2 for x in range(1000000)]  # 立即生成100万个元素

# 生成器表达式
squares_gen = (x**2 for x in range(1000000))  # 不占内存，按需生成
print(next(squares_gen))  # 0
print(next(squares_gen))  # 1
```

**实际应用场景：**
- 数据量大时用生成器表达式
- 需要多次遍历时用列表推导式

---

### Q21: Python中的__slots__是什么？有什么作用？

**答案：**
- `__slots__` 限制类可以拥有的属性，节省内存
- 使用 `__slots__` 后，类实例不能有动态属性

**代码示例：**
```python
class PersonWithSlots:
    __slots__ = ('name', 'age')
    
    def __init__(self, name, age):
        self.name = name
        self.age = age

p = PersonWithSlots("Alice", 30)
p.city = "Beijing"  # ❌ AttributeError: 'PersonWithSlots' object has no attribute 'city'
```

**实际应用场景：**
- 创建大量实例时（如百万级对象），用 `__slots__` 可显著减少内存占用

---

### Q22: Python中的pickle模块安全吗？

**答案：**
- **不安全**。`pickle` 可以执行任意代码，不要反序列化不可信的数据
- 安全的替代方案：`json`、`marshal`（有限场景）、`joblib`（针对numpy数据）

**危险示例：**
```python
import pickle

# 恶意代码
class Malicious:
    def __reduce__(self):
        import os
        return (os.system, ('echo hacked',))

# 反序列化时会执行恶意代码
pickle.loads(pickle.dumps(Malicious()))  # 输出: hacked
```

**安全建议：**
- 只反序列化来自可信源的数据
- 使用 `json` 替代（如果数据结构允许）

---

## 高级（23-30题）

### Q23: Python中的 asyncio 底层实现原理是什么？

**答案：**
- `asyncio` 基于事件循环（event loop）
- 使用 `yield from`（Python 3.4）或 `await`（Python 3.5+）暂停协程
- 事件循环负责调度协程的执行

**简化实现：**
```python
# 简化版事件循环
class SimpleEventLoop:
    def __init__(self):
        self.tasks = []
    
    def add_task(self, task):
        self.tasks.append(task)
    
    def run(self):
        while self.tasks:
            task = self.tasks.pop(0)
            try:
                next(task)
                self.tasks.append(task)  # 如果没结束，继续排队
            except StopIteration:
                pass

loop = SimpleEventLoop()
loop.add_task(fetch_data("url1"))
loop.add_task(fetch_data("url2"))
loop.run()
```

---

### Q24: Python中的GIL能被移除吗？为什么？

**答案：**
- **很难移除**。GIL保护了CPython的内存管理（引用计数）不被并发访问破坏
- 移除GIL需要重写内存管理，会牺牲单线程性能
- Python 3.13+正在尝试移除GIL（实验性，默认关闭）

**现状：**
- 多进程可以绕过GIL
- 使用其他Python实现（如PyPy、IronPython）没有GIL

---

### Q25: Python中的内存泄漏如何排查？

**答案：**
- 使用 `objgraph` 查看对象引用关系
- 使用 `tracemalloc` 追踪内存分配
- 使用 `gc.get_objects()` 查看所有存活对象

**代码示例：**
```python
import tracemalloc

tracemalloc.start()

# 执行可疑代码
leak_list = []
for i in range(100000):
    leak_list.append(object())

current, peak = tracemalloc.get_traced_memory()
print(f"当前内存: {current / 1024 / 1024:.2f} MB")
print(f"峰值内存: {peak / 1024 / 1024:.2f} MB")

tracemalloc.stop()
```

---

### Q26: Python中的C扩展如何编写？

**答案：**
- 使用 `ctypes` 调用C动态库
- 使用 `cffi` 调用C代码
- 编写C扩展模块（复杂，需要了解Python C API）

**简单示例（ctypes）：**
```c
// mylib.c
int add(int a, int b) {
    return a + b;
}
```

```python
# test.py
import ctypes

lib = ctypes.CDLL("./mylib.so")
print(lib.add(10, 20))  # 30
```

---

### Q27: Python中的类型注解（Type Hints）有什么用？

**答案：**
- 提高代码可读性
- 支持静态类型检查（如 `mypy`）
- IDE可以提供更好的自动补全和错误提示

**代码示例：**
```python
def greet(name: str, age: int) -> str:
    return f"Hello {name}, you are {age} years old"

# mypy会报错
greet("Alice", "30")  # Argument 2 to "greet" has incompatible type "str"; expected "int"
```

**实际应用场景：**
- 大型项目维护
- 团队协作

---

### Q28: Python中的__import__()和importlib有什么不同？

**答案：**
- `__import__()` 是内置函数，动态导入模块（不推荐直接使用）
- `importlib` 是标准库模块，提供更灵活的导入功能

**代码示例：**
```python
import importlib

# 动态导入
module_name = "json"
module = importlib.import_module(module_name)
print(module.dumps({"key": "value"}))
```

**实际应用场景：**
- 插件系统
- 动态加载模块

---

### Q29: Python中的coroutine和generator有什么区别？

**答案：**
- **generator**：使用 `yield`，单向输出数据（ producer）
- **coroutine**：使用 `yield` 或 `await`，可以接收和发送数据（producer + consumer）

**代码示例：**
```python
# generator（只能输出）
def gen():
    yield 1
    yield 2

# coroutine（可以接收和发送）
def coro():
    while True:
        x = yield
        print(f"收到: {x}")

c = coro()
next(c)  # 启动coroutine
c.send(10)  # 收到: 10
c.send(20)  # 收到: 20
```

---

### Q30: Python性能优化有哪些常用方法？

**答案：**
1. 使用内置函数（`map`、`filter`、`sum` 等，用C实现，更快）
2. 使用 `numpy` 处理数值计算
3. 使用 `__slots__` 减少内存占用
4. 使用生成器处理大数据
5. 使用 `lru_cache` 缓存计算结果
6. 使用多进程绕过GIL

**代码示例：**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(100))  # 快速计算，有缓存
```

---

## 总结

| 级别 | 题号 | 核心知识点 |
|------|------|-----------|
| 初级 | 1-10 | 基础语法、数据结构、常用内置功能 |
| 中级 | 11-22 | 面向对象、异步编程、高级特性 |
| 高级 | 23-30 | 底层原理、性能优化、扩展开发 |

**下一步：**
- 刷题时重点关注实际应用场景
- 结合项目经验理解每个知识点
- 准备1-2个能深入讲解的知识点（如GIL、asyncio、装饰器）

---

**文件版本：** 2026-05-13  
**作者：** 智能行程规划器项目  
**许可：** MIT License
