import { NextResponse } from 'next/server';
import { createPublicClient, http } from 'viem';
import { baseSepolia } from 'viem/chains';

// In-memory cache for proof verification
const proofCache = new Map<string, { timestamp: number; status: boolean }>();
const PROOF_TTL = parseInt(process.env.PROOF_TTL || '3600', 10); // Default 1 hour

const publicClient = createPublicClient({
  chain: baseSepolia,
  transport: http(),
});

export async function POST(request: Request) {
  try {
    const { transactionHash } = await request.json();

    if (!transactionHash) {
      return NextResponse.json({ error: 'Missing transactionHash' }, { status: 400 });
    }

    // Check cache
    const cached = proofCache.get(transactionHash);
    const now = Math.floor(Date.now() / 1000);
    if (cached && (now - cached.timestamp) < PROOF_TTL) {
      return NextResponse.json({ 
        verified: cached.status, 
        source: 'cache',
        expiresIn: PROOF_TTL - (now - cached.timestamp)
      });
    }

    // Verify on-chain
    const receipt = await publicClient.waitForTransactionReceipt({ 
      hash: transactionHash 
    });

    const isVerified = receipt.status === 'success';

    // Update cache
    proofCache.set(transactionHash, {
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
    return NextResponse.json({ error: 'Verification failed' }, { status: 500 });
  }
}
