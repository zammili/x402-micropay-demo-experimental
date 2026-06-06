export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 md:p-24 bg-slate-950 text-white">
      <div className="max-w-5xl w-full text-center">
        <p className="inline-flex rounded-full border border-emerald-500/40 bg-emerald-500/10 px-4 py-2 text-sm text-emerald-200">
          Casper Network Testnet • x402 • Agentic AI
        </p>

        <h1 className="mt-8 text-4xl md:text-6xl font-bold tracking-tight">
          Casper x402 Micropay Demo
        </h1>

        <p className="mt-6 text-lg text-slate-300 max-w-3xl mx-auto">
          Demo ini menampilkan agen AI yang menerima HTTP 402, membuat intent pembayaran CSPR.click,
          mengirim bukti deploy Casper, lalu membuka layanan terjemahan, riset RWA, dan biaya DeFi mikro.
        </p>
      </div>

      <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-5xl">
        <div className="p-6 border border-slate-800 rounded-xl bg-slate-900/70">
          <h3 className="text-lg font-semibold mb-2">1. Casper Payments</h3>
          <p className="text-sm text-slate-400">
            API memverifikasi deploy hash Casper Testnet dengan proteksi replay dan validasi status eksekusi.
          </p>
        </div>
        <div className="p-6 border border-slate-800 rounded-xl bg-slate-900/70">
          <h3 className="text-lg font-semibold mb-2">2. AI Toolkit</h3>
          <p className="text-sm text-slate-400">
            Endpoint MCP-friendly dan CSPR.click intent membantu agen membaca state kontrak dan menandatangani pembayaran.
          </p>
        </div>
        <div className="p-6 border border-slate-800 rounded-xl bg-slate-900/70">
          <h3 className="text-lg font-semibold mb-2">3. DeFi/RWA + PQC</h3>
          <p className="text-sm text-slate-400">
            Agen riset dapat membayar data RWA, biaya protokol DeFi, dan bukti kriptografi tahan kuantum.
          </p>
        </div>
      </div>
    </main>
  );
}
