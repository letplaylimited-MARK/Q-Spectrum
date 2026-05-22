# Sub-Skill 07 · 通用封装 Universal Packaging
## Skill Dev SOP — 阶段07 · v1.0.0

---

## 职责声明 | Responsibility

本子Skill将工程包中的核心提示词封装为 **CodeBuddy 官方 SKILL.md 格式** 和通用 `.skill` 文件，确保格式完全合规、可直接安装、跨平台兼容。

**输入**：v1.1.0 工程包（核心提示词 + 使用指南）
**输出**：最终合规的 `SKILL.md` + `.skill` 打包文件
**门控**：格式验证检查通过（字符数/格式规范/工具声明）后，进入阶段08

---

## 执行逻辑 | Execution Logic

### Step 1 · SKILL.md 最终合规检查

在封装前，对现有 `SKILL.md` 执行全面格式审计：

**SKILL.md 合规检查清单（必须全部通过）：**

```
格式合规检查
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ [格式] YAML frontmatter 正确开始：---
□ [格式] YAML frontmatter 正确结束：---
□ [名称] name: 全小写，只含字母/数字/连字符
□ [名称] name: 无空格，无下划线，无大写字母
□ [描述] description: 实际字符数 ≤ 1024
□ [描述] description: 包含功能描述段落
□ [描述] description: 包含触发短语（Trigger phrases: ...）
□ [描述] description: 触发短语中英双语
□ [工具] allowed-tools: 已声明（最小权限原则）
□ [工具] allowed-tools: 无未实际使用的多余工具
□ [正文] 包含角色定义段落
□ [正文] 包含激活后输出模板
□ [正文] 包含核心工作流说明
□ [正文] 代码块层级不超过三重反引号嵌套
□ [正文] 无孤立的 ``` 造成渲染错误
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
通过：[N]/15 项
```

---

### Step 2 · Description 精确字符数验证

description 字符数限制是 CodeBuddy SKILL.md 最关键的格式约束，需精确验证：

**验证方法（Python脚本）：**

```python
#!/usr/bin/env python3
"""验证 SKILL.md description 字符数"""

description = """在此粘贴你的description内容"""

char_count = len(description)
print(f"字符数: {char_count}")
print(f"状态: {'✅ 合规' if char_count <= 1024 else f'❌ 超限 {char_count - 1024} 字符'}")

if char_count > 1024:
    # 建议截断位置
    print(f"\n建议在第 {1024} 字符处截断：")
    print(description[:1024])
```

**若超限，按以下优先级精简：**

1. 删除冗余的介绍性词语（「这是一个用于...的工具」→ 直接描述功能）
2. 合并近义的触发短语
3. 将中英双语触发短语从「完整句子」改为「关键词列表」
4. 保留顺序：功能摘要 > 使用场景 > 触发短语

---

### Step 3 · allowed-tools 最小权限审计

审计 allowed-tools 声明，确保最小权限原则：

**权限映射表：**

| 工具 | 需要该工具的场景 | 无此工具的影响 |
|---|---|---|
| Read | 读取用户上传的文件/Skill工程包文件 | 无法读取本地文件 |
| Write | 创建工程包文件/生成SKILL.md | 无法自动写入文件 |
| Edit | 修改已有文件 | 无法执行阶段05修复 |
| Bash | 执行字符数验证/打包脚本 | 无法自动化验证 |
| Glob | 搜索文件结构 | 不影响核心功能 |
| Grep | 搜索内容 | 不影响核心功能 |

**审计结论输出：**
```
allowed-tools 审计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
实际声明：[Read, Write, Edit, Bash]
分析：
  Read - ✅ 必需（文件读取）
  Write - ✅ 必需（工程包生成）
  Edit - ✅ 必需（迭代修复）
  Bash - ✅ 必需（字符数验证脚本）
多余声明：无
缺少声明：无
结论：✅ 最小权限原则通过
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Step 4 · 嵌套代码块检测与修复

多层嵌套代码块是最常见的 P0 格式问题，需自动检测：

**检测规则：**
- 在三重反引号（```）包裹的代码块内，绝不允许再出现三重反引号
- 若要在代码块内展示代码块，改用缩进（4个空格）或引用块（>）

**常见错误模式与修复方案：**

```
错误模式（会导致渲染失败）：
  ```markdown
  这里展示一段代码：
  ```python        ← 错误：嵌套三重反引号
  print("hello")
  ```
  ```

正确方案1（改用缩进）：
  ```markdown
  这里展示一段代码：

      print("hello")   ← 4空格缩进表示代码
  ```

正确方案2（改用引用块描述）：
  ```markdown
  这里展示的是一段Python代码：
  > python: print("hello")
  ```
```

---

### Step 5 · `.skill` 文件打包

生成跨平台通用的 `.skill` 压缩包：

**打包脚本 `deploy/package_skill.py`：**

```python
#!/usr/bin/env python3
"""
Skill 工程包打包脚本
生成 [skill-name]-v[version].skill 文件
"""
import zipfile
import os
import json
from datetime import datetime

SKILL_NAME = "[skill-name]"  # 替换为实际名称
VERSION = "1.1.0"
OUTPUT_FILE = f"{SKILL_NAME}-v{VERSION}.skill"

# 打包文件清单
INCLUDE_FILES = [
    "SKILL.md",
    "README.md",
    "LICENSE",
    "core/system-prompt-full.md",
    "core/system-prompt-lite.md",
    "core/activation-card.md",
    "docs/user-guide.md",
    "docs/changelog.md",
    "docs/design-principles.md",
]

# 生成 manifest.json
manifest = {
    "name": SKILL_NAME,
    "version": VERSION,
    "packaged_at": datetime.now().isoformat(),
    "files": INCLUDE_FILES
}

with zipfile.ZipFile(OUTPUT_FILE, 'w', zipfile.ZIP_DEFLATED) as zf:
    # 写入 manifest
    zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
    
    # 打包核心文件
    for file_path in INCLUDE_FILES:
        if os.path.exists(file_path):
            zf.write(file_path)
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ 缺失: {file_path}")

print(f"\n打包完成: {OUTPUT_FILE}")
```

**运行方式：**
```bash
cd /workspace/[skill-name]
python3 deploy/package_skill.py
```

---

### Step 6 · 封装完成验证

格式验证全部通过后，输出封装报告：

```markdown
## 📦 封装完成报告 · 阶段07

**Skill名称**：[name]
**封装版本**：v1.1.0
**封装时间**：[时间]

### 格式验证
| 检查项 | 结果 |
|---|---|
| SKILL.md格式合规 | ✅ 通过（15/15项）|
| description字符数 | ✅ [N]字符（≤1024）|
| allowed-tools最小权限 | ✅ 4项工具全部必需 |
| 无嵌套代码块冲突 | ✅ 无嵌套错误 |

### 打包文件
| 文件 | 大小 |
|---|---|
| SKILL.md | [N]字节 |
| [skill-name]-v1.1.0.skill | [N]字节 |

---
🚦 **阶段07门控**：格式验证通过，进入阶段08 GitHub发布
```

---

## 防错护栏 | Error Guards

| 错误场景 | 护栏动作 |
|---|---|
| description 精简后失去关键触发词 | 检查并恢复最重要的3~5个触发词 |
| 打包脚本找不到文件 | 列出缺失文件，等待补全后重新打包 |
| 格式检查部分未通过 | 逐项修复，直到全部通过，不允许「将就发布」 |
| allowed-tools 删减导致功能损失 | 权衡后告知用户：「移除[工具]将无法[功能]，建议保留」|

---

## 与其他子Skill的接口 | Interface

**上游**：06-user-guide.md → 使用指南确认
**下游**：08-github-publish.md 接收「SKILL.md路径 + .skill文件路径 + 完整工程包」
**传递数据格式**：

```yaml
stage_07_output:
  skill_md_path: "/workspace/[skill-name]/SKILL.md"
  skill_package_path: "/workspace/[skill-name]/[name]-v1.1.0.skill"
  format_check_passed: true
  description_char_count: [N]
  version: "1.1.0"
```
