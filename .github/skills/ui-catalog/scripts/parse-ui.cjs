const docgen = require("react-docgen-typescript");
const fs = require("fs");
const path = require("path");
const { Project } = require("ts-morph");

// =====================
// CONFIG
// =====================
const UI_DIR = path.resolve(__dirname, "../../../../src/components/shared-ui");
const SPEC_OUTPUT = path.resolve(__dirname, "../.ui-spec.json");
const MD_OUTPUT = path.resolve(__dirname, "../COMPONENTS.md");

// =====================
// TS-MORPH PROJECT
// =====================
const project = new Project({
    tsConfigFilePath: path.resolve(__dirname, "../../../../tsconfig.json"),
});

// =====================
// FILE SCAN
// =====================
function getFilesRecursively(dir) {
    let results = [];
    if (!fs.existsSync(dir)) return results;

    const list = fs.readdirSync(dir);
    for (const file of list) {
        const fullPath = path.join(dir, file);
        const stat = fs.statSync(fullPath);

        if (stat.isDirectory()) {
            results = results.concat(getFilesRecursively(fullPath));
        } else if (
            file.endsWith(".tsx") &&
            !file.includes(".test.") &&
            !file.includes(".spec.")
        ) {
            results.push(fullPath);
        }
    }
    return results;
}

// =====================
// JSDOC PARSER (your original)
// =====================
function getJSDocByPhysicalSlice(filePath) {
    const result = { description: "", examples: [] };
    const code = fs.readFileSync(filePath, "utf-8");

    const commentMatch = code.match(
        /\/\*\*([\s\S]*?)\*\/\s*(interface|type|export\s+(const|function|default))/
    );

    if (!commentMatch) return result;

    const lines = commentMatch[1].split("\n");

    let currentExample = [];
    let isInsideExample = false;

    for (let line of lines) {
        let trimmed = line.replace(/^\s*\*\s*/, "").trim();

        if (trimmed.startsWith("@description")) {
            isInsideExample = false;
            result.description = trimmed.replace("@description", "").trim();
            continue;
        }

        if (trimmed.startsWith("@example")) {
            if (currentExample.length) {
                result.examples.push(currentExample.join("\n"));
                currentExample = [];
            }
            isInsideExample = true;
            let remain = trimmed.replace("@example", "").trim();
            if (remain) currentExample.push(remain);
            continue;
        }

        if (trimmed.startsWith("@")) {
            isInsideExample = false;
            if (currentExample.length) {
                result.examples.push(currentExample.join("\n"));
                currentExample = [];
            }
            continue;
        }

        if (isInsideExample) {
            currentExample.push(trimmed);
        } else if (!result.description && trimmed) {
            result.description = trimmed;
        }
    }

    if (currentExample.length) {
        result.examples.push(currentExample.join("\n"));
    }

    return result;
}

// =====================
// CHILDREN FIX (CRITICAL)
// =====================
function ensureChildren(props, sourceFile) {
    const text = sourceFile.getFullText();

    const hasChildren = props.some(p => p.name === "children");

    if (!hasChildren && (
        text.includes("children") ||
        text.includes("React.FC") ||
        text.includes("PropsWithChildren")
    )) {
        props.push({
            name: "children",
            type: "React.ReactNode",
            required: false,
            description: "Component children",
            defaultValue: undefined,
        });
    }

    return props;
}

// =====================
// GENERIC + DEFAULT VALUE FIX
// =====================
function enrichWithTSMorph(props, sourceFile) {
    const final = [];

    for (const p of props) {
        let type = p.type;

        try {
            const propDecl = sourceFile.getDescendantsOfKind(
                require("ts-morph").SyntaxKind.PropertySignature
            ).find(d => d.getName?.() === p.name);

            if (propDecl) {
                type = propDecl.getType().getText();
            }
        } catch (e) {
            // ignore resolution errors
        }

        final.push({
            ...p,
            type,
        });
    }

    return final;
}

// =====================
// DOCGEN CONFIG
// =====================
const options = {
    savePropValueFromString: true,
    propFilter: (prop) => {
        if (prop.name === "children") return true;
        if (prop.parent) {
            return !prop.parent.fileName.includes("node_modules");
        }
        return true;
    },
};

// =====================
// MAIN
// =====================
const componentFiles = getFilesRecursively(UI_DIR);
console.log(`🔍 Found ${componentFiles.length} components`);

const docs = docgen.parse(componentFiles, options);

const output = docs.map(doc => {
    const file = componentFiles.find(f =>
        f.endsWith(`${doc.displayName}.tsx`) ||
        f.endsWith(`${doc.displayName}/index.tsx`)
    );

    const sourceFile = file ? project.addSourceFileAtPath(file) : null;

    const jsdoc = file ? getJSDocByPhysicalSlice(file) : {
        description: "",
        examples: [],
    };

    let props = doc.props
        ? Object.keys(doc.props).map(name => ({
            name,
            type: doc.props[name].type?.name || "unknown",
            required: doc.props[name].required ?? false,
            description: doc.props[name].description || "",
            defaultValue: doc.props[name].defaultValue || undefined,
        }))
        : [];

    if (sourceFile) {
        props = ensureChildren(props, sourceFile);
        props = enrichWithTSMorph(props, sourceFile);
    }

    return {
        name: doc.displayName,
        description: jsdoc.description || "Shared UI component",
        examples: jsdoc.examples,
        props,
    };
});

// =====================
// WRITE JSON
// =====================
fs.writeFileSync(
    SPEC_OUTPUT,
    JSON.stringify(output, null, 2),
    "utf-8"
);

console.log("📦 .ui-spec.json generated");

// =====================
// WRITE MD
// =====================
let md = `# Shared UI Components\n\n`;
md += `Auto-generated: ${new Date().toLocaleString()}\n\n`;

for (const c of output) {
    md += `- **${c.name}**: ${c.description}\n`;
}

fs.writeFileSync(MD_OUTPUT, md, "utf-8");

console.log("📝 COMPONENTS.md generated");
console.log("🎉 Done");