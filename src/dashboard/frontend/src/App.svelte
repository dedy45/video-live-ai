<script lang="ts">
  import Header from './components/layout/Header.svelte';
  import TruthBar from './components/common/TruthBar.svelte';
  import TabNav from './components/layout/TabNav.svelte';
  import PageShell from './components/layout/PageShell.svelte';

  const tabs = [
    'Live Console',
    'Products & Offers',
    'Voice & Face',
    'Stream & Platform',
    'Validation & Readiness',
    'Monitor & Incidents',
    'Diagnostics',
  ];

  let activeTab = $state('Live Console');

  function handleTabChange(tab: string) {
    activeTab = tab;
  }
</script>

<div class="app">
  <Header />
  <TruthBar />
  <TabNav {tabs} {activeTab} onTabChange={handleTabChange} />
  <PageShell {activeTab} />
</div>
