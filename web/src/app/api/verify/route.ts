import { NextResponse } from 'next/server';

const usedProofs = new Map<string, { timestamp: number; status: boolean }>();
const PROOF_TTL = parseInt(process.env.PROOF_TTL || '3600', 10);
const CASPER_RPC_URL = process.env.CASPER_RPC_URL || 'https://rpc.testnet.casperlabs.io';

function deploySucceeded(executionResults: unknown): boolean {
  if (!Array.isArray(executionResults)) return false;
  return executionResults.some((item) => {
    if (typeof item !== 'object' || item === null) return false;
    const result = (item as { result?: Record<string, unknown> }).result;
    if (!result) return false;
    return 'Success' in result || result.status === 'success';
  });
}

export async function POST(request: Request) {
  try {
    const { deployHash } = await request.json();

    if (!deployHash || typeof deployHash !== 'string') {
      return NextResponse.json({ error: 'Missing deployHash' }, { status: 400 });
    }

    const normalizedHash = deployHash.replace(/^0x/, '');
    const existingProof = usedProofs.get(normalizedHash);
    const now = Math.floor(Date.now() / 1000);

    if (existingProof && now - existingProof.timestamp < PROOF_TTL) {
      return NextResponse.json(
        {
          error: 'Replay attack detected: this Casper deploy hash has already been used.',
          verified: existingProof.status,
          usedAt: existingProof.timestamp,
        },
        { status: 409 },
      );
    }

    const rpcResponse = await fetch(CASPER_RPC_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'info_get_deploy',
        params: { deploy_hash: normalizedHash },
        id: 1,
      }),
    });

    if (!rpcResponse.ok) {
      return NextResponse.json({ error: 'Casper RPC request failed' }, { status: 502 });
    }

    const rpcJson = await rpcResponse.json();
    const executionResults = rpcJson?.result?.execution_results;
    const isVerified = deploySucceeded(executionResults);

    usedProofs.set(normalizedHash, { timestamp: now, status: isVerified });

    return NextResponse.json({
      verified: isVerified,
      source: 'casper-info_get_deploy',
      chain: 'casper',
      deployHash: normalizedHash,
    });
  } catch (error) {
    console.error('Casper verification error:', error);
    return NextResponse.json({ error: 'Verification failed or deploy not found' }, { status: 500 });
  }
}
