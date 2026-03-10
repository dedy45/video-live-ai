<script lang="ts">
 import Header from './components/layout/Header.svelte';
 import TruthBar from './components/common/TruthBar.svelte';
 import LiveConsolePage from './pages/LiveConsolePage.svelte';
 import ProductsPage from './pages/ProductsPage.svelte';
 import PerformerPage from './pages/PerformerPage.svelte';
 import StreamPage from './pages/StreamPage.svelte';
 import ValidationPage from './pages/ValidationPage.svelte';
 import MonitorPage from './pages/MonitorPage.svelte';
 import DiagnosticsPage from './pages/DiagnosticsPage.svelte';

 // Page routing definition with icons
 const pages = [
 { path: '/', name: 'Konsol Live', icon: '📺' },
 { path: '/products', name: 'Produk', icon: '📦' },
 { path: '/performer', name: 'Performer', icon: '🎭' },
 { path: '/stream', name: 'Streaming', icon: '📡' },
 { path: '/validation', name: 'Validasi', icon: '✅' },
 { path: '/monitor', name: 'Monitor', icon: '📊' },
 { path: '/diagnostics', name: 'Diagnostik', icon: '🔧' },
 ] as const;

 // Get current page from hash
 function getCurrentPath(): string {
 if (typeof window === 'undefined') return '/';
 const hash = window.location.hash.slice(1);
 return hash || '/';
 }

 let currentPage = $state<string>(getCurrentPath());

 function navigate(path: string) {
 if (typeof window !== 'undefined') {
 window.location.hash = path;
 currentPage = path;
 }
 }

 // Listen to hash changes
 if (typeof window !== 'undefined') {
 window.addEventListener('hashchange', () => {
 currentPage = getCurrentPath();
 });
 }

 // Map paths to components
 const pageComponents: Record<string, any> = {
 '/': LiveConsolePage,
 '/products': ProductsPage,
 '/performer': PerformerPage,
 '/stream': StreamPage,
 '/validation': ValidationPage,
 '/monitor': MonitorPage,
 '/diagnostics': DiagnosticsPage,
 };

 const ActiveComponent = $derived(
 pageComponents[currentPage] || LiveConsolePage
 );
</script>

<div class="app">
 <Header />

 <div class="layout-container">
 <!-- Fixed Sidebar Navigation -->
 <aside class="sidebar">
 <nav class="sidebar-nav">
 {#each pages as page}
 <a
 class="nav-item {currentPage === page.path ? 'active' : ''}"
 href="#{page.path}"
 on:click={(e) => { e.preventDefault(); navigate(page.path); }}
 >
 <span class="nav-icon">{page.icon}</span>
 <span class="nav-label">{page.name}</span>
 </a>
 {/each}
 </nav>
 </aside>

 <!-- Main Content Area -->
 <main class="main-content">
 <TruthBar />
 <div class="page-content">
 <ActiveComponent />
 </div>
 </main>
 </div>
</div>

<style>
 .app {
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
 flex-shrink: 0;
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
 cursor: pointer;
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
