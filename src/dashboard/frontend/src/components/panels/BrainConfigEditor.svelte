<script lang="ts">
 interface Props {
   config: any | null;
   onUpdate?: () => void;
 }

 let { config, onUpdate }: Props = $props();

 let editMode = $state(false);
 let saving = $state(false);
 let error = $state('');
 let success = $state('');

 // Editable state
 let editedRoutingTable = $state<Record<string, string[]>>({});
 let editedBudget = $state(5.0);
 let editedFallbackOrder = $state<string[]>([]);

 function startEdit() {
   if (!config) return;
   
   editedRoutingTable = { ...config.routing_table };
   editedBudget = config.daily_budget_usd;
   editedFallbackOrder = [...config.fallback_order];
   editMode = true;
   error = '';
   success = '';
 }

 function cancelEdit() {
   editMode = false;
   error = '';
   success = '';
 }

 async function saveChanges() {
   saving = true;
   error = '';
   success = '';

   try {
     // Save configuration
     const response = await fetch('/api/brain/config', {
       method: 'PUT',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({
         routing_table: editedRoutingTable,
         daily_budget_usd: editedBudget,
         fallback_order: editedFallbackOrder
       })
     });

     if (!response.ok) {
       throw new Error('Failed to save configuration');
     }

     success = 'Configuration updated successfully!';
     editMode = false;
     
     if (onUpdate) {
       setTimeout(onUpdate, 500);
     }
   } catch (e: any) {
     error = e.message || 'Failed to save configuration';
   } finally {
     saving = false;
   }
 }

 function moveProvider(taskType: string, index: number, direction: 'up' | 'down') {
   const providers = [...editedRoutingTable[taskType]];
   if (direction === 'up' && index > 0) {
     [providers[index - 1], providers[index]] = [providers[index], providers[index - 1]];
   } else if (direction === 'down' && index < providers.length - 1) {
     [providers[index], providers[index + 1]] = [providers[index + 1], providers[index]];
   }
   editedRoutingTable[taskType] = providers;
 }

 function moveFallbackProvider(index: number, direction: 'up' | 'down') {
   const providers = [...editedFallbackOrder];
   if (direction === 'up' && index > 0) {
     [providers[index - 1], providers[index]] = [providers[index], providers[index - 1]];
   } else if (direction === 'down' && index < providers.length - 1) {
     [providers[index], providers[index + 1]] = [providers[index + 1], providers[index]];
   }
   editedFallbackOrder = providers;
 }
</script>

<div class="config-editor">
 {#if !config}
   <div class="empty-state">No configuration loaded</div>
 {:else}
   <div class="config-header">
     <div class="config-info">
       <div class="info-item">
         <span class="label">Daily Budget:</span>
         <strong>${config.daily_budget_usd?.toFixed(2) || '5.00'}</strong>
       </div>
       <div class="info-item">
         <span class="label">Fallback Order:</span>
         <strong>{config.fallback_order?.join(' → ') || 'N/A'}</strong>
       </div>
     </div>
     
     {#if !editMode}
       <button class="edit-btn" onclick={startEdit}>Edit Configuration</button>
     {/if}
   </div>

   {#if error}
     <div class="alert alert-error">{error}</div>
   {/if}

   {#if success}
     <div class="alert alert-success">{success}</div>
   {/if}

   {#if editMode}
     <div class="edit-section">
       <h3>Budget Configuration</h3>
       <div class="budget-input">
         <label for="budget">Daily Budget (USD):</label>
         <input
           id="budget"
           type="number"
           bind:value={editedBudget}
           min="0"
           step="0.1"
           class="input"
         />
       </div>

       <h3>Fallback Order</h3>
       <div class="provider-list">
         {#each editedFallbackOrder as provider, index}
           <div class="provider-item">
             <span class="provider-name">{index + 1}. {provider}</span>
             <div class="provider-actions">
               <button
                 class="btn-icon"
                 onclick={() => moveFallbackProvider(index, 'up')}
                 disabled={index === 0}
               >
                 ↑
               </button>
               <button
                 class="btn-icon"
                 onclick={() => moveFallbackProvider(index, 'down')}
                 disabled={index === editedFallbackOrder.length - 1}
               >
                 ↓
               </button>
             </div>
           </div>
         {/each}
       </div>

       <h3>Routing Table</h3>
       <div class="routing-table">
         {#each Object.entries(editedRoutingTable) as [taskType, providers]}
           <div class="task-section">
             <h4>{taskType}</h4>
             <div class="provider-list">
               {#each providers as provider, index}
                 <div class="provider-item">
                   <span class="provider-name">{index + 1}. {provider}</span>
                   <div class="provider-actions">
                     <button
                       class="btn-icon"
                       onclick={() => moveProvider(taskType, index, 'up')}
                       disabled={index === 0}
                     >
                       ↑
                     </button>
                     <button
                       class="btn-icon"
                       onclick={() => moveProvider(taskType, index, 'down')}
                       disabled={index === providers.length - 1}
                     >
                       ↓
                     </button>
                   </div>
                 </div>
               {/each}
             </div>
           </div>
         {/each}
       </div>

       <div class="edit-actions">
         <button class="btn-cancel" onclick={cancelEdit} disabled={saving}>Cancel</button>
         <button class="btn-save" onclick={saveChanges} disabled={saving}>
           {saving ? 'Saving...' : 'Save Changes'}
         </button>
       </div>
     </div>
   {:else}
     <div class="routing-display">
       <h3>Current Routing Table</h3>
       <div class="routing-grid">
         {#each Object.entries(config.routing_table || {}) as [taskType, providers]}
           <div class="routing-item">
             <div class="task-label">{taskType}</div>
             <div class="provider-chain">{providers.join(' → ')}</div>
           </div>
         {/each}
       </div>
     </div>
   {/if}
 {/if}
</div>

<style>
 .config-editor {
   display: flex;
   flex-direction: column;
   gap: 16px;
 }

 .config-header {
   display: flex;
   justify-content: space-between;
   align-items: center;
   gap: 16px;
   padding-bottom: 16px;
   border-bottom: 1px solid var(--border);
 }

 .config-info {
   display: flex;
   gap: 24px;
   flex-wrap: wrap;
 }

 .info-item {
   display: flex;
   gap: 8px;
   align-items: center;
 }

 .label {
   color: var(--text-secondary);
   font-size: 14px;
 }

 .edit-btn {
   padding: 8px 16px;
   border-radius: 8px;
   border: 1px solid var(--border);
   background: rgba(99, 102, 241, 0.1);
   color: var(--accent);
   cursor: pointer;
   font-weight: 600;
   transition: all 0.2s;
 }

 .edit-btn:hover {
   background: rgba(99, 102, 241, 0.2);
 }

 .alert {
   padding: 12px 16px;
   border-radius: 8px;
   font-size: 14px;
 }

 .alert-error {
   background: rgba(239, 68, 68, 0.1);
   border: 1px solid rgba(239, 68, 68, 0.3);
   color: #ef4444;
 }

 .alert-success {
   background: rgba(16, 185, 129, 0.1);
   border: 1px solid rgba(16, 185, 129, 0.3);
   color: #10b981;
 }

 .edit-section {
   display: flex;
   flex-direction: column;
   gap: 20px;
 }

 .edit-section h3 {
   margin: 0;
   font-size: 16px;
   font-weight: 700;
   color: var(--text);
 }

 .budget-input {
   display: flex;
   align-items: center;
   gap: 12px;
 }

 .input {
   padding: 8px 12px;
   border-radius: 8px;
   border: 1px solid var(--border);
   background: rgba(255, 255, 255, 0.05);
   color: var(--text);
   font-size: 14px;
   width: 150px;
 }

 .provider-list {
   display: flex;
   flex-direction: column;
   gap: 8px;
 }

 .provider-item {
   display: flex;
   justify-content: space-between;
   align-items: center;
   padding: 10px 14px;
   border-radius: 8px;
   background: rgba(255, 255, 255, 0.03);
   border: 1px solid var(--border);
 }

 .provider-name {
   font-size: 14px;
   color: var(--text);
 }

 .provider-actions {
   display: flex;
   gap: 4px;
 }

 .btn-icon {
   width: 28px;
   height: 28px;
   border-radius: 4px;
   border: 1px solid var(--border);
   background: rgba(255, 255, 255, 0.05);
   color: var(--text);
   cursor: pointer;
   font-size: 14px;
   display: flex;
   align-items: center;
   justify-content: center;
   transition: all 0.2s;
 }

 .btn-icon:hover:not(:disabled) {
   background: rgba(255, 255, 255, 0.1);
   border-color: var(--accent);
 }

 .btn-icon:disabled {
   opacity: 0.3;
   cursor: not-allowed;
 }

 .routing-table {
   display: grid;
   grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
   gap: 16px;
 }

 .task-section {
   padding: 14px;
   border-radius: 8px;
   background: rgba(255, 255, 255, 0.02);
   border: 1px solid var(--border);
 }

 .task-section h4 {
   margin: 0 0 12px;
   font-size: 14px;
   font-weight: 600;
   color: var(--accent);
 }

 .edit-actions {
   display: flex;
   gap: 12px;
   justify-content: flex-end;
   padding-top: 16px;
   border-top: 1px solid var(--border);
 }

 .btn-cancel,
 .btn-save {
   padding: 10px 20px;
   border-radius: 8px;
   border: 1px solid var(--border);
   cursor: pointer;
   font-weight: 600;
   transition: all 0.2s;
 }

 .btn-cancel {
   background: rgba(255, 255, 255, 0.05);
   color: var(--text);
 }

 .btn-cancel:hover:not(:disabled) {
   background: rgba(255, 255, 255, 0.1);
 }

 .btn-save {
   background: rgba(99, 102, 241, 0.2);
   color: var(--accent);
 }

 .btn-save:hover:not(:disabled) {
   background: rgba(99, 102, 241, 0.3);
 }

 .btn-cancel:disabled,
 .btn-save:disabled {
   opacity: 0.5;
   cursor: not-allowed;
 }

 .routing-display h3 {
   margin: 0 0 16px;
   font-size: 16px;
   font-weight: 700;
 }

 .routing-grid {
   display: grid;
   grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
   gap: 12px;
 }

 .routing-item {
   padding: 12px 14px;
   border-radius: 8px;
   background: rgba(255, 255, 255, 0.03);
   border: 1px solid var(--border);
 }

 .task-label {
   font-size: 12px;
   font-weight: 600;
   color: var(--accent);
   margin-bottom: 6px;
 }

 .provider-chain {
   font-size: 13px;
   color: var(--text);
 }

 .empty-state {
   padding: 40px;
   text-align: center;
   color: var(--text-secondary);
 }

 @media (max-width: 768px) {
   .config-header {
     flex-direction: column;
     align-items: flex-start;
   }

   .edit-btn {
     width: 100%;
   }

   .routing-table,
   .routing-grid {
     grid-template-columns: 1fr;
   }

   .edit-actions {
     flex-direction: column;
   }

   .btn-cancel,
   .btn-save {
     width: 100%;
   }
 }
</style>
