<script lang="ts">
  import PerformerWorkspace from '../components/panels/PerformerWorkspace.svelte';
</script>

<div class="page page-full-width" data-testid="performer-page">
  <div class="page-header">
    <h1 class="page-title">Avatar & Suara</h1>
    <p class="page-subtitle">Workspace operator untuk mengendalikan suara, avatar, preview, validasi, dan data teknis tanpa kehilangan konteks runtime.</p>
  </div>

  <div class="page-grid">
    <PerformerWorkspace />
  </div>
</div>

<style>
  .page {
    padding: 20px;
    width: 100%;
    min-width: 0;
  }

  .page-header {
    margin-bottom: 24px;
    min-width: 0;
  }

  .page-title {
    font-size: 28px;
    font-weight: 800;
    margin: 0 0 8px 0;
    color: var(--text);
    line-height: 1.2;
  }

  .page-subtitle {
    margin: 0;
    color: var(--muted);
    font-size: 14px;
    line-height: 1.5;
  }

  .page-grid {
    display: grid;
    gap: 20px;
    min-width: 0;
  }

  @media (max-width: 768px) {
    .page {
      padding: 16px;
    }

    .page-title {
      font-size: 26px;
    }
  }
</style>
