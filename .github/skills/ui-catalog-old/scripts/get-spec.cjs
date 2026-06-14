// get-spec.cjs (极致优化 Token 版)
const fs = require('fs');
const path = require('path');

const componentName = process.argv[2];

if (!componentName) {
    console.log("<error>Missing component name</error>");
    process.exit(1);
}

const specPath = path.resolve(__dirname, '../.ui-spec.json');

if (!fs.existsSync(specPath)) {
    console.log("<error>Missing .ui-spec.json, run npm run build:spec</error>");
    process.exit(1);
}

try {
    const specData = JSON.parse(fs.readFileSync(specPath, 'utf-8'));
    const targetName = componentName.replace('.tsx', '').toLowerCase();

    const matchedComponent = specData.find(item => item.name.toLowerCase() === targetName);

    if (!matchedComponent) {
        console.log(`<error>Component '${componentName}' not found</error>`);
        process.exit(0);
    }

    // 1. 紧凑格式化 Props (用 ? 表示可选，去掉多余缩进和连字符)
    let propsStr = "";
    matchedComponent.props.forEach(p => {
        const optionalSign = p.required ? "" : "?";
        // 如果你有把属性描述翻译成英文，这里可以换成英文，不换也行，因为中文单行注释很短
        const desc = p.description ? ` // ${p.description}` : "";

        // 移除类型里的 " | undefined" 字符，因为 ? 已经代表了 undefined，再次缩减 Token
        let cleanType = p.type.replace(' | undefined', '').replace(/\s*\|\s*/g, '|');

        propsStr += `${p.name}${optionalSign}: ${cleanType}${desc}\n`;
    });

    // 2. 紧凑格式化 Examples (剥离描述文本，只留纯代码，且不留空行)
    let examplesStr = "";
    matchedComponent.examples.forEach(ex => {
        // 通过正则剥离人为写的 "Few-Shot:" "1. xxx" 以及普通文本描述，只提取尖括号包裹的 React 代码
        const codeOnlyMatch = ex.match(/<[\s\S]*>/);
        const cleanEx = codeOnlyMatch ? codeOnlyMatch[0].trim() : ex.trim();
        examplesStr += `<ex><![CDATA[${cleanEx}]]></ex>\n`;
    });

    // 3. 组装为极致压缩的 XML 结构
    const xmlOutput =
        `<comp name="${matchedComponent.name}">
<desc>${matchedComponent.description}</desc>
<props>
${propsStr.trim()}
</props>
${examplesStr.trim()}
</comp>`;

    console.log(xmlOutput);

} catch (e) {
    console.log(`<error>Failed to read spec: ${e.message}</error>`);
}