import '../../app.css';
import ValidationPage from '../pages/ValidationPage.svelte';

const app = new ValidationPage({
 target: document.getElementById('app')!,
});

export default app;