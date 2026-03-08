<script lang="ts">
  // Header shows app title only. Mode badge lives in TruthBar.
</script>

<header class="header">
  <h1>AI Live Commerce — Command Center</h1>
</header>

<style>
  .header {
    background: linear-gradient(135deg, var(--surface) 0%, rgba(67,97,238,.15) 100%);
    padding: 12px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(12px);
  }
  h1 {
    font-size: 17px;
    font-weight: 700;
  }
</style>
