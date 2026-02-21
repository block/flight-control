import { PROVIDERS, getModelsForProvider, getDefaultModel } from '../lib/models'

export default function ProviderModelSelect({ provider, model, onChange }) {
  const models = getModelsForProvider(provider)

  const handleProviderChange = (newProvider) => {
    onChange({ provider: newProvider, model: getDefaultModel(newProvider) })
  }

  const handleModelChange = (newModel) => {
    onChange({ provider, model: newModel })
  }

  // Group models by tier
  const tiers = {}
  for (const m of models) {
    if (!tiers[m.tier]) tiers[m.tier] = []
    tiers[m.tier].push(m)
  }

  return (
    <>
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Provider</label>
        <select
          value={provider}
          onChange={(e) => handleProviderChange(e.target.value)}
          className="input-field"
        >
          {Object.entries(PROVIDERS).map(([key, p]) => (
            <option key={key} value={key}>{p.label}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Model</label>
        <select
          value={model}
          onChange={(e) => handleModelChange(e.target.value)}
          className="input-field font-mono text-[13px]"
        >
          {models.length > 0 ? (
            Object.entries(tiers).map(([tier, tierModels]) => (
              <optgroup key={tier} label={tier}>
                {tierModels.map((m) => (
                  <option key={m.id} value={m.id}>{m.id}</option>
                ))}
              </optgroup>
            ))
          ) : (
            <option value={model}>{model}</option>
          )}
        </select>
      </div>
    </>
  )
}
