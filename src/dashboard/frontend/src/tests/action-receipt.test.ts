import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import ActionReceipt from '../components/common/ActionReceipt.svelte';

describe('ActionReceipt', () => {
  it('renders operator-first copy with title, next step, and hidden technical details', async () => {
    render(ActionReceipt, {
      props: {
        receipt: {
          title: 'Avatar menerima perintah jalan',
          action: 'engine.start',
          status: 'warning',
          message: 'Perintah sudah dikirim, tetapi status avatar belum ikut berubah.',
          nextStep: 'Tunggu beberapa detik lalu cek lagi status avatar.',
          details: ['reason_code engine_start_requested', 'state running'],
          timestamp: Date.now(),
        },
      },
    });

    expect(screen.getByTestId('action-receipt')).toBeInTheDocument();
    expect(screen.getByText(/avatar menerima perintah jalan/i)).toBeInTheDocument();
    expect(screen.getByText(/status avatar belum ikut berubah/i)).toBeInTheDocument();
    expect(screen.getByText(/tunggu beberapa detik/i)).toBeInTheDocument();
    expect(screen.queryByText(/engine.start/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/engine_start_requested/i)).not.toBeInTheDocument();

    await fireEvent.click(screen.getByRole('button', { name: /lihat detail teknis/i }));
    expect(screen.getByText(/engine_start_requested/i)).toBeInTheDocument();
  });

  it('shows pending receipts with neutral operator styling', () => {
    render(ActionReceipt, {
      props: {
        receipt: {
          title: 'Sedang menyinkronkan status avatar',
          status: 'pending',
          message: 'Dashboard sedang menunggu status terbaru dari runtime.',
          timestamp: Date.now(),
        },
      },
    });

    const receipt = screen.getByTestId('action-receipt');
    expect(receipt).toHaveTextContent(/sedang menyinkronkan/i);
    expect(receipt.classList.contains('receipt-pending')).toBe(true);
  });
});
