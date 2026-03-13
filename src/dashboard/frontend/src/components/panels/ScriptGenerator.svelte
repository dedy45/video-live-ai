<script lang="ts">
 let productName = $state('');
 let price = $state(0);
 let features = $state('');
 let duration = $state(30);
 let provider = $state('');
 let generating = $state(false);
 let generatedScript = $state('');
 let generatedProvider = $state('');
 let generatedModel = $state('');
 let generatedLatencyMs = $state<number | null>(null);
 let error = $state('');

 async function generateScript() {
   if (!productName || price <= 0) {
     error = 'Please fill in product name and price';
     return;
   }

   generating = true;
   error = '';
   generatedScript = '';

   try {
     const response = await fetch('/api/brain/generate-script', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({
         product_name: productName,
         price,
         features: features.split('\n').filter(f => f.trim()),
         target_duration_sec: duration,
         provider: provider || null,
       })
     });

     const data = await response.json();
     if (!response.ok) {
       throw new Error(data.detail || 'Failed to generate script');
     }

     generatedScript = data.script || 'Script generated successfully';
     generatedProvider = data.provider || '';
     generatedModel = data.model || '';
     generatedLatencyMs = typeof data.latency_ms === 'number' ? data.latency_ms : null;
   } catch (e: any) {
     error = e.message || 'Failed to generate script';
   } finally {
     generating = false;
   }
 }

 function clearForm() {
   productName = '';
   price = 0;
   features = '';
   duration = 30;
    provider = '';
    generatedScript = '';
    generatedProvider = '';
    generatedModel = '';
    generatedLatencyMs = null;
    error = '';
  }
</script>

<div class="script-generator">
 <div class="form-section">
   <h3>✨ Generate Selling Script</h3>
   <p class="description">Generate AI-powered selling scripts for your products</p>

   {#if error}
     <div class="alert alert-error">{error}</div>
   {/if}

   <div class="form-grid">
     <div class="form-group">
       <label for="product-name">Product Name</label>
       <input
         id="product-name"
         type="text"
         bind:value={productName}
         placeholder="e.g., Lipstik Matte Premium"
         class="input"
       />
     </div>

     <div class="form-group">
       <label for="price">Price (Rp)</label>
       <input
         id="price"
         type="number"
         bind:value={price}
         min="0"
         placeholder="e.g., 89000"
         class="input"
       />
     </div>

     <div class="form-group full-width">
       <label for="features">Features (one per line)</label>
       <textarea
         id="features"
         bind:value={features}
         rows="4"
         placeholder="Long-lasting&#10;Waterproof&#10;10 warna pilihan"
         class="input"
       ></textarea>
     </div>

     <div class="form-group">
       <label for="duration">Target Duration (seconds)</label>
       <input
         id="duration"
         type="number"
         bind:value={duration}
         min="10"
         max="120"
         class="input"
       />
     </div>

     <div class="form-group">
       <label for="provider">LLM Provider</label>
       <select id="provider" bind:value={provider} class="input">
         <option value="">Auto</option>
         <option value="groq">Groq</option>
         <option value="gemini">Gemini</option>
         <option value="claude">Claude</option>
         <option value="gpt4o">GPT-4o</option>
       </select>
     </div>
   </div>

   <div class="form-actions">
     <button class="btn-secondary" onclick={clearForm}>Clear</button>
     <button class="btn-primary" onclick={generateScript} disabled={generating}>
       {generating ? 'Generating...' : 'Generate Script'}
     </button>
   </div>
 </div>

 {#if generatedScript}
   <div class="result-section">
     <h3>📄 Generated Script</h3>
     <div class="result-meta">
       <span><strong>Provider:</strong> {generatedProvider || 'auto'}</span>
       {#if generatedModel}
         <span><strong>Model:</strong> {generatedModel}</span>
       {/if}
       {#if generatedLatencyMs !== null}
         <span><strong>Latency:</strong> {generatedLatencyMs} ms</span>
       {/if}
     </div>
     <div class="script-output">
       <pre>{generatedScript}</pre>
     </div>
     <button class="btn-copy" onclick={() => navigator.clipboard.writeText(generatedScript)}>
       📋 Copy to Clipboard
     </button>
   </div>
 {/if}
</div>

<style>
 .script-generator {
   display: flex;
   flex-direction: column;
   gap: 24px;
 }

 .form-section h3,
 .result-section h3 {
   margin: 0 0 8px;
   font-size: 18px;
   font-weight: 700;
   color: var(--text);
 }

 .description {
   margin: 0 0 20px;
   color: var(--text-secondary);
   font-size: 14px;
 }

 .alert {
   padding: 12px 16px;
   border-radius: 8px;
   font-size: 14px;
   margin-bottom: 16px;
 }

 .alert-error {
   background: rgba(239, 68, 68, 0.1);
   border: 1px solid rgba(239, 68, 68, 0.3);
   color: #ef4444;
 }

 .form-grid {
   display: grid;
   grid-template-columns: repeat(2, 1fr);
   gap: 16px;
   margin-bottom: 20px;
 }

 .form-group {
   display: flex;
   flex-direction: column;
   gap: 8px;
 }

 .form-group.full-width {
   grid-column: 1 / -1;
 }

 .form-group label {
   font-size: 14px;
   font-weight: 600;
   color: var(--text);
 }

 .input {
   padding: 10px 12px;
   border-radius: 8px;
   border: 1px solid var(--border);
   background: rgba(255, 255, 255, 0.05);
   color: var(--text);
   font-size: 14px;
   font-family: inherit;
 }

 textarea.input {
   resize: vertical;
   font-family: inherit;
 }

 .form-actions {
   display: flex;
   gap: 12px;
   justify-content: flex-end;
 }

 .btn-primary,
 .btn-secondary,
 .btn-copy {
   padding: 10px 20px;
   border-radius: 8px;
   border: 1px solid var(--border);
   cursor: pointer;
   font-weight: 600;
   transition: all 0.2s;
 }

 .btn-primary {
   background: rgba(99, 102, 241, 0.2);
   color: var(--accent);
 }

 .btn-primary:hover:not(:disabled) {
   background: rgba(99, 102, 241, 0.3);
 }

 .btn-primary:disabled {
   opacity: 0.5;
   cursor: not-allowed;
 }

 .btn-secondary {
   background: rgba(255, 255, 255, 0.05);
   color: var(--text);
 }

 .btn-secondary:hover {
   background: rgba(255, 255, 255, 0.1);
 }

 .result-section {
   padding: 20px;
   background: rgba(255, 255, 255, 0.02);
   border-radius: 8px;
   border: 1px solid var(--border);
 }

 .result-meta {
   display: flex;
   flex-wrap: wrap;
   gap: 12px;
   color: var(--text-secondary);
   font-size: 14px;
 }

 .script-output {
   margin: 16px 0;
   padding: 16px;
   background: rgba(0, 0, 0, 0.2);
   border-radius: 8px;
   border: 1px solid var(--border);
 }

 .script-output pre {
   margin: 0;
   white-space: pre-wrap;
   word-wrap: break-word;
   font-size: 14px;
   line-height: 1.6;
   color: var(--text);
 }

 .btn-copy {
   background: rgba(16, 185, 129, 0.1);
   color: #10b981;
 }

 .btn-copy:hover {
   background: rgba(16, 185, 129, 0.2);
 }

 @media (max-width: 768px) {
   .form-grid {
     grid-template-columns: 1fr;
   }

   .form-actions {
     flex-direction: column;
   }

   .btn-primary,
   .btn-secondary {
     width: 100%;
   }
 }
</style>
