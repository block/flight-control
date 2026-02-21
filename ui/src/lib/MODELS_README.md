# Updating Provider and Model Lists

The file `models.js` drives the Provider and Model dropdowns in the Job and Run forms. It requires manual updates when new models are released or Goose adds provider support.

## How the model list works

Provider keys in `models.js` must match Goose's `--provider` flag values exactly (e.g., `openai`, `anthropic`, `google`, `ollama`). Models are grouped by tier for the `<optgroup>` UI. When a user switches providers, the model dropdown repopulates and defaults to the provider's `default` value.

Goose passes the provider and model to the LLM API, so a model must be valid on **both** sides:

1. **Goose must recognize the provider** — it maps provider names to API formats/endpoints
2. **The model must exist on the provider's API** — and the user's API key must have access

## Three sources to cross-reference

### 1. Goose source code (provider support)

Goose maintains a `KNOWN_MODELS` list per provider in its Rust source:

```
github.com/block/goose → crates/goose/src/providers/<provider>.rs
```

Each file defines `KNOWN_MODELS`, `DEFAULT_MODEL`, and `FAST_MODEL`. These are the models shown in `goose configure`, but Goose accepts **any** model string via `--provider` and `--model` flags — the known list is just for the interactive config UI.

**When to check:** After a Goose version upgrade. New providers or model list changes happen here.

**Quick check from a worker container:**
```bash
docker exec flight-control-worker-1 goose --version
```

There is no `goose models` CLI command. Check the source on GitHub or run `goose configure` interactively.

### 2. Provider API docs (model availability)

Models are released by providers independently of Goose. A model can exist on the API but not be in Goose's known list (and still work fine).

| Provider | Model list reference |
|----------|---------------------|
| OpenAI | https://platform.openai.com/docs/models |
| Anthropic | https://docs.anthropic.com/en/docs/about-claude/models |
| Google | https://ai.google.dev/gemini-api/docs/models |
| xAI | https://docs.x.ai/docs/models |
| OpenRouter | https://openrouter.ai/models (dynamic, fetched at runtime by Goose) |
| Ollama | `ollama list` on the host (local models only) |

### 3. Actual API key access (what your key can use)

Not all models are available to all API keys. Tier restrictions, waitlists, and regional availability apply. The most reliable way to discover your available models:

**OpenAI:**
```bash
curl -s -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models | jq '.data[].id' | sort
```

**Anthropic:**
```bash
curl -s -H "x-api-key: $ANTHROPIC_API_KEY" -H "anthropic-version: 2023-06-01" https://api.anthropic.com/v1/models | jq '.data[].id'
```

**Or just try it** — Goose returns a helpful error listing available models when you use one that doesn't exist (this is how the current OpenAI list was validated).

## Update procedure

1. **Check for new models** from the provider docs or API (see above)
2. **Verify the provider is supported in Goose** — check `crates/goose/src/providers/init.rs` in the Goose repo for the registered provider list
3. **Edit `ui/src/lib/models.js`** — add/remove entries. Structure:
   ```js
   { id: 'model-id-string', tier: 'Group Label' }
   ```
   - `id` is the exact string passed to `--model`
   - `tier` groups models under `<optgroup>` labels in the dropdown
4. **Rebuild and restart:**
   ```bash
   docker compose build server && docker compose up -d server
   ```

## Common gotchas

- **Provider names are exact** — `openai` not `open-ai`, `anthropic` not `claude`
- **Codex models may be API-restricted** — e.g., `gpt-5.3-codex` launched for ChatGPT but wasn't on the API yet
- **Goose accepts unlisted models** — a model doesn't need to be in Goose's `KNOWN_MODELS` to work. If the provider and API key support it, it'll work via `--model`
- **Snapshot versions** — providers offer both aliases (`gpt-4.1`) and pinned snapshots (`gpt-4.1-2025-04-14`). Aliases float to the latest; snapshots are frozen. For reproducible runs, prefer snapshots
- **Ollama models are local** — they depend on what's pulled on the worker machine, not a remote API

## Future improvement

Ideally, the model list would be fetched dynamically from each provider's API at runtime (like Goose does for OpenRouter and Ollama). This would eliminate manual updates. The tradeoff is added complexity and API calls on page load.
