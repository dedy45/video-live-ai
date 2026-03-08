<script lang="ts">
  interface Props {
    label: string;
    value: string | number;
    color?: string;
  }
  let { label, value, color = '' }: Props = $props();
</script>

<div class="metric-tile">
  <div class="metric-label">{label}</div>
  <div class="metric-value" style:color>{value}</div>
</div>

<style>
  .metric-tile { padding: 12px; background: var(--card); border-radius: var(--rsm); border: 1px solid var(--border); }
  .metric-label { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; margin-bottom: 4px; }
  .metric-value { font-size: 22px; font-weight: 800; }
</style>
