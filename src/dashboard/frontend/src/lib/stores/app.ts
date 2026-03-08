import { getStatus } from '../api';

export interface AppState {
  status: Record<string, any>;
  loading: boolean;
  error: string;
  lastUpdated: number;
}

let appState: AppState = {
  status: {},
  loading: false,
  error: '',
  lastUpdated: 0,
};

export function getAppState(): AppState {
  return appState;
}

export async function refreshStatus(): Promise<void> {
  appState.loading = true;
  try {
    appState.status = await getStatus();
    appState.error = '';
    appState.lastUpdated = Date.now();
  } catch (e: any) {
    appState.error = e.message;
  } finally {
    appState.loading = false;
  }
}
