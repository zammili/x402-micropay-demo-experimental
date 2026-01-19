# x402 Micropay Demo (AI Agent Economy)

This project demonstrates a machine-to-machine micropayment loop using HTTP `402 Payment Required` and L2 (Base Sepolia) payments.

Overview
- `translation_agent.py` — Flask server that provides translation services and requires payment (mock by default).
- `research_agent.py` — Client that requests translations and automatically pays when agent returns `402` (mock by default).

Proof format
- The research agent must send a full transaction receipt object in the retry request JSON under the `payment_receipt` key. Example:
  {
    "text": "Hello",
    "payment_receipt": {
      "transactionHash": "0x...",
      "blockNumber": 123,
      "status": 1
    }
  }

Quick start (local, mock)
1. Install dependencies:
   pip install -r requirements.txt

2. Start the translation agent:
   python translation_agent.py

3. In another terminal, run the research agent:
   python research_agent.py "Text to translate"

Run tests
- Run the unit tests with:
  pytest -q

Docker Compose
- Copy `.env.example` (or `.env.local.example` for local real-mode example) to `.env`, edit if needed, then:
  docker-compose up --build

Security
- The `.env.local.example` includes a dummy test private key. DO NOT use it in production; replace with a secure key or use a vault.
- Keep `DRY_RUN=true` while experimenting to avoid accidental on-chain payments.

Contributing
- See CONTRIBUTING.md for guidelines.

LICENSE:
MIT License

Copyright (c) 2026 zammili

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
