import '../app.css';
import SetupPage from '../pages/SetupPage.svelte';
import { mount } from 'svelte';

const app = mount(SetupPage, {
 target: document.getElementById('app')!,
});

export default app;
