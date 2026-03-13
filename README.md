# OpenClaw ADHD 特化技能库 (OpenClaw ADHD Skills)

本仓库致力于为 OpenClaw 平台构建一套专为 ADHD (注意缺陷与多动障碍) 群体设计的辅助技能集。这些工具旨在通过任务分解、认知支持、情感调节和危机干预，帮助用户减轻执行功能障碍带来的焦虑，提升生活与科研效率。

## 🛠 包含技能列表

| 技能名称 | 核心功能 | 解决的主要痛点 |
| :--- | :--- | :--- |
| **adhd-task-manager** | 任务微小化分解、优先级排序、估时 | 任务堆积导致的焦虑与拖延瘫痪 |
| **adhd-timer-pomodoro** | 专注辅助番茄钟 + 状态检查 | 难以维持专注、时间盲区 |
| **adhd-body-doubling** | 远程伴读/远程办公 (Body Doubling) 模式 | 缺乏动力、需要外部监督以进入工作状态 |
| **adhd-decision-matrix** | 决策瘫痪辅助，生成决策矩阵 | 面对多选项时的决策困难与纠结 |
| **adhd-energy-audit** | 能量波动追踪与黄金时间规划 | 对自身精力分配缺乏认知 |
| **adhd-shame-killer** | 应对羞耻感，转化消极自我对话 | 因拖延而产生的自我攻击与自责 |
| **adhd-knowledge-base** | ADHD 友好知识库检索 | 应对突发 ADHD 相关心理困扰与小知识 |
| **crisis-response-protocol** | 心理健康危机安全协议 | 处理严重心理健康危机风险 |

## 🚀 安装指南

### 前置要求
- 已安装并配置好 OpenClaw 运行环境。
- 已配置 Git 和 GitHub CLI (`gh`)。

### 安装步骤
1. **克隆本仓库**:
   ```bash
   git clone https://github.com/houchenfeng/openclaw-adhd-skills.git
   cd openclaw-adhd-skills
   ```
2. **将技能部署到本地 OpenClaw 目录**:
   将对应技能文件夹复制到您的 OpenClaw `skills/` 目录下（通常为 `C:\Users\hcf\.openclaw\workspace\skills\`）。
   ```bash
   # 示例命令 (根据实际路径调整)
   cp -r adhd-task-manager C:\Users\hcf\.openclaw\workspace\skills\
   ```
3. **刷新技能列表**:
   重启 OpenClaw 即可识别新安装的技能。

## 💡 使用建议
- **从小步开始**: 优先尝试 `adhd-task-manager` 进行任务分解。
- **寻求支持**: 当感到压力过大时，使用 `adhd-shame-killer` 进行心态调整。
- **安全第一**: 深入了解并配置 `crisis-response-protocol` 以备不时之需。

---
本仓库遵循开源协议，欢迎 ADHD 同仁与开发者贡献优化建议。
