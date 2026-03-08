/**
 * Realtime state module — WebSocket with polling fallback.
 *
 * Connects to /api/ws/dashboard for live updates.
 * Falls back to polling /api/status + /api/runtime/truth every POLL_INTERVAL_MS
 * if the WebSocket is unavailable or disconnects.
 */

import { WS_BASE, POLL_INTERVAL_MS } from './constants';
import { getStatus, getRuntimeTruth } from './api';

export interface RealtimeSnapshot {
  stream_running: boolean;
  emergency_stopped: boolean;
  mock_mode: boolean;
  pipeline_state: string;
  current_product: { name: string; price: string } | null;
  truth: Record<string, any> | null;
  /** ISO timestamp of when this snapshot was received */
  received_at: string;
  /** 'websocket' | 'polling' */
  source: string;
  [key: string]: any;
}

type SnapshotCallback = (snapshot: RealtimeSnapshot) => void;

let _ws: WebSocket | null = null;
let _pollTimer: ReturnType<typeof setInterval> | null = null;
let _callback: SnapshotCallback | null = null;
let _running = false;
let _wsRetryCount = 0;
const MAX_WS_RETRIES = 5;
const WS_RETRY_DELAY_MS = 3000;

function _connectWs(): void {
  if (_ws && (_ws.readyState === WebSocket.OPEN || _ws.readyState === WebSocket.CONNECTING)) {
    return;
  }

  try {
    _ws = new WebSocket(`${WS_BASE}/ws/dashboard`);

    _ws.onopen = () => {
      _wsRetryCount = 0;
      // Stop polling if WS is up
      _stopPolling();
    };

    _ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const snapshot: RealtimeSnapshot = {
          ...data,
          received_at: new Date().toISOString(),
          source: 'websocket',
        };
        _callback?.(snapshot);
      } catch {
        // Ignore malformed messages
      }
    };

    _ws.onclose = () => {
      _ws = null;
      if (_running) {
        _startPolling();
        // Retry WS after delay
        if (_wsRetryCount < MAX_WS_RETRIES) {
          _wsRetryCount++;
          setTimeout(() => {
            if (_running) _connectWs();
          }, WS_RETRY_DELAY_MS);
        }
      }
    };

    _ws.onerror = () => {
      // onclose will fire after onerror
      _ws?.close();
    };
  } catch {
    // WS construction failed — stay on polling
    _startPolling();
  }
}

async function _poll(): Promise<void> {
  try {
    const [status, truth] = await Promise.all([getStatus(), getRuntimeTruth()]);
    const snapshot: RealtimeSnapshot = {
      ...status,
      truth,
      received_at: new Date().toISOString(),
      source: 'polling',
    };
    _callback?.(snapshot);
  } catch {
    // Silently skip failed poll — next interval will retry
  }
}

function _startPolling(): void {
  if (_pollTimer) return;
  _pollTimer = setInterval(_poll, POLL_INTERVAL_MS);
  // Also fire immediately
  _poll();
}

function _stopPolling(): void {
  if (_pollTimer) {
    clearInterval(_pollTimer);
    _pollTimer = null;
  }
}

/**
 * Start receiving realtime dashboard updates.
 * Tries WebSocket first, falls back to polling.
 */
export function startRealtime(callback: SnapshotCallback): void {
  _callback = callback;
  _running = true;
  _wsRetryCount = 0;
  _connectWs();
  // Start polling as initial fallback until WS connects
  _startPolling();
}

/**
 * Stop all realtime updates and clean up.
 */
export function stopRealtime(): void {
  _running = false;
  _callback = null;
  _stopPolling();
  if (_ws) {
    _ws.close();
    _ws = null;
  }
}
