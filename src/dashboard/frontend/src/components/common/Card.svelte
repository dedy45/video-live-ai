<script lang="ts">
  interface Props {
    title?: string;
  }
  let { title }: Props = $props();
</script>

<div class="card">
  {#if title}
    <div class="card-title">{title}</div>
  {/if}
  <slot />
</div>

<style>
  .card { background: var(--card); border-radius: var(--radius); padding: 18px; border: 1px solid var(--border); transition: all .25s; }
  .card:hover { background: var(--card-hover); }
  .card-title { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 12px; }
</style>
