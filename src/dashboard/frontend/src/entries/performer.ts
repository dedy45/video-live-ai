import '../../app.css';
import PerformerPage from '../pages/PerformerPage.svelte';

const app = new PerformerPage({
 target: document.getElementById('app')!,
});

export default app;