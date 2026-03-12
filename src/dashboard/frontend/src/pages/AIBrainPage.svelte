<script lang="ts">
 import { onMount } from 'svelte';
 import Card from '../components/common/Card.svelte';
 import BrainConfigEditor from '../components/panels/BrainConfigEditor.svelte';
 import PromptEditorPanel from '../components/panels/PromptEditorPanel.svelte';
 import ScriptGenerator from '../components/panels/ScriptGenerator.svelte';
 import DirectorRuntimePanel from '../components/panels/DirectorRuntimePanel.svelte';

 // Active tab - only render one section at a time for performance
 let activeTab = $state<'config' | 'prompts' | 'generator' | 'runtime'>('config');
 
 let brainConfig = $state<any | null>(null);
 let directorRuntime = $state<any | null>(null);
 let loading = $state(true);
 let error = $state('');

 async function loadData() {
   loading = true;
   error = '';
   try {
     const [configResult, runtimeResult] = await Promise.allSettled([
       fetch('/api/brain/config').then(r => r.json()),
       fetch('/api/director/runtime').then(r => r.json()),
     ]);

     if (configResult.status === 'fulfilled') {
       brainConfig = configResult.value;
     } else {
       error = 'Failed to load brain config';
     }

     if (runtimeResult.status === 'fulfilled') {
       directorRuntime = runtimeResult.value;
     } else {
       error = error || 'Failed to load director runtime';
     }
   } catch (e: any) {
     error = e.message || 'Failed to load data';
   } finally {
     loading = false;
   }
 }

 function refreshAll() {
   void loadData();
 }

 onMount(() => {
   void loadData();
 });
</script>

<div class="page">
 <div class="page-header">
   <div>
     <h1 class="page-title">🧠 AI Brain</h1>
     <p class="page-subtitle">
       Kelola routing LLM, edit prompt registry, generate naskah, dan monitor director runtime.
     </p>
   </div>
   <button class="refresh-btn" onclick={refreshAll} disabled={loading}>Refresh</button>
 </div>

 {#if error}
   <div class="error-banner" role="alert">{error}</div>
 {/if}

 {#if loading}
   <div class="loading-panel">Memuat AI Brain...</div>
 {:else}
   <!-- Tab Navigation -->
   <div class="tabs">
     <button 
       class="tab {activeTab === 'config' ? 'active' : ''}"
       onclick={() => activeTab = 'config'}
     >
       ⚙️ Configuration
     </button>
     <button 
       class="tab {activeTab === 'prompts' ? 'active' : ''}"
       onclick={() => activeTab = 'prompts'}
     >
       📝 Prompt Registry
     </button>
     <button 
       class="tab {activeTab === 'generator' ? 'active' : ''}"
       onclick={() => activeTab = 'generator'}
     >
       ✨ Script Generator
     </button>
     <button 
       class="tab {activeTab === 'runtime' ? 'active' : ''}"
       onclick={() => activeTab = 'runtime'}
     >
       📊 Runtime Monitor
     </button>
   </div>

   <!-- Tab Content - Only render active tab -->
   <div class="tab-content">
     {#if activeTab === 'config'}
       <Card title="Brain Configuration" size="lg">
         <BrainConfigEditor config={brainConfig} onUpdate={refreshAll} />
       </Card>
     {:else if activeTab === 'prompts'}
       <Card title="Prompt Registry" size="lg">
         <PromptEditorPanel />
       </Card>
     {:else if activeTab === 'generator'}
       <Card title="Script Generator" size="lg">
         <ScriptGenerator />
       </Card>
     {:else if activeTab === 'runtime'}
       <Card title="Director Runtime Monitor" size="lg">
         <DirectorRuntimePanel runtime={directorRuntime} />
       </Card>
     {/if}
   </div>
 {/if}
</div>

<style>
 .page {
   width: 100%;
   padding: 0;
   display: flex;
   flex-direction: column;
   gap: 20px;
 }

 .page-header {
   display: flex;
   justify-content: space-between;
   gap: 16px;
   align-items: flex-start;
 }

 .page-title {
   margin: 0 0 8px;
   font-size: 32px;
   font-weight: 800;
   color: var(--text);
 }

 .page-subtitle {
   margin: 0;
   color: var(--text-secondary);
   max-width: 760px;
   line-height: 1.5;
 }

 .refresh-btn {
   padding: 10px 16px;
   border-radius: 8px;
   border: 1px solid var(--border);
   background: rgba(255, 255, 255, 0.05);
   color: var(--text);
   cursor: pointer;
   font-weight: 700;
   transition: all 0.2s;
 }

 .refresh-btn:hover:not(:disabled) {
   background: rgba(255, 255, 255, 0.1);
 }

 .refresh-btn:disabled {
   opacity: 0.5;
   cursor: not-allowed;
 }

 .error-banner,
 .loading-panel {
   padding: 14px 16px;
   border-radius: 8px;
   border: 1px solid var(--border);
   background: var(--card);
 }

 .error-banner {
   color: var(--error);
   border-color: rgba(239, 68, 68, 0.3);
 }

 /* Tab Navigation */
 .tabs {
   display: flex;
   gap: 4px;
   border-bottom: 2px solid var(--border);
   overflow-x: auto;
 }

 .tab {
   padding: 12px 20px;
   border: none;
   background: transparent;
   color: var(--text-secondary);
   cursor: pointer;
   font-weight: 600;
   font-size: 14px;
   border-bottom: 3px solid transparent;
   transition: all 0.2s;
   white-space: nowrap;
 }

 .tab:hover {
   color: var(--text);
   background: rgba(255, 255, 255, 0.03);
 }

 .tab.active {
   color: var(--accent);
   border-bottom-color: var(--accent);
   background: rgba(99, 102, 241, 0.05);
 }

 .tab-content {
   min-height: 400px;
 }

 @media (max-width: 768px) {
   .page {
     gap: 16px;
   }

   .page-header {
     flex-direction: column;
   }

   .refresh-btn {
     width: 100%;
   }

   .page-title {
     font-size: 28px;
   }

   .tabs {
     gap: 2px;
   }

   .tab {
     padding: 10px 14px;
     font-size: 13px;
   }
 }
</style>
