import { NextResponse } from 'next/server';
import { createPublicClient, http } from 'viem';
import { baseSepolia } from 'viem/chains';

// In-memory cache for proof verification to prevent replay attacks
const usedProofs = new Map<string, { timestamp: number; status: boolean }>();
const PROOF_TTL = parseInt(process.env.PROOF_TTL || '3600', 10); // Default 1 hour

const publicClient = createPublicClient({
  chain: baseSepolia,
  transport: http(),
});

export async function POST(request: Request) {
  try {
    const { txHash } = await request.json();

    if (!txHash) {
      return NextResponse.json({ error: 'Missing txHash' }, { status: 400 });
    }

    // Check if this proof has already been used (Replay Attack Prevention)
    const existingProof = usedProofs.get(txHash);
    const now = Math.floor(Date.now() / 1000);
    
    if (existingProof && (now - existingProof.timestamp) < PROOF_TTL) {
      return NextResponse.json({ 
        error: 'Replay attack detected: This transaction hash has already been used.',
        verified: existingProof.status,
        usedAt: existingProof.timestamp
      }, { status: 409 }); // 409 Conflict
    }

    // Verify on-chain
    const receipt = await publicClient.waitForTransactionReceipt({ 
      hash: txHash as `0x${string}`
    });

    const isVerified = receipt.status === 'success';

    // Store in usedProofs cache
    usedProofs.set(txHash, {
      timestamp: now,
      status: isVerified
    });

    return NextResponse.json({ 
      verified: isVerified, 
      source: 'on-chain',
      blockNumber: receipt.blockNumber.toString()
    });

  } catch (error) {
    console.error('Verification error:', error);
    return NextResponse.json({ error: 'Verification failed or transaction not found' }, { status: 500 });
  }
}
