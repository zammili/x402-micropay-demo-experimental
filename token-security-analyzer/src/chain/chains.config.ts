import { ChainConfig } from '../types';

export const CHAIN_REGISTRY: Record<number, ChainConfig> = {
  // Base Mainnet
  8453: {
    chainId: 8453,
    name: 'Base',
    rpcUrl: process.env.BASE_RPC_URL || 'https://base-rpc.publicnode.com',
    rpcFallbacks: [
      process.env.BASE_RPC_FALLBACK || 'https://base.llamarpc.com',
      process.env.BASE_RPC_TERTIARY || 'https://mainnet.base.org',
    ],
    explorerUrl: 'https://basescan.org',
    explorerApiUrl: 'https://api.basescan.org/api',
    wrappedNativeToken: '0x4200000000000000000000000000000000000006', // WETH on Base
    populousDexRouters: [
      '0x2626664c2603336E57B271c5C0b26F421741e481', // Uniswap V3 Router
      '0xC532a74256fa3DB5137B904A61f0F827Ab1A0A63', // Aerodrome Router
    ],
  },

  // Superfluid Demo Chain 8004
  8004: {
    chainId: 8004,
    name: 'Superfluid Demo (8004)',
    rpcUrl: process.env.SUPERFLUID_8004_RPC_URL || 'https://8004-demo.superfluid.org/',
    rpcFallbacks: [],
    explorerUrl: undefined,
    explorerApiUrl: undefined,
    wrappedNativeToken: undefined,
    populousDexRouters: [],
  },

  // Ethereum Mainnet (optional)
  1: {
    chainId: 1,
    name: 'Ethereum',
    rpcUrl: 'https://eth.public.web3api.io',
    explorerUrl: 'https://etherscan.io',
    wrappedNativeToken: '0xc02aaa39b223fe8d0a0e8e4f27ead9083c756cc2', // WETH
  },

  // Polygon (optional)
  137: {
    chainId: 137,
    name: 'Polygon',
    rpcUrl: 'https://polygon-rpc.com',
    explorerUrl: 'https://polygonscan.com',
    wrappedNativeToken: '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', // WMATIC
  },

  // Arbitrum (optional)
  42161: {
    chainId: 42161,
    name: 'Arbitrum',
    rpcUrl: 'https://arb1.arbitrum.io/rpc',
    explorerUrl: 'https://arbiscan.io',
    wrappedNativeToken: '0x82af49447d8a07e3bd95bd0d56f313d33e4720d4', // WETH
  },

  // Optimism (optional)
  10: {
    chainId: 10,
    name: 'Optimism',
    rpcUrl: 'https://mainnet.optimism.io',
    explorerUrl: 'https://optimistic.etherscan.io',
    wrappedNativeToken: '0x4200000000000000000000000000000000000006', // WETH
  },
};

/**
 * Get chain config by chainId
 */
export function getChainConfig(chainId: number): ChainConfig {
  const config = CHAIN_REGISTRY[chainId];
  if (!config) {
    throw new Error(`Unsupported chain: ${chainId}`);
  }
  return config;
}

/**
 * Get all supported chains
 */
export function getSupportedChains(): ChainConfig[] {
  return Object.values(CHAIN_REGISTRY);
}