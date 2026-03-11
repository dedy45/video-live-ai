import type { ActionReceipt } from './stores/actions';
import type { EngineStatus, OperatorActionResult, RuntimeTruth } from './types';

interface BuildReceiptOptions {
  action: string;
  title: string;
  status: ActionReceipt['status'];
  message: string;
  nextStep?: string;
  details?: string[];
}

interface OperatorActionOptions<T extends Record<string, any>> {
  action: string;
  title: string;
  pendingTitle?: string;
  pendingMessage?: string;
  fallbackMessage: string;
  execute: () => Promise<T>;
  onReceipt: (receipt: ActionReceipt) => void;
}

interface ReconciledEngineActionOptions {
  action: string;
  title: string;
  desiredState: 'running' | 'stopped';
  execute: () => Promise<OperatorActionResult & Partial<EngineStatus>>;
  getTruth: () => Promise<RuntimeTruth>;
  getStatus: () => Promise<EngineStatus>;
  onReceipt: (receipt: ActionReceipt) => void;
  onTruthUpdate?: (truth: RuntimeTruth) => void;
  onStatusUpdate?: (status: EngineStatus) => void;
  timeoutMs?: number;
  intervalMs?: number;
}

function mapActionStatus(status: string | undefined): ActionReceipt['status'] {
  if (status === 'blocked') return 'blocked';
  if (status === 'pending') return 'pending';
  if (status === 'warning') return 'warning';
  if (status === 'error' || status === 'fail') return 'error';
  return 'success';
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function buildDetails(result: Record<string, any>) {
  const details = Array.isArray(result.details) ? [...result.details] : [];
  if (result.reason_code) details.unshift(`reason_code ${result.reason_code}`);
  if (typeof result.state === 'string' && !details.some((detail) => detail.includes(`state ${result.state}`))) {
    details.push(`state ${result.state}`);
  }
  return details;
}

export function buildReceipt({
  action,
  title,
  status,
  message,
  nextStep,
  details = [],
}: BuildReceiptOptions): ActionReceipt {
  return {
    action,
    title,
    status,
    message,
    timestamp: Date.now(),
    details,
    nextStep,
  };
}

export async function runOperatorAction<T extends Record<string, any>>({
  action,
  title,
  pendingTitle,
  pendingMessage,
  fallbackMessage,
  execute,
  onReceipt,
}: OperatorActionOptions<T>): Promise<T> {
  if (pendingTitle || pendingMessage) {
    onReceipt(
      buildReceipt({
        action,
        title: pendingTitle ?? title,
        status: 'pending',
        message: pendingMessage ?? 'Permintaan sedang diproses.',
      }),
    );
  }

  try {
    const result = await execute();
    onReceipt(
      buildReceipt({
        action,
        title,
        status: mapActionStatus(String(result.status ?? 'success')),
        message: String(result.message ?? fallbackMessage),
        nextStep: typeof result.next_step === 'string' ? result.next_step : undefined,
        details: buildDetails(result),
      }),
    );
    return result;
  } catch (error: any) {
    onReceipt(
      buildReceipt({
        action,
        title,
        status: 'error',
        message: error?.message ?? fallbackMessage,
      }),
    );
    throw error;
  }
}

export async function runReconciledEngineAction({
  action,
  title,
  desiredState,
  execute,
  getTruth,
  getStatus,
  onReceipt,
  onTruthUpdate,
  onStatusUpdate,
  timeoutMs = 5000,
  intervalMs = 500,
}: ReconciledEngineActionOptions): Promise<void> {
  let result: OperatorActionResult & Partial<EngineStatus>;

  try {
    result = await execute();
  } catch (error: any) {
    onReceipt(
      buildReceipt({
        action,
        title,
        status: 'error',
        message: error?.message ?? 'Aksi avatar gagal dijalankan.',
      }),
    );
    return;
  }

  const startMessage =
    desiredState === 'running'
      ? 'Dashboard sedang menunggu avatar tercatat berjalan.'
      : 'Dashboard sedang menunggu avatar tercatat berhenti.';

  onReceipt(
    buildReceipt({
      action,
      title,
      status: 'pending',
      message: startMessage,
      nextStep: typeof result.next_step === 'string' ? result.next_step : undefined,
      details: buildDetails(result),
    }),
  );

  const deadline = Date.now() + timeoutMs;

  while (Date.now() <= deadline) {
    try {
      const truth = await getTruth();
      onTruthUpdate?.(truth);
      if (truth.face_engine?.engine_state === desiredState) {
        onReceipt(
          buildReceipt({
            action,
            title,
            status: 'success',
            message:
              desiredState === 'running'
                ? 'Status avatar sudah tersinkron dengan runtime terbaru.'
                : 'Status avatar berhenti sudah tersinkron dengan runtime terbaru.',
            nextStep:
              desiredState === 'running'
                ? 'Buka tab Preview untuk memastikan feed avatar tampil normal.'
                : 'Avatar sudah aman dihentikan.',
            details: buildDetails(result),
          }),
        );
        return;
      }
    } catch {
      // Ignore transient truth fetch errors during reconciliation.
    }

    try {
      const status = await getStatus();
      onStatusUpdate?.(status);
      if (status.state === desiredState) {
        onReceipt(
          buildReceipt({
            action,
            title,
            status: 'success',
            message:
              desiredState === 'running'
                ? 'Engine avatar sudah melapor berjalan. Dashboard akan mengikuti snapshot terbaru.'
                : 'Engine avatar sudah melapor berhenti. Dashboard akan mengikuti snapshot terbaru.',
            nextStep:
              desiredState === 'running'
                ? 'Jika preview masih kosong, cek tab Preview dan Teknis.'
                : 'Jika status masih tertahan, cek tab Teknis untuk log terbaru.',
            details: buildDetails({ ...result, state: status.state }),
          }),
        );
        return;
      }
    } catch {
      // Ignore transient status fetch errors during reconciliation.
    }

    await sleep(intervalMs);
  }

  onReceipt(
    buildReceipt({
      action,
      title,
      status: 'warning',
      message:
        desiredState === 'running'
          ? 'Perintah sudah diterima, tetapi dashboard belum melihat avatar berjalan.'
          : 'Perintah sudah diterima, tetapi dashboard belum melihat avatar berhenti.',
      nextStep:
        typeof result.next_step === 'string'
          ? result.next_step
          : 'Muat ulang status langsung atau cek tab Teknis untuk log terbaru.',
      details: buildDetails(result),
    }),
  );
}
