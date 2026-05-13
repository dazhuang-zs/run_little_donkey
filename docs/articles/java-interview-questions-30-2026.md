# Java面试题（30题）- 2026年版

> 适用于：初级（10题）、中级（12题）、高级（8题）
> 每题含答案和解析，覆盖Java核心知识点和高频考点

---

## 初级（1-10题）

### Q1: Java中的==和equals()有什么区别？

**答案：**
- `==`：比较基本类型的值或引用类型的地址
- `equals()`：比较对象的内容（需重写，否则等价于`==`）

**代码示例：**
```java
String s1 = new String("hello");
String s2 = new String("hello");

System.out.println(s1 == s2);      // false（不同对象）
System.out.println(s1.equals(s2)); // true（内容相同）

String s3 = "hello";
String s4 = "hello";
System.out.println(s3 == s4);      // true（字符串常量池）
```

**实际应用场景：**
- 比较字符串用`equals()`，不要用`==`
- 自定义类要重写`equals()`和`hashCode()`

---

### Q2: Java中的String、StringBuffer、StringBuilder有什么区别？

**答案：**
| 类 | 可变性 | 线程安全 | 性能 |
|----|--------|----------|------|
| String | 不可变 | 安全 | 低（每次修改创建新对象） |
| StringBuffer | 可变 | 安全（synchronized） | 中 |
| StringBuilder | 可变 | 不安全 | 高 |

**代码示例：**
```java
// String（不可变）
String s = "hello";
s = s + " world";  // 创建新对象

// StringBuilder（推荐，单线程）
StringBuilder sb = new StringBuilder("hello");
sb.append(" world");  // 修改原对象
System.out.println(sb.toString());  // hello world

// StringBuffer（多线程）
StringBuffer sbf = new StringBuffer("hello");
sbf.append(" world");
```

**实际应用场景：**
- 单线程字符串拼接 → `StringBuilder`
- 多线程字符串拼接 → `StringBuffer`
- 字符串常量 → `String`

---

### Q3: Java中的ArrayList和LinkedList有什么区别？

**答案：**
| 特性 | ArrayList | LinkedList |
|------|-----------|------------|
| 底层结构 | 动态数组 | 双向链表 |
| 访问元素 | O(1) | O(n) |
| 插入/删除 | O(n)（需移动元素） | O(1)（已知位置） |
| 内存占用 | 小（只存数据） | 大（存前后节点指针） |

**代码示例：**
```java
List<String> arrayList = new ArrayList<>();
arrayList.add("A");  // 快
String a = arrayList.get(0);  // 快 O(1)

List<String> linkedList = new LinkedList<>();
linkedList.add("A");  // 快
String b = linkedList.get(0);  // 慢 O(n)
```

**实际应用场景：**
- 频繁访问 → `ArrayList`
- 频繁插入/删除 → `LinkedList`

---

### Q4: Java中的HashMap底层原理是什么？

**答案：**
- JDK 1.8之前：数组 + 链表
- JDK 1.8及之后：数组 + 链表 + 红黑树（链表长度>8时转红黑树）
- 哈希冲突解决：链地址法

**核心参数：**
- 初始容量：16
- 加载因子：0.75
- 扩容：容量翻倍

**代码示例：**
```java
HashMap<String, Integer> map = new HashMap<>();
map.put("key1", 100);
map.put("key2", 200);

// 遍历
for (Map.Entry<String, Integer> entry : map.entrySet()) {
    System.out.println(entry.getKey() + ": " + entry.getValue());
}
```

**实际应用场景：**
- 需要快速查找 → `HashMap`
- 需要有序 → `LinkedHashMap` 或 `TreeMap`

---

### Q5: Java中的异常处理机制是什么？

**答案：**
- **检查异常（Checked Exception）**：必须捕获或声明抛出（`IOException`、`SQLException`）
- **运行时异常（RuntimeException）**：可以不处理（`NullPointerException`、`IndexOutOfBoundsException`）
- **finally块**：无论是否异常都会执行（除非`System.exit()`）

**代码示例：**
```java
try {
    FileInputStream fis = new FileInputStream("file.txt");
} catch (FileNotFoundException e) {
    System.out.println("文件未找到");
} finally {
    System.out.println("资源释放");
}
```

**实际应用场景：**
- 不要捕获`Exception`（太宽泛）
- 资源关闭用`try-with-resources`（Java 7+）

---

### Q6: Java中的接口和抽象类有什么区别？

**答案：**
| 特性 | 接口（Interface） | 抽象类（Abstract Class） |
|------|-------------------|--------------------------|
| 方法 | 抽象方法（Java 8+可有default方法） | 抽象方法 + 具体方法 |
| 变量 | public static final（常量） | 普通变量 |
| 继承 | 可多实现 | 单继承 |
| 构造函数 | 无 | 有 |

**代码示例：**
```java
// 接口
interface Animal {
    void eat();  // 抽象方法
    default void sleep() {  // default方法（Java 8+）
        System.out.println("睡觉");
    }
}

// 抽象类
abstract class AbstractAnimal {
    abstract void eat();
    void run() {  // 具体方法
        System.out.println("跑");
    }
}
```

**实际应用场景：**
- 定义规范 → 接口
- 代码复用 → 抽象类

---

### Q7: Java中的==和equals()和hashCode()的关系？

**答案：**
- 如果`equals()`相等，则`hashCode()`必须相等
- 如果`hashCode()`相等，则`equals()`不一定相等（哈希冲突）
- 重写`equals()`必须重写`hashCode()`

**代码示例：**
```java
class Person {
    String name;
    Person(String name) { this.name = name; }
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Person person = (Person) o;
        return Objects.equals(name, person.name);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(name);
    }
}
```

**实际应用场景：**
- 将对象作为HashMap的key时必须重写`equals()`和`hashCode()`

---

### Q8: Java中的final关键字有哪些用法？

**答案：**
- **final变量**：不可重新赋值（常量）
- **final方法**：不可重写
- **final类**：不可继承（如`String`）
- **final参数**：不可修改（匿名内部类访问局部变量需用final）

**代码示例：**
```java
final class FinalClass {}  // 不可继承

class Parent {
    final void method() {}  // 不可重写
}

// final变量
final int MAX_SIZE = 100;  // 常量
```

**实际应用场景：**
- 创建不可变类（如`String`）
- 防止方法被重写

---

### Q9: Java中的static关键字有哪些用法？

**答案：**
- **static变量**：类变量，所有实例共享
- **static方法**：类方法，可直接通过类名调用（不能访问非static成员）
- **static代码块**：类加载时执行，只执行一次
- **static内部类**：不依赖外部类实例

**代码示例：**
```java
class Counter {
    static int count = 0;  // static变量
    
    Counter() {
        count++;  // 所有实例共享
    }
    
    static void printCount() {  // static方法
        System.out.println(count);
    }
    
    static {  // static代码块
        System.out.println("类加载时执行");
    }
}
```

**实际应用场景：**
- 工具类（`Math.sqrt()`）
- 单例模式

---

### Q10: Java中的try-with-resources是什么？

**答案：**
- Java 7引入，自动关闭实现了`AutoCloseable`接口的资源
- 无需显式写`finally`块关闭资源

**代码示例：**
```java
// 传统方式
FileInputStream fis = null;
try {
    fis = new FileInputStream("file.txt");
} catch (IOException e) {
    e.printStackTrace();
} finally {
    if (fis != null) {
        try {
            fis.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}

// try-with-resources（推荐）
try (FileInputStream fis = new FileInputStream("file.txt");
     BufferedReader br = new BufferedReader(new InputStreamReader(fis))) {
    String line = br.readLine();
} catch (IOException e) {
    e.printStackTrace();
}
```

**实际应用场景：**
- 文件IO、数据库连接、网络连接等资源管理

---

## 中级（11-22题）

### Q11: Java中的volatile关键字是什么？

**答案：**
- 保证可见性（一个线程修改，其他线程立即看到）
- 禁止指令重排
- **不保证原子性**

**代码示例：**
```java
class Flag {
    volatile boolean running = true;  // 可见性
    
    void stop() {
        running = false;  // 其他线程立即看到
    }
}
```

**实际应用场景：**
- 状态标志（如停止线程）
- 双重检查锁的单例模式

---

### Q12: Java中的synchronized和Lock有什么区别？

**答案：**
| 特性 | synchronized | Lock（如ReentrantLock） |
|------|--------------|-------------------------|
| 锁获取 | 自动获取和释放 | 手动`lock()`和`unlock()` |
| 中断响应 | 不支持 | 支持（`lockInterruptibly()`） |
| 尝试获取锁 | 不支持 | 支持（`tryLock()`） |
| 公平性 | 非公平 | 可选公平/非公平 |
| 性能 | JDK 6+优化后差不多 | 灵活但代码复杂 |

**代码示例：**
```java
// synchronized
synchronized (obj) {
    // 临界区
}

// ReentrantLock
Lock lock = new ReentrantLock();
lock.lock();
try {
    // 临界区
} finally {
    lock.unlock();
}
```

**实际应用场景：**
- 简单场景 → `synchronized`
- 需要高级功能（中断、超时） → `ReentrantLock`

---

### Q13: Java中的线程池原理是什么？

**答案：**
- 核心参数：
  - `corePoolSize`：核心线程数
  - `maximumPoolSize`：最大线程数
  - `keepAliveTime`：空闲线程存活时间
  - `workQueue`：任务队列
- 执行流程：
  1. 核心线程未满 → 创建核心线程执行
  2. 核心线程已满 → 任务进入队列
  3. 队列已满 → 创建非核心线程执行
  4. 线程数达到最大值且队列满 → 执行拒绝策略

**代码示例：**
```java
ThreadPoolExecutor executor = new ThreadPoolExecutor(
    5,                      // corePoolSize
    10,                     // maximumPoolSize
    60L, TimeUnit.SECONDS,  // keepAliveTime
    new LinkedBlockingQueue<>(100)  // workQueue
);

executor.execute(() -> System.out.println("任务执行"));
```

**实际应用场景：**
- 高并发任务执行
- 控制资源消耗

---

### Q14: Java中的ThreadLocal是什么？

**答案：**
- 线程本地变量，每个线程有独立的副本
- 避免线程安全问题

**代码示例：**
```java
ThreadLocal<Integer> threadLocal = ThreadLocal.withInitial(() -> 0);

threadLocal.set(100);  // 当前线程设置值
System.out.println(threadLocal.get());  // 100

// 其他线程看不到这个值
new Thread(() -> {
    System.out.println(threadLocal.get());  // 0（初始值）
}).start();
```

**实际应用场景：**
- 数据库连接管理（每个线程独立连接）
- 日期格式化（`SimpleDateFormat`线程不安全）

---

### Q15: Java中的反射机制是什么？

**答案：**
- 运行时动态获取类信息、调用方法、修改字段
- 核心类：`Class`、`Method`、`Field`、`Constructor`

**代码示例：**
```java
Class<?> clazz = Class.forName("com.example.Person");
Object obj = clazz.newInstance();  // 创建实例

Method method = clazz.getMethod("setName", String.class);
method.invoke(obj, "Alice");  // 调用方法

Field field = clazz.getDeclaredField("name");
field.setAccessible(true);  // 访问私有字段
field.set(obj, "Bob");
```

**实际应用场景：**
- 框架开发（Spring IOC、MyBatis）
- 注解处理

---

### Q16: Java中的注解（Annotation）是什么？

**答案：**
- 元数据，用于修饰代码元素
- 生命周期：`@Retention`（SOURCE、CLASS、RUNTIME）
- 作用目标：`@Target`（TYPE、METHOD、FIELD等）

**代码示例：**
```java
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
@interface MyAnnotation {
    String value();
}

class Test {
    @MyAnnotation("hello")
    void method() {}
}

// 反射读取注解
Method method = Test.class.getMethod("method");
MyAnnotation anno = method.getAnnotation(MyAnnotation.class);
System.out.println(anno.value());  // hello
```

**实际应用场景：**
- Spring的`@Autowired`、`@RequestMapping`
- 单元测试的`@Test`

---

### Q17: Java中的泛型（Generics）是什么？

**答案：**
- 编译时类型检查，避免强制类型转换
- **类型擦除**：运行时泛型信息被擦除（兼容旧版本）

**代码示例：**
```java
List<String> list = new ArrayList<>();
list.add("hello");
String s = list.get(0);  // 无需强制类型转换

// 泛型方法
static <T> T getFirst(List<T> list) {
    return list.get(0);
}
```

**实际应用场景：**
- 集合框架
- 通用工具类

---

### Q18: Java中的IO和NIO有什么区别？

**答案：**
| 特性 | IO | NIO |
|------|----|----|
| 面向 | 流（Stream） | 缓冲区（Buffer） |
| 阻塞 | 阻塞 | 非阻塞 |
| 选择器 | 无 | 有（Selector） |
| 性能 | 低 | 高（高并发） |

**代码示例：**
```java
// NIO读取文件
Path path = Paths.get("file.txt");
try (SeekableByteChannel channel = Files.newByteChannel(path)) {
    ByteBuffer buffer = ByteBuffer.allocate(1024);
    channel.read(buffer);
}
```

**实际应用场景：**
- 高并发网络编程 → NIO（Netty）
- 简单文件操作 → IO

---

### Q19: Java中的序列化和反序列化是什么？

**答案：**
- 序列化：对象 → 字节序列
- 反序列化：字节序列 → 对象
- 实现`Serializable`接口（标记接口）

**代码示例：**
```java
class Person implements Serializable {
    private static final long serialVersionUID = 1L;
    String name;
    transient int age;  // transient字段不序列化
}

// 序列化
ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream("person.obj"));
oos.writeObject(new Person("Alice", 30));

// 反序列化
ObjectInputStream ois = new ObjectInputStream(new FileInputStream("person.obj"));
Person p = (Person) ois.readObject();
```

**实际应用场景：**
- 网络传输对象
- 对象持久化

---

### Q20: Java中的JVM内存模型是什么？

**答案：**
- **堆（Heap）**：存放对象实例（垃圾回收主要区域）
- **方法区（Method Area）**：存放类信息、常量、静态变量
- **虚拟机栈（VM Stack）**：存放局部变量表、操作数栈
- **本地方法栈（Native Method Stack）**：Native方法
- **程序计数器（PC Register）**：当前线程执行的字节码行号

**实际应用场景：**
- 内存泄漏排查（堆转储分析）
- JVM调优（`-Xms`、`-Xmx`）

---

### Q21: Java中的垃圾回收机制是什么？

**答案：**
- **判断对象可回收**：引用计数（循环引用问题）、可达性分析（GC Roots）
- **垃圾回收算法**：
  - 标记-清除（Mark-Sweep）
  - 复制（Copying）
  - 标记-整理（Mark-Compact）
  - 分代收集（Generational Collection）
- **垃圾回收器**：
  - 新生代：Serial、ParNew、Parallel Scavenge
  - 老年代：Serial Old、Parallel Old、CMS
  - 整堆：G1、ZGC、Shenandoah

**实际应用场景：**
- JVM调优选择垃圾回收器
- 分析GC日志

---

### Q22: Java中的Spring IOC和AOP是什么？

**答案：**
- **IOC（控制反转）**：对象创建和依赖注入由Spring容器管理
- **AOP（面向切面编程）**：在不修改代码的情况下增强功能（如日志、事务）

**代码示例：**
```java
// IOC
@Component
class Service {
    @Autowired
    private Repository repo;  // 依赖注入
}

// AOP
@Aspect
@Component
class LogAspect {
    @Before("execution(* com.example.*.*(..))")
    public void log() {
        System.out.println("方法执行前");
    }
}
```

**实际应用场景：**
- 企业级应用开发
- 事务管理、日志记录

---

## 高级（23-30题）

### Q23: Java中的JMM（Java内存模型）是什么？

**答案：**
- 定义多线程读写共享变量的规范
- 保证**原子性、可见性、有序性**
- **happens-before原则**：
  - 程序顺序规则
  - volatile规则
  - synchronized规则
  - 线程启动、终止规则

**实际应用场景：**
- 并发编程正确性保证
- 理解`volatile`、`synchronized`的底层原理

---

### Q24: Java中的CAS（Compare-And-Swap）是什么？

**答案：**
- 乐观锁，比较并交换
- 底层依赖CPU原子指令（如`cmpxchg`）
- **ABA问题**：用版本号解决（`AtomicStampedReference`）

**代码示例：**
```java
AtomicInteger atomicInt = new AtomicInteger(0);
boolean success = atomicInt.compareAndSet(0, 1);  // 期望值是0，更新为1
```

**实际应用场景：**
- 并发容器（`ConcurrentHashMap`）
- 原子类（`AtomicInteger`、`AtomicLong`）

---

### Q25: Java中的线程状态有哪些？

**答案：**
- **NEW**：创建未启动
- **RUNNABLE**：就绪或运行中
- **BLOCKED**：等待获取锁
- **WAITING**：无限等待（如`wait()`、`join()`）
- **TIMED_WAITING**：限时等待（如`sleep(timeout)`）
- **TERMINATED**：终止

**实际应用场景：**
- 线程dump分析
- 死锁排查

---

### Q26: Java中的死锁如何排查和解决？

**答案：**
- **产生条件**：互斥、占有且等待、不可抢占、循环等待
- **排查**：`jstack`查看线程堆栈
- **解决**：
  - 按顺序获取锁
  - 使用`tryLock(timeout)`
  - 银行家算法（避免循环等待）

**代码示例：**
```java
// 死锁示例
Thread t1 = new Thread(() -> {
    synchronized (lockA) {
        synchronized (lockB) { }
    }
});

Thread t2 = new Thread(() -> {
    synchronized (lockB) {
        synchronized (lockA) { }
    }
});
```

**实际应用场景：**
- 数据库死锁
- 多线程资源竞争

---

### Q27: Java中的Spring Boot自动配置原理是什么？

**答案：**
- `@EnableAutoConfiguration` + `spring.factories`（Spring Boot 2.x）或`META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`（Spring Boot 3.x）
- 条件注解：`@ConditionalOnClass`、`@ConditionalOnMissingBean`等

**实际应用场景：**
- 自定义Starter
- 理解Spring Boot约定大于配置

---

### Q28: Java中的MySQL索引优化有哪些技巧？

**答案：**
- **索引类型**：B+树索引、哈希索引、全文索引
- **优化技巧**：
  - 最左前缀原则
  - 避免索引失效（函数、类型转换、like '%xxx'）
  - 覆盖索引
  - 索引下推（Index Condition Pushdown）
- **EXPLAIN分析**：`type`（ALL、range、ref、eq_ref、const）、`key`、`rows`

**实际应用场景：**
- SQL慢查询优化
- 数据库设计

---

### Q29: Java中的分布式锁实现方案有哪些？

**答案：**
- **数据库**：唯一索引（性能低）
- **Redis**：`SET key value NX EX`（Redisson）
- **ZooKeeper**：临时顺序节点
- **Etcd**：租约机制

**代码示例（Redis）：**
```java
// Redisson
RLock lock = redisson.getLock("lock");
lock.lock();
try {
    // 临界区
} finally {
    lock.unlock();
}
```

**实际应用场景：**
- 分布式系统幂等性
- 秒杀系统

---

### Q30: Java中的微服务架构有哪些组件？

**答案：**
- **服务注册与发现**：Eureka、Nacos、Consul
- **负载均衡**：Ribbon、LoadBalancer
- **服务调用**：Feign、RestTemplate、WebClient
- **熔断降级**：Hystrix、Sentinel、Resilience4j
- **网关**：Zuul、Gateway
- **配置中心**：Config、Nacos、Apollo
- **链路追踪**：Sleuth、Zipkin、SkyWalking

**实际应用场景：**
- 大型分布式系统架构设计

---

## 总结

| 级别 | 题号 | 核心知识点 |
|------|------|-----------|
| 初级 | 1-10 | 基础语法、集合框架、异常处理 |
| 中级 | 11-22 | 多线程、反射、IO/NIO、JVM |
| 高级 | 23-30 | 并发原理、分布式、微服务 |

**下一步：**
- 结合项目经验理解每个知识点
- 重点掌握高并发、JVM调优、微服务架构

---

**文件版本：** 2026-05-13  
**作者：** 智能行程规划器项目  
**许可：** MIT License
