// Provider and model configuration derived from Goose v1.25.0 source code
// Source: crates/goose/src/providers/<provider>.rs KNOWN_MODELS constants
// Provider keys must match Goose --provider flag values exactly

export const PROVIDERS = {
  openai: {
    label: 'OpenAI',
    models: [
      { id: 'gpt-5.2', tier: 'Flagship' },
      { id: 'gpt-5.2-pro', tier: 'Flagship' },
      { id: 'gpt-5.1', tier: 'Flagship' },
      { id: 'gpt-5', tier: 'GPT-5' },
      { id: 'gpt-5-pro', tier: 'GPT-5' },
      { id: 'gpt-5-mini', tier: 'GPT-5' },
      { id: 'gpt-5-nano', tier: 'GPT-5' },
      { id: 'gpt-5.2-codex', tier: 'Codex' },
      { id: 'gpt-5.1-codex', tier: 'Codex' },
      { id: 'gpt-5.1-codex-max', tier: 'Codex' },
      { id: 'gpt-5.1-codex-mini', tier: 'Codex' },
      { id: 'gpt-5-codex', tier: 'Codex' },
      { id: 'gpt-4.1', tier: 'Standard' },
      { id: 'gpt-4.1-mini', tier: 'Standard' },
      { id: 'gpt-4.1-nano', tier: 'Standard' },
      { id: 'gpt-4o', tier: 'Standard' },
      { id: 'gpt-4o-mini', tier: 'Standard' },
      { id: 'o3-pro', tier: 'Reasoning' },
      { id: 'o3', tier: 'Reasoning' },
      { id: 'o3-mini', tier: 'Reasoning' },
      { id: 'o4-mini', tier: 'Reasoning' },
      { id: 'o1-pro', tier: 'Reasoning' },
      { id: 'o1', tier: 'Reasoning' },
    ],
    default: 'gpt-4.1',
  },
  anthropic: {
    label: 'Anthropic',
    models: [
      { id: 'claude-sonnet-4-5', tier: 'Latest' },
      { id: 'claude-sonnet-4-5-20250929', tier: 'Latest' },
      { id: 'claude-opus-4-5', tier: 'Latest' },
      { id: 'claude-opus-4-5-20251101', tier: 'Latest' },
      { id: 'claude-haiku-4-5', tier: 'Fast' },
      { id: 'claude-haiku-4-5-20251001', tier: 'Fast' },
      { id: 'claude-sonnet-4-0', tier: 'Claude 4' },
      { id: 'claude-sonnet-4-20250514', tier: 'Claude 4' },
      { id: 'claude-opus-4-0', tier: 'Claude 4' },
      { id: 'claude-opus-4-20250514', tier: 'Claude 4' },
    ],
    default: 'claude-sonnet-4-5',
  },
  google: {
    label: 'Google Gemini',
    models: [
      { id: 'gemini-2.5-pro', tier: 'Latest' },
      { id: 'gemini-2.5-flash', tier: 'Latest' },
      { id: 'gemini-2.5-flash-lite', tier: 'Latest' },
      { id: 'gemini-3-pro-preview', tier: 'Preview' },
      { id: 'gemini-2.0-flash', tier: 'Stable' },
      { id: 'gemini-2.0-flash-lite', tier: 'Stable' },
    ],
    default: 'gemini-2.5-pro',
  },
  openrouter: {
    label: 'OpenRouter',
    models: [
      { id: 'anthropic/claude-sonnet-4.5', tier: 'Anthropic' },
      { id: 'anthropic/claude-sonnet-4', tier: 'Anthropic' },
      { id: 'anthropic/claude-opus-4.1', tier: 'Anthropic' },
      { id: 'anthropic/claude-opus-4', tier: 'Anthropic' },
      { id: 'google/gemini-2.5-pro', tier: 'Google' },
      { id: 'google/gemini-2.5-flash', tier: 'Google' },
      { id: 'x-ai/grok-code-fast-1', tier: 'xAI' },
      { id: 'deepseek/deepseek-r1-0528', tier: 'DeepSeek' },
      { id: 'qwen/qwen3-coder', tier: 'Qwen' },
      { id: 'moonshotai/kimi-k2', tier: 'Other' },
    ],
    default: 'anthropic/claude-sonnet-4',
  },
  ollama: {
    label: 'Ollama (Local)',
    models: [
      { id: 'qwen3', tier: 'Default' },
      { id: 'qwen3-vl', tier: 'Default' },
      { id: 'qwen3-coder:30b', tier: 'Coding' },
    ],
    default: 'qwen3',
  },
  databricks: {
    label: 'Databricks',
    models: [
      { id: 'databricks-claude-sonnet-4-5', tier: 'Claude' },
      { id: 'databricks-claude-sonnet-4', tier: 'Claude' },
      { id: 'databricks-claude-haiku-4-5', tier: 'Claude' },
      { id: 'databricks-claude-3-7-sonnet', tier: 'Claude' },
      { id: 'databricks-meta-llama-3-3-70b-instruct', tier: 'Meta' },
      { id: 'databricks-meta-llama-3-1-405b-instruct', tier: 'Meta' },
    ],
    default: 'databricks-claude-sonnet-4',
  },
  xai: {
    label: 'xAI (Grok)',
    models: [
      { id: 'grok-code-fast-1', tier: 'Coding' },
      { id: 'grok-4-0709', tier: 'Latest' },
      { id: 'grok-3', tier: 'Standard' },
      { id: 'grok-3-fast', tier: 'Standard' },
      { id: 'grok-3-mini', tier: 'Mini' },
      { id: 'grok-3-mini-fast', tier: 'Mini' },
    ],
    default: 'grok-code-fast-1',
  },
  bedrock: {
    label: 'AWS Bedrock',
    models: [
      { id: 'us.anthropic.claude-sonnet-4-5-20250929-v1:0', tier: 'Claude' },
      { id: 'us.anthropic.claude-sonnet-4-20250514-v1:0', tier: 'Claude' },
      { id: 'us.anthropic.claude-opus-4-20250514-v1:0', tier: 'Claude' },
      { id: 'us.anthropic.claude-opus-4-1-20250805-v1:0', tier: 'Claude' },
      { id: 'us.anthropic.claude-3-7-sonnet-20250219-v1:0', tier: 'Claude' },
    ],
    default: 'us.anthropic.claude-sonnet-4-5-20250929-v1:0',
  },
  azure: {
    label: 'Azure OpenAI',
    models: [
      { id: 'gpt-4o', tier: 'Standard' },
      { id: 'gpt-4o-mini', tier: 'Standard' },
      { id: 'gpt-4', tier: 'Standard' },
    ],
    default: 'gpt-4o',
  },
  'github-copilot': {
    label: 'GitHub Copilot',
    models: [
      { id: 'gpt-4.1', tier: 'OpenAI' },
      { id: 'gpt-5-mini', tier: 'OpenAI' },
      { id: 'gpt-5', tier: 'OpenAI' },
      { id: 'gpt-4o', tier: 'OpenAI' },
      { id: 'gpt-5-codex', tier: 'OpenAI' },
      { id: 'grok-code-fast-1', tier: 'xAI' },
      { id: 'claude-sonnet-4', tier: 'Anthropic' },
      { id: 'claude-sonnet-4.5', tier: 'Anthropic' },
      { id: 'claude-haiku-4.5', tier: 'Anthropic' },
      { id: 'gemini-2.5-pro', tier: 'Google' },
    ],
    default: 'gpt-4.1',
  },
}

export const PROVIDER_LIST = Object.keys(PROVIDERS)

export function getModelsForProvider(provider) {
  return PROVIDERS[provider]?.models || []
}

export function getDefaultModel(provider) {
  return PROVIDERS[provider]?.default || ''
}
