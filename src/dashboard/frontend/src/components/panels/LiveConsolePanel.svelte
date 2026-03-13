<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import {
    emergencyStop,
    getDirectorRuntime,
    getLiveSession,
    getLiveTalkingConfig,
    ingestChatEvent,
    getOpsSummary,
    getProducts,
    getRuntimeTruth,
    getStatus,
    setLiveSessionFocus,
    startLiveTalking,
    stopLiveTalking,
    switchProduct,
    voiceTestSpeak,
  } from '../../lib/api';
  import StatusBadge from '../common/StatusBadge.svelte';
  import Card from '../common/Card.svelte';
  import ActionReceipt from '../common/ActionReceipt.svelte';
  import DirectorRuntimePanel from './DirectorRuntimePanel.svelte';
  import type { ActionReceipt as ReceiptType } from '../../lib/stores/actions';
  import type { DirectorRuntimeContract, EngineConfig, LiveSessionSummary, OpsSummary, RuntimeTruth } from '../../lib/types';

  let status = $state<Record<string, any>>({});
  let opsSummary = $state<OpsSummary | null>(null);
  let truth = $state<RuntimeTruth | null>(null);
  let config = $state<EngineConfig | null>(null);
  let directorRuntime = $state<DirectorRuntimeContract | null>(null);
  let liveSession = $state<LiveSessionSummary | null>(null);
  let products = $state<any[]>([]);
  let loading = $state(true);
  let error = $state('');
  let directorError = $state('');
  let receipt = $state<ReceiptType | null>(null);
  let sessionLogs = $state<string[]>([]);
  let pollHandle: number | null = null;
  let simulatedViewerName = $state('Ayu');
  let simulatedViewerMessage = $state('Kak ini ori ga?');

  function addLog(message: string) {
    const timestamp = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
    sessionLogs = [`${timestamp} — ${message}`, ...sessionLogs].slice(0, 12);
  }

  function getErrorMessage(reason: unknown, fallback: string): string {
    if (reason instanceof Error && reason.message) return reason.message;
    if (typeof reason === 'string' && reason.trim().length > 0) return reason;
    return fallback;
  }

  async function refresh() {
    directorError = '';
    try {
      const [nextStatus, nextOpsSummary, nextTruth, nextProducts, nextConfig, nextDirectorRuntime, nextLiveSession] = await Promise.allSettled([
        getStatus(),
        getOpsSummary() as Promise<OpsSummary>,
        getRuntimeTruth() as Promise<RuntimeTruth>,
        getProducts(),
        getLiveTalkingConfig() as Promise<EngineConfig>,
        getDirectorRuntime() as Promise<DirectorRuntimeContract>,
        getLiveSession() as Promise<LiveSessionSummary>,
      ]);

      const loadErrors: string[] = [];

      if (nextStatus.status === 'fulfilled') {
        status = nextStatus.value;
      } else {
        status = {};
        loadErrors.push(getErrorMessage(nextStatus.reason, 'Status sesi gagal dimuat.'));
      }

      if (nextOpsSummary.status === 'fulfilled') {
        opsSummary = nextOpsSummary.value;
      } else {
        opsSummary = null;
        loadErrors.push(getErrorMessage(nextOpsSummary.reason, 'Ringkasan operasi gagal dimuat.'));
      }

      if (nextTruth.status === 'fulfilled') {
        truth = nextTruth.value;
      } else {
        truth = null;
        loadErrors.push(getErrorMessage(nextTruth.reason, 'Runtime truth gagal dimuat.'));
      }

      if (nextProducts.status === 'fulfilled') {
        products = nextProducts.value;
      } else {
        products = [];
        loadErrors.push(getErrorMessage(nextProducts.reason, 'Daftar produk gagal dimuat.'));
      }

      if (nextConfig.status === 'fulfilled') {
        config = nextConfig.value;
      } else {
        config = null;
        loadErrors.push(getErrorMessage(nextConfig.reason, 'Konfigurasi preview avatar gagal dimuat.'));
      }

      if (nextDirectorRuntime.status === 'fulfilled') {
        directorRuntime = nextDirectorRuntime.value;
      } else {
        directorRuntime = null;
        directorError = getErrorMessage(nextDirectorRuntime.reason, 'Runtime director belum bisa dimuat.');
      }

      if (nextLiveSession.status === 'fulfilled') {
        liveSession = nextLiveSession.value;
      } else {
        liveSession = null;
        loadErrors.push(getErrorMessage(nextLiveSession.reason, 'Sesi live gagal dimuat.'));
      }

      error = loadErrors.join(' ');
    } catch (nextError: unknown) {
      error = getErrorMessage(nextError, 'Failed to load live console');
    } finally {
      loading = false;
    }
  }

  async function runAction(action: string, work: () => Promise<{ message?: string } | void>, successMessage: string) {
    receipt = null;
    try {
      const result = await work();
      const message = result?.message || successMessage;
      receipt = { action, status: 'success', message, timestamp: Date.now() };
      addLog(message);
      await refresh();
    } catch (nextError: any) {
      const message = nextError.message || `${action} failed`;
      receipt = { action, status: 'error', message, timestamp: Date.now() };
      addLog(message);
    }
  }

  const activeProduct = $derived.by(() => {
    const focusId = liveSession?.state?.current_focus_product_id;
    if (focusId) {
      const fromSession = liveSession?.products.find((item) => item.product_id === focusId)?.product;
      if (fromSession) return fromSession;
      const fromCatalog = products.find((product) => product.id === focusId);
      if (fromCatalog) return fromCatalog;
    }

    if (!products.length) return liveSession?.products[0]?.product || null;
    const currentId = status.current_product?.id;
    return products.find((product) => product.id === currentId) || liveSession?.products[0]?.product || products[0];
  });

  const queuedProducts = $derived.by(() => {
    if (liveSession?.products?.length) {
      const currentId = activeProduct?.id;
      return liveSession.products
        .filter((item) => item.product_id !== currentId)
        .map((item) => ({ ...item.product, session_product_id: item.id }));
    }
    const currentId = activeProduct?.id;
    return products.filter((product) => product.id !== currentId);
  });

  const firstAffiliateLink = $derived.by(() => {
    const entries = Object.entries(activeProduct?.affiliate_links || {});
    return entries.length ? { platform: entries[0][0], url: String(entries[0][1]) } : null;
  });

  const currentScript = $derived.by(() => {
    if (!activeProduct) {
      return 'Belum ada produk aktif. Pilih produk terlebih dahulu sebelum live.';
    }

    const sellingPoints = (activeProduct.selling_points || []).slice(0, 3).join(', ');
    const price = activeProduct.price_formatted || activeProduct.price || 'harga belum tersedia';
    const commission = activeProduct.commission_rate ? `Komisi ${activeProduct.commission_rate}%` : 'Komisi cek dashboard';
    return `Produk aktif ${activeProduct.name}. Harga ${price}. Sorot nilai jual utama: ${sellingPoints || 'stok, manfaat, dan urgensi beli'}. Tutup dengan call to action ke ${firstAffiliateLink?.platform || 'keranjang'} sekarang. ${commission}.`;
  });

  const uptimeMinutes = $derived(Math.floor((status.uptime_sec || 0) / 60));
  const viewerCount = $derived(status.viewer_count || 0);
  const streamLive = $derived(directorRuntime?.director?.stream_running ?? status.stream_running === true);
  const faceRunning = $derived(truth?.face_engine?.engine_state === 'running');
  const voiceReady = $derived(Boolean(truth?.voice_engine?.server_reachable && truth?.voice_engine?.reference_ready));
  const totalRestarts = $derived(
    (opsSummary?.restart_counters?.voice || 0) +
    (opsSummary?.restart_counters?.face || 0) +
    (opsSummary?.restart_counters?.stream || 0),
  );

  async function handleRotateProduct() {
    const nextProduct = queuedProducts[0];
    if (!nextProduct) {
      receipt = { action: 'product.rotate', status: 'error', message: 'Tidak ada produk cadangan untuk dirotasi', timestamp: Date.now() };
      return;
    }

    if (liveSession?.session && nextProduct.session_product_id) {
      await runAction(
        'session.focus',
        () => setLiveSessionFocus({ session_product_id: nextProduct.session_product_id }),
        `Fokus sesi dipindah ke ${nextProduct.name}`,
      );
      return;
    }

    await runAction(
      'product.rotate',
      () => switchProduct(nextProduct.id),
      `Produk aktif diganti ke ${nextProduct.name}`,
    );
  }

  async function handleVoiceTest() {
    await runAction(
      'voice.test',
      () => voiceTestSpeak(currentScript),
      'Tes suara operator selesai',
    );
  }

  async function handleCopyLink() {
    if (!firstAffiliateLink?.url) {
      receipt = { action: 'affiliate.copy', status: 'error', message: 'Link affiliate belum tersedia', timestamp: Date.now() };
      return;
    }
    await navigator.clipboard.writeText(firstAffiliateLink.url);
    receipt = { action: 'affiliate.copy', status: 'success', message: `Link ${firstAffiliateLink.platform} disalin`, timestamp: Date.now() };
    addLog(`Link ${firstAffiliateLink.platform} disalin`);
  }

  async function handleAvatarToggle() {
    await runAction(
      faceRunning ? 'avatar.stop' : 'avatar.start',
      () => (faceRunning ? stopLiveTalking() : startLiveTalking()),
      faceRunning ? 'Avatar dihentikan' : 'Avatar dijalankan',
    );
  }

  async function handleEmergencyStop() {
    await runAction(
      'emergency.stop',
      () => emergencyStop(),
      'Emergency stop diaktifkan',
    );
  }

  async function handleInjectChat() {
    const username = simulatedViewerName.trim() || 'viewer';
    const message = simulatedViewerMessage.trim();
    if (!message) {
      receipt = { action: 'chat.inject', status: 'error', message: 'Pesan viewer tidak boleh kosong', timestamp: Date.now() };
      return;
    }

    await runAction(
      'chat.inject',
      async () => {
        const result = await ingestChatEvent({
          platform: 'tiktok',
          username,
          message,
        });
        simulatedViewerMessage = '';
        return {
          message: result.auto_paused
            ? `Chat ${username} direkam dan sesi otomatis pause untuk Q&A.`
            : `Chat ${username} direkam ke dashboard.`,
        };
      },
      `Chat ${username} direkam ke dashboard.`,
    );
  }

  function openPreview() {
    const url = config?.debug_urls?.webrtcapi;
    if (!url) {
      receipt = { action: 'preview.open', status: 'error', message: 'Preview URL belum tersedia', timestamp: Date.now() };
      return;
    }
    window.open(url, '_blank', 'noopener,noreferrer');
    addLog('Preview window dibuka');
  }

  onMount(async () => {
    await refresh();
    pollHandle = window.setInterval(() => {
      void refresh();
    }, 10000);
  });

  onDestroy(() => {
    if (pollHandle !== null) {
      window.clearInterval(pollHandle);
    }
  });
</script>

<div class="live-command-center">
  <div class="command-header">
    <div class="title-section">
      <h1 class="command-title">📺 Konsol Live</h1>
      <p class="command-subtitle">Command center operator untuk produk aktif, avatar, skrip panduan, dan quick actions saat sesi live berjalan.</p>
    </div>
    <div class="status-bar">
      <StatusBadge status={streamLive ? 'ready' : 'idle'} label={streamLive ? 'LIVE' : 'OFFLINE'} size="lg" />
      <span class="status-meta">Uptime {uptimeMinutes} menit</span>
      <span class="status-meta">Viewer {viewerCount}</span>
    </div>
  </div>

  <ActionReceipt {receipt} />

  {#if error}
    <div class="error-banner">{error}</div>
  {/if}

  {#if loading}
    <div class="loading-panel">Memuat konsol live...</div>
  {:else}
    <div class="command-grid">
      <div class="command-col">
        <Card title="Produk Aktif" size="lg" className="product-card">
          {#if activeProduct}
            <div class="product-name">{activeProduct.name}</div>
            <div class="product-meta">
              <span>{activeProduct.price_formatted || 'Harga belum tersedia'}</span>
              <span>{activeProduct.commission_rate ? `${activeProduct.commission_rate}% komisi` : 'Komisi belum tersedia'}</span>
              <span>{queuedProducts.length} produk antrian</span>
            </div>
            <div class="selling-points">
              {#each activeProduct.selling_points || [] as point}
                <div class="selling-point">{point}</div>
              {/each}
            </div>
            <div class="link-row">
              {#each Object.entries(activeProduct.affiliate_links || {}) as [platform, url]}
                <a class="affiliate-link" href={String(url)} target="_blank" rel="noreferrer">{platform}</a>
              {/each}
            </div>
          {:else}
            <div class="empty-copy">Belum ada produk aktif di runtime.</div>
          {/if}
        </Card>

        <Card title="Status Avatar" size="lg">
          <div class="status-rows">
            <div class="status-row">
              <span>Suara</span>
              <StatusBadge status={voiceReady ? 'ready' : 'warning'} label={truth?.voice_engine?.resolved_engine || 'unknown'} />
            </div>
            <div class="status-row">
              <span>Wajah</span>
              <StatusBadge status={faceRunning ? 'ready' : 'idle'} label={truth?.face_engine?.resolved_model || 'unknown'} />
            </div>
            <div class="status-row">
              <span>Stream</span>
              <StatusBadge status={streamLive ? 'ready' : 'idle'} label={status.stream_status || 'idle'} />
            </div>
          </div>
          <button class="secondary-btn" onclick={openPreview}>Buka Preview</button>
        </Card>

        <Card title="Skrip Panduan" size="lg">
          <div class="script-copy">{currentScript}</div>
          <div class="script-hint">Asal data: derived dari produk aktif + runtime truth, bukan browser cache.</div>
        </Card>
      </div>

      <div class="command-col">
        <DirectorRuntimePanel runtime={directorRuntime} loading={loading} error={directorError} />

        <Card title="Aksi Cepat" size="lg">
          <div class="action-grid">
            <button class="primary-btn" onclick={handleRotateProduct}>Ganti Produk</button>
            <button class="secondary-btn" onclick={handleVoiceTest}>Tes Suara</button>
            <button class="secondary-btn" onclick={handleCopyLink}>Salin Link</button>
            <button class="secondary-btn" onclick={handleAvatarToggle}>{faceRunning ? 'Hentikan Avatar' : 'Jalankan Avatar'}</button>
            <button class="critical-btn" onclick={handleEmergencyStop}>Stop Darurat</button>
          </div>
        </Card>

        <Card title="Kontrol Sesi" size="lg">
          <div class="summary-list">
            <div class="summary-row"><span>Status sesi</span><strong>{liveSession?.session?.status || 'idle'}</strong></div>
            <div class="summary-row"><span>Mode</span><strong>{liveSession?.state?.current_mode || 'unknown'}</strong></div>
            <div class="summary-row"><span>Pause reason</span><strong>{liveSession?.state?.pause_reason || 'tidak ada'}</strong></div>
            <div class="summary-row"><span>Target RTMP</span><strong>{liveSession?.stream_target?.label || 'belum aktif'}</strong></div>
            <div class="summary-row"><span>Produk sesi</span><strong>{liveSession?.products?.length || 0}</strong></div>
          </div>
          {#if liveSession?.state?.pending_question?.text}
            <div class="script-hint">Pertanyaan tertunda: {liveSession.state.pending_question.text}</div>
          {/if}
          {#if liveSession?.state?.pending_question?.answer_draft}
            <div class="script-hint">Draft jawaban: {liveSession.state.pending_question.answer_draft}</div>
          {/if}
        </Card>

        <Card title="Simulasi Chat" size="lg">
          <div class="chat-form">
            <label class="chat-field">
              <span>Nama Viewer</span>
              <input bind:value={simulatedViewerName} placeholder="Ayu" />
            </label>
            <label class="chat-field">
              <span>Pesan Viewer</span>
              <textarea bind:value={simulatedViewerMessage} rows="3" placeholder="Kak ini ori ga?"></textarea>
            </label>
          </div>
          <div class="script-hint">Dipakai untuk debug jalur ingest chat, auto-pause, dan draft jawaban langsung dari dashboard.</div>
          <button class="secondary-btn" onclick={handleInjectChat}>Kirim Chat Simulasi</button>
        </Card>

        <Card title="Ringkasan Sesi" size="lg">
          <div class="summary-list">
            <div class="summary-row"><span>Deploy</span><strong>{opsSummary?.deployment_mode || 'unknown'}</strong></div>
            <div class="summary-row"><span>Produk aktif</span><strong>{activeProduct?.name || 'none'}</strong></div>
            <div class="summary-row"><span>Restart</span><strong>{totalRestarts}</strong></div>
            <div class="summary-row"><span>Insiden terbuka</span><strong>{opsSummary?.incident_summary?.open_count ?? 0}</strong></div>
          </div>
        </Card>

        <Card title="Log Aktivitas" size="lg">
          <div class="log-list">
            {#each sessionLogs as log}
              <div class="log-item">{log}</div>
            {:else}
              <div class="empty-copy">Belum ada aksi operator pada sesi ini.</div>
            {/each}
          </div>
        </Card>
      </div>
    </div>
  {/if}
</div>

<style>
  .live-command-center {
    width: 100%;
    padding: 0;
  }
  .command-header {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: flex-start;
    margin-bottom: 24px;
  }
  .command-title {
    margin: 0 0 8px;
    font-size: 32px;
    font-weight: 800;
  }
  .command-subtitle {
    margin: 0;
    color: var(--muted);
    max-width: 760px;
    line-height: 1.5;
  }
  .status-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 14px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: rgba(255, 255, 255, 0.03);
    flex-wrap: wrap;
  }
  .status-meta {
    color: var(--muted);
    font-size: 12px;
    font-weight: 700;
  }
  .error-banner,
  .loading-panel {
    padding: 14px 16px;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    background: var(--card);
    margin-bottom: 18px;
  }
  .error-banner {
    color: var(--accent);
    border-color: rgba(233, 69, 96, 0.3);
  }
  .command-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(360px, 100%), 1fr));
    gap: 20px;
  }
  .command-col {
    display: flex;
    flex-direction: column;
    gap: 18px;
  }
  .product-name {
    font-size: 22px;
    font-weight: 800;
    margin-bottom: 8px;
  }
  .product-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    color: var(--muted);
    font-size: 12px;
    margin-bottom: 14px;
  }
  .selling-points {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 14px;
  }
  .selling-point {
    padding: 10px 12px;
    border-radius: var(--rsm);
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
  }
  .link-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .affiliate-link {
    padding: 8px 10px;
    border-radius: 999px;
    border: 1px solid rgba(34, 211, 238, 0.2);
    background: rgba(34, 211, 238, 0.08);
    color: var(--text);
    text-decoration: none;
    font-size: 12px;
    font-weight: 700;
  }
  .status-rows,
  .summary-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 14px;
  }
  .status-row,
  .summary-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: center;
    padding: 10px 12px;
    border-radius: var(--rsm);
    background: rgba(255, 255, 255, 0.03);
  }
  .script-copy {
    padding: 16px;
    border-radius: var(--radius);
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.02)),
      radial-gradient(circle at top left, rgba(34, 211, 238, 0.1), transparent 45%);
    border: 1px solid rgba(255, 255, 255, 0.05);
    line-height: 1.7;
  }
  .script-hint {
    margin-top: 12px;
    color: var(--muted);
    font-size: 12px;
  }
  .action-grid {
    display: grid;
    gap: 10px;
  }
  .chat-form {
    display: grid;
    gap: 12px;
    margin-bottom: 14px;
  }
  .chat-field {
    display: grid;
    gap: 6px;
    font-size: 12px;
    color: var(--muted);
  }
  .chat-field input,
  .chat-field textarea {
    width: 100%;
    padding: 12px 14px;
    border-radius: var(--rsm);
    border: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.04);
    color: var(--text);
    font: inherit;
    resize: vertical;
  }
  .primary-btn,
  .secondary-btn,
  .critical-btn {
    padding: 12px 14px;
    border-radius: var(--rsm);
    border: 1px solid var(--border);
    font-weight: 800;
    font-family: inherit;
    cursor: pointer;
  }
  .primary-btn {
    background: linear-gradient(135deg, rgba(34, 211, 238, 0.9), rgba(59, 130, 246, 0.9));
    color: #04111f;
    border: none;
  }
  .secondary-btn {
    background: rgba(255, 255, 255, 0.04);
    color: var(--text);
  }
  .critical-btn {
    background: rgba(233, 69, 96, 0.18);
    border-color: rgba(233, 69, 96, 0.3);
    color: #ffb6c1;
  }
  .log-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 260px;
    overflow-y: auto;
  }
  .log-item,
  .empty-copy {
    padding: 10px 12px;
    border-radius: var(--rsm);
    background: rgba(255, 255, 255, 0.03);
    color: var(--muted);
    font-size: 12px;
  }
  @media (max-width: 768px) {
    .command-header {
      flex-direction: column;
    }
    .command-title {
      font-size: 28px;
    }
  }
</style>
