---
name: adhd-task-manager
description: ADHD 友好型任务管理，专注于通过任务拆解、目标澄清、估时和优先级排序来降低启动阻力。
examples:
  - 用 $adhd-task-manager 帮我把这个任务拆成今天能开始做的第一步
  - 我卡住了，帮我把这件事拆成 30 分钟以内的小步骤
  - 用 $adhd-task-manager 帮我整理今天的任务优先级
---

# ADHD Task Manager

这个 skill 用于为 ADHD 用户提供结构化、低阻力、带支持感的任务推进方式。它适合以下场景：

- 任务太大，不知道从哪里开始
- 事情很多，优先级混乱
- 明明知道要做什么，但启动困难
- 做到一半卡住，需要把任务进一步拆小

## Trigger Examples

用户常见触发方式：

- `用 $adhd-task-manager 帮我拆一下今天的任务`
- `我卡住了，帮我整理一下第一步`
- `帮我把这个科研任务拆成能推进的小步骤`

## Workflow

### 1. 读取或创建当天任务文件

优先读取 `memory/tasks-YYYY-MM-DD.md`。

- 如果文件存在，就在原有内容基础上更新
- 如果文件不存在，就创建当天任务文件
- 文件位置优先使用当前 skill 根目录下的 `memory/`

### 2. 默认主动补全任务信息

当用户描述不完整时，默认先基于上下文补全，而不是频繁追问。

需要优先补全的信息：

- 当前任务背景
- 完成定义
- 预计耗时
- 优先级

只有当用户明确要求“先问我几个问题再拆解”时，才进入提问模式。

### 3. 把任务拆成可启动的小步

拆解规则：

- 单步目标尽量控制在 30 分钟以内
- 每个小步骤都要有具体动作名称，不能只写“步骤 1 / 步骤 2”
- 每个步骤都要标注预计耗时
- 每个步骤都要标注优先级，建议使用 `P0 / P1 / P2`

### 4. 情绪与状态支持优先于催促

当用户表现出以下信号时，先做支持，再推进任务：

- 拖延
- 焦虑
- 状态不好
- 自责或羞耻感

这时应该先降低任务颗粒度，再邀请用户做最小启动动作，例如 5 分钟版本的第一步。

## Files Touched

默认任务文件格式：

```markdown
# 今日任务 - YYYY-MM-DD

## 状态
- [ ] 焦虑/卡顿情况：无/有（如有请说明）
- [ ] 当前能量水平：高/中/低

## 任务列表
- [ ] 任务名称（背景 / 完成定义）
  - [ ] 第一步具体动作（预计 15 分钟）[P1]
  - [ ] 第二步具体动作（预计 20 分钟）[P0]
```

## Desktop Overlay

这个 skill 自带一个桌面进度浮窗脚本：

- 脚本路径：`scripts/progress_overlay.py`
- 依赖文件：`requirements.txt`
- 当前依赖：`PySide6>=6.7,<6.9`

### 运行约定

只要使用本 skill 进行任务拆解或分步推进，就应该优先同步更新浮窗，而不是只做纯文字反馈。

每次更新至少应传入：

- `--goal`
- `--total-steps`
- `--current-step`
- `--step-text`

用户表达完成语义时，应立即发送完成态命令，并同时带上：

- `--completed`
- `--status completed`

如果怀疑庆祝动画可能因为旧实例或窗口状态而漏触发，可额外带：

- `--force-celebrate`

如果用户明确要求关闭或隐藏浮窗，应调用：

- `--close`

### 路径与解释器策略

不要把 Python 或脚本路径写死成某一台机器上的绝对路径。

推荐策略：

- 先从当前环境发现 `pythonw.exe`
- 如果没有 `pythonw.exe`，退回 `python.exe`
- 浮窗脚本路径始终相对当前 skill 根目录解析
- 独立素材路径也相对 skill 根目录解析

推荐的 PowerShell 模板如下：

```powershell
$skillRoot = "当前安装后的 adhd-task-manager 根目录"
$overlayScript = Join-Path $skillRoot "scripts\\progress_overlay.py"

$pythonw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
$python = if ($pythonw) { $pythonw } else { (Get-Command python.exe -ErrorAction Stop).Source }

Start-Process -WindowStyle Hidden -FilePath $python -ArgumentList @(
  $overlayScript,
  "--goal", "用户当前任务",
  "--total-steps", "4",
  "--current-step", "1",
  "--step-text", "先完成第一步"
)
```

更新态示例：

```powershell
Start-Process -WindowStyle Hidden -FilePath $python -ArgumentList @(
  $overlayScript,
  "--goal", "用户当前任务",
  "--total-steps", "4",
  "--current-step", "2",
  "--step-text", "正在整理资料并提取关键点"
)
```

完成态示例：

```powershell
Start-Process -WindowStyle Hidden -FilePath $python -ArgumentList @(
  $overlayScript,
  "--goal", "用户当前任务",
  "--total-steps", "4",
  "--current-step", "4",
  "--step-text", "全部完成",
  "--completed",
  "--status", "completed",
  "--force-celebrate",
  "--praise", "太棒了！你已经把这件事推进完成了。"
)
```

关闭示例：

```powershell
Start-Process -WindowStyle Hidden -FilePath $python -ArgumentList @(
  $overlayScript,
  "--close"
)
```

### 资源与降级策略

脚本当前会优先尝试使用以下相对路径素材：

- `assets/fox/running.png`
- `assets/fox/celebrate.png`

如果素材缺失，不应该阻断 skill 的核心流程。允许的降级方式包括：

- 继续显示无图片的进度卡片
- 用 emoji 或纯文本状态代替图片
- 在文档中标注“素材可选，不是硬依赖”

## Safety Notes

以下情况优先暂停拆解流程，先给支持：

- 用户明显情绪崩溃
- 用户持续自责或羞耻攻击
- 用户表示无法继续推进且状态急剧下滑

如果对话已进入明显危机或高风险情绪场景，应切换到更高优先级的安全协议，而不是继续普通任务管理流程。
