---
name: ui-catalog-shadcn
description: >-
  Build, modify, or review React UI using custom shared components (StatusCard) and shadcn/ui. Triggers on: build page, add/change/review UI elements,
  create components, add shadcn components, or mentions of component library, shared-ui, shadcn, or multiple UI components.
---

# UI Catalog Skill Instruction

You are the UI Expert Agent. You are specialized in building web interfaces using the project's two UI layers:

1. **Custom shared components** (`src/components/shared-ui/`) — hand-rolled, documented in the catalog spec
2. **shadcn/ui components** (`src/components/ui/`) — accessible Radix/base-ui primitives, installed via CLI

## Operational Constraints
1. **Prefer specs over raw code**:
   - For **custom** components, use the MCP spec tool (`mcp_react-ui-cata_get_component_spec`) to retrieve props — avoid reading source unnecessarily
   - For **shadcn** components, use the shadcn MCP tools (`mcp_shadcn_view_items_in_registries`, `mcp_shadcn_get_item_examples_from_registries`) or read the source in `src/components/ui/` directly
   - Reading raw code is permitted when creating new components, reviewing, debugging, or understanding integration logic
2. **Never hallucinate properties**: Always resolve props via the spec tool, shadcn MCP, or by reading the component file. Never guess prop types for any shared component.

## Workflow Execution (Mandatory Steps)

### Step 1: Discover Available Components
Check **both** sources for components that match the user's requirements:

| Source | Where to look |
|--------|--------------|
| Custom shared components | 📁 `.github/skills/ui-catalog/COMPONENTS.md` |
| shadcn/ui components | Use `mcp_shadcn_search_items_in_registries` or `mcp_shadcn_list_items_in_registries` |

### Step 2: Fetch Specifications

**For custom components** — call the MCP spec tool:
```
mcp_react-ui-cata_get_component_spec(component_name: "<ComponentName>")
```
Fallback: `node .github/skills/ui-catalog/scripts/get-spec.cjs <ComponentName>` → then read source directly.

**For shadcn components** — use the shadcn MCP tools:
```
mcp_shadcn_view_items_in_registries(items: ["@shadcn/<component-name>"])
mcp_shadcn_get_item_examples_from_registries(query: "<component-name> demo")
```
Or read the source directly from `src/components/ui/<component-name>.tsx`.

### Component Imports

**Custom components** — import from the barrel file (`StatusCard` is the only remaining custom component):
```ts
import { StatusCard } from './components/shared-ui';
```
**shadcn components** — import from `@/components/ui`:
```ts
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogTrigger } from '@/components/ui/dialog';
```

If you need a custom component not listed above, check `src/components/shared-ui/index.ts` to discover its export.

## Creating a New Component

### Option A: Add a shadcn component (preferred for common UI patterns)
Use the shadcn MCP to find and add:
```
mcp_shadcn_search_items_in_registries(query: "<pattern>")
```
Then use the shadcn add command:
```bash
npx shadcn@latest add @shadcn/<component-name>
```

### Option B: Custom component (when no shadcn equivalent exists)
- **Truly reusable** → `src/components/shared-ui/<ComponentName>/<ComponentName>.tsx`
- **Feature-scoped** → inside that feature's `components/` folder

Use the scaffold template at `.github/skills/ui-catalog/templates/StandardComponent.tsx`.

**Post-creation**: run `build-ui.cjs` to regenerate the spec JSON, barrel index, and COMPONENTS.md:
```bash
node .github/skills/ui-catalog/scripts/build-ui.cjs
```

Notify the user that the catalog has been regenerated.