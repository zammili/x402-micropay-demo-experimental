// ERC-20 standard function signatures
export const ERC20_SIGNATURES = {
  transfer: '0xa9059cbb', // transfer(address,uint256)
  transferFrom: '0x23b872dd', // transferFrom(address,address,uint256)
  approve: '0x095ea7b3', // approve(address,uint256)
  allowance: '0xdd62ed3e', // allowance(address,address)
  balanceOf: '0x70a08231', // balanceOf(address)
  totalSupply: '0x18160ddd', // totalSupply()
  decimals: '0x313ce567', // decimals()
  symbol: '0x95d89b41', // symbol()
  name: '0x06fdde03', // name()
};

// Potentially dangerous function signatures
export const DANGEROUS_SIGNATURES = {
  mint: '0x40c10f39', // mint(address,uint256)
  burn: '0x42966c68', // burn(uint256)
  setTax: '0xf0cdf1d6', // setTaxFee(uint256)
  setSellFee: '0x1a8e55dd', // setSellFee(uint256)
  setBuyFee: '0xf305d719', // setBuyFee(uint256)
  blacklist: '0x29f2e0d8', // blacklistAddress(address)
  pause: '0x8456cb59', // pause()
  unpause: '0x3f4ba83a', // unpause()
  setRouter: '0xce5494bb', // setRouter(address)
  setPair: '0xf3995ba7', // setPair(address)
  removeBlacklist: '0x66cd2720', // removeBlacklist(address)
};

// EIP-1967 proxy storage slots
export const PROXY_SLOTS = {
  LOGIC: '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc', // EIP1967Proxy.sol
  ADMIN: '0xb53127684a568b3173ae13b9f8a6b6664aa312928872c0fa7375bae69efb4947', // EIP1967Proxy.sol
  BEACON: '0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50', // BeaconProxy.sol
};

// Risk score thresholds
export const RISK_THRESHOLDS = {
  CRITICAL: 75,
  HIGH: 50,
  MEDIUM: 25,
  LOW: 0,
};

// Risk categories
export const RISK_CATEGORIES = {
  OWNER_POWERS: 'ownerPowers',
  TRANSFER_RESTRICTION: 'transferRestriction',
  HONEYPOT: 'honeypot',
  LIQUIDITY_CONTROL: 'liquidityControl',
  PROXY_RISK: 'proxyRisk',
  COMPLIANCE: 'compliance',
};

// Common DEX routers
export const COMMON_DEX_ROUTERS = {
  UNISWAP_V2: '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
  UNISWAP_V3: '0xE592427A0AEce92De3Edee1F18E0157C05861564',
  SUSHISWAP: '0xd9e1cE17f2641f24aE9f302d1327850f8D8b0F1d',
};
