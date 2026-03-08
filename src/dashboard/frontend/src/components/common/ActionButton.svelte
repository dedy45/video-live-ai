<script lang="ts">
  interface Props {
    variant?: 'primary' | 'start' | 'stop' | 'emergency' | 'ghost';
    size?: 'sm' | 'md';
    disabled?: boolean;
    onclick?: () => void;
  }
  let { variant = 'ghost', size = 'md', disabled = false, onclick }: Props = $props();
</script>

<button class="btn btn-{variant}" class:btn-sm={size === 'sm'} {disabled} {onclick}>
  <slot />
</button>

<style>
  .btn { padding: 8px 16px; border: none; border-radius: var(--rsm); cursor: pointer; font-size: 12px; font-weight: 700; font-family: inherit; transition: all .2s; display: inline-flex; align-items: center; gap: 5px; }
  .btn:hover { transform: translateY(-1px); }
  .btn:active { transform: translateY(0); }
  .btn:disabled { opacity: .4; cursor: not-allowed; transform: none; }
  .btn-primary { background: var(--blue); color: #fff; }
  .btn-start { background: var(--green); color: #000; }
  .btn-stop { background: var(--yellow); color: #000; }
  .btn-emergency { background: var(--accent); color: #fff; }
  .btn-ghost { background: rgba(255,255,255,.06); color: var(--text); border: 1px solid var(--border); }
  .btn-ghost:hover { background: rgba(255,255,255,.1); }
  .btn-sm { padding: 5px 10px; font-size: 11px; }
</style>
