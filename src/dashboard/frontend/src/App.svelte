<script lang="ts">
 import Header from './components/layout/Header.svelte';
 import TruthBar from './components/common/TruthBar.svelte';
 import LiveConsolePage from './pages/LiveConsolePage.svelte';
 import ProductsPage from './pages/ProductsPage.svelte';
 import PerformerPage from './pages/PerformerPage.svelte';
 import StreamPage from './pages/StreamPage.svelte';
 import SetupPage from './pages/SetupPage.svelte';
 import MonitorPage from './pages/MonitorPage.svelte';

 // Color coding definitions
 const STATUS_COLORS = {
   ready: '#10b981', // Emerald green
   warning: '#f59e0b', // Amber
   error: '#ef4444', // Red
   idle: '#6b7280' // Gray
 } as const;

 // Enhanced error handler
 function handleNavigationError(path: string, error: Error) {
   console.error(`Navigation error to ${path}:`, error);
   // Fallback to root path if error occurs
   window.location.hash = '/';
 }

 // New page structure with workflow sections and diagnostics removed
 const navSections = [
   {
     title: 'PERSIAPAN',
     items: [
       { path: '/setup', name: 'Setup & Validasi', icon: '🔧' },
       { path: '/products', name: 'Produk & Penawaran', icon: '📦' },
       { path: '/performer', name: 'Avatar & Suara', icon: '🎭' }
     ]
   },
   {
     title: 'OPERASI',
     items: [
       { path: '/stream', name: 'Streaming & Platform', icon: '📡' },
       { path: '/', name: 'Konsol Live', icon: '📺' }
     ]
   },
   {
     title: 'PENGAWASAN',
     items: [
       { path: '/monitor', name: 'Monitor & Insiden', icon: '📊' }
     ]
   }
 ] as const;

 // Get current page from hash with error handling
 function getCurrentPath(): string {
 try {
   if (typeof window === 'undefined') return '/';
   const hash = window.location.hash.slice(1);
   return hash || '/';
 } catch (error) {
   console.error('Error getting current path:', error);
   return '/';
 }
 }

 let currentPage = $state<string>(getCurrentPath());

 function navigate(path: string) {
 if (typeof window !== 'undefined') {
   try {
     window.location.hash = path;
     currentPage = path;
   } catch (error) {
     handleNavigationError(path, error as Error);
   }
 }
 }

 // Listen to hash changes
 if (typeof window !== 'undefined') {
 try {
   window.addEventListener('hashchange', () => {
     currentPage = getCurrentPath();
   });
 } catch (error) {
   console.error('Error setting up hashchange listener:', error);
 }
 }

 // Map paths to components
 const pageComponents: Record<string, any> = {
 '/': LiveConsolePage,
 '/products': ProductsPage,
 '/performer': PerformerPage,
 '/stream': StreamPage,
 '/setup': SetupPage,
 '/monitor': MonitorPage,
 };

 // Flatten navigation for easier lookup
 const allPages = navSections.flatMap(section => section.items);

 const ActiveComponent = $derived(
 pageComponents[currentPage] || pageComponents['/']
 );
</script>

<div class="app">
 <Header />

 <div class="layout-container">
 <!-- Fixed Sidebar Navigation -->
 <aside class="sidebar">
 <nav class="sidebar-nav">
 {#each navSections as section, sectionIndex}
 <div class="nav-section">
 <div class="section-header">{section.title}</div>
 {#each section.items as page}
 <a
 class="nav-item {currentPage === page.path ? 'active' : ''}"
 href="#{page.path}"
 onclick={(e) => {
 try {
 e.preventDefault();
 navigate(page.path);
 } catch (error) {
 handleNavigationError(page.path, error as Error);
 e.stopPropagation();
 }
 }}
 >
 <span class="nav-icon">{page.icon}</span>
 <span class="nav-label">{page.name}</span>
 </a>
 {/each}
 </div>
 {#if sectionIndex < navSections.length - 1}
 <div class="section-divider"></div>
 {/if}
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
 gap: 0;
 padding: 0 8px;
 }

 .nav-section {
 margin-bottom: 16px;
 }

 .section-header {
 font-size: 11px;
 font-weight: 600;
 text-transform: uppercase;
 color: var(--text-secondary);
 padding: 8px 12px 4px 12px;
 letter-spacing: 0.5px;
 margin-bottom: 4px;
 }

 .section-divider {
 height: 1px;
 background: var(--border);
 margin: 8px 12px;
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
