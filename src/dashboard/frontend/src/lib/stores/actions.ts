/** Action receipt type for operator-visible feedback. */

export interface ActionReceipt {
  action: string;
  status: 'success' | 'error';
  message: string;
  timestamp: number;
}
