# Claude Code with Microsoft Foundry Setup Guide

**For: Developers sharing the Foundry account**
**Created: 2025-12-17**

---

## Overview

This guide configures Claude Code CLI to use Claude Opus 4.5 via Microsoft Azure AI Foundry. This gives you access to Anthropic's most intelligent model through Azure's infrastructure.

## Prerequisites

- Node.js 18+ installed
- Claude Code CLI installed (`npm install -g @anthropic-ai/claude-code`)
- API key provided by account owner

## Configuration Steps

### Step 1: Set Environment Variables

Add these lines to your shell profile (`~/.zshrc` for macOS/Linux with zsh, or `~/.bashrc` for bash):

```bash
# Microsoft Foundry for Claude Opus 4.5
export CLAUDE_CODE_USE_FOUNDRY=1
export ANTHROPIC_FOUNDRY_API_KEY="YOUR_API_KEY_HERE"
export ANTHROPIC_FOUNDRY_RESOURCE="vishal-sachdev-claude-resource"
export ANTHROPIC_DEFAULT_OPUS_MODEL="claude-opus-4-5"
export ANTHROPIC_MODEL="claude-opus-4-5"
```

**Important**: Replace `YOUR_API_KEY_HERE` with the API key provided to you.

### Step 2: Reload Your Shell

```bash
source ~/.zshrc   # or source ~/.bashrc
```

### Step 3: Configure Claude Code Settings

Create or edit `~/.claude/settings.json`:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "model": "claude-opus-4-5"
}
```

If the file already exists, just ensure the `"model"` key is set to `"claude-opus-4-5"`.

### Step 4: Verify Configuration

Launch Claude Code and run:

```bash
claude
```

Then use the `/status` command inside Claude Code to verify:
- Model shows `claude-opus-4-5`
- Provider shows Microsoft Foundry

## Environment Variables Reference

| Variable | Value | Description |
|----------|-------|-------------|
| `CLAUDE_CODE_USE_FOUNDRY` | `1` | Enables Microsoft Foundry backend |
| `ANTHROPIC_FOUNDRY_API_KEY` | `<your-key>` | Your Azure AI Foundry API key |
| `ANTHROPIC_FOUNDRY_RESOURCE` | `vishal-sachdev-claude-resource` | Shared Azure resource name |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | `claude-opus-4-5` | Default model for Opus requests |
| `ANTHROPIC_MODEL` | `claude-opus-4-5` | Primary model to use |

## Optional: Use Different Models

You can switch between models by changing `ANTHROPIC_MODEL`:

| Model | Value |
|-------|-------|
| Claude Opus 4.5 (most capable) | `claude-opus-4-5` |
| Claude Sonnet 4.5 (balanced) | `claude-sonnet-4-5` |
| Claude Haiku 4.5 (fastest) | `claude-haiku-4-5` |

## Troubleshooting

### "Authentication failed" errors
- Verify your API key is correct (no extra spaces)
- Ensure `ANTHROPIC_FOUNDRY_RESOURCE` matches exactly: `vishal-sachdev-claude-resource`

### Model not found
- Check that the model name is exactly `claude-opus-4-5` (not `opus-4.5` or similar)
- Run `/status` in Claude Code to see current configuration

### Environment variables not loading
- Ensure you sourced your shell profile: `source ~/.zshrc`
- Open a new terminal window
- Verify with: `echo $CLAUDE_CODE_USE_FOUNDRY` (should output `1`)

## Quick Setup Script

Save this as `setup-claude-foundry.sh` and run it:

```bash
#!/bin/bash

# Prompt for API key
read -p "Enter your Foundry API key: " API_KEY

# Add to shell profile
PROFILE="$HOME/.zshrc"
if [ -f "$HOME/.bashrc" ] && [ ! -f "$HOME/.zshrc" ]; then
    PROFILE="$HOME/.bashrc"
fi

cat >> "$PROFILE" << EOF

# Microsoft Foundry for Claude Opus 4.5
export CLAUDE_CODE_USE_FOUNDRY=1
export ANTHROPIC_FOUNDRY_API_KEY="$API_KEY"
export ANTHROPIC_FOUNDRY_RESOURCE="vishal-sachdev-claude-resource"
export ANTHROPIC_DEFAULT_OPUS_MODEL="claude-opus-4-5"
export ANTHROPIC_MODEL="claude-opus-4-5"
EOF

# Create Claude settings directory
mkdir -p "$HOME/.claude"

# Create settings file if it doesn't exist
if [ ! -f "$HOME/.claude/settings.json" ]; then
    echo '{"model": "claude-opus-4-5"}' > "$HOME/.claude/settings.json"
fi

echo "Setup complete! Run: source $PROFILE"
```

## AI Agent Configuration

If your AI agent (e.g., Cursor, Continue, or custom agent) needs to use Claude via Foundry, configure it with:

```
Base URL: https://vishal-sachdev-claude-resource.services.ai.azure.com/anthropic/v1
API Key: <your-provided-key>
Model: claude-opus-4-5
```

For agents using the Anthropic SDK directly:

```python
import anthropic

client = anthropic.Anthropic(
    base_url="https://vishal-sachdev-claude-resource.services.ai.azure.com/anthropic/v1",
    api_key="YOUR_API_KEY_HERE"
)

message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=4096,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({
    baseURL: 'https://vishal-sachdev-claude-resource.services.ai.azure.com/anthropic/v1',
    apiKey: 'YOUR_API_KEY_HERE',
});

const message = await client.messages.create({
    model: 'claude-opus-4-5',
    max_tokens: 4096,
    messages: [{ role: 'user', content: 'Hello!' }],
});
```

---

## Sources

- [Claude Code on Azure AI Foundry - Official Docs](https://code.claude.com/docs/en/azure-ai-foundry)
- [Claude Code on Microsoft Foundry - Official Docs](https://code.claude.com/docs/en/microsoft-foundry)
- [Deploy Claude models in Microsoft Foundry - Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/use-foundry-models-claude)
- [Claude Code + Microsoft Foundry Enterprise Setup - Microsoft DevBlogs](https://devblogs.microsoft.com/all-things-azure/claude-code-microsoft-foundry-enterprise-ai-coding-agent-setup/)
- [Claude in Microsoft Foundry - Anthropic Docs](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry)
