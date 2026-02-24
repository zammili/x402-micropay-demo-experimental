import { ethers } from 'ethers';
import { logger } from '../utils/logger';
import { getChainConfig } from './chains.config';

export class RpcClient {
  private providers: Map<number, ethers.Provider> = new Map();

  /**
   * Get provider for a chain with fallback support
   */
  async getProvider(chainId: number): Promise<ethers.Provider> {
    if (this.providers.has(chainId)) {
      return this.providers.get(chainId)!;
    }

    const config = getChainConfig(chainId);
    let provider: ethers.Provider | null = null;

    // Try primary RPC
    try {
      provider = new ethers.JsonRpcProvider(config.rpcUrl, chainId);
      await provider.getNetwork();
      logger.info(`✓ Connected to ${config.name} (${config.rpcUrl})`);
      this.providers.set(chainId, provider);
      return provider;
    } catch (error) {
      logger.warn(`Primary RPC failed for ${config.name}: ${error}`);
    }

    // Try fallbacks
    if (config.rpcFallbacks && config.rpcFallbacks.length > 0) {
      for (const fallbackUrl of config.rpcFallbacks) {
        try {
          provider = new ethers.JsonRpcProvider(fallbackUrl, chainId);
          await provider.getNetwork();
          logger.info(`✓ Connected to ${config.name} via fallback (${fallbackUrl})`);
          this.providers.set(chainId, provider);
          return provider;
        } catch (error) {
          logger.warn(`Fallback RPC failed for ${config.name}: ${fallbackUrl}`);
        }
      }
    }

    throw new Error(
      `Could not connect to chain ${chainId}. All RPC endpoints failed.`
    );
  }

  /**
   * Get contract code at address
   */
  async getCode(chainId: number, address: string): Promise<string> {
    const provider = await this.getProvider(chainId);
    return provider.getCode(address);
  }

  /**
   * Get account info
   */
  async getAccount(chainId: number, address: string) {
    const provider = await this.getProvider(chainId);
    const balance = await provider.getBalance(address);
    const code = await provider.getCode(address);
    return { balance, code, isContract: code !== '0x' };
  }

  /**
   * Call contract function
   */
  async call(
    chainId: number,
    to: string,
    data: string
  ): Promise<string> {
    const provider = await this.getProvider(chainId);
    return provider.call({ to, data });
  }

  /**
   * Get block number
   */
  async getBlockNumber(chainId: number): Promise<number> {
    const provider = await this.getProvider(chainId);
    return provider.getBlockNumber();
  }
}

export const rpcClient = new RpcClient();