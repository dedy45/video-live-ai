<script lang="ts">
  interface Props {
    tabs: string[];
    activeTab: string;
    onTabChange: (tab: string) => void;
  }

  let { tabs, activeTab, onTabChange }: Props = $props();
</script>

<div class="tabs" role="tablist">
  {#each tabs as tab}
    <button
      class="tab"
      class:active={activeTab === tab}
      role="tab"
      aria-selected={activeTab === tab}
      onclick={() => onTabChange(tab)}
    >
      {tab}
    </button>
  {/each}
</div>

<style>
  .tabs {
    display: flex;
    gap: 0;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    overflow-x: auto;
  }
  .tab {
    padding: 11px 18px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    color: var(--muted);
    border: none;
    border-bottom: 2px solid transparent;
    background: none;
    transition: all .2s;
    white-space: nowrap;
    user-select: none;
    font-family: inherit;
  }
  .tab:hover {
    color: var(--text);
    background: rgba(255,255,255,.03);
  }
  .tab.active {
    color: var(--cyan);
    border-bottom-color: var(--cyan);
  }
</style>
