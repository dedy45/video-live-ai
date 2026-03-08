<script lang="ts">
  import type { ActionReceipt } from '../../lib/stores/actions';

  interface Props {
    receipt: ActionReceipt | null;
  }

  let { receipt }: Props = $props();

  const timeDisplay = $derived(() => {
    if (!receipt) return '';
    const d = new Date(receipt.timestamp);
    return d.toLocaleTimeString();
  });
</script>

{#if receipt}
  <div class="action-receipt" class:receipt-success={receipt.status === 'success'} class:receipt-error={receipt.status === 'error'} data-testid="action-receipt">
    <span class="receipt-icon">{receipt.status === 'success' ? '>' : '!'}</span>
    <span class="receipt-action">{receipt.action}</span>
    <span class="receipt-message">{receipt.message}</span>
    <span class="receipt-time">{timeDisplay()}</span>
  </div>
{/if}

<style>
  .action-receipt {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 12px;
    font-family: monospace;
    margin-bottom: 10px;
  }
  .receipt-success {
    background: rgba(16,185,129,.1);
    border: 1px solid rgba(16,185,129,.25);
    color: var(--green, #10b981);
  }
  .receipt-error {
    background: rgba(239,68,68,.1);
    border: 1px solid rgba(239,68,68,.25);
    color: var(--red, #ef4444);
  }
  .receipt-icon {
    font-weight: 800;
    font-size: 14px;
    flex-shrink: 0;
  }
  .receipt-action {
    font-weight: 700;
    flex-shrink: 0;
  }
  .receipt-message {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .receipt-time {
    color: var(--muted, #888);
    font-size: 10px;
    flex-shrink: 0;
  }
</style>
