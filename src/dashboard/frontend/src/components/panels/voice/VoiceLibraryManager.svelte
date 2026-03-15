<script lang="ts">
  import type { VoiceGeneration, VoiceLibrarySummary } from '../../../lib/types';

  interface Props {
    busy: boolean;
    voiceGenerations: VoiceGeneration[];
    voiceLibrarySummary: VoiceLibrarySummary | null;
    onDeleteGeneration: (generationId: number) => void | Promise<void>;
    onClearLibrary: () => void | Promise<void>;
  }

  let { busy, voiceGenerations, voiceLibrarySummary, onDeleteGeneration, onClearLibrary }: Props = $props();

  let searchQuery = $state('');
  let filterLanguage = $state('id');
  let filterMode = $state('all');

  const latestGeneration = $derived(voiceLibrarySummary?.latest_generation || voiceGenerations[0] || null);
  const filteredGenerations = $derived.by(() =>
    voiceGenerations.filter((item) => {
      const haystack = `${item.profile_name || ''} ${item.input_text || ''} ${item.download_name || ''}`.toLowerCase();
      const matchesQuery = !searchQuery.trim() || haystack.includes(searchQuery.trim().toLowerCase());
      const matchesLanguage = (item.language || 'id') === filterLanguage;
      const matchesMode = filterMode === 'all' || item.mode === filterMode;
      return matchesQuery && matchesLanguage && matchesMode;
    }),
  );

  function artifactExists(item: VoiceGeneration | null | undefined) {
    return Boolean(item?.artifact_exists ?? true);
  }

  function artifactMessage(item: VoiceGeneration | null | undefined) {
    return item?.missing_reason || 'Artifact file hilang dari disk. Hapus record ini atau generate ulang audio.';
  }

  function formatBytes(value: number | null | undefined) {
    const bytes = Number(value || 0);
    if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${bytes} B`;
  }
</script>

<section class="card">
  <div class="section-head">
    <div>
      <h3>5. Manajer File Lokal</h3>
      <p>Semua artifact suara tersimpan lokal. Operator bisa memutar, mengunduh, dan menghapus tanpa pindah ke workspace lain.</p>
    </div>
    <button class="btn btn-secondary" type="button" onclick={onClearLibrary} disabled={busy || voiceGenerations.length === 0}>
      Hapus Semua Artifact
    </button>
  </div>

  <div class="summary-grid">
    <article class="summary-card">
      <span class="eyebrow">Folder artifact</span>
      <strong>{voiceLibrarySummary?.artifact_dir || 'Belum ada'}</strong>
      <p>{voiceLibrarySummary?.artifact_dir_abs || 'Path absolut belum tersedia.'}</p>
    </article>
    <article class="summary-card">
      <span class="eyebrow">Total file</span>
      <strong>{voiceLibrarySummary?.existing_files ?? 0}</strong>
      <p>{voiceLibrarySummary?.total_generations ?? 0} record · missing {voiceLibrarySummary?.missing_files ?? 0}</p>
    </article>
    <article class="summary-card">
      <span class="eyebrow">Storage</span>
      <strong>{formatBytes(voiceLibrarySummary?.total_size_bytes)}</strong>
      <p>Akumulasi artifact audio lokal.</p>
    </article>
  </div>

  {#if latestGeneration}
    <article class="latest-card">
      <div class="section-head compact">
        <div>
          <h4>Hasil Terbaru</h4>
          <p>{latestGeneration.profile_name || 'Profile tidak diketahui'} · {(latestGeneration.language || 'id').toUpperCase()} · {latestGeneration.style_preset || 'natural'}</p>
        </div>
        <span class:attach-badge={latestGeneration.attached_to_avatar} class="status-chip">
          {latestGeneration.attached_to_avatar ? 'Sudah dikirim ke avatar' : 'Audio lokal'}
        </span>
      </div>
      <p class="prompt-text">{latestGeneration.input_text}</p>
      {#if artifactExists(latestGeneration)}
        <audio controls src={latestGeneration.audio_url || `/api/voice/audio/${latestGeneration.id}`}></audio>
      {:else}
        <div class="missing-artifact" role="status">
          <strong>Artifact file hilang dari disk.</strong>
          <p>{artifactMessage(latestGeneration)}</p>
        </div>
      {/if}
      <div class="meta-grid">
        <div><span>Latency</span><strong>{latestGeneration.latency_ms} ms</strong></div>
        <div><span>Durasi</span><strong>{latestGeneration.duration_ms} ms</strong></div>
        <div><span>Ukuran</span><strong>{formatBytes(latestGeneration.audio_size_bytes)}</strong></div>
        <div><span>Path</span><strong>{latestGeneration.audio_path}</strong></div>
      </div>
      <div class="action-row">
        {#if artifactExists(latestGeneration)}
          <a class="link-button" href={latestGeneration.audio_url || `/api/voice/audio/${latestGeneration.id}`} target="_blank" rel="noreferrer">
            Putar {latestGeneration.download_name || latestGeneration.audio_filename || `voice-${latestGeneration.id}.wav`}
          </a>
          <a class="link-button" href={latestGeneration.download_url || `/api/voice/audio/${latestGeneration.id}/download`} target="_blank" rel="noreferrer">
            Unduh {latestGeneration.download_name || latestGeneration.audio_filename || `voice-${latestGeneration.id}.wav`}
          </a>
        {/if}
        <button
          class="btn btn-danger"
          type="button"
          onclick={() => onDeleteGeneration(latestGeneration.id)}
          disabled={busy}
          aria-label={`Hapus artifact ${latestGeneration.download_name || latestGeneration.audio_filename || `voice-${latestGeneration.id}.wav`}`}
        >
          Hapus Artifact
        </button>
      </div>
    </article>
  {/if}

  <div class="filter-row">
    <input bind:value={searchQuery} placeholder="Cari nama profile, prompt, atau file" aria-label="Cari artifact suara" />
    <select bind:value={filterLanguage} aria-label="Filter bahasa">
      <option value="id">Indonesia</option>
    </select>
    <select bind:value={filterMode} aria-label="Filter mode output">
      <option value="all">Semua output</option>
      <option value="standalone">Audio lokal</option>
      <option value="attach_avatar">Avatar live</option>
    </select>
  </div>

  <div class="library-list">
    {#if filteredGenerations.length === 0}
      <p class="empty-copy">Belum ada artifact yang cocok dengan filter saat ini.</p>
    {:else}
      {#each filteredGenerations as item}
        <article class="library-card">
          <div class="section-head compact">
            <div>
              <strong>{item.profile_name || 'Profile tidak diketahui'}</strong>
              <p>{item.language || 'id'} · {item.style_preset || 'natural'} · {item.source_type}</p>
            </div>
            <span class="status-chip">{item.mode === 'attach_avatar' ? 'Avatar live' : 'Audio lokal'}</span>
          </div>
          <p class="prompt-text">{item.input_text}</p>
          {#if artifactExists(item)}
            <audio controls src={item.audio_url || `/api/voice/audio/${item.id}`}></audio>
          {:else}
            <div class="missing-artifact" role="status">
              <strong>Artifact file hilang dari disk.</strong>
              <p>{artifactMessage(item)}</p>
            </div>
          {/if}
          <div class="meta-grid">
            <div><span>Latency</span><strong>{item.latency_ms} ms</strong></div>
            <div><span>Durasi</span><strong>{item.duration_ms} ms</strong></div>
            <div><span>Ukuran</span><strong>{formatBytes(item.audio_size_bytes)}</strong></div>
            <div><span>Path</span><strong>{item.audio_path}</strong></div>
          </div>
          <div class="action-row">
            {#if artifactExists(item)}
              <a class="link-button" href={item.audio_url || `/api/voice/audio/${item.id}`} target="_blank" rel="noreferrer">
                Putar {item.download_name || item.audio_filename || `voice-${item.id}.wav`}
              </a>
              <a class="link-button" href={item.download_url || `/api/voice/audio/${item.id}/download`} target="_blank" rel="noreferrer">
                Unduh {item.download_name || item.audio_filename || `voice-${item.id}.wav`}
              </a>
            {/if}
            <button
              class="btn btn-danger"
              type="button"
              onclick={() => onDeleteGeneration(item.id)}
              disabled={busy}
              aria-label={`Hapus artifact ${item.download_name || item.audio_filename || `voice-${item.id}.wav`}`}
            >
              Hapus Artifact
            </button>
          </div>
        </article>
      {/each}
    {/if}
  </div>
</section>

<style>
  .section-head {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: flex-start;
  }

  .section-head h3,
  .section-head.compact h4,
  .section-head.compact p,
  .section-head.compact strong,
  .section-head p {
    margin: 0;
  }

  .section-head h3 {
    font-size: 1.22rem;
    line-height: 1.2;
    letter-spacing: -0.02em;
  }

  .section-head p {
    margin-top: 0.45rem;
    color: var(--text-secondary);
    line-height: 1.55;
  }

  .summary-grid,
  .meta-grid {
    display: grid;
    gap: 0.75rem;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    min-width: 0;
  }

  .summary-card,
  .latest-card,
  .library-card {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 1.25rem;
    padding: 1.05rem;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.015)),
      rgba(18, 18, 35, 0.9);
  }

  .filter-row {
    display: grid;
    gap: 0.75rem;
    grid-template-columns: minmax(0, 2fr) repeat(2, minmax(180px, 1fr));
    min-width: 0;
  }

  .filter-row input,
  .filter-row select {
    width: 100%;
    min-width: 0;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    padding: 0.92rem 1rem;
    background: rgba(8, 8, 18, 0.72);
    color: var(--text);
    font: inherit;
    transition: border-color 0.18s ease, box-shadow 0.18s ease;
  }

  .filter-row input:focus,
  .filter-row select:focus {
    outline: none;
    border-color: rgba(233, 69, 96, 0.48);
    box-shadow: 0 0 0 3px rgba(233, 69, 96, 0.14);
  }

  .library-list {
    display: grid;
    gap: 1rem;
    min-width: 0;
  }

  .prompt-text {
    color: var(--text-secondary);
    line-height: 1.55;
  }

  .status-chip,
  .attach-badge {
    align-self: start;
    border-radius: 999px;
    padding: 0.35rem 0.75rem;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: var(--text-soft);
  }

  .attach-badge {
    border-color: rgba(233, 69, 96, 0.22);
    background: rgba(233, 69, 96, 0.14);
    color: #ffc5cf;
  }

  .action-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .empty-copy {
    color: var(--text-secondary);
  }

  .missing-artifact {
    display: grid;
    gap: 0.35rem;
    padding: 0.95rem 1rem;
    border-radius: 1rem;
    border: 1px solid rgba(245, 158, 11, 0.18);
    background:
      linear-gradient(180deg, rgba(245, 158, 11, 0.12), rgba(245, 158, 11, 0.08)),
      rgba(36, 24, 7, 0.9);
    color: #ffd68a;
  }

  .missing-artifact p,
  .missing-artifact strong {
    margin: 0;
  }

  audio {
    width: 100%;
    min-width: 0;
    border-radius: 999px;
    background: rgba(7, 7, 16, 0.75);
  }

  .meta-grid span {
    display: block;
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .meta-grid strong {
    display: block;
    word-break: break-word;
  }

  .link-button,
  .btn-danger {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 46px;
    padding: 0.8rem 1rem;
    border-radius: 999px;
    text-decoration: none;
    font-weight: 700;
    transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
  }

  .link-button:hover,
  .btn-danger:hover {
    transform: translateY(-1px);
  }

  .link-button {
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(255, 255, 255, 0.04);
    color: var(--text);
  }

  .btn-danger {
    border: 1px solid rgba(255, 107, 107, 0.2);
    background: rgba(255, 107, 107, 0.12);
    color: #ffc1c1;
  }

  @media (max-width: 768px) {
    .section-head,
    .filter-row {
      grid-template-columns: 1fr;
      display: grid;
    }
  }

  @media (max-width: 1280px) {
    .filter-row {
      grid-template-columns: 1fr;
    }
  }
</style>
