import '../../app.css';
import StreamPage from '../pages/StreamPage.svelte';

const app = new StreamPage({
 target: document.getElementById('app')!,
});

export default app;