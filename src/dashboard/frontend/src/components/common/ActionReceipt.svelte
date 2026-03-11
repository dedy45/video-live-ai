<script lang="ts">
  import type { ActionReceipt } from '../../lib/stores/actions';

  interface Props {
    receipt: ActionReceipt | null;
  }

  let { receipt }: Props = $props();
  let showDetails = $state(false);

  const actionLabels: Record<string, string> = {
    'engine.start': 'Avatar menerima perintah jalan',
    'engine.stop': 'Avatar menerima perintah berhenti',
    'engine.validate': 'Pemeriksaan engine avatar selesai',
    'voice.warmup': 'Permintaan pemanasan suara dikirim',
    'voice.restart': 'Permintaan mulai ulang suara dikirim',
    'voice.queue.clear': 'Antrian suara diminta untuk dikosongkan',
    'voice.test.speak': 'Tes suara selesai',
    'production.gate': 'Pemeriksaan kesiapan runtime selesai',
    'pipeline.transition': 'Perubahan status pipeline diproses',
    'stream.start': 'Permintaan mulai streaming dikirim',
    'stream.stop': 'Permintaan berhenti streaming dikirim',
    'rtmp.validate': 'Pemeriksaan target RTMP selesai',
    'incident.ack': 'Insiden ditandai sudah diterima operator',
    'brain.test': 'Pemeriksaan diagnostik selesai',
    'product.switch': 'Produk aktif berhasil diganti',
    'readiness.refresh': 'Status kesiapan berhasil dimuat ulang',
    'preview.open': 'Preview dibuka di tab baru',
    'affiliate.copy': 'Link affiliate berhasil disalin',
  };

  function fallbackTitle(nextReceipt: ActionReceipt | null) {
    if (!nextReceipt) return '';
    if (nextReceipt.title) return nextReceipt.title;
    if (nextReceipt.action && actionLabels[nextReceipt.action]) return actionLabels[nextReceipt.action];
    if (nextReceipt.status === 'error') return 'Aksi belum berhasil';
    if (nextReceipt.status === 'blocked') return 'Aksi tertahan';
    if (nextReceipt.status === 'pending') return 'Aksi sedang diproses';
    if (nextReceipt.status === 'warning') return 'Aksi perlu perhatian';
    return 'Aksi selesai';
  }

  function badgeLabel(status: ActionReceipt['status']) {
    if (status === 'success') return 'Selesai';
    if (status === 'blocked') return 'Tertahan';
    if (status === 'pending') return 'Diproses';
    if (status === 'warning') return 'Perhatian';
    return 'Gagal';
  }

  function timeDisplay(timestamp: number) {
    return new Date(timestamp).toLocaleTimeString();
  }
</script>

{#if receipt}
  <section
    class="action-receipt"
    class:receipt-success={receipt.status === 'success'}
    class:receipt-blocked={receipt.status === 'blocked'}
    class:receipt-error={receipt.status === 'error'}
    class:receipt-pending={receipt.status === 'pending'}
    class:receipt-warning={receipt.status === 'warning'}
    data-testid="action-receipt"
  >
    <div class="receipt-head">
      <span class="receipt-badge">{badgeLabel(receipt.status)}</span>
      <span class="receipt-time">{timeDisplay(receipt.timestamp)}</span>
    </div>

    <div class="receipt-body">
      <p class="receipt-title">{fallbackTitle(receipt)}</p>
      <p class="receipt-message">{receipt.message}</p>
      {#if receipt.nextStep}
        <p class="receipt-next-step">Langkah berikutnya: {receipt.nextStep}</p>
      {/if}
    </div>

    {#if receipt.details && receipt.details.length > 0}
      <div class="receipt-detail-toggle">
        <button class="detail-button" type="button" onclick={() => (showDetails = !showDetails)}>
          {showDetails ? 'Sembunyikan Detail Teknis' : 'Lihat Detail Teknis'}
        </button>
      </div>
      {#if showDetails}
        <div class="receipt-details">
          {#if receipt.action}
            <div class="detail-line"><strong>Aksi:</strong> {receipt.action}</div>
          {/if}
          {#each receipt.details as detail}
            <div class="detail-line">{detail}</div>
          {/each}
        </div>
      {/if}
    {/if}
  </section>
{/if}

<style>
  .action-receipt {
    border-radius: 18px;
    border: 1px solid var(--border);
    padding: 16px;
    margin-bottom: 16px;
    background: rgba(15, 23, 42, 0.72);
    display: grid;
    gap: 10px;
  }

  .receipt-success {
    border-color: rgba(16, 185, 129, 0.35);
    background: linear-gradient(180deg, rgba(16, 185, 129, 0.14), rgba(15, 23, 42, 0.82));
  }

  .receipt-blocked {
    border-color: rgba(245, 158, 11, 0.4);
    background: linear-gradient(180deg, rgba(245, 158, 11, 0.14), rgba(15, 23, 42, 0.82));
  }

  .receipt-error {
    border-color: rgba(239, 68, 68, 0.42);
    background: linear-gradient(180deg, rgba(239, 68, 68, 0.14), rgba(15, 23, 42, 0.82));
  }

  .receipt-pending {
    border-color: rgba(59, 130, 246, 0.35);
    background: linear-gradient(180deg, rgba(59, 130, 246, 0.12), rgba(15, 23, 42, 0.82));
  }

  .receipt-warning {
    border-color: rgba(251, 191, 36, 0.4);
    background: linear-gradient(180deg, rgba(251, 191, 36, 0.12), rgba(15, 23, 42, 0.82));
  }

  .receipt-head {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: center;
  }

  .receipt-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.08);
    color: var(--text);
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }

  .receipt-time {
    color: var(--muted);
    font-size: 12px;
  }

  .receipt-body {
    display: grid;
    gap: 8px;
  }

  .receipt-title {
    margin: 0;
    font-size: 18px;
    font-weight: 800;
    color: var(--text);
  }

  .receipt-message,
  .receipt-next-step {
    margin: 0;
    color: var(--muted);
    line-height: 1.5;
  }

  .receipt-next-step {
    color: var(--text);
  }

  .receipt-detail-toggle {
    display: flex;
    justify-content: flex-start;
  }

  .detail-button {
    border: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.04);
    color: var(--text);
    border-radius: 999px;
    padding: 8px 12px;
    font: inherit;
    cursor: pointer;
  }

  .receipt-details {
    display: grid;
    gap: 6px;
    padding: 12px;
    border-radius: 14px;
    background: rgba(0, 0, 0, 0.24);
    color: var(--muted);
    font-size: 13px;
  }

  .detail-line strong {
    color: var(--text);
  }
</style>
