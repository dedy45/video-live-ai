import '../app.css';
import ProductsPage from '../pages/ProductsPage.svelte';
import { mount } from 'svelte';

const app = mount(ProductsPage, {
 target: document.getElementById('app')!,
});

export default app;
