const http = require('http');

async function runTest() {
  const txHash = "0x" + "a".repeat(64);
  const data = JSON.stringify({ txHash });

  const options = {
    hostname: 'localhost',
    port: 3000,
    path: '/api/verify',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': data.length,
    },
  };

  console.log("--- Memulai Pengujian API Verifikasi ---");

  // Skenario 1: Verifikasi Pertama (Harus 200 atau 500 jika hash tidak valid di on-chain, tapi kontrak harus benar)
  // Karena kita menggunakan mock hash, kemungkinan besar akan 500 di on-chain, tapi kita cek kontraknya.
  console.log("\nSkenario 1: Verifikasi Pertama");
  try {
    const res1 = await makeRequest(options, data);
    console.log(`Status: ${res1.status}`);
    console.log(`Body: ${res1.body}`);
  } catch (e) {
    console.log(`Error Skenario 1: ${e.message}`);
  }

  // Skenario 2: Replay Attack (Harus 409 Conflict)
  // Kita perlu memastikan hash yang sama dikirim lagi.
  console.log("\nSkenario 2: Deteksi Replay Attack");
  try {
    // Kita asumsikan Skenario 1 berhasil menyimpan hash di cache (meskipun on-chain gagal, cache tetap menyimpan status)
    const res2 = await makeRequest(options, data);
    console.log(`Status: ${res2.status}`);
    if (res2.status === 409) {
      console.log("✅ LULUS: Replay attack terdeteksi dengan status 409.");
    } else {
      console.log("❌ GAGAL: Replay attack tidak terdeteksi dengan status 409.");
    }
  } catch (e) {
    console.log(`Error Skenario 2: ${e.message}`);
  }
}

function makeRequest(options, data) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => resolve({ status: res.statusCode, body }));
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

// Catatan: Skrip ini membutuhkan server Next.js berjalan di localhost:3000
// Karena di sandbox kita tidak menjalankan server secara terus menerus, 
// saya akan melakukan verifikasi logika secara manual atau simulasi jika perlu.
console.log("Catatan: Skrip ini dikonfigurasi untuk menguji server lokal.");
runTest();
