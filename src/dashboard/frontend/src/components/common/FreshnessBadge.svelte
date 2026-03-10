<script lang="ts">
  interface Props {
    timestamp: string | null;
  }

  let { timestamp }: Props = $props();

  const display = $derived.by(() => {
    if (!timestamp) return 'never';
    try {
      const d = new Date(timestamp);
      const now = Date.now();
      const diffSec = Math.floor((now - d.getTime()) / 1000);
      if (diffSec < 5) return 'just now';
      if (diffSec < 60) return `${diffSec}s ago`;
      if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
      return d.toLocaleTimeString();
    } catch {
      return timestamp;
    }
  });

  const freshClass = $derived.by(() => {
    if (!timestamp) return 'stale';
    try {
      const diffSec = Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000);
      if (diffSec < 30) return 'fresh';
      if (diffSec < 120) return 'aging';
      return 'stale';
    } catch {
      return 'stale';
    }
  });
</script>

<span class="freshness-badge {freshClass}" data-testid="freshness-badge">{display}</span>

<style>
  .freshness-badge {
    font-size: 10px;
    font-family: monospace;
  }
  .fresh { color: var(--green, #10b981); }
  .aging { color: var(--yellow, #f59e0b); }
  .stale { color: var(--muted, #888); }
</style>
