---
description: "Prompt compression workflow: run compress_prompts.py after editing any.instructions.md source file in prompts-uncompressed/."
applyTo: "**/prompts-uncompressed/**"
---

# Prompt Compression Workflow

Source files: `~/.config/Code/User/prompts-uncompressed/*.instructions.md`
Compressed output: `~/.config/Code/User/prompts/*.instructions.md`
Script: `~/.config/Code/User/prompts-uncompressed/compress_prompts.py`

## After editing any `.instructions.md` source file

Run:

```bash
cd ~/.config/Code/User/prompts-uncompressed && pipx run compress_prompts.py
```

This compresses all source prompts → `~/.config/Code/User/prompts/` using a BPE-validated telegraphic pipeline (tiktoken, gpt-4o-mini tokenizer).

## Rules

- **Never edit files in `prompts/` directly** → they are overwritten by script
- **Always edit in `prompts-uncompressed/`** → these are source of truth
- After running script, verify diff if change is significant
- This file itself gets compressed too — keep it concise
