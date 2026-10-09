import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;

/**
 * DeepSeek 聊天 API 最小示例（JDK 11+ HttpClient，无第三方依赖）。
 *
 * 运行前：
 *   export DEEPSEEK_API_KEY="你的密钥"
 *
 * 运行：
 *   javac DeepSeekChatDemo.java
 *   java DeepSeekChatDemo
 *   java DeepSeekChatDemo "用三句话介绍什么是 RAG"
 */
public class DeepSeekChatDemo {

    private static final String API_URL = "https://api.deepseek.com/chat/completions";
    // 省钱/练手可用 flash；要更强可改 deepseek-v4-pro
    private static final String MODEL = "deepseek-v4-flash";

    public static void main(String[] args) throws Exception {
        String apiKey = System.getenv("DEEPSEEK_API_KEY");
        if (apiKey == null || apiKey.isBlank()) {
            System.err.println("请先设置环境变量 DEEPSEEK_API_KEY");
            System.err.println("  Windows PowerShell: $env:DEEPSEEK_API_KEY=\"你的密钥\"");
            System.err.println("  macOS/Linux:        export DEEPSEEK_API_KEY=\"你的密钥\"");
            System.exit(1);
        }

        String userMessage = args.length > 0 ? args[0] : "你好，请用一句话介绍你自己。";

        // 注意：JSON 里引号需转义；正式项目请用 Jackson / Gson
        String body = """
                {
                  "model": "%s",
                  "messages": [
                    {"role": "system", "content": "你是简洁的技术助手。"},
                    {"role": "user", "content": "%s"}
                  ],
                  "stream": false
                }
                """.formatted(MODEL, escapeJson(userMessage));

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(API_URL))
                .timeout(Duration.ofSeconds(60))
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer " + apiKey)
                .POST(HttpRequest.BodyPublishers.ofString(body, StandardCharsets.UTF_8))
                .build();

        HttpClient client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(20))
                .build();

        System.out.println("请求中...");
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("HTTP 状态: " + response.statusCode());
        System.out.println("原始响应:");
        System.out.println(response.body());

        if (response.statusCode() == 200) {
            String content = extractAssistantContent(response.body());
            if (content != null) {
                System.out.println();
                System.out.println("助手回复:");
                System.out.println(content);
            }
        } else {
            System.err.println("调用失败，请检查 Key、余额、模型名是否正确。");
        }
    }

    private static String escapeJson(String s) {
        return s.replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }

    /** 极简解析：从 choices[0].message.content 抠出文本（示例用）。 */
    private static String extractAssistantContent(String json) {
        String marker = "\"content\":\"";
        // 优先找 message 里的 content（避免 reasoning_content）
        int msgIdx = json.indexOf("\"message\"");
        int from = msgIdx >= 0 ? json.indexOf(marker, msgIdx) : json.indexOf(marker);
        if (from < 0) {
            return null;
        }
        from += marker.length();
        StringBuilder sb = new StringBuilder();
        boolean escape = false;
        for (int i = from; i < json.length(); i++) {
            char c = json.charAt(i);
            if (escape) {
                switch (c) {
                    case 'n' -> sb.append('\n');
                    case 't' -> sb.append('\t');
                    case 'r' -> sb.append('\r');
                    case '"' -> sb.append('"');
                    case '\\' -> sb.append('\\');
                    default -> sb.append(c);
                }
                escape = false;
            } else if (c == '\\') {
                escape = true;
            } else if (c == '"') {
                break;
            } else {
                sb.append(c);
            }
        }
        return sb.toString();
    }
}
