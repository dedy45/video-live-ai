import '../app.css';
import MonitorPage from '../pages/MonitorPage.svelte';
import { mount } from 'svelte';

const app = mount(MonitorPage, {
 target: document.getElementById('app')!,
});

export default app;
