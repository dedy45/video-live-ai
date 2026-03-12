import '../app.css';
import AIBrainPage from '../pages/AIBrainPage.svelte';

const app = new AIBrainPage({
 target: document.getElementById('app')!,
});

export default app;
