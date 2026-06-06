import http from 'node:http';

async function runTest() {
  const deployHash = '0x' + 'a'.repeat(64);
  const data = JSON.stringify({ deployHash });

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

  console.log('--- Memulai Pengujian API Verifikasi Casper ---');

  console.log('\nSkenario 1: Verifikasi deploy pertama');
  try {
    const res1 = await makeRequest(options, data);
    console.log(`Status: ${res1.status}`);
    console.log(`Body: ${res1.body}`);
  } catch (e) {
    console.log(`Error Skenario 1: ${e.message}`);
  }

  console.log('\nSkenario 2: Deteksi replay deploy hash');
  try {
    const res2 = await makeRequest(options, data);
    console.log(`Status: ${res2.status}`);
    if (res2.status === 409) {
      console.log('✅ LULUS: Replay attack terdeteksi dengan status 409.');
    } else {
      console.log('❌ GAGAL: Replay attack tidak terdeteksi dengan status 409.');
    }
  } catch (e) {
    console.log(`Error Skenario 2: ${e.message}`);
  }
}

function makeRequest(options, data) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => {
        body += chunk;
      });
      res.on('end', () => resolve({ status: res.statusCode, body }));
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

console.log('Catatan: Skrip ini membutuhkan server Next.js berjalan di localhost:3000.');
runTest();
