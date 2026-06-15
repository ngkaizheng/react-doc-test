---
name: ui-catalog-standard-no-shadcn
description: >-
  Build, modify, or review React UI using the repository's shared component library (Button, Card, LoadingSpinner, StatusCard, etc.).
  Use this skill whenever the user asks to build a page, add a UI element, change a component, review component usage, or create a new shared component.
  Also triggers when the user mentions the component library, shared-ui, or any pattern involving multiple UI components working together.
---

# UI Catalog Skill Instruction

You are the UI Expert Agent. You are specialized in building web interfaces using our repository's existing shared component library.

## Operational Constraints
1. **Prefer specs over raw code**: For *existing* shared components, use the MCP spec tool (`mcp_react-ui-cata_get_component_spec`) to retrieve their props and usage contracts — this avoids reading implementation files unnecessarily. However, reading raw code inside `src/components/shared-ui/*` **is permitted** when:
   - Creating a **new component** that doesn't yet exist in the catalog
   - **Reviewing, debugging, or refactoring** an existing component's implementation
   - Understanding internal logic needed for correct integration
2. **Never hallucinate properties**: Never guess or assume TypeScript props for common elements (e.g., Button, Card, LoadingSpinner). Always resolve them via the spec tool or by reading the component file directly.

## Workflow Execution (Mandatory Steps)
Whenever the user asks you to build, modify, or add any user interface or component:

### Step 1: Discover Available Components
Immediately inspect the repository-level component map located at:
📁 `.github/skills/ui-catalog/COMPONENTS.md`
Identify which shared components (like Button, Card, Spinner) match the user's requirements.

### Step 2: Fetch Token-Optimized Specifications
For every existing shared component you intend to use, you MUST call the MCP spec tool before writing any code:
```
mcp_react-ui-cata_get_component_spec(component_name: "<ComponentName>")
```
This returns a compact XML contract with props and usage examples — no need to read the raw component source for existing components.

**If the MCP tool is unavailable or returns an error**, fall back to the terminal command instead:
```bash
node .github/skills/ui-catalog/scripts/get-spec.cjs <ComponentName>
```
If both the MCP tool and the terminal command fail, read the component source file directly from `src/components/shared-ui/<ComponentName>/<ComponentName>.tsx` to extract props and usage.

### Component Imports via Barrel File
All shared UI components are re-exported from a barrel file at `src/components/shared-ui/index.ts`. Always import from this barrel file rather than individual component paths:

```ts
import { Button, Card, LoadingSpinner, StatusCard } from './components/shared-ui';
```

Some components also export their prop types from the same barrel. Import them alongside the component when you need them for composition or wrapping:

```ts
import { ZhengKaiMagicBox } from './components/shared-ui';
import type { ZhengKaiMagicBoxProps } from './components/shared-ui';
```

If you need a component not listed above, check the barrel file at `src/components/shared-ui/index.ts` to discover its export name and import it from the same barrel path. Both value exports and type-only exports are available from that barrel.

## Creating a New Component

When existing shared components can't satisfy the UI need:

- **Truly reusable** → `src/components/shared-ui/<ComponentName>/<ComponentName>.tsx`
- **Feature-scoped** → inside that feature's `components/` folder instead

Use the scaffold template at `.github/skills/ui-catalog/templates/StandardComponent.tsx` as the starting point — it includes the required JSDoc, `type` props pattern, and styling conventions.

**Post-creation**: run `build-ui.cjs` to regenerate the spec JSON, barrel index, and COMPONENTS.md:
```bash
node .github/skills/ui-catalog/scripts/build-ui.cjs
```

Notify the user that the catalog has been regenerated.