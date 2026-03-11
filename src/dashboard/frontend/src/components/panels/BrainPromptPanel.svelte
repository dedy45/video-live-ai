<script lang="ts">
  import Card from '../common/Card.svelte';
  import type { BrainConfig, BrainProviderConfig, DirectorRuntimeContract } from '../../lib/types';

  interface Props {
    config: BrainConfig | null;
    runtime: DirectorRuntimeContract | null;
    loading?: boolean;
    error?: string;
  }

  let { config, runtime, loading = false, error = '' }: Props = $props();

  const activeRevision = $derived(config?.prompt?.active_revision || runtime?.prompt?.active_revision || 'belum tersedia');
  const routingEntries = $derived(Object.entries(config?.routing_table || runtime?.brain?.routing_table || {}));

  const orderedProviders = $derived.by(() => {
    const providers = config?.providers || {};
    const fallback = config?.fallback_order || [];
    const orderedIds = [...fallback, ...Object.keys(providers).filter((provider) => !fallback.includes(provider))];
    return orderedIds
      .map((id) => ({ id, ...(providers[id] as BrainProviderConfig | undefined) }))
      .filter((provider) => Boolean(provider.model));
  });

  function formatTask(task: string): string {
    return task.replaceAll('_', ' ');
  }
</script>

<Card title="Brain & Prompt" size="lg" className="brain-prompt-card">
  <p class="panel-copy">Konfigurasi LLM aktif, prompt yang dipakai saat live, dan jalur fallback jika provider utama turun.</p>

  {#if loading}
    <div class="panel-state">Memuat konfigurasi brain dan prompt...</div>
  {:else if error}
    <div class="panel-state panel-state-error" role="status">{error}</div>
  {:else if !config && !runtime}
    <div class="panel-state">Konfigurasi brain belum tersedia.</div>
  {:else}
    <div class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">Prompt aktif</span>
        <strong class="summary-value">{activeRevision}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">Provider utama</span>
        <strong class="summary-value">{runtime?.brain?.active_provider || 'unknown'}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">Model runtime</span>
        <strong class="summary-value">{runtime?.brain?.active_model || 'unknown'}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">Budget harian</span>
        <strong class="summary-value">${config?.daily_budget_usd ?? runtime?.brain?.daily_budget_usd ?? 0}</strong>
      </div>
    </div>

    <div class="content-grid">
      <section class="content-block">
        <div class="content-title">Provider & Fallback</div>
        <div class="provider-list">
          {#each orderedProviders as provider}
            <div class:provider-active={provider.id === runtime?.brain?.active_provider} class="provider-card">
              <strong>{provider.id}</strong>
              <span>{provider.model}</span>
              <span>{provider.timeout_ms} ms</span>
            </div>
          {:else}
            <div class="empty-copy">Belum ada provider yang dibaca dari runtime.</div>
          {/each}
        </div>
      </section>

      <section class="content-block">
        <div class="content-title">Routing & Persona</div>
        <div class="meta-list">
          <div class="meta-row">
            <span>Host persona</span>
            <strong>{runtime?.persona?.name || 'unknown'}</strong>
          </div>
          <div class="meta-row">
            <span>Gaya bicara</span>
            <strong>{runtime?.persona?.tone || 'unknown'}</strong>
          </div>
          <div class="meta-row">
            <span>Bahasa</span>
            <strong>{runtime?.persona?.language || 'unknown'}</strong>
          </div>
        </div>
        <div class="routing-list">
          {#each routingEntries as [task, providers]}
            <div class="routing-row">
              <span>{formatTask(task)}</span>
              <strong>{providers.join(' -> ')}</strong>
            </div>
          {:else}
            <div class="empty-copy">Routing LLM belum terlapor.</div>
          {/each}
        </div>
      </section>
    </div>
  {/if}
</Card>

<style>
  .panel-copy,
  .panel-state,
  .empty-copy {
    color: var(--muted);
    line-height: 1.6;
  }

  .panel-state {
    padding: 16px;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.03);
  }

  .panel-state-error {
    border-color: rgba(233, 69, 96, 0.28);
    color: var(--text);
  }

  .summary-grid,
  .content-grid {
    display: grid;
    gap: 14px;
  }

  .summary-grid {
    grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr));
    margin-top: 16px;
  }

  .summary-card,
  .provider-card,
  .meta-row,
  .routing-row {
    padding: 14px;
    border-radius: var(--radius);
    border: 1px solid rgba(255, 255, 255, 0.06);
    background: rgba(255, 255, 255, 0.03);
  }

  .summary-label,
  .content-title {
    display: block;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 11px;
  }

  .summary-value {
    display: block;
    margin-top: 8px;
    font-size: 18px;
  }

  .content-grid {
    grid-template-columns: repeat(auto-fit, minmax(min(300px, 100%), 1fr));
    margin-top: 16px;
  }

  .content-block {
    display: grid;
    gap: 12px;
  }

  .provider-list,
  .meta-list,
  .routing-list {
    display: grid;
    gap: 10px;
  }

  .provider-card,
  .meta-row,
  .routing-row {
    display: grid;
    gap: 6px;
  }

  .provider-active {
    border-color: rgba(34, 211, 238, 0.26);
    background: rgba(34, 211, 238, 0.08);
  }

  .meta-row,
  .routing-row {
    grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr);
    align-items: center;
    gap: 12px;
  }

  .meta-row span,
  .routing-row span,
  .provider-card span {
    color: var(--muted);
    word-break: break-word;
  }
</style>
