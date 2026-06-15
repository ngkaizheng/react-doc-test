const fs = require("fs");
const path = require("path");
const { Project, SyntaxKind } = require("ts-morph");

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
// UTILS
// =====================
function cleanExample(str) {
    return str
        .replace(/\r?\n/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}

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
// JSDOC PARSER (unchanged, optional enrichment)
// =====================
function getJSDocByPhysicalSlice(filePath) {
    const result = { description: "", examples: [] };
    const code = fs.readFileSync(filePath, "utf-8");

    const commentMatch = code.match(
        /\/\*\*([\s\S]*?)\*\/\s*(export|function|const|interface|type)/
    );

    if (!commentMatch) return result;

    const lines = commentMatch[1].split("\n");

    let current = [];
    let inExample = false;

    for (let line of lines) {
        let t = line.replace(/^\s*\*\s*/, "").trim();

        if (t.startsWith("@description")) {
            result.description = t.replace("@description", "").trim();
            continue;
        }

        if (t.startsWith("@example")) {
            inExample = true;
            current.push(t.replace("@example", "").trim());
            continue;
        }

        if (t.startsWith("@") && !t.startsWith("@example")) {
            inExample = false;
            if (current.length) result.examples.push(cleanExample(current.join("\n")));
            current = [];
            continue;
        }

        if (inExample) current.push(t);
        else if (!result.description && t) result.description = t;
    }

    if (current.length) result.examples.push(cleanExample(current.join("\n")));

    return result;
}

// =====================
// EXTRACT DEFAULT VALUE
// =====================
function getDefaultValue(param) {
    if (!param) return undefined;
    const decl = param.getDescendantAtPos?.(param.getStart());

    if (param.getInitializer) {
        const init = param.getInitializer();
        if (init) return init.getText();
    }

    return undefined;
}

// =====================
// CORE PROP EXTRACTOR (AST ONLY)
// =====================
function extractProps(sourceFile) {
    const props = [];

    // -------------------------
    // 1. INTERFACE PROPS
    // -------------------------
    const interfaces = sourceFile.getInterfaces();

    for (const i of interfaces) {
        for (const p of i.getProperties()) {
            props.push({
                name: p.getName(),
                type: p.getType().getText(),
                required: !p.hasQuestionToken(),
                description: p.getJsDocs?.()?.map(d => d.getComment()).join(" ") || "",
                defaultValue: undefined,
            });
        }
    }

    // -------------------------
    // 2. TYPE ALIAS PROPS
    // -------------------------
    const typeAliases = sourceFile.getTypeAliases();

    for (const t of typeAliases) {
        const typeNode = t.getTypeNode();

        if (typeNode?.getKind() === SyntaxKind.TypeLiteral) {
            const members = typeNode.getMembers();

            for (const m of members) {
                if (m.getKind() === SyntaxKind.PropertySignature) {
                    props.push({
                        name: m.getName(),
                        type: m.getType().getText(),
                        required: !m.hasQuestionToken(),
                        description: "",
                        defaultValue: undefined,
                    });
                }
            }
        }
    }

    // -------------------------
    // 3. FUNCTION COMPONENT PROPS (MOST IMPORTANT)
    // -------------------------
    const functions = sourceFile.getFunctions();

    for (const fn of functions) {
        const params = fn.getParameters();

        if (params.length === 0) continue;

        const first = params[0];

        const type = first.getType();

        const properties = type.getProperties();

        for (const p of properties) {
            props.push({
                name: p.getName(),
                type: p.getValueDeclaration()?.getType().getText() || "unknown",
                required: true,
                description: "",
                defaultValue: undefined,
            });
        }

        // destructuring defaults (best-effort)
        const text = first.getText();
        const matches = text.matchAll(/(\w+)\s*=\s*([^,}]+)/g);

        for (const m of matches) {
            const name = m[1];
            const value = m[2];

            const existing = props.find(x => x.name === name);

            if (existing) {
                existing.defaultValue = value.trim();
            }
        }
    }

    // -------------------------
    // 4. ENSURE CHILDREN (DERIVED, NOT HARDCODED HACK)
    // -------------------------
    const hasChildren = props.some(p => p.name === "children");

    const text = sourceFile.getFullText();

    if (!hasChildren && text.includes("children")) {
        props.push({
            name: "children",
            type: "React.ReactNode",
            required: false,
            description: "React children node",
            defaultValue: undefined,
        });
    }

    return props;
}

// =====================
// MAIN
// =====================
const files = getFilesRecursively(UI_DIR);
console.log(`🔍 Found ${files.length} components`);

const output = [];

for (const file of files) {
    const sourceFile = project.addSourceFileAtPath(file);

    const name =
        sourceFile.getBaseNameWithoutExtension().replace(".tsx", "");

    const jsdoc = getJSDocByPhysicalSlice(file);

    const props = extractProps(sourceFile);

    output.push({
        name,
        description: jsdoc.description || "Shared UI component",
        examples: jsdoc.examples || [],
        props,
    });
}

// =====================
// WRITE JSON
// =====================
fs.writeFileSync(SPEC_OUTPUT, JSON.stringify(output, null, 2));
console.log("📦 .ui-spec.json generated");

// =====================
// WRITE MD
// =====================
let md = `# Shared UI Components\n\n`;
md += `Auto-generated: ${new Date().toLocaleString()}\n\n`;

for (const c of output) {
    md += `- **${c.name}**: ${c.description}\n`;
}

fs.writeFileSync(MD_OUTPUT, md);
console.log("📝 COMPONENTS.md generated");
console.log("🎉 Done");