<script lang="ts">
 import Header from './Header.svelte';
 import TruthBar from '../common/TruthBar.svelte';

 export let currentPage: string = '/';

 const menuItems = [
  { path: '/', label: 'Live Console', icon: '📺' },
  { path: '/products', label: 'Products', icon: '📦' },
  { path: '/performer', label: 'Performer', icon: '🎭' },
  { path: '/stream', label: 'Stream', icon: '📡' },
  { path: '/validation', label: 'Validation', icon: '✅' },
  { path: '/monitor', label: 'Monitor', icon: '📊' },
  { path: '/diagnostics', label: 'Diagnostics', icon: '🔧' },
 ];

 function isActive(path: string): boolean {
  return currentPage === path || (currentPage === '' && path === '/');
 }
</script>

<div class="app-layout">
 <Header />

 <div class="layout-container">
  <aside class="sidebar">
   <nav class="sidebar-nav">
    {#each menuItems as item}
     <a
      href="{item.path}"
      class="nav-item {isActive(item.path) ? 'active' : ''}"
     >
      <span class="nav-icon">{item.icon}</span>
      <span class="nav-label">{item.label}</span>
     </a>
    {/each}
   </nav>
  </aside>

  <main class="main-content">
   <TruthBar />
   <div class="page-content">
    <slot />
   </div>
  </main>
 </div>
</div>

<style>
 .app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg);
 }

 .layout-container {
  display: flex;
  flex: 1;
 }

 .sidebar {
  width: 220px;
  background: var(--card);
  border-right: 1px solid var(--border);
  padding: 16px 0;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
 }

 .sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 0 12px;
 }

 .nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
 }

 .nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text);
 }

 .nav-item.active {
  background: rgba(99, 102, 241, 0.15);
  color: var(--accent);
 }

 .nav-icon {
  font-size: 18px;
  width: 24px;
  text-align: center;
 }

 .nav-label {
  flex: 1;
 }

 .main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
 }

 .page-content {
  flex: 1;
  padding: 24px;
  max-width: 1200px;
  width: 100%;
 }

 @media (max-width: 768px) {
  .sidebar {
   width: 60px;
  }

  .nav-label {
   display: none;
  }

  .nav-icon {
   margin: 0 auto;
  }
 }
</style>