const fs = require('fs');
const path = require('path');

async function runSpecLogic(args) {
    const compName = args.component_name;
    if (!compName) return "<error>Missing component_name</error>";

    const jsonPath = path.join(__dirname, '..', '.ui-spec.json');

    try {
        const rawData = fs.readFileSync(jsonPath, 'utf8');
        const specData = JSON.parse(rawData);

        // 由于 .ui-spec.json 是数组，直接 find 即可
        const matched = specData.find(item =>
            item.name && item.name.toLowerCase() === compName.toLowerCase()
        );

        if (!matched) {
            const available = specData.map(i => i.name).join(', ');
            return `<error>Component '${compName}' not found. Available: ${available}</error>`;
        }

        // 格式化 props
        const propsBlock = matched.props ? matched.props.map(p =>
            `${p.name}${p.required ? '' : '?'}: ${p.type}${p.description ? ' // ' + p.description : ''}`
        ).join('\n') : "";

        // 格式化 examples
        const exBlock = matched.examples ? matched.examples.map(ex =>
            `<ex><![CDATA[${ex.trim()}]]></ex>`
        ).join('\n') : "";

        return `<comp name="${matched.name}">\n<props>\n${propsBlock}\n</props>\n${exBlock}\n</comp>`;
    } catch (error) {
        return `<error>Failed to process spec: ${error.message}</error>`;
    }
}

// 导出与 CLI 执行逻辑
module.exports = {
    name: "get_component_spec",
    description: "获取组件紧凑 XML 合约",
    inputSchema: { type: "object", properties: { component_name: { type: "string" } }, required: ["component_name"] },
    handler: async (args) => runSpecLogic(args)
};

if (require.main === module) {
    runSpecLogic({ component_name: process.argv[2] }).then(console.log);
}