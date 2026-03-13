import '../app.css';
import AIBrainPage from '../pages/AIBrainPage.svelte';
import { mount } from 'svelte';

const app = mount(AIBrainPage, {
 target: document.getElementById('app')!,
});

export default app;
