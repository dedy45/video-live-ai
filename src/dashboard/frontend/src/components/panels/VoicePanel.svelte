<script lang="ts">
  import type {
    RuntimeTruth,
    VoiceGeneration,
    VoiceLabState,
    VoiceProfile,
    VoiceTestSpeakResult,
    VoiceTrainingJob,
  } from '../../lib/types';

  type WorkspaceId = 'generate' | 'quick_clone' | 'studio_voice' | 'training_jobs' | 'library';

  interface Props {
    truth: RuntimeTruth | null;
    busyAction: string;
    voiceTestResult: VoiceTestSpeakResult | null;
    voiceProfiles: VoiceProfile[];
    voiceLabState: VoiceLabState | null;
    voiceGenerations: VoiceGeneration[];
    voiceTrainingJobs: VoiceTrainingJob[];
    onWarmup: () => void | Promise<void>;
    onRestart: () => void | Promise<void>;
    onClearQueue: () => void | Promise<void>;
    onTestSpeak: (text: string) => void | Promise<void>;
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
    onChangeMode: (payload: Partial<VoiceLabState>) => void | Promise<void>;
    onGenerateVoice: (payload: {
      mode: string;
      profile_id: number | null;
      text: string;
      language: string;
      emotion: string;
      style_preset: string;
      stability: number;
      similarity: number;
      speed: number;
      attach_to_avatar: boolean;
    }) => void | Promise<void>;
    onCreateTrainingJob: (payload: {
      profile_id: number;
      job_type: string;
      dataset_path: string;
    }) => void | Promise<void>;
  }

  let {
    truth,
    busyAction,
    voiceTestResult,
    voiceProfiles = [],
    voiceLabState = null,
    voiceGenerations = [],
    voiceTrainingJobs = [],
    onWarmup,
    onRestart,
    onClearQueue,
    onTestSpeak,
    onCreateProfile,
    onActivateProfile,
    onChangeMode,
    onGenerateVoice,
    onCreateTrainingJob,
  }: Props = $props();

  const workspaces: Array<{ id: WorkspaceId; label: string }> = [
    { id: 'generate', label: 'Generate' },
    { id: 'quick_clone', label: 'Quick Clone' },
    { id: 'studio_voice', label: 'Studio Voice' },
    { id: 'training_jobs', label: 'Training Jobs' },
    { id: 'library', label: 'Library' },
  ];

  let activeWorkspace = $state<WorkspaceId>('generate');
  let promptText = $state('Halo operator');
  let quickTestText = $state('Halo operator');
  let selectedLanguage = $state('id');
  let selectedStylePreset = $state('natural');
  let selectedStability = $state(0.75);
  let selectedSimilarity = $state(0.8);
  let selectedGenerateProfileId = $state<number | null>(null);

  let quickCloneName = $state('');
  let quickCloneWavPath = $state('');
  let quickCloneRefText = $state('');
  let quickCloneNotes = $state('');

  let studioVoiceName = $state('');
  let studioVoiceRefPath = $state('');
  let studioVoiceRefText = $state('');
  let studioVoiceNotes = $state('');

  let trainingProfileId = $state('');
  let trainingDatasetPath = $state('');

  const voice = $derived(truth?.voice_engine);
  const busy = $derived(busyAction !== '');
  const currentMode = $derived(voiceLabState?.mode || 'standalone');
  const attachReady = $derived(Boolean(voiceLabState?.preview_session_id));
  const quickCloneProfiles = $derived(voiceProfiles.filter((item) => (item.profile_type || 'quick_clone') === 'quick_clone'));
  const studioProfiles = $derived(voiceProfiles.filter((item) => item.profile_type === 'studio_voice'));
  const activeProfile = $derived(
    voiceProfiles.find((item) => item.id === (selectedGenerateProfileId ?? voiceLabState?.active_profile_id)) || null,
  );
  const voiceStatus = $derived.by(() => {
    if (!voice) return { label: 'Belum ada data', summary: 'Snapshot suara belum tersedia.' };
    if (voice.server_reachable && voice.reference_ready) {
      return { label: 'Siap', summary: 'Mesin suara terhubung dan referensi sudah siap.' };
    }
    if (!voice.server_reachable) {
      return { label: 'Tertahan', summary: 'Sidecar suara belum bisa dijangkau.' };
    }
    if (!voice.reference_ready) {
      return { label: 'Perlu referensi', summary: 'Referensi suara belum siap dipakai.' };
    }
    return { label: 'Belum aktif', summary: 'Mesin suara belum dipanaskan.' };
  });

  $effect(() => {
    promptText = voiceLabState?.draft_text || 'Halo operator';
    selectedLanguage = voiceLabState?.selected_language || 'id';
    selectedStylePreset = voiceLabState?.selected_style_preset || 'natural';
    selectedStability = Number(voiceLabState?.selected_stability ?? 0.75);
    selectedSimilarity = Number(voiceLabState?.selected_similarity ?? 0.8);
    selectedGenerateProfileId = voiceLabState?.active_profile_id ?? voiceProfiles[0]?.id ?? null;
    trainingProfileId = studioProfiles[0]?.id ? String(studioProfiles[0].id) : '';
  });

  function selectWorkspace(workspace: WorkspaceId) {
    activeWorkspace = workspace;
  }

  function changeMode(mode: 'standalone' | 'attach_avatar') {
    onChangeMode({
      mode,
      active_profile_id: selectedGenerateProfileId ?? voiceLabState?.active_profile_id ?? null,
      preview_session_id: voiceLabState?.preview_session_id || '',
      selected_avatar_id: voiceLabState?.selected_avatar_id || '',
      selected_language: selectedLanguage,
      selected_profile_type: activeProfile?.profile_type || 'quick_clone',
      selected_revision_id: voiceLabState?.selected_revision_id ?? null,
      selected_style_preset: selectedStylePreset,
      selected_stability: selectedStability,
      selected_similarity: selectedSimilarity,
      draft_text: promptText,
      last_generation_id: voiceLabState?.last_generation_id ?? null,
    });
  }

  function submitGenerate() {
    onGenerateVoice({
      mode: currentMode,
      profile_id: selectedGenerateProfileId ?? voiceLabState?.active_profile_id ?? activeProfile?.id ?? null,
      text: promptText.trim() || 'Halo operator',
      language: selectedLanguage,
      emotion: 'neutral',
      style_preset: selectedStylePreset,
      stability: Number(selectedStability),
      similarity: Number(selectedSimilarity),
      speed: 1,
      attach_to_avatar: currentMode === 'attach_avatar',
    });
  }

  function submitQuickTest() {
    onTestSpeak(quickTestText.trim() || 'Halo operator');
  }

  function submitQuickClone() {
    onCreateProfile({
      name: quickCloneName.trim() || 'Voice Clone Baru',
      reference_wav_path: quickCloneWavPath.trim(),
      reference_text: quickCloneRefText.trim(),
      language: 'id',
      supported_languages: ['id', 'en'],
      profile_type: 'quick_clone',
      quality_tier: 'quick',
      guidance: {
        min_seconds: 30,
        ideal_seconds: 90,
        tips: ['clean_voice', 'exact_transcript', 'bilingual_ready'],
      },
      notes: quickCloneNotes.trim(),
      engine: 'fish_speech',
    });
  }

  function submitStudioVoice() {
    onCreateProfile({
      name: studioVoiceName.trim() || 'Studio Voice Baru',
      reference_wav_path: studioVoiceRefPath.trim(),
      reference_text: studioVoiceRefText.trim(),
      language: 'id',
      supported_languages: ['id', 'en'],
      profile_type: 'studio_voice',
      quality_tier: 'studio',
      guidance: {
        training_target_minutes: { id: [30, 60], en: [30, 60] },
        dataset_mode: 'automatic_first',
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
</script>

<section class="panel" data-testid="voice-panel">
  <div class="panel-head">
    <div>
      <h2>Suara</h2>
      <p>{voiceStatus.summary}</p>
    </div>
    <div class="status-pill">{voiceStatus.label}</div>
  </div>

  <div class="hero-grid">
    <article class="hero-card">
      <span class="eyebrow">Mesin</span>
      <strong>{voice?.resolved_engine || 'Belum diketahui'}</strong>
      <p>Diminta {voice?.requested_engine || 'unknown'}</p>
    </article>
    <article class="hero-card">
      <span class="eyebrow">Profile aktif</span>
      <strong>{activeProfile?.name || 'Belum dipilih'}</strong>
      <p>{activeProfile?.reference_wav_path || 'Pilih clone/reference dulu'}</p>
    </article>
    <article class="hero-card">
      <span class="eyebrow">Attach session</span>
      <strong>{attachReady ? 'Terhubung' : 'Belum ada'}</strong>
      <p>{attachReady ? `Session ${voiceLabState?.preview_session_id}` : 'Buka preview avatar dan tekan Start dulu.'}</p>
    </article>
  </div>

  <div class="mode-switch" role="group" aria-label="Voice lab mode">
    <button class:is-active={currentMode === 'standalone'} class="mode-button" type="button" onclick={() => changeMode('standalone')} disabled={busy}>
      Standalone Fish TTS
    </button>
    <button class:is-active={currentMode === 'attach_avatar'} class="mode-button" type="button" onclick={() => changeMode('attach_avatar')} disabled={busy}>
      Attach ke Avatar
    </button>
  </div>

  <div class="workspace-tabs" role="tablist" aria-label="Voice Lab Workspace">
    {#each workspaces as workspace}
      <button
        role="tab"
        type="button"
        class:is-active={activeWorkspace === workspace.id}
        class="workspace-tab"
        aria-selected={activeWorkspace === workspace.id}
        onclick={() => selectWorkspace(workspace.id)}
      >
        {workspace.label}
      </button>
    {/each}
  </div>

  <div class="layout-grid">
    <div class="workspace-card">
      {#if activeWorkspace === 'generate'}
        <div class="section-head">
          <h3>Generate</h3>
          <p>Generate suara langsung dari web. Utamakan Indonesia dan English untuk preview cepat maupun live attach.</p>
        </div>
        <div class="form-grid">
          <label class="field">
            <span>Bahasa output</span>
            <select aria-label="Bahasa output" bind:value={selectedLanguage} disabled={busy}>
              <option value="id">Indonesia</option>
              <option value="en">English</option>
            </select>
          </label>
          <label class="field">
            <span>Voice Profile</span>
            <select aria-label="Voice profile" bind:value={selectedGenerateProfileId} disabled={busy}>
              {#each voiceProfiles as profile}
                <option value={profile.id}>
                  {profile.name} · {profile.profile_type === 'studio_voice' ? 'Studio Voice' : 'Quick Clone'}
                </option>
              {/each}
            </select>
          </label>
          <label class="field">
            <span>Gaya suara</span>
            <select aria-label="Gaya suara" bind:value={selectedStylePreset} disabled={busy}>
              <option value="natural">Natural</option>
              <option value="conversational">Conversational</option>
              <option value="sales_live">Sales Live</option>
            </select>
          </label>
          <label class="field">
            <span>Stability</span>
            <input aria-label="Stability" type="range" min="0.2" max="1" step="0.01" bind:value={selectedStability} disabled={busy} />
            <small>{selectedStability.toFixed(2)}</small>
          </label>
          <label class="field">
            <span>Similarity</span>
            <input aria-label="Similarity" type="range" min="0.2" max="1" step="0.01" bind:value={selectedSimilarity} disabled={busy} />
            <small>{selectedSimilarity.toFixed(2)}</small>
          </label>
        </div>
        <label class="field">
          <span>Prompt suara</span>
          <textarea aria-label="Prompt suara" bind:value={promptText} rows="6" placeholder="Masukkan prompt suara" disabled={busy}></textarea>
        </label>
        <div class="action-row">
          <button class="btn btn-primary" type="button" onclick={submitGenerate} disabled={busy}>
            {currentMode === 'attach_avatar' ? 'Generate & Attach' : 'Generate Audio'}
          </button>
          <span class="hint">
            {currentMode === 'attach_avatar'
              ? attachReady
                ? `Attach siap ke session ${voiceLabState?.preview_session_id}`
                : 'Attach butuh preview avatar aktif lebih dulu.'
              : 'Hasil generate akan masuk ke Library dan bisa diputar atau diunduh.'}
          </span>
        </div>
      {:else if activeWorkspace === 'quick_clone'}
        <div class="section-head">
          <h3>Quick Clone</h3>
          <p>Clone cepat untuk eksperimen operator. Cocok untuk draft, A/B test, dan voice lab interaktif.</p>
        </div>
        <div class="guidance-grid">
          <article class="note-card">
            <strong>Syarat referensi</strong>
            <p>Durasi ideal 30-90 detik. Gunakan suara tunggal, jarak mic stabil, dan transkrip harus sesuai audio.</p>
          </article>
          <article class="note-card">
            <strong>QC minimum</strong>
            <p>Hindari noise, musik, dan clipping. Untuk bilingual, usahakan ada sampel Indonesia dan English.</p>
          </article>
        </div>
        <div class="profile-list">
          {#if quickCloneProfiles.length === 0}
            <p class="card-copy">Belum ada quick clone.</p>
          {:else}
            {#each quickCloneProfiles as profile}
              <div class="profile-row">
                <div>
                  <strong>{profile.name}</strong>
                  <p>{profile.reference_wav_path}</p>
                </div>
                <button class="btn btn-secondary" type="button" onclick={() => onActivateProfile(profile.id)} disabled={busy || profile.is_active}>
                  {profile.is_active ? 'Aktif' : 'Pilih Clone'}
                </button>
              </div>
            {/each}
          {/if}
        </div>
        <div class="form-grid">
          <label class="field">
            <span>Nama clone</span>
            <input aria-label="Nama clone" bind:value={quickCloneName} placeholder="Nama clone" disabled={busy} />
          </label>
          <label class="field">
            <span>Path WAV referensi</span>
            <input aria-label="Path WAV referensi" bind:value={quickCloneWavPath} placeholder="Path WAV referensi" disabled={busy} />
          </label>
          <label class="field field-full">
            <span>Transkrip referensi</span>
            <textarea aria-label="Transkrip referensi" bind:value={quickCloneRefText} rows="4" placeholder="Transkrip referensi" disabled={busy}></textarea>
          </label>
          <label class="field field-full">
            <span>Catatan clone</span>
            <input aria-label="Catatan clone" bind:value={quickCloneNotes} placeholder="Catatan clone" disabled={busy} />
          </label>
        </div>
        <button class="btn btn-primary" type="button" onclick={submitQuickClone} disabled={busy}>Simpan Quick Clone</button>
      {:else if activeWorkspace === 'studio_voice'}
        <div class="section-head">
          <h3>Studio Voice</h3>
          <p>Voice produksi bilingual tunggal. Target kualitas: production stable dengan dataset 30-60 menit per bahasa.</p>
        </div>
        <div class="guidance-grid">
          <article class="note-card">
            <strong>Bilingual production</strong>
            <p>1 Studio Voice bilingual dengan generate eksplisit per bahasa. Dashboard tetap minta pilihan `Indonesia` atau `English` setiap synth.</p>
          </article>
          <article class="note-card">
            <strong>Automatic-first dataset</strong>
            <p>Upload panjang nantinya dipecah, ditranskrip, dan di-QC otomatis. Day-1 ini fokus pada profile dan training job control-plane.</p>
          </article>
        </div>
        <div class="profile-list">
          {#if studioProfiles.length === 0}
            <p class="card-copy">Belum ada studio voice.</p>
          {:else}
            {#each studioProfiles as profile}
              <div class="profile-row">
                <div>
                  <strong>{profile.name}</strong>
                  <p>{profile.notes || 'Studio voice production stable'}</p>
                </div>
                <button class="btn btn-secondary" type="button" onclick={() => onActivateProfile(profile.id)} disabled={busy || profile.is_active}>
                  {profile.is_active ? 'Aktif' : 'Set Aktif'}
                </button>
              </div>
            {/each}
          {/if}
        </div>
        <div class="form-grid">
          <label class="field">
            <span>Nama studio voice</span>
            <input bind:value={studioVoiceName} placeholder="Nama studio voice" disabled={busy} />
          </label>
          <label class="field">
            <span>Path reference utama</span>
            <input bind:value={studioVoiceRefPath} placeholder="Path reference utama" disabled={busy} />
          </label>
          <label class="field field-full">
            <span>Transkrip sample utama</span>
            <textarea bind:value={studioVoiceRefText} rows="4" placeholder="Transkrip sample utama" disabled={busy}></textarea>
          </label>
          <label class="field field-full">
            <span>Catatan studio voice</span>
            <input bind:value={studioVoiceNotes} placeholder="Catatan studio voice" disabled={busy} />
          </label>
        </div>
        <button class="btn btn-primary" type="button" onclick={submitStudioVoice} disabled={busy}>Buat Studio Voice</button>
      {:else if activeWorkspace === 'training_jobs'}
        <div class="section-head">
          <h3>Training Jobs</h3>
          <p>Dashboard menjadi single source of truth untuk queue training. Training diblok saat live aktif.</p>
        </div>
        <div class="note-card warning">
          <strong>Guardrail live</strong>
          <p>Training diblok saat live aktif agar host GPU tetap fokus ke runtime TTS/avatar/live session.</p>
        </div>
        <div class="form-grid">
          <label class="field">
            <span>Studio Voice target</span>
            <select aria-label="Studio voice target" bind:value={trainingProfileId} disabled={busy}>
              <option value="">Pilih studio voice</option>
              {#each studioProfiles as profile}
                <option value={profile.id}>{profile.name}</option>
              {/each}
            </select>
          </label>
          <label class="field field-full">
            <span>Lokasi dataset</span>
            <input aria-label="Lokasi dataset" bind:value={trainingDatasetPath} placeholder="data/runtime/voice/datasets/studio-sari" disabled={busy} />
          </label>
        </div>
        <button class="btn btn-primary" type="button" onclick={submitTrainingJob} disabled={busy || !trainingProfileId}>Queue Training Job</button>
        <div class="history-list">
          {#if voiceTrainingJobs.length === 0}
            <p class="card-copy">Belum ada training job.</p>
          {:else}
            {#each voiceTrainingJobs as job}
              <div class="history-row">
                <div>
                  <strong>{job.profile_name || `Profile ${job.profile_id}`}</strong>
                  <p>{job.job_type} · {job.current_stage}</p>
                </div>
                <div class="history-meta">
                  <span>{job.status}</span>
                  <span>{job.progress_pct}%</span>
                </div>
              </div>
            {/each}
          {/if}
        </div>
      {:else}
        <div class="section-head">
          <h3>Library</h3>
          <p>Semua hasil synth disimpan sebagai artifact lokal sehingga bisa diputar, diunduh, atau di-attach ulang.</p>
        </div>
        <div class="history-list">
          {#if voiceGenerations.length === 0}
            <p class="card-copy">Belum ada histori generate.</p>
          {:else}
            {#each voiceGenerations as item}
              <article class="library-card">
                <div class="library-head">
                  <div>
                    <strong>{item.profile_name || 'Profile tidak diketahui'}</strong>
                    <p>{item.language || 'id'} · {item.style_preset || 'natural'} · {item.source_type}</p>
                  </div>
                  <div class="history-meta">
                    <span>Latency {item.latency_ms} ms</span>
                    <span>Durasi {item.duration_ms} ms</span>
                  </div>
                </div>
                <p class="card-copy">{item.input_text}</p>
                <audio controls src={item.audio_url || `/api/voice/audio/${item.id}`}></audio>
                <div class="action-row">
                  <a class="link-button" href={item.audio_url || `/api/voice/audio/${item.id}`} target="_blank" rel="noreferrer">
                    Putar {item.download_name || item.audio_filename || `voice-${item.id}.wav`}
                  </a>
                  <a class="link-button" href={item.download_url || `/api/voice/audio/${item.id}/download`} target="_blank" rel="noreferrer">
                    Unduh {item.download_name || item.audio_filename || `voice-${item.id}.wav`}
                  </a>
                </div>
              </article>
            {/each}
          {/if}
        </div>
      {/if}
    </div>

    <div class="side-stack">
      <article class="card">
        <h3>Kontrol Operator</h3>
        <div class="button-stack">
          <button class="btn btn-primary" type="button" onclick={onWarmup} disabled={busy}>Panaskan Mesin Suara</button>
          <button class="btn btn-secondary" type="button" onclick={onRestart} disabled={busy}>Mulai Ulang Mesin Suara</button>
          <button class="btn btn-secondary" type="button" onclick={onClearQueue} disabled={busy}>Kosongkan Antrian Suara</button>
        </div>
      </article>

      <article class="card">
        <h3>Telemetri</h3>
        <div class="metric-list">
          <div><span>Chunk audio</span><strong>{voice?.chunk_chars ?? '—'}</strong></div>
          <div><span>Latency p50 / p95</span><strong>{voice?.latency_p50_ms ?? '—'} / {voice?.latency_p95_ms ?? '—'} ms</strong></div>
          <div><span>Audio pertama</span><strong>{voice?.time_to_first_audio_ms ?? '—'} ms</strong></div>
          <div><span>Error terakhir</span><strong>{voice?.last_error || 'Tidak ada'}</strong></div>
        </div>
      </article>

      <article class="card">
        <h3>Tes Suara Cepat</h3>
        <div class="test-row">
          <input bind:value={quickTestText} placeholder="Masukkan teks untuk disintesis" disabled={busy} />
          <button class="btn btn-primary" type="button" onclick={submitQuickTest} disabled={busy}>Tes Suara</button>
        </div>
        {#if voiceTestResult}
          <div class="telemetry-strip">
            <span>Latency {voiceTestResult.latency_ms ?? '—'} ms</span>
            <span>Durasi {voiceTestResult.duration_ms ?? '—'} ms</span>
            <span>Ukuran audio {voiceTestResult.audio_length_bytes ?? '—'} bytes</span>
          </div>
        {/if}
      </article>
    </div>
  </div>
</section>

<style>
  .panel,.hero-grid,.layout-grid,.side-stack,.card,.button-stack,.metric-list,.history-list,.profile-list,.guidance-grid { display:grid; gap:16px; }
  .panel-head,.mode-switch,.workspace-tabs,.action-row,.history-meta,.library-head,.test-row,.profile-row { display:flex; gap:12px; }
  .panel-head,.profile-row,.library-head { justify-content:space-between; align-items:flex-start; }
  .hero-grid,.layout-grid { grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); }
  .layout-grid { align-items:start; }
  .workspace-card { min-width:0; border-radius:var(--radius); border:1px solid var(--border); background:var(--card); padding:20px; display:grid; gap:18px; }
  .side-stack { min-width:0; }
  .card,.hero-card,.note-card,.library-card { border-radius:var(--radius); border:1px solid var(--border); background:var(--card); padding:18px; }
  .hero-card strong,.profile-row strong,.library-card strong { color:var(--text); }
  .hero-card strong { display:block; font-size:22px; }
  .eyebrow { display:block; margin-bottom:8px; font-size:12px; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); }
  .panel-head h2,.section-head h3,.card h3 { margin:0 0 6px; color:var(--text); }
  .panel-head p,.section-head p,.card-copy,.note-card p,.hero-card p,.profile-row p { margin:0; color:var(--muted); line-height:1.5; }
  .mode-switch,.workspace-tabs { flex-wrap:wrap; }
  .mode-button,.workspace-tab,.status-pill,.btn,.link-button { border-radius:12px; border:1px solid var(--border); padding:10px 14px; font:inherit; font-weight:700; text-decoration:none; }
  .mode-button,.workspace-tab,.btn-secondary,.link-button { background:rgba(255,255,255,.05); color:var(--text); }
  .mode-button.is-active,.workspace-tab.is-active,.btn-primary { background:var(--accent); color:#111827; border-color:transparent; }
  .workspace-tab[aria-selected="true"] { background:var(--accent); color:#111827; border-color:transparent; }
  .form-grid { display:grid; gap:14px; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); }
  .field { display:grid; gap:8px; color:var(--text); }
  .field-full { grid-column:1 / -1; }
  .field input,.field textarea,.field select,input,textarea,select {
    width:100%; min-width:0; padding:12px 14px; border-radius:12px; border:1px solid var(--border);
    background:rgba(255,255,255,.03); color:var(--text); font:inherit;
  }
  .field small,.hint,.history-meta,.telemetry-strip { color:var(--muted); }
  .guidance-grid { grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); }
  .warning { border-color:rgba(250,204,21,.4); background:rgba(250,204,21,.08); }
  .profile-row,.history-row { border-bottom:1px solid rgba(255,255,255,.05); padding-bottom:12px; }
  .profile-row:last-child,.history-row:last-child { border-bottom:none; padding-bottom:0; }
  .action-row { flex-wrap:wrap; align-items:center; }
  .button-stack { grid-template-columns:1fr; }
  .metric-list div { display:flex; justify-content:space-between; gap:12px; border-bottom:1px solid rgba(255,255,255,.05); padding-bottom:10px; }
  .metric-list div:last-child { border-bottom:none; padding-bottom:0; }
  .history-list,.library-card { gap:14px; }
  audio { width:100%; }
  .btn:disabled,.mode-button:disabled,.workspace-tab:disabled { opacity:.55; cursor:not-allowed; }
  @media (max-width: 900px) {
    .layout-grid { grid-template-columns:1fr; }
  }
  @media (max-width: 720px) {
    .panel-head,.profile-row,.library-head,.test-row { flex-direction:column; }
  }
</style>
