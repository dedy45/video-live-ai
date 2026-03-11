import '../app.css';
import PerformerPage from '../pages/PerformerPage.svelte';
import { mount } from 'svelte';

const app = mount(PerformerPage, {
 target: document.getElementById('app')!,
});

export default app;
