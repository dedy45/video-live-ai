<script lang="ts">
  import type { StatusType } from '../../lib/types';

  interface Props {
    status: StatusType | string; // Support both typed and string
    label?: string;
    size?: 'sm' | 'md' | 'lg';
    showDot?: boolean;
    className?: string;
  }

  let {
    status = 'info',
    label = '',
    size = 'md',
    showDot = true,
    className = ''
  }: Props = $props();

  // Map status to colors - matching the documentation
  const STATUS_COLORS = {
    ready: '#10b981', // Emerald green
    warning: '#f59e0b', // Amber
    error: '#ef4444', // Red
    idle: '#6b7280', // Gray
    info: '#ff7a59', // Warm coral for dark theme readability
    blocked: '#f59e0b',
    // Legacy support
    running: '#10b981',
    live: '#10b981',
    healthy: '#10b981',
    mock: '#f59e0b',
    stopped: '#ef4444',
    failed: '#ef4444',
  } as const;

  // Normalize status
  const normalizedStatus = $derived(() => {
    const statusMap: Record<string, StatusType> = {
      'running': 'ready',
      'live': 'ready',
      'healthy': 'ready',
      'blocked': 'warning',
      'mock': 'warning',
      'stopped': 'error',
      'idle': 'idle',
      'failed': 'error',
      'error': 'error',
      'ready': 'ready',
      'warning': 'warning',
      'info': 'info',
    };
    return statusMap[status] || 'info';
  });

  // Get color based on status
  const color = $derived(STATUS_COLORS[status] || STATUS_COLORS.info);

  // Calculate contrasting text color
  function getContrastColor(hexColor: string): string {
    const r = parseInt(hexColor.slice(1, 3), 16);
    const g = parseInt(hexColor.slice(3, 5), 16);
    const b = parseInt(hexColor.slice(5, 7), 16);
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.5 ? '#000000' : '#ffffff';
  }

  const calculatedTextColor = $derived(getContrastColor(color));
  const finalStatus = $derived(normalizedStatus());

  // Get size-specific styles
  const sizeClasses = $derived({
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base'
  }[size]);
</script>

<span
 class="status-badge {sizeClasses} {className} status-{finalStatus}"
 style:background-color={color}
 style:color={calculatedTextColor}
 role="status"
 aria-label={`Status: ${finalStatus}`}>
 {#if showDot}
   <span class="status-dot"></span>
 {/if}
 {label || status}
</span>

<style>
 .status-badge {
   display: inline-flex;
   align-items: center;
   gap: 6px;
   border-radius: 9999px;
   font-weight: 500;
   white-space: nowrap;
   transition: all 0.2s ease;
   border: 1px solid transparent;
 }

 .status-badge:hover {
   transform: translateY(-1px);
   box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
 }

 .status-dot {
   width: 8px;
   height: 8px;
   border-radius: 9999px;
   background: currentColor;
   animation: pulse 2s infinite;
 }

 @keyframes pulse {
   0%, 100% {
     opacity: 1;
   }
   50% {
     opacity: 0.7;
   }
 }

 /* Size variants */
 .text-xs {
   font-size: 0.75rem;
   line-height: 1rem;
 }

 .text-sm {
   font-size: 0.875rem;
   line-height: 1.25rem;
 }

 .text-base {
   font-size: 1rem;
   line-height: 1.5rem;
 }

 /* Status-specific variants */
 .status-ready {
   border-color: rgba(16, 185, 129, 0.3);
 }

 .status-warning {
   border-color: rgba(245, 158, 11, 0.3);
 }

 .status-error {
   border-color: rgba(239, 68, 68, 0.3);
 }

 .status-idle {
   border-color: rgba(107, 114, 128, 0.3);
 }

 .status-info {
   border-color: rgba(255, 122, 89, 0.32);
 }

 /* Legacy support for old class names */
 .badge-live { composes: status-ready; }
 .badge-mock { composes: status-warning; }
 .badge-idle { composes: status-idle; }
 .badge-error { composes: status-error; }

 /* Accessibility */
 [role="status"] {
   cursor: help;
 }

 [role="status"]:hover::after {
   content: attr(aria-label);
   position: absolute;
   bottom: 100%;
   left: 50%;
   transform: translateX(-50%);
   padding: 4px 8px;
   background: var(--bg);
   color: var(--text);
   border: 1px solid var(--border);
   border-radius: 4px;
   font-size: 12px;
   white-space: nowrap;
   z-index: 1000;
   margin-bottom: 4px;
 }

 /* Focus styles for accessibility */
 .status-badge:focus {
   outline: 2px solid currentColor;
   outline-offset: 2px;
 }

 /* High contrast mode support */
 @media (prefers-contrast: high) {
   .status-badge {
     border-width: 2px;
   }
 }

 /* Reduced motion support */
 @media (prefers-reduced-motion: reduce) {
   .status-dot {
     animation: none;
   }

   .status-badge {
     transition: none;
   }

   .status-badge:hover {
     transform: none;
   }
 }
</style>
