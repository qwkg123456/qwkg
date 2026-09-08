# DeepSeek 聊天 API · 最小调用示例

对应学习计划第 1 周：先 `curl` 打通，再 Java `HttpClient` 调用。

## 1. 准备 Key（不要提交到 Git）

```bash
# macOS / Linux / Git Bash
export DEEPSEEK_API_KEY="sk-xxxxxxxx"

# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-xxxxxxxx"
```

Key 在 [DeepSeek 开放平台](https://platform.deepseek.com/) 创建。

## 2. 先用 curl 验证（30 秒）

```bash
curl https://api.deepseek.com/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -d '{
    "model": "deepseek-v4-flash",
    "messages": [
      {"role": "system", "content": "你是简洁的技术助手。"},
      {"role": "user", "content": "用三句话介绍什么是 RAG"}
    ],
    "stream": false
  }'
```

成功时会看到 JSON，其中 `choices[0].message.content` 是模型回复。

常见模型名：

| model | 说明 |
|-------|------|
| `deepseek-v4-flash` | 更快更省，练手推荐 |
| `deepseek-v4-pro` | 更强，费一点 |

> 若控制台仍显示旧名 `deepseek-chat`，以你平台文档为准，多数仍可兼容。

## 3. Java 程序（无 Maven 依赖）

需要 **JDK 11+**（推荐 17）。

```bash
cd month1-chat-api
javac DeepSeekChatDemo.java
java DeepSeekChatDemo
java DeepSeekChatDemo "用三句话介绍 RAG"
```

## 4. 请求里各字段含义

| 字段 | 作用 |
|------|------|
| `model` | 用哪个模型 |
| `messages` | 对话历史；API **无状态**，多轮要把历史自己带上 |
| `role: system` | 系统设定 |
| `role: user` | 用户问题 |
| `role: assistant` | 模型历史回复（多轮时回传） |
| `stream: false` | 非流式，等全部生成完一次性返回 |

## 5. 下一步

- 自己维护 `List<Message>` 做多轮对话  
- 改 `stream: true` 学流式（SSE）  
- 再上 Spring Boot + Spring AI  

密钥切勿写进代码仓库；可用 `.env` + `.gitignore`。
