import { RiskFinding } from '../types';
import { DANGEROUS_SIGNATURES } from '../utils/constants';
import { logger } from '../utils/logger';

export class OwnerPowersDetector {
  /**
   * Detect mint function
   */
  detectMint(bytecode: string): RiskFinding | null {
    // Look for mint function signature
    const mintSig = '40c10f39'; // mint(address,uint256)
    
    if (bytecode.toLowerCase().includes(mintSig)) {
      return {
        id: 'UNCAPPED_MINT',
        severity: 'CRITICAL',
        category: 'ownerPowers',
        title: 'Uncapped Mint Function Found',
        evidence: `Bytecode contains mint function signature (0x${mintSig})`,
        recommendation: 'Verify if mint has cap or if supply is limited',
      };
    }

    return null;
  }

  /**
   * Detect pause/unpause functionality
   */
  detectPause(bytecode: string): RiskFinding | null {
    const pauseSig = '8456cb59'; // pause()
    const unpauseSig = '3f4ba83a'; // unpause()

    if (
      bytecode.toLowerCase().includes(pauseSig) ||
      bytecode.toLowerCase().includes(unpauseSig)
    ) {
      return {
        id: 'PAUSE_FUNCTIONALITY',
        severity: 'HIGH',
        category: 'ownerPowers',
        title: 'Pause/Unpause Functionality Detected',
        evidence: 'Contract contains pause() or unpause() functions',
        recommendation: 'Verify pause authority and timelock protection',
      };
    }

    return null;
  }

  /**
   * Detect adjustable fees
   */
  detectAdjustableFees(bytecode: string): RiskFinding | null {
    const setTaxSig = 'f0cdf1d6'; // setTaxFee(uint256)
    const setSellFeeSig = '1a8e55dd'; // setSellFee(uint256)
    const setBuyFeeSig = 'f305d719'; // setBuyFee(uint256)

    let found = false;
    let functionName = '';

    if (bytecode.toLowerCase().includes(setTaxSig)) {
      found = true;
      functionName = 'setTaxFee';
    }
    if (bytecode.toLowerCase().includes(setSellFeeSig)) {
      found = true;
      functionName = 'setSellFee';
    }
    if (bytecode.toLowerCase().includes(setBuyFeeSig)) {
      found = true;
      functionName = 'setBuyFee';
    }

    if (found) {
      return {
        id: 'ADJUSTABLE_FEES',
        severity: 'HIGH',
        category: 'ownerPowers',
        title: 'Adjustable Fees Detected',
        evidence: `Found ${functionName}() - Owner can change transaction fees`,
        recommendation: 'Check if there are caps on fees (max 50% is risky)',
      };
    }

    return null;
  }

  /**
   * Detect router or pair change capability
   */
  detectRouterControl(bytecode: string): RiskFinding | null {
    const setRouterSig = 'ce5494bb'; // setRouter(address)
    const setPairSig = 'f3995ba7'; // setPair(address)

    if (
      bytecode.toLowerCase().includes(setRouterSig) ||
      bytecode.toLowerCase().includes(setPairSig)
    ) {
      return {
        id: 'ROUTER_CONTROL',
        severity: 'HIGH',
        category: 'ownerPowers',
        title: 'DEX Router/Pair Control',
        evidence: 'Contract allows owner to change DEX router or trading pair',
        recommendation: 'Verify that router/pair changes are timelock-protected',
      };
    }

    return null;
  }

  /**
   * Detect rescue/recovery functions
   */
  detectRescueFunction(bytecode: string, source?: string): RiskFinding | null {
    const rescuePatterns = [
      'rescueerc20',
      'rescuetokens',
      'withdrawtoken',
      'emergencywithdraw',
    ];

    if (source) {
      const lowerSource = source.toLowerCase();
      for (const pattern of rescuePatterns) {
        if (lowerSource.includes(pattern)) {
          return {
            id: 'RESCUE_FUNCTION',
            severity: 'MEDIUM',
            category: 'ownerPowers',
            title: 'Token Rescue Function Found',
            evidence: `Contract contains ${pattern}() function`,
            recommendation: 'Verify authorization and access control',
          };
        }
      }
    }

    return null;
  }

  /**
   * Analyze all owner powers
   */
  analyze(bytecode: string, source?: string): RiskFinding[] {
    const findings: RiskFinding[] = [];

    const mintFinding = this.detectMint(bytecode);
    if (mintFinding) findings.push(mintFinding);

    const pauseFinding = this.detectPause(bytecode);
    if (pauseFinding) findings.push(pauseFinding);

    const feesFinding = this.detectAdjustableFees(bytecode);
    if (feesFinding) findings.push(feesFinding);

    const routerFinding = this.detectRouterControl(bytecode);
    if (routerFinding) findings.push(routerFinding);

    const rescueFinding = this.detectRescueFunction(bytecode, source);
    if (rescueFinding) findings.push(rescueFinding);

    logger.debug(`OwnerPowersDetector found ${findings.length} risks`);
    return findings;
  }
}