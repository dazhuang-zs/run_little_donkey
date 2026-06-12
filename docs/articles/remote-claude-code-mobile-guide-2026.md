# 手机远程控制Mac上的Claude Code开发：完整实战指南

你有没有想过，在地铁上、咖啡馆里，甚至躺在床上，都能用手机写代码？

不是那种"远程桌面"的卡顿体验，而是**原生的终端操作**，流畅、稳定、随时随地。

这篇文章教你用手机SSH连接Mac，在tmux会话里跑Claude Code CLI，实现真正的移动开发。

---

## 一、方案架构：为什么是这套组合

### 核心三件套

| 组件 | 作用 | 为什么选它 |
|------|------|-----------|
| **Tailscale** | 内网穿透 | 无需公网IP，点对点直连，延迟低 |
| **SSH + tmux** | 远程终端 + 会话保持 | 断网不丢进度，多窗口并行 |
| **Claude Code CLI** | AI编程助手 | 原生终端体验，直接改代码 |

### 方案优势

- **无需公网IP**：Tailscale构建虚拟局域网，Mac在内网也能连
- **断线不丢会话**：tmux保护你的Claude Code会话，网络波动不受影响
- **手机原生体验**：Termius提供真正的终端，不是远程桌面的镜像
- **安全可控**：Tailscale的ACL权限控制，SSH密钥认证

---

## 二、第一步：Tailscale组网（安全配置）

### 2.1 安装Tailscale

**Mac端**

```bash
# 方式一：Homebrew安装
brew install tailscale

# 方式二：官网下载pkg安装包
# https://tailscale.com/download
```

**手机端**

- iOS：App Store搜索"Tailscale"
- Android：Google Play或官网下载APK

### 2.2 注册与登录

1. 打开Tailscale，选择登录方式（Google/GitHub/Microsoft/邮箱）
2. 同一账号在Mac和手机上都登录
3. 设备会自动出现在同一网络中

### 2.3 安全配置（关键步骤）

Tailscale默认配置已经比较安全，但建议进一步加固：

**关闭高风险功能**

在Mac的Tailscale设置中：

- **关闭"Use exit node"**：不要让其他设备通过你的Mac上网
- **关闭"Route local network"**：不要暴露本地网络
- 如果不使用子网路由，确保**Subnet router**未启用

**开启MFA两步验证**

1. 登录Tailscale管理后台：https://login.tailscale.com
2. 进入Settings → Security
3. 启用"Two-factor authentication"

**配置最小权限ACL**

在管理后台的ACL编辑器中：

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["tag:mobile"],
      "dst": ["tag:mac:22"]
    }
  ],
  "tagOwners": {
    "tag:mobile": ["autogroup:member"],
    "tag:mac": ["你的邮箱"]
  }
}
```

这段配置的含义：
- 只允许带`tag:mobile`标签的设备连接带`tag:mac`标签设备的22端口（SSH端口）
- 其他端口全部拒绝

**定期清理设备**

在管理后台的Machines列表中：
- 移除不再使用的设备
- 检查是否有异常连接

### 2.4 验证组网成功

在Mac终端查看Tailscale状态：

```bash
tailscale status
```

输出示例：

```
100.64.0.1   macbook-pro      your-email@  macOS -
100.64.0.2   iphone-15        your-email@  iOS   -
```

看到两个设备都在列表中，且IP地址在同一网段（100.64.x.x），说明组网成功。

---

## 三、第二步：Mac开启SSH服务

### 3.1 通过系统设置开启（推荐）

**macOS Ventura及以上**

1. 点击屏幕左上角苹果图标 → **系统设置**
2. 左侧边栏 → **通用** → **共享**
3. 在服务列表中找到**远程登录**
4. 将开关切换为**开启**
5. 右侧显示"已允许访问"，可选择"所有用户"或指定用户

**macOS Monterey及以下**

1. 点击苹果图标 → **系统偏好设置**
2. 点击**共享**图标
3. 勾选**远程登录**
4. 右侧设置允许访问的用户

### 3.2 通过终端命令开启

如果你更喜欢命令行：

```bash
# 检查SSH当前状态
sudo systemsetup -getremotelogin

# 开启SSH
sudo systemsetup -setremotelogin on

# 再次验证
sudo systemsetup -getremotelogin
# 输出: Remote Login: On
```

### 3.3 配置防火墙

如果Mac开启了防火墙，需确保SSH端口放行：

**系统设置 → 隐私与安全性 → 防火墙 → 选项**

确保列表中有"远程登录（SSH）"，状态为"允许传入连接"。

如果没有，点击"+"号添加。

### 3.4 验证SSH服务

```bash
# 检查sshd进程是否运行
ps aux | grep sshd

# 检查22端口是否监听
lsof -i :22

# 本地自测SSH连接
ssh localhost
# 首次连接会提示确认指纹，输入yes
```

### 3.5 获取连接信息

在"远程登录"设置页面，会显示：

```
要从此电脑登录此Mac，请输入：
ssh 用户名@100.64.0.1
```

记下这个IP地址（Tailscale分配的虚拟IP）和用户名。

---

## 四、第三步：tmux会话管理

### 4.1 安装tmux

```bash
# Homebrew安装
brew install tmux

# 验证安装
tmux -V
```

### 4.2 核心概念

tmux有三个层级：

| 层级 | 说明 | 类比 |
|------|------|------|
| **Session（会话）** | 顶层的独立环境 | 一个完整的终端窗口 |
| **Window（窗口）** | 会话内的标签页 | 浏览器的Tab |
| **Pane（窗格）** | 窗口内的分割区域 | 分屏后的每一块 |

### 4.3 基础操作

**创建命名会话（推荐）**

```bash
# 创建一个叫"claude-code"的会话
tmux new -s claude-code
```

**所有tmux快捷键都要先按"前缀键"：`Ctrl + b`**

常用快捷键：

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+b d` | 分离会话（后台运行） |
| `Ctrl+b c` | 新建窗口 |
| `Ctrl+b 0-9` | 切换到第0-9个窗口 |
| `Ctrl+b %` | 左右分屏 |
| `Ctrl+b "` | 上下分屏 |
| `Ctrl+b 方向键` | 切换窗格 |
| `Ctrl+b x` | 关闭当前窗格 |
| `Ctrl+b [` | 进入滚动模式（按q退出） |

**会话管理命令**

```bash
# 查看所有会话
tmux ls

# 重新连接到会话
tmux attach -t claude-code
# 简写
tmux a -t claude-code

# 只有一个会话时直接连接
tmux a

# 结束会话
tmux kill-session -t claude-code
```

### 4.4 为什么tmux是必需的

**场景一：网络断开**

没有tmux：
- SSH断开 → Claude Code进程被杀 → 所有工作丢失

有tmux：
- SSH断开 → tmux会话仍在后台运行 → 重连后`tmux a`恢复现场

**场景二：切换网络**

- 从家里WiFi切换到移动数据
- Termius重新连接
- `tmux a`回到之前的Claude Code会话，代码还在

**场景三：多任务并行**

在一个tmux会话中：
- 窗口0：跑Claude Code写代码
- 窗口1：跑pytest测试
- 窗口2：查看日志文件

手机小屏幕，用窗口切换比分屏更实用。

---

## 五、第四步：手机端Termius配置

### 5.1 安装Termius

- **iOS**：App Store搜索"Termius"
- **Android**：Google Play或官网下载

Termius免费版已足够使用，付费版提供云同步功能。

### 5.2 新建主机连接

打开Termius，点击右下角"+"号 → 选择"New Host"

填写连接信息：

| 字段 | 填写内容 |
|------|----------|
| **Alias（别名）** | My MacBook Pro（自定义名称） |
| **Hostname/IP** | 100.64.0.1（Tailscale分配的IP） |
| **Port** | 22（默认SSH端口） |
| **Username** | 你的Mac用户名 |
| **Password** | 你的Mac登录密码 |

点击右上角"✓"保存。

### 5.3 首次连接

在Termius主机列表中点击刚创建的主机：

1. 首次连接会提示"未知主机指纹"，点击"Continue"确认
2. 输入Mac登录密码
3. 连接成功后看到Mac的终端提示符

**测试连接**

```bash
# 查看系统信息
uname -a

# 查看当前目录
pwd

# 测试Tailscale连接
tailscale status
```

### 5.4 进阶：SSH密钥认证（可选但推荐）

密码认证每次都要输入密码，密钥认证更安全更方便。

**在Mac上生成密钥对**

```bash
# 生成ED25519密钥（推荐）
ssh-keygen -t ed25519 -C "your-email@example.com"

# 一路回车使用默认设置
# 密钥保存在 ~/.ssh/id_ed25519（私钥）和 ~/.ssh/id_ed25519.pub（公钥）
```

**将公钥添加到授权列表**

```bash
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys

# 设置正确权限
chmod 600 ~/.ssh/authorized_keys
```

**导出私钥到手机**

```bash
# 在Mac上查看私钥内容
cat ~/.ssh/id_ed25519
```

复制输出的全部内容（包括`-----BEGIN OPENSSH PRIVATE KEY-----`和`-----END OPENSSH PRIVATE KEY-----`）。

**在Termius中导入密钥**

1. Termius → 右下角"..." → Keychain
2. 点击"Add Key"
3. Label填写：MacBook Key
4. Private Key粘贴刚才复制的内容
5. 保存

**修改主机连接使用密钥**

1. 编辑之前创建的主机
2. Password字段清空
3. 点击"Keys"选择刚导入的密钥
4. 保存

现在连接无需输入密码。

### 5.5 Termius实用技巧

**中文界面设置**

Termius默认英文，可切换中文：
1. 右下角"Settings"（齿轮图标）
2. General → Language → 选择"中文"

**快速命令片段**

常用命令可以保存为Snippet：
1. Termius → Snippets → "+"
2. 添加常用命令如：`tmux a -t claude-code`
3. 连接后快速执行

---

## 六、第五步：Claude Code CLI安装与验证

### 6.1 安装Node.js

Claude Code CLI基于Node.js运行，需先安装：

```bash
# Homebrew安装
brew install node

# 验证安装
node -v
npm -v
```

Node.js版本需18.0以上。

### 6.2 安装Claude Code CLI

```bash
# npm全局安装
npm install -g @anthropic-ai/claude-code

# 验证安装
claude --version
```

### 6.3 配置API Key

Claude Code需要Anthropic API Key才能使用。

**获取API Key**

1. 访问：https://console.anthropic.com
2. 注册/登录账号
3. API Keys → Create Key
4. 复制生成的Key（以`sk-ant-`开头）

**配置环境变量**

```bash
# 临时配置（当前终端会话有效）
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# 永久配置（写入shell配置文件）
# 如果使用zsh（macOS默认）
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.zshrc
source ~/.zshrc

# 如果使用bash
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.bash_profile
source ~/.bash_profile
```

**国内用户中转配置**

如果无法直接访问Anthropic API，可配置中转地址：

```bash
export ANTHROPIC_BASE_URL="https://你的中转地址"
export ANTHROPIC_API_KEY="中转平台提供的Key"
```

### 6.4 在tmux会话中启动Claude Code

**完整流程**

```bash
# 1. SSH连接到Mac后，创建tmux会话
tmux new -s claude-code

# 2. 进入项目目录
cd ~/projects/my-project

# 3. 启动Claude Code
claude

# 4. 首次启动会提示：
#    - 选择主题（推荐默认）
#    - 确认安全须知
#    - 信任当前目录
#    按Enter使用默认选项即可

# 5. 按 Ctrl+b d 分离会话（Claude Code继续后台运行）

# 6. 断开SSH连接也没关系

# 7. 下次重新连接后恢复
tmux a -t claude-code
```

### 6.5 Claude Code基础使用

Claude Code是交互式AI编程助手，直接用自然语言对话：

```
你: 帮我写一个Python脚本，读取CSV文件并计算每列的平均值

Claude Code: 我来创建这个脚本...
[自动创建文件并写入代码]

你: 能加上错误处理吗？

Claude Code: 好的，我来添加try-except...
[修改代码]
```

**常用命令**

- `/help`：查看帮助
- `/clear`：清除对话历史
- `/compact`：压缩对话上下文
- `Ctrl+C`：中断当前操作

---

## 七、完整工作流演示

### 场景：在地铁上修复一个Bug

**早上出门前**

```bash
# 在Mac上
cd ~/projects/my-app
tmux new -s my-app
claude
# 让Claude Code理解项目结构
```

按`Ctrl+b d`分离会话，让Mac保持开机。

**地铁上（手机操作）**

1. 打开Termius
2. 点击"My MacBook Pro"连接
3. 执行`tmux a -t my-app`
4. 看到之前的Claude Code会话，继续对话：

```
你: 我发现用户登录后偶尔会报500错误，帮我排查

Claude Code: 我来检查登录相关的代码...
[读取auth.py]
问题可能出在数据库连接超时处理上，我建议...
```

5. 修复完成后按`Ctrl+b d`分离
6. 断开SSH

**到公司后**

在公司的电脑上：

```bash
ssh 你的用户名@100.64.0.1
tmux a -t my-app
# 继续之前的会话
```

无缝衔接。

---

## 八、常见问题与解决方案

### 问题1：Tailscale连接不上

**症状**

Termius提示"Connection refused"或"Timeout"

**排查步骤**

```bash
# 在Mac上检查Tailscale状态
tailscale status

# 如果显示"stopped"
tailscale up

# 检查防火墙是否阻止
# 系统设置 → 隐私与安全性 → 防火墙 → 确保SSH在允许列表
```

**检查ACL权限**

登录Tailscale管理后台，确认ACL没有阻止手机到Mac的22端口。

### 问题2：SSH连接被拒绝

**症状**

`ssh: connect to host 100.64.0.1 port 22: Connection refused`

**解决方案**

```bash
# 检查SSH服务状态
sudo systemsetup -getremotelogin

# 如果显示Off，开启它
sudo systemsetup -setremotelogin on

# 检查sshd进程
ps aux | grep sshd

# 如果没有sshd进程，尝试重启
sudo launchctl unload /System/Library/LaunchDaemons/ssh.plist
sudo launchctl load -w /System/Library/LaunchDaemons/ssh.plist
```

### 问题3：tmux会话丢失

**症状**

`tmux ls`提示"no server running on /tmp/tmux-xxx`

**原因**

Mac重启了，或tmux进程被杀。

**预防措施**

tmux会话不持久化，Mac重启会丢失。可以考虑：

1. 使用脚本自动恢复关键会话
2. 重要工作记得及时提交Git
3. 使用launchd在开机后自动启动tmux

### 问题4：手机输入命令太慢

**解决方案**

**方法一：使用Snippet**

在Termius中保存常用命令片段：
- `tmux a -t claude-code`
- `git status`
- `npm test`

一键执行，无需手打。

**方法二：配置tmux快捷键**

创建`~/.tmux.conf`：

```bash
# 改变前缀键为Ctrl+a（手机上更容易按）
set -g prefix C-a
unbind C-b
bind C-a send-prefix

# 更直观的窗口切换
bind -n M-Left select-window -t -1
bind -n M-Right select-window -t +1
```

**方法三：外接蓝牙键盘**

如果经常移动办公，蓝牙键盘能大幅提升效率。

### 问题5：Claude Code响应慢

**可能原因**

- 网络延迟高（Tailscale中继模式）
- API服务器响应慢
- 项目文件过多

**解决方案**

```bash
# 检查Tailscale是否直连
tailscale status
# 如果显示"relay"，说明走了中继服务器

# 优化：在同一地域的设备更易直连
# 如果直连，延迟通常<50ms
```

使用`/compact`定期压缩对话上下文，减少每次请求的数据量。

---

## 九、安全最佳实践

### 9.1 最小权限原则

**Tailscale ACL**

只开放必要端口：

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["tag:mobile"],
      "dst": ["tag:mac:22"]
    }
  ]
}
```

**SSH用户限制**

在"远程登录"设置中，只允许特定用户SSH登录，不要选"所有用户"。

### 9.2 密钥优于密码

密码可能被暴力破解，ED25519密钥更安全。

**禁用密码登录**

编辑`/etc/ssh/sshd_config`：

```
PasswordAuthentication no
PubkeyAuthentication yes
```

重启SSH服务：

```bash
sudo launchctl unload /System/Library/LaunchDaemons/ssh.plist
sudo launchctl load -w /System/Library/LaunchDaemons/ssh.plist
```

### 9.3 定期审计

**检查登录日志**

```bash
# 查看最近的SSH登录
last | head -20

# 查看失败的登录尝试
lastb | head -20
```

**检查Tailscale连接日志**

在管理后台的Logs页面查看所有连接记录。

### 9.4 紧急情况处理

**发现异常访问**

1. 立即在Tailscale管理后台移除可疑设备
2. 在Mac上关闭SSH：`sudo systemsetup -setremotelogin off`
3. 更改密码和密钥

**远程关闭SSH**

如果手机被盗，通过Tailscale管理后台的ACL立即阻止所有连接。

---

## 十、进阶玩法

### 10.1 多设备协同

**场景**：手机写代码，iPad看日志

```bash
# Mac上创建两个tmux会话
tmux new -s coding    # 会话1：跑Claude Code
tmux new -s logs      # 会话2：tail -f logs/app.log

# 手机连接coding会话
tmux a -t coding

# iPad连接logs会话
tmux a -t logs
```

两个设备同时操作，互不干扰。

### 10.2 自动化脚本

创建`~/scripts/start-remote-dev.sh`：

```bash
#!/bin/bash
SESSION_NAME="claude-code"

# 检查会话是否存在
tmux has-session -t $SESSION_NAME 2>/dev/null

if [ $? != 0 ]; then
    # 创建新会话
    tmux new-session -s $SESSION_NAME -d
    # 进入项目目录
    tmux send-keys -t $SESSION_NAME "cd ~/projects/my-project" C-m
    # 启动Claude Code
    tmux send-keys -t $SESSION_NAME "claude" C-m
fi

echo "会话 '$SESSION_NAME' 已就绪"
echo "手机SSH连接后执行: tmux a -t $SESSION_NAME"
```

Mac开机后自动运行：

```bash
chmod +x ~/scripts/start-remote-dev.sh
```

在"系统设置 → 通用 → 登录项"中添加此脚本。

### 10.3 端口转发

如果需要访问Mac上的本地服务（如`localhost:3000`）：

**SSH端口转发**

```bash
# 在手机Termius中连接时添加端口转发
# 编辑主机 → Port Forwarding → Add
# Local Port: 3000
# Remote Host: localhost
# Remote Port: 3000
```

连接后，手机浏览器访问`localhost:3000`就是Mac上的服务。

---

## 十一、总结

这套方案的核心价值：

1. **随时随地**：只要有网络就能连接Mac开发
2. **稳定可靠**：tmux保护会话，网络波动不影响
3. **安全可控**：Tailscale的ACL + SSH密钥双重保护
4. **原生体验**：Termius提供真正的终端，不是远程桌面

**适用场景**

- 通勤路上处理紧急Bug
- 外出时需要查看服务器日志
- 多台设备协同工作
- 没有公网IP的内网环境

**不适用场景**

- 需要图形界面操作（用VNC或Parsec）
- 大文件传输（用Syncthing或scp）
- 高频输入（外接蓝牙键盘更好）

**关键要点**

- Tailscale的安全配置是基础
- tmux是会话保持的核心
- Termius让手机变成真正的终端
- Claude Code在tmux中才能断线不丢进度

现在，试试从手机连接你的Mac，开始第一次移动开发体验吧。

---

## 附录：命令速查表

**Tailscale**

```bash
tailscale status          # 查看连接状态
tailscale up              # 启动连接
tailscale down            # 断开连接
tailscale ip              # 查看虚拟IP
```

**SSH**

```bash
ssh user@100.64.0.1      # 连接远程主机
ssh-keygen -t ed25519    # 生成密钥对
ssh-copy-id user@host    # 复制公钥到远程
```

**tmux**

```bash
tmux new -s name         # 创建命名会话
tmux ls                  # 列出所有会话
tmux a -t name           # 连接到会话
tmux kill-session -t name # 结束会话
```

**tmux快捷键（先按Ctrl+b）**

```
d     分离会话
c     新建窗口
0-9   切换窗口
%     左右分屏
"     上下分屏
x     关闭窗格
[     滚动模式（q退出）
```

**Claude Code**

```bash
claude              # 启动交互界面
claude --version    # 查看版本
/help               # 查看帮助
/clear              # 清除对话
/compact            # 压缩上下文
```
