// Chain configuration
export interface ChainConfig {
  chainId: number;
  name: string;
  rpcUrl: string;
  rpcFallbacks?: string[];
  explorerUrl?: string;
  explorerApiUrl?: string;
  wrappedNativeToken?: string;
  populousDexRouters?: string[];
}

// Token analysis request
export interface TokenAnalysisRequest {
  chainId: number;
  tokenAddress: string;
  simulateSwap?: boolean;
}

// Risk finding
export interface RiskFinding {
  id: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  category: string;
  title: string;
  evidence: string;
  location?: string;
  recommendation?: string;
}

// Analysis result
export interface TokenAnalysisResult {
  token: string;
  chain: string;
  chainId: number;
  timestamp: string;
  riskScore: number; // 0-100
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  breakdown: RiskBreakdown;
  findings: RiskFinding[];
  metadata: TokenMetadata;
  warnings: string[];
  notes: string[];
}

// Risk score breakdown
export interface RiskBreakdown {
  ownerPowers?: number;
  transferRestriction?: number;
  honeypot?: number;
  liquidityControl?: number;
  proxyRisk?: number;
  other?: number;
}

// Token metadata
export interface TokenMetadata {
  name?: string;
  symbol?: string;
  decimals?: number;
  totalSupply?: string;
  owner?: string;
  verified?: boolean;
  sourceAvailable?: boolean;
}

// Static analysis result
export interface StaticAnalysisResult {
  hasMint: boolean;
  hasBlacklist: boolean;
  hasPause: boolean;
  hasAdjustableFees: boolean;
  isProxy: boolean;
  proxyType?: string;
  proxyAdmin?: string;
  hasRescueFunction: boolean;
  hasUpgradeFunction: boolean;
  suspiciousPatterns: string[];
}

// Analyzer options
export interface AnalyzerOptions {
  includeSimulation: boolean;
  includeBytecodeAnalysis: boolean;
  timeout?: number;
}