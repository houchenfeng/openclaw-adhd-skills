---
name: adhd-task-manager
description: ADHD友好型任务管理，专注于通过任务分解、目标清晰化、估时与优先级排序来减轻焦虑和克服拖延。
---

# ADHD Task Manager

此技能旨在为 ADHD 用户提供结构化且充满支持的任务管理环境，特别适用于科研工作中的任务跟踪。

## 核心工作流

### 1. 任务读取与管理
读取 `memory/tasks-YYYY-MM-DD.md` (当日任务文件)。如果不存在，则创建一个。

### 2. 目标清晰化（默认自动补全，不主动追问）
当用户添加新任务但信息不完整时，默认策略是：
- **先基于上下文主动补全**任务背景、完成定义、优先级与估时，再继续推进。
- **不要频繁向用户提问补信息**，避免打断执行节奏。
- 仅当用户明确表达“你来问我问题补全背景/补全细节”时，才进入提问模式。

提问模式触发短语示例（用户明确授权时才问）：
- “你来问我问题补全背景”
- “先问我几个问题再分解”
- “你先把缺的信息问出来”

### 3. 任务分解与估时
将大任务拆解为 **< 30 分钟**的微型任务。对每个微任务：
- 评估预计耗时。
- 标注优先级（P0-紧急且重要, P1-重要, P2-次要）。
- **必须写出每一个小步骤的具体名称**（不能只写“步骤1/步骤2”）。
- **提醒龙虾**：分解时一定要把每个小步骤命名清楚，并在进度更新时带上该步骤名称（`--step-text`）。

### 4. 情绪支持与状态评估
- 当识别到“拖延”、“状态不好”或“焦虑”时，立即暂停逻辑输出，优先进行情绪疏导，肯定用户的努力，并提议：**“我们把现在的任务再拆小一点，哪怕只做 5 分钟，可以吗？”**

## 文件格式 (`memory/tasks-YYYY-MM-DD.md`)

```markdown
# 今日任务 - YYYY-MM-DD

## 状态
- [ ] 焦虑/卡顿情况：无/有（如有，请说明）
- [ ] 当前能量水平：高/中/低

## 任务列表
- [ ] 任务名称 (分解)
    - [ ] 细分步骤 1 (预计 15 分钟) [P1]
    - [ ] 细分步骤 2 (预计 20 分钟) [P0]
- [ ] 任务名称 (背景：...)
```

## 主动提醒策略
- 在会话中通过 `cron` 设定周期性的任务推进检查，并在消息中保持鼓励性语调。

## 桌面进度条（MVP）

本 skill 内置了一个 Python 悬浮进度条脚本：
- 脚本路径：`scripts/progress_overlay.py`
- 默认调用解释器：`D:\miniconda\envs\xiaozhi\pythonw.exe`（无黑框）
- 调试时解释器：`D:\miniconda\envs\xiaozhi\python.exe`（看报错）
- 内置小狐狸素材：
  - 进行中：`assets/fox/running.png`
  - 完成庆祝：`assets/fox/celebrate.png`

### 单一执行规则（以此为准）

1. **任务分解时必须触发本 skill 的可视化进度脚本**，不能只文字反馈。
2. 每一步更新都必须带：
   - `--current-step`
   - `--step-text`（当前小步骤名称/正在做什么）
3. 用户表达“全部完成/都做完了/搞定了/收工了”等完成语义时，必须立刻触发完成命令。
4. 完成命令必须双保险：
   - `--completed`
   - `--status completed`
5. **最后完成时必须放烟花**（全屏烟花 + 夸夸语），不允许漏触发。
6. 如遇异常场景（进程切换/实例冲突/窗口最小化），完成命令额外加 `--force-celebrate` 兜底。
7. 若用户反馈“命令成功但没看到烟花”，先执行一次 `--close` 清理旧实例，再重发完成命令。
8. **默认行为（强制）**：只要是完成态命令，skill 会先处理旧实例，再触发庆祝；无需用户额外说明。

### 运行行为说明

- 脚本会优先复用已运行实例；若旧实例异常占用，会自动回退到可用实例名继续显示。
- 每一步更新都采用“先处理旧实例，再执行当前状态”的流程（前置清理旧实例）。
- 更新时保持单实例显示，不堆叠多个同类窗口。
- 若用户要求隐藏或关闭浮窗，立即调用 `--close`。

### 标准命令模板（稳定版）

开始：

```powershell
Start-Process -WindowStyle Hidden -FilePath "D:\miniconda\envs\xiaozhi\pythonw.exe" -ArgumentList @("C:\Users\hcf\.openclaw\workspace\skills\adhd-task-manager\scripts\progress_overlay.py","--goal","用户当前任务","--total-steps","6","--current-step","1","--step-text","正在做第1步的具体动作")
```

更新：

```powershell
Start-Process -WindowStyle Hidden -FilePath "D:\miniconda\envs\xiaozhi\pythonw.exe" -ArgumentList @("C:\Users\hcf\.openclaw\workspace\skills\adhd-task-manager\scripts\progress_overlay.py","--goal","用户当前任务","--total-steps","6","--current-step","3","--step-text","正在做第3步的具体动作")
```

完成（必须放烟花）：

```powershell
Start-Process -WindowStyle Hidden -FilePath "D:\miniconda\envs\xiaozhi\pythonw.exe" -ArgumentList @("C:\Users\hcf\.openclaw\workspace\skills\adhd-task-manager\scripts\progress_overlay.py","--goal","用户当前任务","--total-steps","6","--current-step","6","--step-text","全部完成","--completed","--status","completed","--force-celebrate","--praise","太棒了！你全部完成了，烟花庆祝！")
```

说明：完成命令已内置“先清理旧实例 -> 再强制庆祝”流程，调用一次即可。

关闭：

```powershell
Start-Process -WindowStyle Hidden -FilePath "D:\miniconda\envs\xiaozhi\pythonw.exe" -ArgumentList @("C:\Users\hcf\.openclaw\workspace\skills\adhd-task-manager\scripts\progress_overlay.py","--close")
```
