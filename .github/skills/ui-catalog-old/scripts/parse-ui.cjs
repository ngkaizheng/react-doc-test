const docgen = require('react-docgen-typescript');
const fs = require('fs');
const path = require('path');

// 🎯 配置你共享组件库的根目录
const UI_DIR = path.resolve(__dirname, '../../../../src/components/shared-ui');
const SPEC_OUTPUT = path.resolve(__dirname, '../.ui-spec.json');
const MD_OUTPUT = path.resolve(__dirname, '../COMPONENTS.md');

// 1. 递归获取目录下所有的 .tsx 文件
function getFilesRecursively(dir) {
    let results = [];
    if (!fs.existsSync(dir)) return results;
    const list = fs.readdirSync(dir);
    list.forEach((file) => {
        const fullPath = path.join(dir, file);
        const stat = fs.statSync(fullPath);
        if (stat && stat.isDirectory()) {
            results = results.concat(getFilesRecursively(fullPath));
        } else if (file.endsWith('.tsx') && !file.includes('.test.') && !file.includes('.spec.')) {
            results.push(fullPath);
        }
    });
    return results;
}

// 2. 物理切片提取头部 JSDoc (100% 稳定拿到 @description 和 @example)
function getJSDocByPhysicalSlice(filePath) {
    const result = { description: "", examples: [] };
    const code = fs.readFileSync(filePath, 'utf-8');

    // 匹配紧贴着 interface/type/export 的 /** ... */ 注释
    const commentMatch = code.match(/\/\*\*([\s\S]*?)\*\/\s*(interface|type|export\s+(const|function|default))/);
    if (!commentMatch) return result;

    const lines = commentMatch[1].split('\n');
    let currentExample = [];
    let isInsideExample = false;

    for (let line of lines) {
        let trimmed = line.replace(/^\s*\*\s*/, '').trim();

        if (trimmed.startsWith('@description')) {
            isInsideExample = false;
            result.description = trimmed.replace('@description', '').trim();
            continue;
        }
        if (trimmed.startsWith('@example')) {
            if (currentExample.length > 0) {
                result.examples.push(currentExample.join('\n'));
                currentExample = [];
            }
            isInsideExample = true;
            let remain = trimmed.replace('@example', '').trim();
            if (remain) currentExample.push(remain);
            continue;
        }
        if (trimmed.startsWith('@')) {
            isInsideExample = false;
            if (currentExample.length > 0) {
                result.examples.push(currentExample.join('\n'));
                currentExample = [];
            }
            continue;
        }

        if (isInsideExample) {
            currentExample.push(trimmed);
        } else if (!result.description && trimmed && !trimmed.startsWith('@component')) {
            result.description = trimmed;
        }
    }

    if (currentExample.length > 0) {
        result.examples.push(currentExample.join('\n'));
    }
    return result;
}

// 执行扫描与解析
const componentFiles = getFilesRecursively(UI_DIR);
console.log(`🔍 扫描到 ${componentFiles.length} 个 UI 组件，开始深度解析...`);

const options = {
    savePropValueFromString: true,
    propFilter: (prop) => {
        if (prop.parent) {
            // 100% 过滤第三方依赖和 React 原生的 1000+ 行属性
            return !prop.parent.fileName.includes('node_modules');
        }
        return true;
    },
};

const docs = docgen.parse(componentFiles, options);

const output = docs.map(doc => {
    const matchedFile = componentFiles.find(f => f.endsWith(`${doc.displayName}.tsx`) || f.endsWith(`${doc.displayName}/index.tsx`));
    const jsdoc = matchedFile ? getJSDocByPhysicalSlice(matchedFile) : { description: "", examples: [] };

    return {
        name: doc.displayName,
        description: jsdoc.description || "共享 UI 组件",
        examples: jsdoc.examples,
        props: Object.keys(doc.props).map(propName => ({
            name: propName,
            type: doc.props[propName].type.name,
            required: doc.props[propName].required,
            description: doc.props[propName].description,
        }))
    };
});

// 💾 产物一：写入用于给 AI 精准查询的 JSON 文件
fs.writeFileSync(
    SPEC_OUTPUT,
    JSON.stringify(output, null, 2, 'utf-8')
);
console.log('📦 1. 瘦身版数据燃料 .ui-spec.json 生成成功！');


// 🚀 产物二：自动生成/更新给 AI 当作导航地图的 COMPONENTS.md
let mdContent = `# 项目共享组件库索引 (Shared UI Components)\n\n`;
mdContent += `> ⚠️ 此文件由脚本自动维护，请勿手动修改。最后更新时间: ${new Date().toLocaleString()}\n\n`;
mdContent += `当前项目中可用的共享组件列表如下：\n\n`;

output.forEach(comp => {
    mdContent += `- **${comp.name}**: ${comp.description}\n`;
});

fs.writeFileSync(MD_OUTPUT, mdContent, 'utf-8');
console.log('📝 2. AI 导航地图 COMPONENTS.md 自动更新成功！');
console.log('🎉 所有流程闭环完成！');