# Installing Superpowers for Codex

Quick setup to enable superpowers skills in Codex.

## Installation

1. **Clone superpowers repository**:
   ```bash
   mkdir -p .coco/superpowers
   cd .coco/superpowers
   git clone https://github.com/obra/superpowers.git .
   ```

2. **Create personal skills directory**:
   ```bash
   mkdir -p .coco/skills
   ```

3. **Update .coco/AGENTS.md** to include this superpowers section:
   ```markdown
   ## Superpowers System

   <EXTREMELY_IMPORTANT>
   You have superpowers. Superpowers teach you new skills and capabilities. RIGHT NOW run: `.coco/superpowers/.coco/superpowers-codex bootstrap` and follow the instructions it returns.
   </EXTREMELY_IMPORTANT>
   ```

## Verification

Test the installation:
```bash
~/.coco/superpowers/.coco/superpowers-codex bootstrap
```

You should see skill listings and bootstrap instructions. The system is now ready for use.