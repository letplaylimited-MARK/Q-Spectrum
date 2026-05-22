# Sub-Skill 02 · 阶段任务拆解器

**所属 Skill**：Skill 04 · Planner  
**版本**：v1.0.0  
**职责**：将解析后的 SOP 拆解为三层结构：Phase / Task / Step

---

## 三层结构定义

```
Phase（阶段）
  └── Task（任务）
        └── Step（步骤）
```

| 层级 | 粒度 | 时间单位 | 命名格式 |
|------|------|---------|---------|
| Phase | 里程碑 | 3-14 天 | P{N}：{名称} |
| Task | 工作项 | 1-3 天 | T{N}：{名称} |
| Step | 可执行操作 | 30分钟-2小时 | P{M}-T{N}-S{K} |

---

## 标准 Phase 模板

典型 AI 项目的标准阶段划分：

```yaml
phases:
  - id: "P0"
    name: "环境配置"
    objective: "确保所有工具和环境就绪"
    estimated_days: 0.5
    
  - id: "P1"
    name: "数据/输入层构建"
    objective: "建立数据处理管道"
    estimated_days: 2-3
    
  - id: "P2"
    name: "核心逻辑实现"
    objective: "实现主要业务逻辑"
    estimated_days: 3-5
    
  - id: "P3"
    name: "集成与联调"
    objective: "将各模块集成，端到端测试"
    estimated_days: 2-3
    
  - id: "P4"
    name: "部署与上线"
    objective: "部署到目标环境"
    estimated_days: 1-2
```

---

## Step 原子操作模板

每个 Step 必须包含以下所有字段：

```yaml
step:
  id: "P1-T2-S3"
  description: "{动词 + 对象} 的操作描述"    # 如：安装 FastAPI 框架
  type: "command/file_edit/config/verify/manual"
  tool: "{使用的工具}"                        # 如：终端、VS Code、浏览器
  action: |
    {具体操作内容}
    {多行命令或操作说明}
  expected_output: "{预期的输出或状态}"
  verify: "{如何验证步骤成功}"
  estimated_minutes: {X}                     # [估算，请根据实际调整]
  dependencies:
    - "{依赖的前序步骤 ID，如：P1-T1-S2}"
  optional: false                            # 是否可选步骤
  on_failure: |
    {失败时的处理建议}
```

---

## 拆解规则

### 拆解深度规则

| 步骤类型 | 最小粒度 | 最大粒度 |
|---------|---------|---------|
| 安装/配置类 | 单个命令 | 一个配置文件 |
| 编码实现类 | 一个函数/类 | 一个模块 |
| 测试验证类 | 一个测试用例 | 一个测试文件运行 |
| 部署类 | 单个部署命令 | 一个服务启动 |

### 禁止的拆解方式

- ❌ 步骤描述模糊（如"完善代码"、"优化性能"）
- ❌ 一个步骤超过2小时工作量（应继续拆分）
- ❌ 步骤缺少验证方式
- ❌ 添加 SOP 中未包含的功能步骤

### 并行步骤标注

可以并行执行的步骤使用 `parallel_group` 标注：

```yaml
- step_id: "P1-T1-S1"
  parallel_group: "setup"
  
- step_id: "P1-T1-S2"
  parallel_group: "setup"    # 与 S1 可同时执行
```

---

## 拆解输出示例

```yaml
# 示例：情绪分析 API 项目 Phase 1

phase:
  id: "P1"
  name: "API 框架搭建"
  tasks:
    - id: "T1"
      name: "项目初始化"
      estimated_hours: 2
      steps:
        - id: "P1-T1-S1"
          description: "创建项目目录结构"
          type: "command"
          tool: "终端"
          action: |
            mkdir -p sentiment-api/{src,tests,config}
            cd sentiment-api
            git init
          expected_output: "目录结构创建成功"
          verify: "ls -la 查看目录存在"
          estimated_minutes: 10
          
        - id: "P1-T1-S2"
          description: "初始化 Python 虚拟环境"
          type: "command"
          tool: "终端"
          action: |
            python -m venv venv
            source venv/bin/activate  # Linux/Mac
            # 或 venv\Scripts\activate  # Windows
          expected_output: "虚拟环境激活，命令行前缀显示 (venv)"
          verify: "which python 应指向 venv 目录"
          estimated_minutes: 5
          dependencies: ["P1-T1-S1"]
          
        - id: "P1-T1-S3"
          description: "安装核心依赖包"
          type: "command"
          tool: "终端"
          action: "pip install fastapi uvicorn transformers torch"
          expected_output: "Successfully installed ..."
          verify: "python -c \"import fastapi; print(fastapi.__version__)\""
          estimated_minutes: 300    # [估算，依网速而定]
          dependencies: ["P1-T1-S2"]
          
    - id: "T2"
      name: "FastAPI 基础结构"
      ...
```

---

## 检查点生成规则

每个 Phase 末尾自动生成验收检查点：

```markdown
### ✅ Phase {N} 检查点

在继续下一阶段前，确认以下所有项目完成：

| 编号 | 检查内容 | 验证方式 | 状态 |
|------|---------|---------|------|
| C{N}-1 | {检查项1} | {验证命令} | [ ] |
| C{N}-2 | {检查项2} | {验证命令} | [ ] |

**全部通过后**，运行状态保存命令：
```bash
echo "PHASE_{N}=COMPLETE" >> .project_state
echo "COMPLETED_AT=$(date -Iseconds)" >> .project_state
```
```
