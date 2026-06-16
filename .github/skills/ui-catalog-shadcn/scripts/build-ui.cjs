const { execSync } = require("child_process");
const path = require("path");

function run(cmd) {
    console.log("\n====================================");
    console.log("▶️ Running:", cmd);
    console.log("====================================\n");

    execSync(cmd, {
        stdio: "inherit",
        cwd: process.cwd()
    });
}

// =====================
// STEP 1: UI SPEC + MD (ts-morph: includes children prop, no more react-docgen-typescript blind spots)
// =====================
run("node .github\\skills\\ui-catalog\\scripts\\generate-spec-tsmorph.cjs");

// =====================
// STEP 2: INDEX GENERATION (ts-morph)
// =====================
run("node .github\\skills\\ui-catalog\\scripts\\generate-index-tsmorph.cjs");

// =====================
// DONE
// =====================
console.log("\n🎉 UI BUILD COMPLETE (spec + index generated)\n");