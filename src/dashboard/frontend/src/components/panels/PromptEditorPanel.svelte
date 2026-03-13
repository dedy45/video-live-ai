<script lang="ts">
 import { onMount } from 'svelte';

 let revisions: any[] = $state([]);
 let selectedRevision: any = $state(null);
 let loading = $state(false);
 let error = $state('');
 let mode: 'list' | 'view' | 'edit' | 'create' | 'generate' = $state('list');
 let showDeleteConfirm = $state(false);
 let deleteTarget: number | null = $state(null);

 // Form state
 let formSlug = $state('');
 let formTemplates: Record<string, string> = $state({});
 let formPersona: Record<string, any> = $state({});
 let catchphrasesText = $state('');
 let forbiddenTopicsText = $state('');

 // Generate form state
 let generateProductContext = $state('Produk fashion dan lifestyle');
 let generatePersonaName = $state('Sari');
 let generatePersonaTraits = $state('friendly, energetic, knowledgeable');
 let generateLanguage = $state('Indonesian casual');
 let generateProvider = $state('');
 let generating = $state(false);

 async function loadRevisions() {
   loading = true;
   error = '';
   try {
     const response = await fetch('/api/brain/prompts');
     if (response.ok) {
       revisions = await response.json();
     } else {
       error = 'Failed to load prompt revisions';
     }
   } catch (e: any) {
     error = e.message;
   } finally {
     loading = false;
   }
 }

 async function viewRevision(id: number) {
   loading = true;
   error = '';
   try {
     const response = await fetch(`/api/brain/prompts/${id}`);
     if (response.ok) {
       selectedRevision = await response.json();
       mode = 'view';
     } else {
       error = 'Failed to load revision';
     }
   } catch (e: any) {
     error = e.message;
   } finally {
     loading = false;
   }
 }

 function splitLines(value: string): string[] {
   return value
     .split('\n')
     .map(item => item.trim())
     .filter(Boolean);
 }

 function syncPersonaTextareas() {
   catchphrasesText = Array.isArray(formPersona.catchphrases)
     ? formPersona.catchphrases.join('\n')
     : '';
   forbiddenTopicsText = Array.isArray(formPersona.forbidden_topics)
     ? formPersona.forbidden_topics.join('\n')
     : '';
 }

 function startEdit() {
   if (!selectedRevision) return;
   formSlug = selectedRevision.slug;
   formTemplates = { ...selectedRevision.templates };
   formPersona = { ...selectedRevision.persona };
   syncPersonaTextareas();
   mode = 'edit';
 }

 function startCreate() {
   formSlug = 'default-live-commerce';
   formTemplates = {
     system_base: '',
     selling_mode: '',
     reacting_mode: '',
     engaging_mode: '',
     filler: '',
     selling_script: '',
   };
   formPersona = {
     name: 'Sari',
     personality: '',
     language: 'Indonesian casual',
     tone: '',
     expertise: '',
     catchphrases: [],
     forbidden_topics: [],
   };
   syncPersonaTextareas();
   mode = 'create';
 }

 function startGenerate() {
   mode = 'generate';
   error = '';
 }

 async function handleGenerate() {
   generating = true;
   error = '';
   try {
     const response = await fetch('/api/brain/prompts/generate', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({
         product_context: generateProductContext,
         persona_name: generatePersonaName,
         persona_traits: generatePersonaTraits,
         language: generateLanguage,
         provider: generateProvider || null,
       })
     });

     if (!response.ok) {
       const errorData = await response.json();
       throw new Error(errorData.detail || 'Failed to generate prompt');
     }

     const result = await response.json();
     
     if (result.success) {
       // Populate form with generated data
       formSlug = 'generated-' + Date.now();
       formTemplates = result.templates;
       formPersona = result.persona;
       syncPersonaTextareas();
       mode = 'create';
       error = '';
     } else {
       throw new Error('Generation failed');
     }
   } catch (e: any) {
     error = e.message || 'Failed to generate prompt';
   } finally {
     generating = false;
   }
 }

 async function handleSave() {
   loading = true;
   error = '';
   try {
     const personaPayload = {
       ...formPersona,
       catchphrases: splitLines(catchphrasesText),
       forbidden_topics: splitLines(forbiddenTopicsText),
     };

     if (mode === 'create') {
       const response = await fetch('/api/brain/prompts', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({
           slug: formSlug,
           templates: formTemplates,
           persona: personaPayload
         })
       });
       if (!response.ok) {
         const errorData = await response.json().catch(() => ({}));
         throw new Error(errorData.detail || 'Failed to create revision');
       }
     } else if (mode === 'edit' && selectedRevision) {
       const response = await fetch(`/api/brain/prompts/${selectedRevision.id}`, {
         method: 'PUT',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({
           templates: formTemplates,
           persona: personaPayload
         })
       });
       if (!response.ok) {
         const errorData = await response.json().catch(() => ({}));
         throw new Error(errorData.detail || 'Failed to update revision');
       }
     }
     await loadRevisions();
     mode = 'list';
   } catch (e: any) {
     error = e.message;
   } finally {
     loading = false;
   }
 }

 async function handlePublish(id: number) {
   loading = true;
   error = '';
   try {
     const response = await fetch(`/api/brain/prompts/${id}/publish`, {
       method: 'POST'
     });
     if (!response.ok) {
       const errorData = await response.json().catch(() => ({}));
       throw new Error(errorData.detail || 'Failed to publish revision');
     }
     await loadRevisions();
     mode = 'list';
   } catch (e: any) {
     error = e.message;
   } finally {
     loading = false;
   }
 }

 function confirmDelete(id: number) {
   deleteTarget = id;
   showDeleteConfirm = true;
 }

 async function handleDelete() {
   if (deleteTarget === null) return;
   loading = true;
   error = '';
   try {
     const response = await fetch(`/api/brain/prompts/${deleteTarget}`, {
       method: 'DELETE'
     });
     if (!response.ok) {
       const errorData = await response.json().catch(() => ({}));
       throw new Error(errorData.detail || 'Failed to delete revision');
     }
     await loadRevisions();
     showDeleteConfirm = false;
     deleteTarget = null;
     mode = 'list';
   } catch (e: any) {
     error = e.message;
   } finally {
     loading = false;
   }
 }

 function cancelDelete() {
   showDeleteConfirm = false;
   deleteTarget = null;
 }

 function cancel() {
   mode = 'list';
   selectedRevision = null;
 }

 // LAZY LOAD: Don't load on mount, only when user interacts
 let hasLoaded = $state(false);
 
 function ensureLoaded() {
   if (!hasLoaded && mode === 'list') {
     hasLoaded = true;
     void loadRevisions();
   }
 }
 
 onMount(() => {
   setTimeout(ensureLoaded, 100);
 });
</script>

<div class="prompt-editor-panel">
 <div class="header">
   <h3>Prompt Registry Editor</h3>
   {#if mode === 'list'}
     <div class="header-actions">
       <button class="btn-secondary" onclick={startGenerate}>🤖 Generate with AI</button>
       <button class="btn-primary" onclick={startCreate}>+ Create New Revision</button>
     </div>
   {:else}
     <button class="btn-secondary" onclick={cancel}>← Back to List</button>
   {/if}
 </div>

 {#if error}
   <div class="error-banner">{error}</div>
 {/if}

 {#if mode === 'list'}
   <!-- List View -->
   <div class="revisions-list">
     {#if loading}
       <div class="loading">Loading revisions...</div>
     {:else if revisions.length === 0}
       <div class="empty">
         <p>📝 No prompt revisions found.</p>
         <p class="hint">Create your first revision to manage AI persona and templates.</p>
       </div>
     {:else}
       <table>
         <thead>
           <tr>
             <th>ID</th>
             <th>Slug</th>
             <th>Version</th>
             <th>Status</th>
             <th>Updated</th>
             <th>Actions</th>
           </tr>
         </thead>
         <tbody>
           {#each revisions as rev}
             <tr class:active={rev.status === 'active'}>
               <td>{rev.id}</td>
               <td>{rev.slug}</td>
               <td>v{rev.version}</td>
               <td><span class="status-badge status-{rev.status}">{rev.status}</span></td>
               <td>{new Date(rev.updated_at).toLocaleString()}</td>
               <td class="actions">
                 <button class="btn-sm" onclick={() => viewRevision(rev.id)}>View</button>
                 {#if rev.status === 'draft'}
                   <button class="btn-sm btn-success" onclick={() => handlePublish(rev.id)}>Publish</button>
                   <button class="btn-sm btn-danger" onclick={() => confirmDelete(rev.id)}>Delete</button>
                 {/if}
               </td>
             </tr>
           {/each}
         </tbody>
       </table>
     {/if}
   </div>

 {:else if mode === 'generate'}
   <!-- Generate with AI Mode -->
   <div class="generate-form">
     <h4>🤖 Generate Prompt Templates with AI</h4>
     <p class="hint">Biarkan AI membuat prompt templates berdasarkan konteks produk dan persona yang Anda inginkan.</p>

     <div class="form-group">
       <label for="gen-product">Konteks Produk</label>
       <input
         id="gen-product"
         type="text"
         bind:value={generateProductContext}
         placeholder="e.g., Produk fashion dan lifestyle"
       />
     </div>

     <div class="form-group">
       <label for="gen-name">Nama Persona</label>
       <input
         id="gen-name"
         type="text"
         bind:value={generatePersonaName}
         placeholder="e.g., Sari"
       />
     </div>

     <div class="form-group">
       <label for="gen-traits">Kepribadian</label>
       <input
         id="gen-traits"
         type="text"
         bind:value={generatePersonaTraits}
         placeholder="e.g., friendly, energetic, knowledgeable"
       />
     </div>

     <div class="form-group">
       <label for="gen-lang">Bahasa</label>
       <input
         id="gen-lang"
         type="text"
         bind:value={generateLanguage}
         placeholder="e.g., Indonesian casual"
       />
     </div>

     <div class="form-group">
       <label for="gen-provider">LLM Provider (Optional)</label>
       <select id="gen-provider" bind:value={generateProvider}>
         <option value="">Auto (Best Available)</option>
         <option value="groq">Groq (Fast)</option>
         <option value="gemini">Gemini</option>
         <option value="claude">Claude</option>
         <option value="gpt4o">GPT-4o</option>
       </select>
     </div>

     <div class="form-actions">
       <button class="btn-primary" onclick={handleGenerate} disabled={generating}>
         {generating ? '🔄 Generating...' : '✨ Generate Templates'}
       </button>
       <button class="btn-secondary" onclick={cancel} disabled={generating}>Cancel</button>
     </div>
   </div>

 {:else if mode === 'view'}
   <!-- View Mode -->
   <div class="revision-view">
     {#if selectedRevision}
       <div class="view-header">
         <h4>{selectedRevision.slug} v{selectedRevision.version}</h4>
         <div class="view-actions">
           {#if selectedRevision.status === 'draft'}
             <button class="btn-primary" onclick={startEdit}>Edit</button>
             <button class="btn-success" onclick={() => handlePublish(selectedRevision.id)}>Publish</button>
           {:else if selectedRevision.status === 'active'}
             <span class="active-badge">✓ Active Revision</span>
           {/if}
         </div>
       </div>

       <div class="view-section">
         <h5>Persona</h5>
         <pre>{JSON.stringify(selectedRevision.persona, null, 2)}</pre>
       </div>

       <div class="view-section">
         <h5>Templates</h5>
         {#each Object.entries(selectedRevision.templates) as [key, value]}
           <div class="template-item">
             <strong>{key}:</strong>
             <pre>{value}</pre>
           </div>
         {/each}
       </div>
     {/if}
   </div>

 {:else if mode === 'edit' || mode === 'create'}
   <!-- Edit/Create Form -->
   <div class="revision-form">
     <h4>{mode === 'create' ? 'Create New Revision' : 'Edit Draft Revision'}</h4>

     <div class="form-group">
       <label for="prompt-slug">Slug</label>
       <input id="prompt-slug" type="text" bind:value={formSlug} disabled={mode === 'edit'} />
     </div>

     <div class="form-section">
       <h5>Persona</h5>
       <div class="form-group">
         <label for="persona-name">Name</label>
         <input id="persona-name" type="text" bind:value={formPersona.name} />
       </div>
       <div class="form-group">
         <label for="persona-personality">Personality</label>
         <input id="persona-personality" type="text" bind:value={formPersona.personality} />
       </div>
       <div class="form-group">
         <label for="persona-language">Language</label>
         <input id="persona-language" type="text" bind:value={formPersona.language} />
       </div>
       <div class="form-group">
         <label for="persona-tone">Tone</label>
         <input id="persona-tone" type="text" bind:value={formPersona.tone} />
       </div>
       <div class="form-group">
         <label for="persona-expertise">Expertise</label>
         <input id="persona-expertise" type="text" bind:value={formPersona.expertise} />
       </div>
       <div class="form-group">
         <label for="persona-catchphrases">Catchphrases</label>
         <textarea
           id="persona-catchphrases"
           bind:value={catchphrasesText}
           rows="4"
           placeholder="Satu catchphrase per baris"
         ></textarea>
       </div>
       <div class="form-group">
         <label for="persona-forbidden-topics">Forbidden Topics</label>
         <textarea
           id="persona-forbidden-topics"
           bind:value={forbiddenTopicsText}
           rows="4"
           placeholder="Satu topik terlarang per baris"
         ></textarea>
       </div>
     </div>

     <div class="form-section">
       <h5>Templates</h5>
       {#each Object.keys(formTemplates) as key}
         <div class="form-group">
           <label for={"template-" + key}>{key}</label>
           <textarea id={"template-" + key} bind:value={formTemplates[key]} rows="6"></textarea>
         </div>
       {/each}
     </div>

     <div class="form-actions">
       <button class="btn-primary" onclick={handleSave} disabled={loading}>
         {loading ? 'Saving...' : 'Save'}
       </button>
       <button class="btn-secondary" onclick={cancel}>Cancel</button>
     </div>
   </div>
 {/if}

 <!-- Delete Confirmation Modal -->
 {#if showDeleteConfirm}
   <div class="modal-overlay">
     <div class="modal" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title">
       <h4 id="delete-dialog-title">Confirm Delete</h4>
       <p>Are you sure you want to delete this draft revision? This action cannot be undone.</p>
       <div class="modal-actions">
         <button class="btn-danger" onclick={handleDelete} disabled={loading}>
           {loading ? 'Deleting...' : 'Delete'}
         </button>
         <button class="btn-secondary" onclick={cancelDelete}>Cancel</button>
       </div>
     </div>
   </div>
 {/if}
</div>

<style>
 .prompt-editor-panel {
   padding: 1.5rem;
   max-width: 1400px;
   margin: 0 auto;
 }

 .header {
   display: flex;
   justify-content: space-between;
   align-items: center;
   margin-bottom: 1.5rem;
 }

 .header-actions {
   display: flex;
   gap: 0.5rem;
 }

 h3 {
   margin: 0;
   font-size: 1.5rem;
   font-weight: 600;
   color: var(--text);
 }

 h4 {
   margin: 0 0 0.5rem 0;
   font-size: 1.25rem;
   color: var(--text);
 }

 .error-banner {
   background: rgba(239, 68, 68, 0.1);
   border: 1px solid rgba(239, 68, 68, 0.3);
   color: #ef4444;
   padding: 1rem;
   border-radius: 8px;
   margin-bottom: 1rem;
 }

 .loading, .empty {
   text-align: center;
   padding: 3rem 2rem;
   color: var(--text-secondary);
 }

 .empty .hint {
   font-size: 14px;
   margin-top: 8px;
 }

 /* Table Styles */
 table {
   width: 100%;
   border-collapse: collapse;
   background: var(--card);
   border-radius: 8px;
   overflow: hidden;
   box-shadow: 0 1px 3px rgba(0,0,0,0.1);
 }

 thead {
   background: rgba(255, 255, 255, 0.05);
 }

 th, td {
   padding: 0.75rem 1rem;
   text-align: left;
   border-bottom: 1px solid var(--border);
 }

 th {
   font-weight: 600;
   color: var(--text);
   font-size: 0.875rem;
   text-transform: uppercase;
 }

 tbody tr:hover {
   background: rgba(255, 255, 255, 0.03);
 }

 tbody tr.active {
   background: rgba(34, 211, 238, 0.05);
 }

 .status-badge {
   display: inline-block;
   padding: 0.25rem 0.5rem;
   border-radius: 0.25rem;
   font-size: 0.75rem;
   font-weight: 600;
   text-transform: uppercase;
 }

 .status-active {
   background: rgba(16, 185, 129, 0.2);
   color: #10b981;
 }

 .status-draft {
   background: rgba(251, 191, 36, 0.2);
   color: #fbbf24;
 }

 .status-inactive {
   background: rgba(156, 163, 175, 0.2);
   color: #9ca3af;
 }

 .actions {
   display: flex;
   gap: 0.5rem;
 }

 /* View Mode */
 .revision-view {
   background: var(--card);
   border-radius: 8px;
   padding: 1.5rem;
   box-shadow: 0 1px 3px rgba(0,0,0,0.1);
 }

 .view-header {
   display: flex;
   justify-content: space-between;
   align-items: center;
   margin-bottom: 1.5rem;
   padding-bottom: 1rem;
   border-bottom: 2px solid var(--border);
 }

 .view-header h4 {
   margin: 0;
   font-size: 1.25rem;
   color: var(--text);
 }

 .view-actions {
   display: flex;
   gap: 0.5rem;
 }

 .active-badge {
   background: rgba(16, 185, 129, 0.2);
   color: #10b981;
   padding: 0.5rem 1rem;
   border-radius: 8px;
   font-weight: 600;
 }

 .view-section {
   margin-bottom: 2rem;
 }

 .view-section h5 {
   margin: 0 0 1rem 0;
   font-size: 1rem;
   font-weight: 600;
   color: var(--text);
 }

 .template-item {
   margin-bottom: 1.5rem;
 }

 .template-item strong {
   display: block;
   margin-bottom: 0.5rem;
   color: var(--text);
 }

 pre {
   background: rgba(255, 255, 255, 0.03);
   border: 1px solid var(--border);
   border-radius: 8px;
   padding: 1rem;
   overflow-x: auto;
   font-size: 0.875rem;
   line-height: 1.5;
   color: var(--text);
 }

 /* Form Styles */
 .revision-form,
 .generate-form {
   background: var(--card);
   border-radius: 8px;
   padding: 1.5rem;
   box-shadow: 0 1px 3px rgba(0,0,0,0.1);
 }

 .revision-form h4,
 .generate-form h4 {
   margin: 0 0 1.5rem 0;
   font-size: 1.25rem;
   color: var(--text);
 }

 .generate-form .hint {
   margin: -0.5rem 0 1.5rem 0;
   color: var(--text-secondary);
   font-size: 14px;
 }

 .form-section {
   margin-bottom: 2rem;
   padding: 1rem;
   background: rgba(255, 255, 255, 0.02);
   border-radius: 8px;
 }

 .form-section h5 {
   margin: 0 0 1rem 0;
   font-size: 1rem;
   font-weight: 600;
   color: var(--text);
 }

 .form-group {
   margin-bottom: 1rem;
 }

 .form-group label {
   display: block;
   margin-bottom: 0.5rem;
   font-weight: 500;
   color: var(--text);
 }

 .form-group input,
 .form-group textarea,
 .form-group select {
   width: 100%;
   padding: 0.5rem;
   border: 1px solid var(--border);
   border-radius: 8px;
   font-family: inherit;
   font-size: 0.875rem;
   background: rgba(255, 255, 255, 0.05);
   color: var(--text);
 }

 .form-group input:disabled {
   background: rgba(255, 255, 255, 0.02);
   cursor: not-allowed;
   opacity: 0.6;
 }

 .form-group textarea {
   font-family: 'Courier New', monospace;
   resize: vertical;
 }

 .form-group select {
   cursor: pointer;
 }

 .form-actions {
   display: flex;
   gap: 0.5rem;
   margin-top: 1.5rem;
 }

 /* Buttons */
 button {
   padding: 0.5rem 1rem;
   border: none;
   border-radius: 8px;
   font-weight: 500;
   cursor: pointer;
   transition: all 0.2s;
 }

 button:disabled {
   opacity: 0.5;
   cursor: not-allowed;
 }

 .btn-primary {
   background: rgba(99, 102, 241, 0.2);
   color: var(--accent);
   border: 1px solid var(--accent);
 }

 .btn-primary:hover:not(:disabled) {
   background: rgba(99, 102, 241, 0.3);
 }

 .btn-secondary {
   background: rgba(255, 255, 255, 0.05);
   color: var(--text);
   border: 1px solid var(--border);
 }

 .btn-secondary:hover:not(:disabled) {
   background: rgba(255, 255, 255, 0.1);
 }

 .btn-success {
   background: rgba(16, 185, 129, 0.2);
   color: #10b981;
   border: 1px solid #10b981;
 }

 .btn-success:hover:not(:disabled) {
   background: rgba(16, 185, 129, 0.3);
 }

 .btn-danger {
   background: rgba(239, 68, 68, 0.2);
   color: #ef4444;
   border: 1px solid #ef4444;
 }

 .btn-danger:hover:not(:disabled) {
   background: rgba(239, 68, 68, 0.3);
 }

 .btn-sm {
   padding: 0.25rem 0.75rem;
   font-size: 0.875rem;
 }

 /* Modal */
 .modal-overlay {
   position: fixed;
   top: 0;
   left: 0;
   right: 0;
   bottom: 0;
   background: rgba(0, 0, 0, 0.5);
   display: flex;
   align-items: center;
   justify-content: center;
   z-index: 1000;
 }

 .modal {
   background: var(--card);
   border-radius: 8px;
   padding: 1.5rem;
   max-width: 500px;
   width: 90%;
   box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
   border: 1px solid var(--border);
 }

 .modal h4 {
   margin: 0 0 1rem 0;
   font-size: 1.25rem;
   color: var(--text);
 }

 .modal p {
   margin: 0 0 1.5rem 0;
   color: var(--text-secondary);
 }

 .modal-actions {
   display: flex;
   gap: 0.5rem;
   justify-content: flex-end;
 }

 @media (max-width: 768px) {
   .prompt-editor-panel {
     padding: 1rem;
   }

   .header {
     flex-direction: column;
     align-items: flex-start;
     gap: 1rem;
   }

   .header button {
     width: 100%;
   }

   table {
     font-size: 0.875rem;
   }

   th, td {
     padding: 0.5rem;
   }

   .actions {
     flex-direction: column;
   }

   .view-header {
     flex-direction: column;
     align-items: flex-start;
     gap: 1rem;
   }

   .view-actions {
     width: 100%;
     flex-direction: column;
   }

   .view-actions button {
     width: 100%;
   }

   .form-actions {
     flex-direction: column;
   }

   .form-actions button {
     width: 100%;
   }
 }
</style>
