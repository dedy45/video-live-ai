<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    title?: string;
    size?: 'sm' | 'md' | 'lg' | 'xl';
    className?: string;
    children?: Snippet;
  }
  let { title, size = 'md', className = '', children }: Props = $props();
</script>

<div class="card card-{size} {className}" role="region">
  {#if title}
    <div class="card-header">
      <h3 class="card-title">{title}</h3>
    </div>
  {/if}
  <div class="card-content">
    {@render children?.()}
  </div>
</div>

<style>
  .card {
    background: var(--card);
    border-radius: var(--radius, 12px);
    border: 1px solid var(--border);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    flex-direction: column;
    position: relative;
    overflow: hidden;
  }

  .card::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, transparent 0%, rgba(255,255,255,0.02) 100%);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.3s ease;
  }

  .card:hover::before {
    opacity: 1;
  }

  .card:hover {
    background: var(--card-hover, #1c1c44);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    transform: translateY(-2px);
  }

  .card-header {
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 16px;
  }

  .card-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin: 0;
  }

  .card-content {
    flex: 1;
  }

  /* Size variants */
  .card-sm {
    border-radius: calc(var(--radius, 12px) * 0.75);
  }

  .card-md {
    border-radius: var(--radius, 12px);
  }

  .card-lg {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .card-xl {
    border-radius: calc(var(--radius, 12px) * 1.25);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .card {
      border-radius: calc(var(--radius, 12px) * 0.85);
    }

    .card-header {
      padding-bottom: 12px;
      margin-bottom: 12px;
    }

    .card-title {
      font-size: 12px;
    }
  }

  /* High contrast mode */
  @media (prefers-contrast: high) {
    .card {
      border-width: 2px;
    }
  }

  /* Reduced motion */
  @media (prefers-reduced-motion: reduce) {
    .card {
      transition: none;
    }

    .card:hover {
      transform: none;
    }
  }
</style>
