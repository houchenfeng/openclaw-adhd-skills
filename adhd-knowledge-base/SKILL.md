---
name: adhd-knowledge-base
description: ADHD 友好型知识库检索与应用。用于从 C:\Users\hcf\.openclaw\workspace\memory\ADHD 下的 Markdown 文件中，提取针对 ADHD 的小知识、应对措施，并结合用户当前的心理状况提供建议。
---

# ADHD 知识库管理与应用

此技能用于高效管理和检索您的 ADHD 知识库，帮助您在焦虑或状态不佳时获得即时支持。

## 核心功能

### 1. 知识检索 (Search)
当您询问 ADHD 相关问题或感到状态不佳时，使用 `memory_search` 对 `memory/ADHD/*.md` 进行语义搜索。
- **注意多语言处理**：知识库包含中英文 Markdown 文件。检索时，请同时使用中文和对应的英文关键词进行搜索（例如：检索“焦虑”时，请同时检索 "anxiety"），以确保覆盖全面。

### 2. 状态关联 (Empathy & Adaptation)
在检索到知识后，**必须**结合您当前在 `memory/tasks-YYYY-MM-DD.md` 中记录的“能量水平”和“焦虑情况”，对知识进行“翻译”，使其转化为此时此刻您可以执行的微小动作。
- **返回语言**：无论检索到的是中文还是英文内容，**返回给用户的最终建议必须是中文**。

## 检索工作流

1. **确定状态**：检查对话上下文或 `tasks-YYYY-MM-DD.md` 中的状态。
2. **执行检索**：
   ```bash
   # 示例：同时检索中英文
   memory_search(query="[中文关键词] [英文对应关键词]")
   ```
3. **知识提炼**：
   - 筛选出最能解决当前困难的 1-2 条策略。
   - 用平实、鼓励的话语总结（去掉冗长的理论）。
4. **行动转化**：询问：“根据这些经验，我们现在尝试做【某件极小的事】，可以吗？”

## 知识库结构 (C:\Users\hcf\.openclaw\workspace\memory\ADHD\)
- 建议将知识归类，例如：
    - `ADHD/coping-mechanisms.md` (应对拖延、注意力分散的技巧)
    - `ADHD/science.md` (ADHD 的底层科学知识)
    - `ADHD/emergency.md` (焦虑发作时的即时干预)

## 注意事项
- **不讲大道理**：ADHD 大脑在焦虑时不需要长篇论述，需要的是极简的操作步骤。
- **正向反馈**：始终肯定用户哪怕只有一点点的尝试。
