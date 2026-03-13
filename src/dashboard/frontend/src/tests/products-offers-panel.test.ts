import { describe, it, expect, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import ProductsOffersPanel from '../components/panels/ProductsOffersPanel.svelte';

const { createProduct } = vi.hoisted(() => ({
  createProduct: vi.fn().mockResolvedValue({ id: 3, name: 'Serum Retinol' }),
}));

vi.mock('../lib/api', () => ({
  getProducts: vi.fn().mockResolvedValue([
    {
      id: 1,
      name: 'Smart Watch X1',
      price: 299000,
      price_formatted: 'Rp 299,000',
      category: 'electronics',
      is_active: true,
      affiliate_links: {
        tiktok: 'https://tiktok.com/shop/product1',
        shopee: 'https://shopee.co.id/product1',
      },
      selling_points: ['Waterproof IP68', 'Battery 7 days', 'Heart rate monitor'],
      commission_rate: 15.0,
      objection_handling: {
        'too expensive': 'Bandingkan dengan brand lain, ini lebih murah dengan fitur lengkap',
      },
      compliance_notes: 'Garansi resmi 1 tahun',
    },
    {
      id: 2,
      name: 'Wireless Earbuds Pro',
      price: 199000,
      price_formatted: 'Rp 199,000',
      category: 'electronics',
      is_active: true,
      affiliate_links: {
        tiktok: 'https://tiktok.com/shop/product2',
        shopee: 'https://shopee.co.id/product2',
      },
      selling_points: ['Active noise cancelling', 'Touch control', 'USB-C charging'],
      commission_rate: 12.0,
      objection_handling: {},
      compliance_notes: '',
    },
  ]),
  getStatus: vi.fn().mockResolvedValue({
    current_product: {
      id: 1,
      name: 'Smart Watch X1',
      price_formatted: 'Rp 299,000',
    },
  }),
  getLiveSession: vi.fn().mockResolvedValue({
    session: { id: 11, status: 'active', platform: 'tiktok' },
    state: {
      current_mode: 'ROTATING',
      current_focus_product_id: 1,
      rotation_paused: false,
      pause_reason: '',
    },
    products: [
      {
        id: 100,
        product_id: 1,
        product: {
          id: 1,
          name: 'Smart Watch X1',
          price_formatted: 'Rp 299,000',
          commission_rate: 15.0,
          affiliate_links: { tiktok: 'https://tiktok.com/shop/product1' },
          selling_points: ['Waterproof IP68', 'Battery 7 days'],
        },
      },
    ],
  }),
  createProduct,
  updateProduct: vi.fn().mockResolvedValue({ id: 1, name: 'Smart Watch X1' }),
  deleteProduct: vi.fn().mockResolvedValue({ status: 'deleted' }),
  addLiveSessionProducts: vi.fn().mockResolvedValue({ status: 'updated', count: 2, items: [] }),
  setLiveSessionFocus: vi.fn().mockResolvedValue({ status: 'updated', state: { current_focus_product_id: 1 } }),
}));

describe('ProductsOffersPanel', () => {
  it('renders catalog, session pool, and product form sections', async () => {
    render(ProductsOffersPanel);

    expect(await screen.findByRole('heading', { name: /produk aktif/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /session pool/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /form produk/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /komisi/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /link affiliate/i })).toBeInTheDocument();
  });

  it('submits product creation through the control-plane API', async () => {
    render(ProductsOffersPanel);

    await fireEvent.input(await screen.findByLabelText(/nama produk/i), {
      target: { value: 'Serum Retinol' },
    });
    await fireEvent.input(screen.getByLabelText(/harga/i), {
      target: { value: '129000' },
    });
    await fireEvent.click(screen.getByRole('button', { name: /simpan produk/i }));

    await waitFor(() => expect(createProduct).toHaveBeenCalledTimes(1));
    expect(createProduct.mock.calls[0][0]).toMatchObject({
      name: 'Serum Retinol',
      price: 129000,
    });
  });
});
