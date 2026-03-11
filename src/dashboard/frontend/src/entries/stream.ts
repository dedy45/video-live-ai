import '../app.css';
import StreamPage from '../pages/StreamPage.svelte';
import { mount } from 'svelte';

const app = mount(StreamPage, {
 target: document.getElementById('app')!,
});

export default app;
