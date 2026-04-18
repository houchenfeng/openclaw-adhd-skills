# OpenClaw ADHD Skills

这个仓库用于维护一组面向 ADHD 支持场景的 Codex / OpenClaw skill 草案。目标不是提供单一脚本，而是把一套可复用的对话流程、任务拆解规则、状态支持方式和辅助脚本整理成可持续迭代的 skill 目录。

## 仓库结构

当前仓库按 skill 分目录组织，每个目录至少包含一个 `SKILL.md`：

- `adhd-task-manager`: 任务拆解、优先级排序、进度可视化
- `adhd-body-doubling`: 陪伴式专注 / body doubling
- `adhd-decision-matrix`: 多选项决策辅助
- `adhd-energy-audit`: 精力审计与节律观察
- `adhd-knowledge-base`: ADHD 相关知识问答
- `adhd-shame-killer`: 拖延、羞耻感与自我攻击缓冲
- `crisis-response-protocol`: 高风险情绪/危机场景的安全协议

## Codex 如何使用这些 Skill

Codex 使用 skill 的关键有两步：

1. 让对应 skill 目录出现在 Codex 可读取的 skills 位置。
2. 在对话中直接点名 skill，或用非常贴近 skill 描述的任务表达。

建议优先使用显式点名方式，例如：

- `用 $adhd-task-manager 帮我把今天的任务拆成能开始做的第一步`
- `用 $adhd-body-doubling 陪我专注 25 分钟`
- `用 $adhd-decision-matrix 帮我在 A / B / C 之间做选择`

一旦触发，Codex 会读取对应的 `SKILL.md`，然后按其中的工作流、文件约定和脚本说明来执行。

## 设计目标

一个对 Codex 友好的 skill，通常应该满足下面几点：

- `SKILL.md` 前部能快速说明它是什么、适用于什么场景。
- 工作流是动作化的，而不只是理念或建议。
- 能明确写出会读写哪些文件、会调用哪些脚本、遇到异常时怎么降级。
- 尽量不依赖某一台机器上的硬编码路径。

## 当前可行性改进建议

这份仓库已经有可复用雏形，但从“个人机器可用”走向“多环境稳定可用”，建议优先补强下面几项：

### 1. 统一文档结构

建议每个 `SKILL.md` 尽量采用一致结构：

- `Purpose`: 这个 skill 解决什么问题
- `Trigger Examples`: 用户会怎么说
- `Workflow`: Codex 应该怎么做
- `Files Touched`: 会写哪些文件
- `Commands / Scripts`: 会调用哪些脚本
- `Fallbacks`: 依赖缺失时如何降级
- `Safety Notes`: 需要停下来、升级处理的情况

这样一方面更利于 Codex 稳定解析，另一方面也方便以后做自动校验。

### 2. 去掉硬编码环境依赖

`adhd-task-manager` 目前最容易出问题的点，是把 Python 和脚本路径写死在特定机器目录上，例如：

- 固定解释器：`D:\miniconda\envs\xiaozhi\pythonw.exe`
- 固定脚本路径：`C:\Users\hcf\.openclaw\workspace\skills\adhd-task-manager\scripts\progress_overlay.py`

更可移植的做法是：

- 优先从当前环境发现 `pythonw.exe`，找不到时退回 `python.exe`
- 脚本路径始终相对 skill 根目录解析
- 内置素材缺失时允许脚本退回 emoji / 纯文本显示，而不是假设资源一定存在

下面是推荐的 PowerShell 调用思路：

```powershell
$skillRoot = "实际的 skill 根目录"
$overlayScript = Join-Path $skillRoot "scripts\\progress_overlay.py"

$pythonw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
$python = if ($pythonw) { $pythonw } else { (Get-Command python.exe -ErrorAction Stop).Source }

Start-Process -WindowStyle Hidden -FilePath $python -ArgumentList @(
  $overlayScript,
  "--goal", "用户当前任务",
  "--total-steps", "4",
  "--current-step", "1",
  "--step-text", "先启动第一步"
)
```

这一版有三个好处：

- 不依赖固定盘符和固定 conda 环境
- skill 被放到别的目录时仍然可运行
- 更适合被 Codex 按规则动态拼装命令

### 3. 明确状态文件和任务文件位置

如果 skill 需要写文件，最好把位置写得很清楚：

- 任务记录是否写入 skill 根目录下的 `memory/`
- 还是写入用户主目录 / OpenClaw 运行目录
- 文件名是否固定为 `tasks-YYYY-MM-DD.md`

越明确，Codex 越不容易在不同会话或不同 workspace 里写错位置。

### 4. 增加资源缺失时的降级说明

当前 `adhd-task-manager/scripts/progress_overlay.py` 默认引用了：

- `assets/fox/running.png`
- `assets/fox/celebrate.png`

但这两个资源目前并不在仓库里。建议文档里明确说明：

- 资源存在时使用图片
- 资源不存在时允许回退到 emoji / 纯文本状态
- 如果后续补资源，路径保持相对 skill 根目录不变

### 5. 给每个 Skill 加触发示例

模型对抽象描述的识别不如对示例稳定。建议每个 skill 至少补 3 条真实触发话术，例如：

- `我现在卡住了，帮我拆成能做的第一步`
- `陪我安静做 20 分钟`
- `我今天精力很差，帮我重新排一下优先级`

## 编码与行尾规范

为了减少 Windows / Git / 编辑器 / 终端之间的乱码与脏状态，建议统一以下约定：

- 所有 Markdown、Python、文本类文件使用 `UTF-8`
- 文本文件统一使用 `LF`
- 图片等二进制资源不做行尾转换

本仓库已补充：

- `.editorconfig`: 约束编码、缩进和行尾
- `.gitattributes`: 约束 Git 文本文件行为

注意：如果 PowerShell 控制台本身不是 UTF-8，即使文件已经是 UTF-8，终端里仍可能显示乱码。这属于终端显示问题，不一定是文件内容损坏。

## adhd-task-manager 说明

`adhd-task-manager` 是目前最接近“可执行 skill”的目录，除了对话流程外，还带了一个桌面进度浮窗脚本：

- 脚本位置：`adhd-task-manager/scripts/progress_overlay.py`
- Python 依赖：`adhd-task-manager/requirements.txt`
- 当前依赖：`PySide6>=6.7,<6.9`

建议使用方式：

- 把脚本路径相对 skill 根目录解析
- 优先使用 `pythonw.exe` 启动无控制台窗口
- 找不到 `pythonw.exe` 时退回 `python.exe`
- 素材图片缺失时允许继续运行，不把图片当硬依赖

## 后续建议

如果后面你继续演进这个仓库，我最推荐的顺序是：

1. 先把 `adhd-task-manager` 作为模板打磨成熟。
2. 统一其它 `SKILL.md` 的章节结构和触发示例。
3. 再补一个简单的校验脚本，检查每个 skill 的 frontmatter、依赖文件和引用资源是否完整。

这个顺序最省力，也最容易让 Codex 的实际表现变稳定。
