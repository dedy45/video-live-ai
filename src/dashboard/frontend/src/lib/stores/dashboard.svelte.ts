import { startRealtime, stopRealtime, type RealtimeSnapshot } from '../realtime';

class DashboardStore {
  snapshot = $state<RealtimeSnapshot | null>(null);
  source = $state<string>('');
  connected = $state<boolean>(false);
  refCount = 0;

  start() {
    this.refCount++;
    if (this.refCount === 1) {
      startRealtime((snap) => {
        this.snapshot = snap;
        this.source = snap.source;
        this.connected = true;
      });
    }
  }

  stop() {
    if (this.refCount > 0) {
      this.refCount--;
      if (this.refCount === 0) {
        stopRealtime();
        this.snapshot = null;
        this.source = '';
        this.connected = false;
      }
    }
  }
}

const dashboardStore = new DashboardStore();

export function useDashboardRealtime() {
  return dashboardStore;
}
