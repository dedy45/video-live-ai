<script lang="ts">
 interface Props {
   runtime: any | null;
 }

 let { runtime }: Props = $props();
</script>

<div class="director-runtime-panel">
 <h3 class="panel-heading">Director Runtime</h3>
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
       <div class="card-value">{runtime.director?.state || 'IDLE'}</div>
     </div>

     <div class="runtime-card">
       <div class="card-header">
         <span class="icon">🧠</span>
         <h4>Active Provider</h4>
       </div>
       <div class="card-value">{runtime.brain?.active_provider || 'unknown'}</div>
     </div>

     <div class="runtime-card">
       <div class="card-header">
         <span class="icon">📝</span>
         <h4>Active Prompt</h4>
       </div>
       <div class="card-value">{runtime.prompt?.active_revision || 'unknown'}</div>
     </div>

     <div class="runtime-card">
       <div class="card-header">
         <span class="icon">🎬</span>
         <h4>Current Phase</h4>
       </div>
       <div class="card-value">{runtime.script?.current_phase || runtime.director?.current_phase || 'unknown'}</div>
     </div>
    </div>

   <div class="runtime-summary">
     <div class="summary-item">
       <span class="summary-label">Model</span>
       <strong>{runtime.brain?.active_model || 'unknown'}</strong>
     </div>
     <div class="summary-item">
       <span class="summary-label">Budget</span>
       <strong>${runtime.brain?.daily_budget_usd?.toFixed?.(2) ?? '0.00'}</strong>
     </div>
     <div class="summary-item">
       <span class="summary-label">Persona</span>
       <strong>{runtime.persona?.name || 'unknown'}</strong>
     </div>
     <div class="summary-item">
       <span class="summary-label">Uptime</span>
       <strong>{runtime.director?.uptime_sec ?? 0}s</strong>
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

.panel-heading {
  margin: 0 0 16px;
  font-size: 18px;
  font-weight: 800;
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

 .runtime-summary {
   display: grid;
   grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
   gap: 12px;
   margin-bottom: 24px;
 }

 .summary-item {
   padding: 14px 16px;
   border-radius: 8px;
   background: rgba(255, 255, 255, 0.03);
   border: 1px solid var(--border);
   display: flex;
   flex-direction: column;
   gap: 6px;
 }

 .summary-label {
   font-size: 12px;
   color: var(--text-secondary);
   text-transform: uppercase;
   letter-spacing: 0.04em;
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
