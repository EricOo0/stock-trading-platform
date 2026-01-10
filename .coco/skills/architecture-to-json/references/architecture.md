# Architecture Extraction Guidelines

This document provides detailed rules and examples for extracting architectural diagrams into a structured JSON format.

## Expected JSON Structure

```json
{
  "diagram": {
    "title": "string",
    "layers": [
      {
        "id": "string",
        "name": "string",
        "level": number,
        "components": [
          {
            "id": "string",
            "name": "string",
            "type": "string",
            "module": "string (optional)",
            "provider": "string (optional)",
            "dependencies": ["string array (optional)"],
            "contains": [/* nested components - MAX 3-4 LEVELS */]
          }
        ]
      }
    ],
    "relationships": [
      {
        "from": "component-id",
        "to": "component-id",
        "type": "calls | uses | depends-on | integrates-with | supports"
      }
    ]
  }
}
```

## Extraction Rules

1. **Identify Layers (Horizontal Sections)**
   - Look for dashed boxes that group components horizontally.
   - Each layer has a name (usually on the left with an icon).
   - Assign level: 1 (top) → 2 (middle) → 3 (bottom).

2. **Extract Components**
   - Component name: Bold text inside boxes.
   - Component type: Text in parentheses below name (e.g., "ui-module", "framework").
   - For nested components (like Tools containing multiple tools), use the `contains` array.
   - **IMPORTANT: Maximum nesting depth is 3-4 levels.**
   - Generate kebab-case IDs from component names.

3. **Nesting Structure Guidelines**
   - Level 1: Layer (e.g., "Console UI", "Agentic System").
   - Level 2: Major component (e.g., "Components", "Tools").
   - Level 3: Sub-component (e.g., "File System Toolset", "Text Editor Tool").
   - Level 4 (if needed): Detailed sub-item (e.g., specific tool functions).
   - **Stop at level 4 - do not nest deeper.**

4. **Identify Relationships**
   - Arrows between components indicate relationships.
   - Bidirectional arrows (↔) = "integrates-with".
   - Downward arrows (↓) = "depends-on".
   - Arrows pointing to specific components = "calls" or "uses".

5. **Special Cases**
   - If a component contains a list of items (like "Tools" containing "File System Toolset", "Text Editor Tool", etc.), put them in the `contains` array.
   - Keep the exact naming from the diagram.
   - For module names in parentheses, add them as a `module` field.
   - If you encounter deeper nesting in the diagram, flatten it to maximum 4 levels.

## Example Nesting

```json
{
   "name": "DeerCode",
   "description": "DeerCode Architecture",
   "layers": [
      {
         "name": "Console UI",
         "type": "presentation",
         "components": [
            {
               "name": "App",
               "type": "ui-module"
            },
            {
               "name": "Theme",
               "type": "ui-module"
            },
            {
               "name": "Components",
               "type": "ui-module"
            }
         ]
      },
      {
         "name": "Agentic System",
         "type": "core",
         "components": [
            {
               "name": "Coding Agent",
               "type": "agent",
               "icon": "robot"
            },
            {
               "name": "Prompt Template",
               "type": "template",
               "icon": "template"
            },
            {
               "name": "Models",
               "type": "model-layer",
               "models": [
                  {
                     "name": "Doubao Seed 1.6",
                     "provider": "bytedance"
                  }
               ]
            },
            {
               "name": "Tools",
               "type": "tool-layer",
               "tools": [
                  {
                     "name": "File System Toolset",
                     "category": "filesystem"
                  },
                  {
                     "name": "Text Editor Tool",
                     "category": "editor"
                  },
                  {
                     "name": "Bash Tool",
                     "category": "command"
                  },
                  {
                     "name": "To-do List Tool",
                     "category": "task"
                  },
                  {
                     "name": "MCP Tool Loader",
                     "category": "extension"
                  }
               ]
            }
         ]
      },
      {
         "name": "Infrastructure",
         "type": "foundation",
         "components": [
            {
               "name": "LangChain",
               "type": "framework"
            },
            {
               "name": "LangGraph",
               "type": "framework"
            },
            {
               "name": "Textual UI",
               "type": "ui-framework"
            },
            {
               "name": "Rich UI",
               "type": "ui-framework"
            },
            {
               "name": "Config",
               "type": "configuration"
            }
         ]
      }
   ]
}
```
