<script lang="ts">
  interface Props {
    status: string;
  }
  let { status }: Props = $props();

  const badgeClass = $derived(
    status === 'running' || status === 'live' || status === 'healthy' ? 'badge-live' :
    status === 'mock' ? 'badge-mock' :
    status === 'stopped' || status === 'idle' ? 'badge-idle' :
    status === 'error' || status === 'failed' ? 'badge-error' :
    'badge-idle'
  );
</script>

<span class="badge {badgeClass}">{status}</span>

<style>
  .badge { padding: 3px 10px; border-radius: 20px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; }
  .badge-live { background: var(--green); color: #000; }
  .badge-mock { background: var(--yellow); color: #000; }
  .badge-idle { background: rgba(255,255,255,.1); color: var(--muted); }
  .badge-error { background: var(--accent); color: #fff; }
</style>
