// CommonJS MCP Server
const { Server } = require("@modelcontextprotocol/sdk/server/index.js");
const {
    StdioServerTransport,
} = require("@modelcontextprotocol/sdk/server/stdio.js");
const {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} = require("@modelcontextprotocol/sdk/types.js");

const path = require("path");

// 1. Load tool
const SPEC_TOOL_PATH = path.join(__dirname, "scripts", "get-spec.cjs");

let specTool;

try {
    specTool = require(SPEC_TOOL_PATH);

    console.error("[MCP] Loaded tool:", specTool.name || "get_component_spec");
} catch (e) {
    console.error("[MCP] Failed loading get-spec.cjs:", e);
}

// 2. Init MCP server
const server = new Server(
    {
        name: "react-ui-catalog-server",
        version: "1.0.0",
    },
    {
        capabilities: {
            tools: {},
        },
    },
);

// 3. List tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
    console.error("[MCP] Listing tools");

    return {
        tools: [
            {
                name: specTool?.name || "get_component_spec",

                description: specTool?.description || "获取指定共享UI组件规范",

                inputSchema: specTool?.inputSchema || {
                    type: "object",

                    properties: {
                        component_name: {
                            type: "string",
                            description: "组件名称，例如 Button",
                        },
                    },

                    required: ["component_name"],
                },
            },
        ],
    };
});

// 4. Tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    console.error("[MCP] Tool called:", name, args);

    const targetName = specTool?.name || "get_component_spec";

    if (name !== targetName) {
        throw new Error(`Unknown tool: ${name}`);
    }

    try {
        if (!specTool || typeof specTool.handler !== "function") {
            throw new Error("get-spec.cjs missing handler export");
        }

        const xmlOutput = await specTool.handler(args);

        return {
            content: [
                {
                    type: "text",
                    text: xmlOutput,
                },
            ],
        };
    } catch (err) {
        console.error("[MCP] Tool error:", err);

        return {
            content: [
                {
                    type: "text",
                    text: `Error executing spec: ${err.message}`,
                },
            ],

            isError: true,
        };
    }
});

// 5. Start stdio transport
async function run() {
    console.error("[MCP] Starting server...");

    const transport = new StdioServerTransport();

    await server.connect(transport);

    console.error("[MCP] Connected");
}

process.on("uncaughtException", (err) => {
    console.error("[MCP] Uncaught Exception:", err);
});

process.on("unhandledRejection", (err) => {
    console.error("[MCP] Unhandled Rejection:", err);
});

run().catch((error) => {
    console.error("[MCP] Fatal:", error);

    process.exit(1);
});
