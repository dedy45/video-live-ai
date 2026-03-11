import { getHealthSummary, getRuntimeTruth, getStatus } from './api';

export interface RealtimeSnapshot {
  stream_running: boolean;
  emergency_stopped: boolean;
  mock_mode: boolean;
  pipeline_state: string;
  current_product: { name: string; price: string } | null;
  truth: Record<string, any> | null;
  health: Record<string, any> | null;
  components?: Record<string, any>;
  gauges?: Record<string, any>;
  llm_stats?: Record<string, any>;
  received_at: string;
  source: 'bootstrap' | 'websocket' | 'polling';
  [key: string]: any;
}

function withRealtimeDefaults(snapshot: Partial<RealtimeSnapshot>, source: RealtimeSnapshot['source']): RealtimeSnapshot {
  const health = snapshot.health ?? null;
  return {
    stream_running: false,
    emergency_stopped: false,
    mock_mode: false,
    pipeline_state: 'UNKNOWN',
    current_product: null,
    truth: null,
    ...snapshot,
    gauges: snapshot.gauges ?? {},
    llm_stats: snapshot.llm_stats ?? {},
    health,
    components: snapshot.components ?? health?.components ?? {},
    received_at: new Date().toISOString(),
    source,
  };
}

export async function bootstrapRuntimeSnapshot(): Promise<RealtimeSnapshot> {
  const [status, truth, health] = await Promise.all([
    getStatus(),
    getRuntimeTruth(),
    getHealthSummary(),
  ]);

  return withRealtimeDefaults(
    {
      ...status,
      pipeline_state: status.state ?? 'UNKNOWN',
      truth,
      health,
    },
    'bootstrap',
  );
}

export async function normalizePolledSnapshot(): Promise<RealtimeSnapshot> {
  const snapshot = await bootstrapRuntimeSnapshot();
  return withRealtimeDefaults(snapshot, 'polling');
}

export function normalizeWebsocketSnapshot(data: Record<string, any>): RealtimeSnapshot {
  return withRealtimeDefaults(
    {
      ...data,
      health: data.health ?? (data.components ? { components: data.components } : null),
    },
    'websocket',
  );
}
