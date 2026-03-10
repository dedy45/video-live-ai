import '../../app.css';
import ProductsPage from '../pages/ProductsPage.svelte';
import App from '../../App.svelte';

// Override the App to render Products page directly
const app = new ProductsPage({
 target: document.getElementById('app')!,
});

export default app;