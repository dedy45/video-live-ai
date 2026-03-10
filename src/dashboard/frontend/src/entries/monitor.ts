import '../../app.css';
import MonitorPage from '../pages/MonitorPage.svelte';

const app = new MonitorPage({
 target: document.getElementById('app')!,
});

export default app;