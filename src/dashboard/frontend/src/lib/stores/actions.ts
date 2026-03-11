/** Action receipt type for operator-visible feedback. */
import type { OperatorActionStatus } from '../types';

export interface ActionReceipt {
  action?: string;
  title?: string;
  status: OperatorActionStatus;
  message: string;
  timestamp: number;
  details?: string[];
  nextStep?: string;
}
