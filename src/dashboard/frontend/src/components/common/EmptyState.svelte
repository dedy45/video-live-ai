<script lang="ts">
  interface Props {
    message?: string;
  }
  let { message = 'No data available' }: Props = $props();
</script>

<div class="empty-state">
  <p>{message}</p>
</div>

<style>
  .empty-state { text-align: center; padding: 40px 20px; color: var(--muted); }
  .empty-state p { font-size: 14px; }
</style>
