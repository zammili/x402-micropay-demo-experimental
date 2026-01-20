'use client';

import { 
  ConnectWallet, 
  Wallet, 
  WalletDropdown, 
  WalletDropdownDisconnect, 
  WalletDropdownLink 
} from '@coinbase/onchainkit/wallet';
import {
  Address,
  Avatar,
  Name,
  Identity,
  EthBalance,
} from '@coinbase/onchainkit/identity';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-slate-950 text-white">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm flex mb-12">
        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit lg:static lg:w-auto  lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4 lg:dark:bg-zinc-800/30">
          x402 Micropay Demo&nbsp;
          <code className="font-bold">feature/nextjs-miniapp</code>
        </p>
        <div className="flex items-center justify-center">
          <Wallet>
            <ConnectWallet>
              <Avatar className="h-6 w-6" />
              <Name />
            </ConnectWallet>
            <WalletDropdown>
              <Identity className="px-4 pt-3 pb-2" hasCopyAddressOnClick>
                <Avatar />
                <Name />
                <Address />
                <EthBalance />
              </Identity>
              <WalletDropdownLink
                icon="wallet"
                href="https://keys.coinbase.com"
                target="_blank"
                rel="noopener noreferrer"
              >
                Wallet
              </WalletDropdownLink>
              <WalletDropdownDisconnect />
            </WalletDropdown>
          </Wallet>
        </div>
      </div>

      <div className="flex flex-col items-center text-center">
        <h1 className="text-4xl font-bold mb-4">OnchainKit Integration</h1>
        <p className="text-xl text-slate-400 max-w-2xl">
          Selamat datang di demo integrasi OnchainKit untuk Next.js. 
          Gunakan tombol di pojok kanan atas untuk menghubungkan Smart Wallet Anda.
        </p>
      </div>

      <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl">
        <div className="p-6 border border-slate-800 rounded-xl bg-slate-900/50">
          <h3 className="text-lg font-semibold mb-2">A. Client Integration</h3>
          <p className="text-sm text-slate-400">OnchainKit Wallet & Identity components ready.</p>
        </div>
        <div className="p-6 border border-slate-800 rounded-xl bg-slate-900/50">
          <h3 className="text-lg font-semibold mb-2">B. Server Verification</h3>
          <p className="text-sm text-slate-400">On-chain proof verification with PROOF_TTL caching.</p>
        </div>
        <div className="p-6 border border-slate-800 rounded-xl bg-slate-900/50">
          <h3 className="text-lg font-semibold mb-2">C. CI/CD & Docs</h3>
          <p className="text-sm text-slate-400">Automated workflows and comprehensive documentation.</p>
        </div>
      </div>
    </main>
  );
}
