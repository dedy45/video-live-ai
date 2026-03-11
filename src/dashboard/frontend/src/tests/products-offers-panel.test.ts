import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import ProductsOffersPanel from '../components/panels/ProductsOffersPanel.svelte';

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
}));

describe('ProductsOffersPanel', () => {
  it('renders active product, queue, and affiliate context sections', async () => {
    render(ProductsOffersPanel);

    expect(await screen.findByRole('heading', { name: /produk aktif/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /antrian produk/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /komisi/i })).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: /link affiliate/i })).toBeInTheDocument();
  });
});
