import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// 1. 直接动态引入你现有的 cjs 脚本
// 确保你的 get-spec.cjs 里面导出了 name, description, inputSchema 和 handler
const SPEC_TOOL_PATH = path.join(__dirname, "scripts", "get-spec.cjs");
let specTool;

try {
    // 用 createRequire 或者直接动态 import 引入 CJS
    import(SPEC_TOOL_PATH).then((mod) => {
        specTool = mod.default || mod;
    });
} catch (e) {
    console.error("加载 get-spec.cjs 失败:", e);
}

// 2. 初始化 MCP 服务
const server = new Server(
    { name: "react-ui-catalog-server", version: "1.0.0" },
    { capabilities: { tools: {} } }
);

// 3. 告诉 Copilot Agent 你有哪些原生工具（大模型在进场时会先读这里）
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: specTool?.name || "get_component_spec",
                description: `${specTool?.description || "获取指定共享UI组件的紧凑Token优化版XML规范 contract。"} \nFew-Shots: ${JSON.stringify(specTool?.fewShot || "")}`,
                inputSchema: specTool?.inputSchema || {
                    type: "object",
                    properties: {
                        component_name: { type: "string", description: "严格区分大小写的组件名称（例如: Button）" }
                    },
                    required: ["component_name"]
                }
            }
        ]
    };
});

// 4. 当 Agent 决定调用工具时的执行路由（底层自动打通，不再走 Bash 终端）
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    if (name === (specTool?.name || "get_component_spec")) {
        try {
            // 直接执行你的 cjs 里的业务逻辑
            const xmlOutput = await specTool.handler(args);
            return {
                content: [{ type: "text", text: xmlOutput }]
            };
        } catch (err) {
            return {
                content: [{ type: "text", text: `Error executing spec: ${err.message}` }],
                isError: true
            };
        }
    }
    throw new Error(`未知工具: ${name}`);
});

// 5. 启动标准输入输出 Stdio 传输通道
const transport = new StdioServerTransport();
await server.connect(transport);