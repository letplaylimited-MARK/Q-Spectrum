# QCM MVP 可扩展架构设计

## 核心理念
**基础最小化 + 接口标准化 + 扩展模块化**

---

## 一、架构分层

```
┌────────────────────────────────────────────────────────────┐
│                    用户界面层                              │
│            (聊天室 / 助手 / 协作空间)                      │
└────────────────────────────┬───────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│                    核心引擎层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 角色引擎 │  │ 记忆引擎 │  │ 工作流   │  │ 飞轮引擎 │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────────────┬───────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│                    幽灵通道层                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 增量同步 │  │ 因果排序 │  │ 加密传输 │  │ 审计追踪 │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────────────┬───────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│                    模型接入层                               │
│     (OpenAI / Claude / Gemini / 国产模型 / 本地模型)       │
└────────────────────────────────────────────────────────────┘
```

---

## 二、核心接口标准

### 2.1 角色接口

```python
class Role(ABC):
    @property
    def name(self) -> str:  # 角色名称
        pass
    
    @property
    def description(self) -> str:  # 角色描述
        pass
    
    @property
    def system_prompt(self) -> str:  # 系统提示词
        pass
    
    def preprocess(self, message: str) -> str:  # 预处理
        pass
    
    def postprocess(self, response: str) -> str:  # 后处理
        pass
    
    def get_tools(self) -> list[Tool]:  # 可用工具
        pass
```

### 2.2 模型接口

```python
class AIModel(ABC):
    @property
    def name(self) -> str:
        pass
    
    async def chat(self, messages: list[Message]) -> str:
        pass
    
    async def embed(self, text: str) -> list[float]:
        pass
    
    def get_config(self) -> dict:
        pass
```

### 2.3 插件接口

```python
class Plugin(ABC):
    @property
    def name(self) -> str:
        pass
    
    @property
    def version(self) -> str:
        pass
    
    def on_message(self, ctx: Context) -> Context:
        """消息钩子"""
        pass
    
    def on_response(self, ctx: Context) -> Context:
        """响应钩子"""
        pass
    
    def on_role_switch(self, ctx: Context) -> Context:
        """角色切换钩子"""
        pass
```

---

## 三、可扩展机制

### 3.1 角色扩展

**方式**：通过配置文件或代码注册

```python
# 方式1：配置文件
# roles.yaml
- name: researcher
  description: 研究员
  system_prompt: 你是一个研究员...
  
- name: architect  
  description: 架构师
  system_prompt: 你是一个架构师...

# 方式2：代码注册
from core.roles import Role

class MyCustomRole(Role):
    @property
    def name(self) -> str:
        return "custom_role"
    
    # ... 实现其他方法

# 注册角色
role_manager.register(MyCustomRole())
```

**扩展场景**：
- 添加新角色 → 只需实现Role接口
- 修改角色 → 修改配置或继承重写
- 删除角色 → 移除注册

---

### 3.2 模型扩展

```python
# models/openai_model.py
class OpenAIModel(AIModel):
    async def chat(self, messages):
        return openai.ChatCompletion.create(...)
    
    async def embed(self, text):
        return openai.Embedding.create(...)

# models/claude_model.py
class ClaudeModel(AIModel):
    async def chat(self, messages):
        return anthropic.messages.create(...)
    
    async def embed(self, text):
        return anthropic.embeddings.create(...)

# models/local_model.py
class LocalModel(AIModel):
    async def chat(self, messages):
        return ollama.chat(...)
    
    async def embed(self, text):
        return ollama.embeddings.create(...)
```

**扩展场景**：
- 添加新模型 → 实现AIModel接口
- 切换模型 → 修改配置
- 同时使用多模型 → 路由策略

---

### 3.3 插件扩展

```python
# plugins/memory.py
class MemoryPlugin(Plugin):
    def on_message(self, ctx):
        # 保存用户消息到记忆
        memory.save(ctx.user_message)
        return ctx
    
    def on_response(self, ctx):
        # 保存AI响应到记忆
        memory.save(ctx.ai_response)
        return ctx

# plugins/recommendation.py
class RecommendationPlugin(Plugin):
    def on_response(self, ctx):
        # 基于记忆推荐相关内容
        recommendations = memory.similar(ctx.ai_response)
        ctx.extra["recommendations"] = recommendations
        return ctx

# plugins/audit.py
class AuditPlugin(Plugin):
    def on_message(self, ctx):
        # 记录消息审计日志
        audit.log(ctx.user_message)
        return ctx
```

**扩展场景**：
- 添加记忆功能 → 实现MemoryPlugin
- 添加推荐功能 → 实现RecommendationPlugin
- 添加审计功能 → 实现AuditPlugin
- 组合多个插件 → 顺序执行

---

### 3.4 工作流扩展

```python
# workflows/collaboration.py
class CollaborationWorkflow(Workflow):
    async def execute(self, task: str, roles: list[Role]) -> str:
        results = []
        for role in roles:
            result = await role.chat(task)
            results.append(result)
        
        # 汇总结果
        summary = await self.coordinator.summarize(results)
        return summary

# workflows/debate.py
class DebateWorkflow(Workflow):
    async def execute(self, topic: str, positions: list[str]) -> str:
        for i, pos in enumerate(positions):
            await self.roles[i].debate(topic, pos)
        
        return self.judge.evaluate(positions)
```

---

### 3.5 存储扩展

```python
# storage/interface.py
class Storage(ABC):
    async def save(self, key: str, value: Any): pass
    async def load(self, key: str) -> Any: pass
    async def delete(self, key: str): pass
    async def search(self, query: str) -> list[Any]: pass

# storage/memory_storage.py
class MemoryStorage(Storage):
    def __init__(self):
        self.data = {}
    
    async def save(self, key, value):
        self.data[key] = value
    
    async def load(self, key):
        return self.data.get(key)

# storage/vector_storage.py
class VectorStorage(Storage):
    async def save(self, key, value):
        embedding = await self.embedding_model.embed(value)
        await self.vector_db.upsert(key, embedding)
    
    async def search(self, query):
        query_emb = await self.embedding_model.embed(query)
        return await self.vector_db.search(query_emb)
```

---

## 四、扩展目录结构

```
qcm-mvp/
├── core/                      # 核心引擎
│   ├── __init__.py
│   ├── role.py               # 角色接口
│   ├── role_manager.py       # 角色管理
│   ├── context.py            # 上下文
│   ├── workflow.py           # 工作流接口
│   └── engine.py             # 主引擎
│
├── roles/                     # 角色实现
│   ├── __init__.py
│   ├── secretary.py           # 秘书长
│   ├── researcher.py          # 研究员
│   ├── architect.py           # 架构师
│   └── custom/                # 自定义角色目录
│       └── example.py
│
├── models/                    # AI模型接入
│   ├── __init__.py
│   ├── interface.py          # 模型接口
│   ├── openai_model.py       # OpenAI
│   ├── claude_model.py       # Claude
│   ├── local_model.py        # 本地模型
│   └── registry.py           # 模型注册
│
├── plugins/                   # 插件系统
│   ├── __init__.py
│   ├── interface.py          # 插件接口
│   ├── manager.py            # 插件管理
│   ├── memory.py             # 记忆插件
│   ├── recommendation.py     # 推荐插件
│   ├── audit.py              # 审计插件
│   └── custom/               # 自定义插件目录
│       └── example.py
│
├── ghost_channel/             # 幽灵通道协议
│   ├── __init__.py
│   ├── sync.py               # 增量同步
│   ├── crypto.py             # 加密传输
│   ├── vector_clock.py       # 因果排序
│   └── audit.py              # 审计追踪
│
├── storage/                   # 存储层
│   ├── __init__.py
│   ├── interface.py          # 存储接口
│   ├── memory.py             # 内存存储
│   ├── vector.py             # 向量存储
│   └── config.py             # 配置存储
│
├── workflows/                 # 工作流
│   ├── __init__.py
│   ├── interface.py          # 工作流接口
│   ├── chat.py               # 闲聊流程
│   ├── collaboration.py      # 协作流程
│   └── analysis.py           # 分析流程
│
├── api/                       # 对外API
│   ├── __init__.py
│   └── routes.py             # Flask路由
│
├── web/                       # 前端
│   ├── index.html
│   └── styles.css
│
├── config/                    # 配置
│   ├── roles.yaml            # 角色配置
│   ├── models.yaml           # 模型配置
│   └── plugins.yaml          # 插件配置
│
├── requirements.txt           # 依赖
├── main.py                    # 入口
└── README.md                 # 说明
```

---

## 五、扩展示例

### 示例1：添加新角色

```python
# roles/custom/coder.py
from core.role import Role

class CoderRole(Role):
    @property
    def name(self) -> str:
        return "coder"
    
    @property
    def description(self) -> str:
        return "专业程序员"
    
    @property
    def system_prompt(self) -> str:
        return """你是一个专业程序员，擅长编写高质量代码。
        你应该：
        - 写出清晰易读的代码
        - 添加必要的注释
        - 考虑边界情况"""
    
    def get_tools(self) -> list[Tool]:
        return [self.code_executor, self.documentation_generator]
```

### 示例2：添加新模型

```python
# models/gemini_model.py
from models.interface import AIModel

class GeminiModel(AIModel):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
    
    @property
    def name(self) -> str:
        return "gemini"
    
    async def chat(self, messages: list[Message]) -> str:
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=messages
        )
        return response.text
```

### 示例3：添加新插件

```python
# plugins/custom/sentiment.py
from plugins.interface import Plugin

class SentimentPlugin(Plugin):
    @property
    def name(self) -> str:
        return "sentiment"
    
    def on_response(self, ctx: Context) -> Context:
        # 分析情感
        sentiment = self.analyze(ctx.ai_response)
        ctx.extra["sentiment"] = sentiment
        return ctx
    
    def analyze(self, text: str) -> dict:
        # 情感分析逻辑
        return {"score": 0.8, "label": "positive"}
```

---

## 六、扩展配置

```yaml
# config.yaml
version: "1.0"

# 角色配置
roles:
  - secretary
  - researcher
  - architect
  # 添加新角色只需添加名称

# 模型配置
models:
  default: openai
  available:
    - openai
    - claude
    - local
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-3.5-turbo

# 插件配置
plugins:
  enabled:
    - memory
    - audit
    # 启用记忆和审计插件
  memory:
    max_history: 50
  audit:
    log_level: info

# 幽灵通道配置
ghost_channel:
  enabled: true
  sync:
    incremental: true
  crypto:
    algorithm: AES-256-GCM
```

---

## 七、扩展原则

| 原则 | 说明 |
|------|------|
| **开闭原则** | 对扩展开放，对修改关闭 |
| **接口标准化** | 所有扩展通过接口实现 |
| **配置驱动** | 通过配置文件添加功能 |
| **插件化** | 功能以插件形式添加 |
| **渐进式** | 从简单开始，逐步扩展 |

---

## 八、下一步

**确认后，我可以开始编写代码**：
1. 创建项目结构
2. 实现核心接口
3. 编写基础角色
4. 添加一个AI模型接入
5. 制作简单界面

**请确认：
1. 这个架构设计是否满足需求？**
2. **是否现在开始编写代码？**
