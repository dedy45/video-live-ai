<script lang="ts">
  interface Props {
    lines: string[];
    maxHeight?: string;
  }
  let { lines, maxHeight = '250px' }: Props = $props();
</script>

<div class="log-viewer" style:max-height={maxHeight}>
  {#each lines as line}
    <div class="log-line">{line}</div>
  {/each}
  {#if lines.length === 0}
    <div class="log-empty">No log entries</div>
  {/if}
</div>

<style>
  .log-viewer { overflow-y: auto; font-family: 'Consolas', 'Monaco', monospace; font-size: 11px; background: rgba(0,0,0,.3); border-radius: var(--rsm); padding: 10px; }
  .log-line { padding: 2px 0; color: var(--muted); white-space: pre-wrap; word-break: break-all; }
  .log-empty { color: var(--muted); font-style: italic; }
</style>
