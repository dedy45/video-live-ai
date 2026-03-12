<script lang="ts">
 interface Props {
   runtime: any | null;
 }

 let { runtime }: Props = $props();
</script>

<div class="director-runtime-panel">
 {#if !runtime}
   <div class="empty-state">
     <p>📊 No runtime data available</p>
     <p class="hint">Director runtime information will appear here when the system is active.</p>
   </div>
 {:else}
   <div class="runtime-grid">
     <div class="runtime-card">
       <div class="card-header">
         <span class="icon">🎯</span>
         <h4>Current State</h4>
       </div>
       <div class="card-value">{runtime.current_state || 'IDLE'}</div>
     </div>

     <div class="runtime-card">
       <div class="card-header">
         <span class="icon">📦</span>
         <h4>Active Product</h4>
       </div>
       <div class="card-value">{runtime.active_product || 'None'}</div>
     </div>

     <div class="runtime-card">
       <div class="card-header">
         <span class="icon">⏱️</span>
         <h4>Uptime</h4>
       </div>
       <div class="card-value">{runtime.uptime || '0s'}</div>
     </div>

     <div class="runtime-card">
       <div class="card-header">
         <span class="icon">💬</span>
         <h4>Messages Processed</h4>
       </div>
       <div class="card-value">{runtime.messages_processed || 0}</div>
     </div>
   </div>

   <div class="runtime-details">
     <h3>Runtime Details</h3>
     <pre>{JSON.stringify(runtime, null, 2)}</pre>
   </div>
 {/if}
</div>

<style>
 .director-runtime-panel {
   padding: 1rem;
 }

 .empty-state {
   text-align: center;
   padding: 3rem 2rem;
   color: var(--text-secondary);
 }

 .empty-state .hint {
   font-size: 14px;
   margin-top: 8px;
 }

 .runtime-grid {
   display: grid;
   grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
   gap: 16px;
   margin-bottom: 24px;
 }

 .runtime-card {
   padding: 16px;
   background: rgba(255, 255, 255, 0.03);
   border-radius: 8px;
   border: 1px solid var(--border);
 }

 .card-header {
   display: flex;
   align-items: center;
   gap: 8px;
   margin-bottom: 12px;
 }

 .icon {
   font-size: 20px;
 }

 .card-header h4 {
   margin: 0;
   font-size: 14px;
   font-weight: 600;
   color: var(--text-secondary);
 }

 .card-value {
   font-size: 24px;
   font-weight: 700;
   color: var(--text);
 }

 .runtime-details {
   padding: 16px;
   background: rgba(0, 0, 0, 0.2);
   border-radius: 8px;
   border: 1px solid var(--border);
 }

 .runtime-details h3 {
   margin: 0 0 12px;
   font-size: 16px;
   font-weight: 700;
   color: var(--text);
 }

 .runtime-details pre {
   margin: 0;
   font-size: 13px;
   line-height: 1.5;
   color: var(--text-secondary);
   overflow-x: auto;
 }

 @media (max-width: 768px) {
   .runtime-grid {
     grid-template-columns: 1fr;
   }
 }
</style>
