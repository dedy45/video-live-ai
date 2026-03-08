<script lang="ts">
  interface Props {
    provenance: string;
  }

  let { provenance }: Props = $props();

  const colorClass = $derived(() => {
    switch (provenance) {
      case 'mock': return 'prov-mock';
      case 'real_local': return 'prov-real-local';
      case 'real_live': return 'prov-real-live';
      case 'derived': return 'prov-derived';
      default: return 'prov-unknown';
    }
  });
</script>

<span class="provenance-badge {colorClass()}" data-testid="provenance-badge">{provenance}</span>

<style>
  .provenance-badge {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    vertical-align: middle;
  }
  .prov-mock { background: rgba(245,158,11,.15); color: var(--yellow, #f59e0b); }
  .prov-real-local { background: rgba(16,185,129,.15); color: var(--green, #10b981); }
  .prov-real-live { background: rgba(34,211,238,.15); color: #22d3ee; }
  .prov-derived { background: rgba(136,136,136,.15); color: var(--muted, #888); }
  .prov-unknown { background: rgba(239,68,68,.15); color: var(--red, #ef4444); }
</style>
