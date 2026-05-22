# QCM MVP 最简可行产品计划

## 核心理念
**先做出一个能用的东西，再逐步完善**

---

## MVP目标
创建一个**最简单的多角色AI协作聊天室**

---

## MVP功能清单

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 1. 与AI对话 | P0 | 能发送消息，得到回复 |
| 2. 角色切换 | P0 | 可以在3个角色间切换 |
| 3. 记住上下文 | P1 | 记住之前的对话 |
| 4. 增量同步 | P2 | 只传输变化内容（可选） |

---

## MVP技术栈

```
前端：HTML + JavaScript（最简单）
后端：Python + Flask
AI模型：OpenAI API（或Claude/国产模型）
```

---

## MVP开发步骤

### Day 1: 基础对话

```
任务：搭建Python项目，调用AI API实现对话

代码量：约50行
验收：能发送消息，得到AI回复
```

### Day 2: 角色系统

```
任务：定义3个角色，实现切换

代码量：约30行
验收：可以切换不同角色
```

### Day 3: 记忆功能

```
任务：保存对话历史

代码量：约20行
验收：AI能记住之前的对话
```

### Day 4: 界面优化

```
任务：做一个简单的网页界面

代码量：约50行
验收：可以在浏览器中使用
```

### Day 5: 测试与发布

```
任务：内部测试，打包部署

验收：有一个可以演示的版本
```

---

## MVP代码示例（Python）

```python
# main.py - 最简版本
from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

# 角色定义
ROLES = {
    "secretary": "你是一个专业的秘书长，负责整理和总结",
    "researcher": "你是一个研究员，负责深入分析和提供洞见",
    "architect": "你是一个架构师，负责提供技术方案"
}

# 记忆存储
memory = []

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    role = data.get("role", "secretary")
    message = data.get("message", "")
    
    # 构建上下文
    system_prompt = ROLES.get(role, ROLES["secretary"])
    messages = [{"role": "system", "content": system_prompt}]
    for m in memory[-5:]:  # 只记最近5条
        messages.append(m)
    messages.append({"role": "user", "content": message})
    
    # 调用AI
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    
    # 保存记忆
    memory.append({"role": "user", "content": message})
    memory.append({"role": "assistant", "content": response.choices[0].message.content})
    
    return jsonify({"reply": response.choices[0].message.content})

if __name__ == "__main__":
    app.run(port=5000)
```

---

## MVP前端代码（HTML）

```html
<!DOCTYPE html>
<html>
<head>
    <title>QCM AI聊天室</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        #messages { height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }
        .role-btn { padding: 10px 20px; margin-right: 5px; cursor: pointer; }
        .role-btn.active { background: #007bff; color: white; }
        input { width: 70%; padding: 10px; }
        button { padding: 10px 20px; }
    </style>
</head>
<body>
    <h1>QCM AI聊天室</h1>
    <div>
        <button class="role-btn active" onclick="setRole('secretary')">秘书长</button>
        <button class="role-btn" onclick="setRole('researcher')">研究员</button>
        <button class="role-btn" onclick="setRole('architect')">架构师</button>
    </div>
    <div id="messages"></div>
    <input id="input" placeholder="输入消息..." onkeypress="if(event.key==='Enter')send()">
    <button onclick="send()">发送</button>
    
    <script>
        let currentRole = 'secretary';
        async function setRole(role) {
            currentRole = role;
            document.querySelectorAll('.role-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
        }
        async function send() {
            const input = document.getElementById('input');
            const msg = input.value;
            if (!msg) return;
            
            addMessage('你', msg);
            input.value = '';
            
            const res = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({role: currentRole, message: msg})
            });
            const data = await res.json();
            addMessage(currentRole, data.reply);
        }
        function addMessage(role, text) {
            document.getElementById('messages').innerHTML += `<p><strong>${role}:</strong> ${text}</p>`;
        }
    </script>
</body>
</html>
```

---

## 执行计划

### 今天（如果现在有空）

1. 注册OpenAI账号，获取API Key
2. 安装Python和Flask
3. 运行上面的代码

### 如果今天没空

1. 明天安装环境
2. 后天运行代码
3. 大后天尝试扩展功能

---

## 所需准备

| 项目 | 说明 |
|------|------|
| OpenAI账号 | 用于调用AI API |
| Python环境 | 3.8+版本 |
| Flask | pip install flask |

---

## 确认

1. **现在是否开始？**（如果环境已准备好，可以直接运行）
2. **或者先准备环境？**（安装Python、获取API Key）

**MVP的理念：先跑通，再完善。一个能用的简单版本，胜过完美但无法运行的复杂版本。**
