<script lang="ts">
  // === PROPS (from PerformerWorkspace) ===
  let {
    truth = null,
    busyAction = '',
    voiceTestResult = null,
    voiceProfiles = [],
    voiceReferenceAssets = [],
    voiceLabState = null,
    voiceGenerations = [],
    voiceLibrarySummary = null,
    voiceTrainingJobs = [],
    onWarmup = () => {},
    onRestart = () => {},
    onClearQueue = () => {},
    onTestSpeak = (_text: string) => {},
    onCreateProfile = (_data: any) => {},
    onActivateProfile = (_id: number) => {},
    onChangeMode = (_mode: string) => {},
    onGenerateVoice = (_data: any) => {},
    onCreateTrainingJob = (_data: any) => {},
    onDeleteGeneration = (_id: string) => {},
    onClearLibrary = () => {},
  }: any = $props();

  // === LOCAL STATE ===
  let activeTab = $state('generate');
  let testText = $state('Halo semuanya, selamat datang di live streaming kami.');
  let generateText = $state('');
  let errorMsg = $state('');
  let lastAudioUrl = $state('');

  // === DERIVED (null-safe) ===
  const voice = $derived(truth?.voice_engine ?? null);
  const engineName = $derived(voice?.requested_engine ?? 'Tidak diketahui');
  // FIX: server_reachable is an object {reachable: bool}, not a boolean
  const serverReachable = $derived(
    typeof voice?.server_reachable === 'object' 
      ? voice?.server_reachable?.reachable === true
      : voice?.server_reachable === true
  );
  const engineReady = $derived(serverReachable === true);
  const activeProfile = $derived(
    (voiceProfiles ?? []).find((p: any) => p.is_active) ?? null
  );
  const profileCount = $derived((voiceProfiles ?? []).length);
  const genCount = $derived((voiceGenerations ?? []).length);
  const isBusy = $derived(busyAction !== '');
  const labMode = $derived(voiceLabState?.mode ?? 'standalone');
  const labText = $derived(voiceLabState?.draft_text ?? '');

  // === ACTIONS ===
  function handleTestSpeak() {
    errorMsg = '';
    if (!testText.trim()) { errorMsg = 'Teks tidak boleh kosong'; return; }
    onTestSpeak(testText);
  }

  function handleGenerate() {
    errorMsg = '';
    const text = generateText.trim() || labText;
    if (!text) { errorMsg = 'Masukkan teks untuk generate audio'; return; }
    if (!activeProfile) { errorMsg = 'Pilih profil suara terlebih dahulu'; return; }
    onGenerateVoice({ text, profile_id: activeProfile.id });
  }

  function handleActivate(id: number) {
    errorMsg = '';
    onActivateProfile(id);
  }
</script>

<!-- === ENGINE STATUS BAR === -->
<div class="status-bar">
  <span class="status-dot" class:online={engineReady} class:offline={!engineReady}></span>
  <strong>{engineName}</strong>
  <span class="status-label">{engineReady ? 'Terhubung' : 'Tidak Terhubung'}</span>
  {#if activeProfile}
    <span class="badge active">Profil: {activeProfile.name}</span>
  {:else}
    <span class="badge inactive">Belum ada profil aktif</span>
  {/if}
  {#if isBusy}
    <span class="badge busy">Proses: {busyAction}</span>
  {/if}
  <div class="status-actions">
    <button class="btn-sm" onclick={onWarmup} disabled={isBusy}>Warmup</button>
    <button class="btn-sm" onclick={onRestart} disabled={isBusy}>Restart</button>
  </div>
</div>

<!-- === ERROR BANNER === -->
{#if errorMsg}
  <div class="error-banner">{errorMsg}</div>
{/if}

<!-- === TAB NAVIGATION === -->
<nav class="tab-nav">
  <button class:active={activeTab === 'generate'} onclick={() => activeTab = 'generate'}>Generate</button>
  <button class:active={activeTab === 'profiles'} onclick={() => activeTab = 'profiles'}>Voice Profiles</button>
  <button class:active={activeTab === 'library'} onclick={() => activeTab = 'library'}>Library</button>
  <button class:active={activeTab === 'settings'} onclick={() => activeTab = 'settings'}>Settings</button>
</nav>

<!-- === TAB CONTENT === -->
<div class="tab-content">

  <!-- GENERATE TAB -->
  {#if activeTab === 'generate'}
    <div class="generate-section">
      <h4>Generate Audio</h4>
      <textarea
        bind:value={generateText}
        placeholder={labText || 'Ketik teks bahasa Indonesia untuk di-generate...'}
        rows="4"
      ></textarea>
      <div class="gen-controls">
        <button class="btn-generate" onclick={handleGenerate} disabled={isBusy || !activeProfile}>
          {isBusy ? 'Memproses...' : 'Generate'}
        </button>
        {#if !activeProfile}
          <span class="gen-hint">Pilih profil suara di tab "Voice Profiles" dulu</span>
        {/if}
      </div>

      <!-- Quick Test -->
      <div class="quick-test">
        <h4>Quick Test</h4>
        <div class="test-row">
          <input type="text" bind:value={testText} placeholder="Ketik teks test..." />
          <button class="btn-sm" onclick={handleTestSpeak} disabled={isBusy || !engineReady}>Test</button>
        </div>
        {#if voiceTestResult}
          <div class="result-player">
            {#if voiceTestResult.audio_url}
              <audio controls src={voiceTestResult.audio_url} autoplay></audio>
            {/if}
            {#if voiceTestResult.error}
              <div class="error-banner">{voiceTestResult.error}</div>
            {/if}
            {#if voiceTestResult.latency_ms}
              <span class="gen-meta">Latency: {voiceTestResult.latency_ms}ms</span>
            {/if}
          </div>
        {/if}
      </div>

      <!-- Recent Generations -->
      {#if genCount > 0}
        <div class="recent-gens">
          <h4>Hasil Generate ({genCount})</h4>
          {#each voiceGenerations as gen}
            <div class="gen-item">
              <div class="gen-text">{gen.text?.substring(0, 60) || 'Audio'}...</div>
              {#if gen.audio_url}
                <audio controls src={gen.audio_url} preload="metadata"></audio>
              {:else}
                <span class="gen-meta error">Audio tidak tersedia</span>
              {/if}
              <button class="btn-sm btn-danger" onclick={() => onDeleteGeneration(gen.id)}>Hapus</button>
            </div>
          {/each}
        </div>
      {/if}
    </div>

      <!-- PROFILES TAB -->
  {:else if activeTab === 'profiles'}
    <div class="profiles-section">
      <h4>Voice Profiles ({profileCount})</h4>
      {#if profileCount === 0}
        <p class="empty-state">Belum ada profil suara. Buat profil baru untuk mulai generate.</p>
      {/if}
      {#each voiceProfiles ?? [] as profile}
        <div class="profile-card" class:active-profile={profile.is_active}>
          <div class="profile-info">
            <strong>{profile.name}</strong>
            <span class="gen-meta">{profile.engine} | {profile.profile_type} | {profile.quality_tier}</span>
            {#if profile.is_active}
              <span class="badge active">Aktif</span>
            {/if}
          </div>
          <div class="profile-actions">
            {#if !profile.is_active}
              <button class="btn-sm" onclick={() => handleActivate(profile.id)}>Aktifkan</button>
            {/if}
          </div>
        </div>
      {/each}
    </div>

  <!-- LIBRARY TAB -->
  {:else if activeTab === 'library'}
    <div class="library-section">
      <h4>Voice Library</h4>
      {#if voiceLibrarySummary}
        <p>Total: {voiceLibrarySummary.total_items ?? 0} item</p>
      {:else}
        <p class="empty-state">Library kosong</p>
      {/if}
      {#if (voiceTrainingJobs ?? []).length > 0}
        <h4>Training Jobs</h4>
        {#each voiceTrainingJobs as job}
          <div class="gen-item">
            <span>{job.name ?? job.id} - {job.status ?? 'unknown'}</span>
          </div>
        {/each}
      {/if}
      <div class="btn-row">
        <button class="btn-sm" onclick={onClearLibrary} disabled={isBusy}>Hapus Library</button>
      </div>
    </div>

  <!-- SETTINGS TAB -->
  {:else if activeTab === 'settings'}
    <div class="settings-section">
      <h4>Voice Settings</h4>
      <div class="setting-row">
        <label>Mode:</label>
        <span>{labMode}</span>
      </div>
      <div class="setting-row">
        <label>Engine:</label>
        <span>{engineName}</span>
      </div>
      <div class="setting-row">
        <label>Server:</label>
        <span>{serverReachable ? 'Terhubung' : 'Tidak terhubung'}</span>
      </div>
      <div class="setting-row">
        <label>Bahasa:</label>
        <span>{voice?.voice_runtime_mode ?? 'Tidak diketahui'}</span>
      </div>
      <div class="operator-controls">
        <h4>Operator Controls</h4>
        <div class="btn-row">
          <button onclick={onWarmup} disabled={isBusy}>Warmup Engine</button>
          <button onclick={onRestart} disabled={isBusy}>Restart Engine</button>
          <button onclick={onClearQueue} disabled={isBusy}>Clear Queue</button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .status-bar { display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem 1rem; background: #1a1a2e; border-radius: 8px; flex-wrap: wrap; margin-bottom: 1rem; }
  .status-dot { width: 10px; height: 10px; border-radius: 50%; }
  .status-dot.online { background: #4caf50; box-shadow: 0 0 6px #4caf50; }
  .status-dot.offline { background: #f44336; }
  .status-label { color: #aaa; font-size: 0.85rem; }
  .badge { padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.75rem; }
  .badge.active { background: #1b5e20; color: #81c784; }
  .badge.inactive { background: #4a3000; color: #ffb74d; }
  .badge.busy { background: #1a237e; color: #90caf9; }
  .status-actions { margin-left: auto; display: flex; gap: 0.5rem; }

  .error-banner { background: #3a1a1a; color: #f87171; padding: 0.5rem 0.75rem; border-radius: 6px; margin-bottom: 0.75rem; }

  .tab-nav { display: flex; gap: 0; border-bottom: 1px solid #333; margin-bottom: 1rem; }
  .tab-nav button { padding: 0.6rem 1.2rem; background: none; color: #888; border: none; border-bottom: 2px solid transparent; cursor: pointer; font-size: 0.9rem; }
  .tab-nav button.active { color: #fff; border-bottom-color: #f87171; }
  .tab-nav button:hover { color: #ccc; }

  .tab-content { min-height: 200px; }

  textarea { width: 100%; padding: 0.75rem; background: #1a1a1a; color: #fff; border: 1px solid #444; border-radius: 6px; resize: vertical; font-size: 0.95rem; }
  textarea:focus { border-color: #f87171; outline: none; }

  .gen-controls { display: flex; align-items: center; gap: 0.75rem; margin-top: 0.75rem; }
  .gen-hint { font-size: 0.8rem; color: #f59e0b; }

  .btn-generate { padding: 0.6rem 2rem; background: #e25b5b; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 1rem; font-weight: bold; }
  .btn-generate:hover:not(:disabled) { background: #c0392b; }
  .btn-generate:disabled { opacity: 0.5; cursor: not-allowed; }

  .btn-sm { padding: 0.3rem 0.8rem; background: #2a2a2a; color: #ccc; border: 1px solid #444; border-radius: 4px; cursor: pointer; font-size: 0.8rem; }
  .btn-sm:hover:not(:disabled) { background: #3a3a3a; }
  .btn-sm:disabled { opacity: 0.4; cursor: not-allowed; }

  .quick-test { margin-top: 1.5rem; border-top: 1px solid #333; padding-top: 1rem; }
  .test-row { display: flex; gap: 0.5rem; align-items: center; }
  .test-row input { flex: 1; padding: 0.4rem 0.6rem; background: #1a1a1a; color: #fff; border: 1px solid #444; border-radius: 4px; }

  .result-player { margin-top: 0.75rem; padding: 0.75rem; background: #1a2a1a; border-radius: 8px; }
  .gen-meta { font-size: 0.75rem; color: #888; }

  .recent-gens { margin-top: 1.5rem; border-top: 1px solid #333; padding-top: 1rem; }
  .gen-item { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; padding: 0.75rem; background: #1a1a2e; border-radius: 6px; border: 1px solid #2a2a3e; }
  .gen-item:hover { border-color: #3a3a4e; }
  .gen-item .gen-text { flex: 0 0 200px; font-size: 0.85rem; color: #ccc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .gen-item audio { flex: 1; height: 36px; min-width: 200px; }
  .gen-meta.error { color: #f87171; font-size: 0.75rem; }
  .btn-danger { background: #7f1d1d !important; color: #fca5a5 !important; }
  .btn-danger:hover:not(:disabled) { background: #991b1b !important; }

  .profile-card { padding: 0.75rem; background: #1a1a2e; border-radius: 8px; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center; border: 1px solid #333; }
  .profile-card.active-profile { border-color: #4caf50; }
  .profile-info { display: flex; flex-direction: column; gap: 0.25rem; }

  .empty-state { color: #666; font-style: italic; }

  .setting-row { display: flex; gap: 1rem; padding: 0.5rem 0; border-bottom: 1px solid #222; }
  .setting-row label { color: #888; min-width: 100px; }

  .operator-controls { margin-top: 1.5rem; border-top: 1px solid #333; padding-top: 1rem; }
  .btn-row { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem; }
  .btn-row button { padding: 0.4rem 0.75rem; background: #2a2a2a; color: #ccc; border: 1px solid #444; border-radius: 4px; cursor: pointer; }
  .btn-row button:hover:not(:disabled) { background: #333; }
  .btn-row button:disabled { opacity: 0.4; cursor: not-allowed; }

  h4 { font-size: 0.95rem; color: #ddd; margin: 0 0 0.75rem; }
  p { color: #aaa; }
</style>