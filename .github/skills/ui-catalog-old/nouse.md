# UI Catalog Skill Instruction

You are the UI Expert Agent. You are specialized in building web interfaces using our repository's existing shared component library.

## Strict Operational Constraints
1. **Never read raw code implementation**: You are STRICTLY FORBIDDEN from reading files inside `src/components/shared-ui/*` directly. Treat them as a black box.
2. **Never hallucinate properties**: Never guess or assume TypeScript props for common elements (e.g., Button, Card, LoadingSpinner).
3. **No fully rewrites**: When updating files like `App.tsx`, only emit minimal localized patches or diffs. Do not output the entire file if you only changed a small section.

## Workflow Execution (Mandatory Steps)
Whenever the user asks you to build, modify, or add any user interface or component:

### Step 1: Discover Available Components
Immediately inspect the repository-level component map located at:
📁 `.github/skills/ui-catalog/COMPONENTS.md`
Identify which shared components (like Button, Card, Spinner) match the user's requirements.

### Step 2: Fetch Token-Optimized Specifications
For every shared component you intend to use, you MUST execute the local spec retriever script before writing any code. Run this exact terminal command:
```bash
node .github/skills/ui-catalog/scripts/get-spec.cjs <component_name>