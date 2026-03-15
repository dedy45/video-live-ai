<script lang="ts">
  import type { VoiceProfile, VoiceReferenceAsset, VoiceTrainingJob } from '../../../lib/types';

  interface Props {
    busy: boolean;
    quickCloneProfiles: VoiceProfile[];
    studioProfiles: VoiceProfile[];
    voiceTrainingJobs: VoiceTrainingJob[];
    voiceReferenceAssets: VoiceReferenceAsset[];
    onCreateProfile: (payload: {
      name: string;
      reference_wav_path: string;
      reference_text: string;
      language: string;
      supported_languages?: string[];
      profile_type?: string;
      quality_tier?: string;
      guidance?: Record<string, any>;
      notes: string;
      engine?: string;
    }) => void | Promise<void>;
    onActivateProfile: (profileId: number) => void | Promise<void>;
    onCreateTrainingJob: (payload: {
      profile_id: number;
      job_type: string;
      dataset_path: string;
    }) => void | Promise<void>;
  }

  let {
    busy,
    quickCloneProfiles,
    studioProfiles,
    voiceTrainingJobs,
    voiceReferenceAssets,
    onCreateProfile,
    onActivateProfile,
    onCreateTrainingJob,
  }: Props = $props();

  let quickCloneName = $state('');
  let quickCloneReferencePath = $state('');
  let quickCloneRefText = $state('');
  let quickCloneLanguage = $state('id');
  let quickCloneNotes = $state('');

  let studioVoiceName = $state('');
  let studioVoiceReferencePath = $state('');
  let studioVoiceRefText = $state('');
  let studioVoiceNotes = $state('');

  let trainingProfileId = $state('');
  let trainingDatasetPath = $state('');

  const defaultReferencePath = $derived(
    voiceReferenceAssets.find((item) => item.is_default)?.path || voiceReferenceAssets[0]?.path || '',
  );
  const selectedQuickCloneAsset = $derived(
    voiceReferenceAssets.find((item) => item.path === quickCloneReferencePath) || null,
  );
  const selectedStudioAsset = $derived(
    voiceReferenceAssets.find((item) => item.path === studioVoiceReferencePath) || null,
  );

  $effect(() => {
    if (!quickCloneReferencePath && defaultReferencePath) {
      quickCloneReferencePath = defaultReferencePath;
    }
    if (!studioVoiceReferencePath && defaultReferencePath) {
      studioVoiceReferencePath = defaultReferencePath;
    }
    if (!trainingProfileId || !studioProfiles.some((profile) => String(profile.id) === trainingProfileId)) {
      trainingProfileId = studioProfiles[0]?.id ? String(studioProfiles[0].id) : '';
    }
  });

  $effect(() => {
    if (!quickCloneRefText.trim() && selectedQuickCloneAsset?.transcript_preview) {
      quickCloneRefText = selectedQuickCloneAsset.transcript_preview;
    }
  });

  $effect(() => {
    if (!studioVoiceRefText.trim() && selectedStudioAsset?.transcript_preview) {
      studioVoiceRefText = selectedStudioAsset.transcript_preview;
    }
  });

  const quickCloneReady = $derived(
    Boolean(quickCloneReferencePath && quickCloneRefText.trim() && quickCloneName.trim()),
  );
  const studioVoiceReady = $derived(
    Boolean(studioVoiceReferencePath && studioVoiceRefText.trim() && studioVoiceName.trim()),
  );
  const hasReferenceAssets = $derived(voiceReferenceAssets.length > 0);

  function submitQuickClone() {
    if (!quickCloneReady) return;
    onCreateProfile({
      name: quickCloneName.trim(),
      reference_wav_path: quickCloneReferencePath.trim(),
      reference_text: quickCloneRefText.trim(),
      language: quickCloneLanguage,
      supported_languages: ['id'],
      profile_type: 'quick_clone',
      quality_tier: 'quick',
      guidance: {
        min_seconds: 30,
        ideal_seconds: 90,
        tips: ['clean_voice', 'exact_transcript', 'indonesian_only'],
      },
      notes: quickCloneNotes.trim(),
      engine: 'fish_speech',
    });
  }

  function submitStudioVoice() {
    if (!studioVoiceReady) return;
    onCreateProfile({
      name: studioVoiceName.trim(),
      reference_wav_path: studioVoiceReferencePath.trim(),
      reference_text: studioVoiceRefText.trim(),
      language: 'id',
      supported_languages: ['id'],
      profile_type: 'studio_voice',
      quality_tier: 'studio',
      guidance: {
        training_target_minutes: { id: [30, 60] },
        dataset_mode: 'automatic_first',
        language_scope: 'indonesian_only',
      },
      notes: studioVoiceNotes.trim(),
      engine: 'fish_speech',
    });
  }

  function submitTrainingJob() {
    const profileId = Number(trainingProfileId);
    if (!profileId) return;
    onCreateTrainingJob({
      profile_id: profileId,
      job_type: 'studio_voice_training',
      dataset_path: trainingDatasetPath.trim(),
    });
  }

  function formatBytes(value: number | null | undefined) {
    const bytes = Number(value || 0);
    if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${bytes} B`;
  }
</script>

<div class="manager-stack">
  <section class="card">
    <div class="section-head">
      <div>
        <h3>2. Quick Clone</h3>
        <p>Pilih file WAV referensi yang valid, isi transkrip sesuai audio, lalu simpan clone agar bisa langsung dipakai di langkah generate.</p>
      </div>
    </div>

    <div class="guidance-grid">
      <article class="note-card">
        <strong>Syarat referensi</strong>
        <p>Durasi ideal 30-90 detik. Gunakan suara tunggal, jarak mic stabil, dan transkrip harus sesuai audio.</p>
      </article>
      <article class="note-card">
        <strong>QC minimum</strong>
        <p>Hindari noise, musik, dan clipping. Gunakan sampel Indonesia yang jelas dan konsisten agar logat tetap natural.</p>
      </article>
      <article class="note-card">
        <strong>Alur cepat</strong>
        <p>1 pilih WAV, 2 isi transkrip, 3 simpan clone, 4 aktifkan clone, 5 kembali ke Generate Audio.</p>
      </article>
    </div>

    {#if !hasReferenceAssets}
      <div class="note-card warning">
        <strong>Belum ada file reference</strong>
        <p>Tambahkan file `.wav` ke `assets/voice` atau `data/runtime/voice/references`, lalu muat ulang tab Suara.</p>
      </div>
    {/if}

    <div class="profile-list">
      {#if quickCloneProfiles.length === 0}
        <p class="empty-copy">Belum ada quick clone.</p>
      {:else}
        {#each quickCloneProfiles as profile}
          <div class="profile-row">
            <div>
              <strong>{profile.name}</strong>
              <p>{profile.reference_wav_path} · {profile.language.toUpperCase()} · Indonesia only</p>
            </div>
            <button class="btn btn-secondary" type="button" onclick={() => onActivateProfile(profile.id)} disabled={busy || profile.is_active}>
              {profile.is_active ? 'Aktif' : 'Pakai Clone'}
            </button>
          </div>
        {/each}
      {/if}
    </div>

    <div class="form-grid">
      <label class="field">
        <span>Nama clone</span>
        <input bind:value={quickCloneName} aria-label="Nama clone" placeholder="Contoh: Host Indo" disabled={busy} />
      </label>
      <label class="field field-full">
        <span>File WAV referensi</span>
        <select bind:value={quickCloneReferencePath} aria-label="File WAV referensi" disabled={busy || !hasReferenceAssets}>
          <option value="">Pilih reference WAV</option>
          {#each voiceReferenceAssets as asset}
            <option value={asset.path}>{asset.label} · {asset.source} · {formatBytes(asset.file_size_bytes)}</option>
          {/each}
        </select>
      </label>
      {#if selectedQuickCloneAsset}
        <article class="asset-card field-full">
          <strong>Reference terpilih</strong>
          <p>{selectedQuickCloneAsset.path}</p>
          <small>{selectedQuickCloneAsset.transcript_path ? `Transkrip sampingan: ${selectedQuickCloneAsset.transcript_path}` : 'Belum ada file .txt sampingan; isi transkrip manual di bawah.'}</small>
        </article>
      {/if}
      <label class="field field-full">
        <span>Transkrip referensi</span>
        <textarea bind:value={quickCloneRefText} aria-label="Transkrip referensi" rows="4" placeholder="Tuliskan transkrip sesuai isi audio referensi" disabled={busy}></textarea>
      </label>
      <label class="field field-full">
        <span>Catatan clone</span>
        <input bind:value={quickCloneNotes} aria-label="Catatan clone" placeholder="Opsional: karakter suara, mic, atau konteks" disabled={busy} />
      </label>
    </div>
    <button class="btn btn-primary" type="button" onclick={submitQuickClone} disabled={busy || !quickCloneReady}>Simpan Quick Clone</button>
  </section>

  <section class="card">
    <div class="section-head">
      <div>
        <h3>3. Studio Voice</h3>
        <p>Profile produksi Indonesia tunggal. Bagian ini untuk menyiapkan identitas suara live yang stabil sebelum masuk ke training job.</p>
      </div>
    </div>
    <div class="guidance-grid">
      <article class="note-card">
        <strong>Indonesia production</strong>
        <p>Studio Voice difokuskan ke Bahasa Indonesia agar logat tidak bercampur. Operator tidak lagi berpindah bahasa di workflow ini.</p>
      </article>
      <article class="note-card">
        <strong>Automatic-first dataset</strong>
        <p>Target produksi: 30-60 menit per bahasa. Seed reference dipakai untuk identitas awal sebelum dataset/training penuh.</p>
      </article>
    </div>
    <div class="profile-list">
      {#if studioProfiles.length === 0}
        <p class="empty-copy">Belum ada studio voice.</p>
      {:else}
        {#each studioProfiles as profile}
          <div class="profile-row">
            <div>
              <strong>{profile.name}</strong>
              <p>{profile.notes || 'Studio voice Indonesia stabil'} · Indonesia only</p>
            </div>
            <button class="btn btn-secondary" type="button" onclick={() => onActivateProfile(profile.id)} disabled={busy || profile.is_active}>
              {profile.is_active ? 'Aktif' : 'Jadikan Aktif'}
            </button>
          </div>
        {/each}
      {/if}
    </div>
    <div class="form-grid">
      <label class="field">
        <span>Nama studio voice</span>
        <input bind:value={studioVoiceName} aria-label="Nama studio voice" placeholder="Contoh: Browser Studio Voice" disabled={busy} />
      </label>
      <label class="field field-full">
        <span>Seed reference WAV</span>
        <select bind:value={studioVoiceReferencePath} aria-label="Seed reference WAV" disabled={busy || !hasReferenceAssets}>
          <option value="">Pilih seed reference</option>
          {#each voiceReferenceAssets as asset}
            <option value={asset.path}>{asset.label} · {asset.source} · {formatBytes(asset.file_size_bytes)}</option>
          {/each}
        </select>
      </label>
      <label class="field field-full">
        <span>Transkrip sample utama</span>
        <textarea bind:value={studioVoiceRefText} aria-label="Transkrip sample utama" rows="4" placeholder="Tuliskan transkrip seed reference untuk studio voice" disabled={busy}></textarea>
      </label>
      <label class="field field-full">
        <span>Catatan studio voice</span>
        <input bind:value={studioVoiceNotes} aria-label="Catatan studio voice" placeholder="Contoh: host utama Indonesia production stable" disabled={busy} />
      </label>
    </div>
    <button class="btn btn-primary" type="button" onclick={submitStudioVoice} disabled={busy || !studioVoiceReady}>Buat Studio Voice</button>
  </section>

  <section class="card">
    <div class="section-head">
      <div>
        <h3>4. Training Jobs</h3>
        <p>Setelah studio voice siap, queue training dari sini. Dashboard tetap jadi single source of truth, dan training diblok saat live aktif.</p>
      </div>
    </div>
    <div class="note-card warning">
      <strong>Guardrail live</strong>
      <p>Training diblok saat live aktif agar host GPU tetap fokus ke runtime TTS, avatar, dan sesi live.</p>
    </div>
    <div class="form-grid">
      <label class="field">
        <span>Studio voice target</span>
        <select aria-label="Studio voice target" bind:value={trainingProfileId} disabled={busy}>
          <option value="">Pilih studio voice</option>
          {#each studioProfiles as profile}
            <option value={String(profile.id)}>{profile.name}</option>
          {/each}
        </select>
      </label>
      <label class="field field-full">
        <span>Lokasi dataset</span>
        <input bind:value={trainingDatasetPath} aria-label="Lokasi dataset" placeholder="data/runtime/voice/datasets/studio-sari" disabled={busy} />
      </label>
    </div>
    <button class="btn btn-primary" type="button" onclick={submitTrainingJob} disabled={busy || !trainingProfileId}>Queue Training Job</button>
    <div class="history-list">
      {#if voiceTrainingJobs.length === 0}
        <p class="empty-copy">Belum ada training job.</p>
      {:else}
        {#each voiceTrainingJobs as job}
          <div class="history-row">
            <div>
              <strong>{job.profile_name || 'Studio voice'}</strong>
              <p>{job.dataset_path || 'Dataset belum diisi'}</p>
            </div>
            <div class="history-meta">
              <span>{job.status}</span>
              <span>{job.current_stage}</span>
            </div>
          </div>
        {/each}
      {/if}
    </div>
  </section>
</div>

<style>
  .manager-stack,
  .guidance-grid,
  .form-grid {
    display: grid;
    gap: 1rem;
  }

  .guidance-grid {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }

  .note-card,
  .profile-row,
  .history-row,
  .asset-card {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 1.25rem;
    padding: 1rem;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.015)),
      rgba(18, 18, 35, 0.9);
  }

  .asset-card {
    display: grid;
    gap: 0.35rem;
  }

  .asset-card p,
  .asset-card small,
  .asset-card strong {
    margin: 0;
  }

  .note-card.warning {
    border-color: rgba(245, 158, 11, 0.18);
    background:
      linear-gradient(180deg, rgba(245, 158, 11, 0.14), rgba(245, 158, 11, 0.08)),
      rgba(36, 24, 7, 0.9);
  }

  .profile-list,
  .history-list {
    display: grid;
    gap: 0.75rem;
  }

  .profile-row,
  .history-row,
  .section-head {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: flex-start;
  }

  .field-full {
    grid-column: 1 / -1;
  }

  .empty-copy {
    color: var(--text-secondary);
  }

  .history-meta {
    display: grid;
    gap: 0.35rem;
    text-align: right;
    color: var(--text-secondary);
  }

  .section-head h3,
  .section-head p,
  .field span {
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

  .field {
    display: grid;
    gap: 0.5rem;
    font-size: 0.95rem;
    color: var(--text-secondary);
  }

  .field span {
    color: var(--text-soft);
    font-weight: 700;
  }

  .field input,
  .field textarea,
  .field select {
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    padding: 0.92rem 1rem;
    background: rgba(8, 8, 18, 0.72);
    color: var(--text);
    font: inherit;
    transition: border-color 0.18s ease, box-shadow 0.18s ease;
  }

  .field textarea {
    resize: vertical;
  }

  .field input:focus,
  .field textarea:focus,
  .field select:focus {
    outline: none;
    border-color: rgba(233, 69, 96, 0.48);
    box-shadow: 0 0 0 3px rgba(233, 69, 96, 0.14);
  }

  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 46px;
    padding: 0.8rem 1rem;
    border-radius: 999px;
    font-weight: 700;
    transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
  }

  .btn:hover {
    transform: translateY(-1px);
  }

  .btn-primary {
    border: 1px solid rgba(255, 191, 202, 0.18);
    background: linear-gradient(135deg, rgba(233, 69, 96, 0.98), rgba(255, 123, 108, 0.94));
    color: #160913;
  }

  .btn-secondary {
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(255, 255, 255, 0.04);
    color: var(--text);
  }

  @media (max-width: 768px) {
    .profile-row,
    .history-row,
    .section-head {
      flex-direction: column;
    }
  }
</style>
