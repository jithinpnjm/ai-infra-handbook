const fs = require('fs');

// Boxes to check:
// 1. Participant nodes:
// B1: W=230, H=175. Text: "Application" (30px bold). Icon at top (y=92..144). Text at y=200.
// B2: W=280, H=175. Lines: "Stub resolver" (30px), "(libc /" (24px), "systemd-resolved)" (24px).
// B3: W=200, H=175. Lines: "Recursive" (30px), "resolver" (30px), "(cache)" (24px).
// B4: W=140, H=175. Lines: "Root" (30px), "server" (30px).
// B5: W=140, H=175. Lines: ".com" (30px), "TLD" (30px), "server" (30px).
// B6: W=230, H=175. Lines: "example.com" (30px), "authoritative" (24px).

// 2. Event badges:
// Step 1: W=216, H=68. Mono 24px.
//   "getaddrinfo(" (12 chars * 14.88 = 178.56) -> pad = (216 - 178.56)/2 = 18.72px
//   '"www.example' (12 chars * 14.88 = 178.56) -> pad = 18.72px
//   '.com")' (6 chars * 14.88 = 89.28) -> pad = 63.36px
// Step 2: W=248, H=92. Sans 24px.
//   "query" (5 * 14.4 = 72) -> pad = 88px
//   "www.example.com" (15 * 14.4 = 216) -> pad = 16.0px (>= 16)
//   "A (recursion" (12 * 14.4 = 172.8) -> pad = 37.6px
//   "desired)" (8 * 14.4 = 115.2) -> pad = 66.4px
// Note: W=180, H=40. Sans 24px.
//   "cache miss" (10 * 14.4 = 144) -> pad = (180 - 144)/2 = 18px (>= 16)
// Step 3: W=195, H=68. Sans 24px.
//   "www." (4 * 14.4 = 57.6)
//   "example.com" (11 * 14.4 = 158.4) -> pad = (195 - 158.4)/2 = 18.3px
//   "A ?" (3 * 14.4 = 43.2)
// Step 4: W=180, H=68. Sans 24px.
//   "referral:" (9 * 14.4 = 129.6) -> pad = 25.2px
//   "NS for com" (10 * 14.4 = 144) -> pad = 18.0px
//   "(+ glue)" (8 * 14.4 = 115.2) -> pad = 32.4px
// Step 5: W=310, H=40. Sans 24px.
//   "www.example.com A ?" (19 * 14.4 = 273.6) -> pad = (310 - 273.6)/2 = 18.2px
// Step 6: W=325, H=54. Sans 24px.
//   "referral: NS for" (16 * 14.4 = 230.4) -> pad = 47.3px
//   "example.com (+ glue)" (20 * 14.4 = 288) -> pad = (325 - 288)/2 = 18.5px
// Step 7: W=310, H=40. Sans 24px.
//   "www.example.com A ?" (19 * 14.4 = 273.6) -> pad = 18.2px
// Step 8: W=270, H=54. Sans 24px.
//   "A 93.184.216.34," (16 * 14.4 = 230.4) -> pad = (270 - 230.4)/2 = 19.8px
//   "TTL 300 (aa)" (12 * 14.4 = 172.8) -> pad = 48.6px
// Step 9: W=195, H=68. Sans 24px.
//   "answer" (6 * 14.4 = 86.4)
//   "(cached for" (11 * 14.4 = 158.4) -> pad = (195 - 158.4)/2 = 18.3px
//   "300 s)" (6 * 14.4 = 86.4)
// Step 10: W=150, H=40. Sans 24px.
//   "address" (7 * 14.4 = 100.8) -> pad = (150 - 100.8)/2 = 24.6px

console.log("Checking all horizontal paddings against rule 0.6*size (sans) and 0.62*size (mono):");
const items = [
  { name: 'B1', w: 230, text: 'Application', size: 30, mono: false },
  { name: 'B2 line 1', w: 280, text: 'Stub resolver', size: 30, mono: false },
  { name: 'B2 line 2', w: 280, text: '(libc /', size: 24, mono: false },
  { name: 'B2 line 3', w: 280, text: 'systemd-resolved)', size: 24, mono: false },
  { name: 'B3 line 1', w: 200, text: 'Recursive', size: 30, mono: false },
  { name: 'B3 line 2', w: 200, text: 'resolver', size: 30, mono: false },
  { name: 'B3 line 3', w: 200, text: '(cache)', size: 24, mono: false },
  { name: 'B4 line 1', w: 140, text: 'Root', size: 30, mono: false },
  { name: 'B4 line 2', w: 140, text: 'server', size: 30, mono: false },
  { name: 'B5 line 1', w: 140, text: '.com', size: 30, mono: false },
  { name: 'B5 line 2', w: 140, text: 'TLD', size: 30, mono: false },
  { name: 'B5 line 3', w: 140, text: 'server', size: 30, mono: false },
  { name: 'B6 line 1', w: 230, text: 'example.com', size: 30, mono: false },
  { name: 'B6 line 2', w: 230, text: 'authoritative', size: 24, mono: false },
  { name: 'Step 1 line 1', w: 216, text: 'getaddrinfo(', size: 24, mono: true },
  { name: 'Step 1 line 2', w: 216, text: '"www.example', size: 24, mono: true },
  { name: 'Step 1 line 3', w: 216, text: '.com")', size: 24, mono: true },
  { name: 'Step 2 line 1', w: 248, text: 'query', size: 24, mono: false },
  { name: 'Step 2 line 2', w: 248, text: 'www.example.com', size: 24, mono: false },
  { name: 'Step 2 line 3', w: 248, text: 'A (recursion', size: 24, mono: false },
  { name: 'Step 2 line 4', w: 248, text: 'desired)', size: 24, mono: false },
  { name: 'Note', w: 180, text: 'cache miss', size: 24, mono: false },
  { name: 'Step 3 line 1', w: 195, text: 'www.', size: 24, mono: false },
  { name: 'Step 3 line 2', w: 195, text: 'example.com', size: 24, mono: false },
  { name: 'Step 3 line 3', w: 195, text: 'A ?', size: 24, mono: false },
  { name: 'Step 4 line 1', w: 180, text: 'referral:', size: 24, mono: false },
  { name: 'Step 4 line 2', w: 180, text: 'NS for com', size: 24, mono: false },
  { name: 'Step 4 line 3', w: 180, text: '(+ glue)', size: 24, mono: false },
  { name: 'Step 5 line 1', w: 310, text: 'www.example.com A ?', size: 24, mono: false },
  { name: 'Step 6 line 1', w: 325, text: 'referral: NS for', size: 24, mono: false },
  { name: 'Step 6 line 2', w: 325, text: 'example.com (+ glue)', size: 24, mono: false },
  { name: 'Step 7 line 1', w: 310, text: 'www.example.com A ?', size: 24, mono: false },
  { name: 'Step 8 line 1', w: 270, text: 'A 93.184.216.34,', size: 24, mono: false },
  { name: 'Step 8 line 2', w: 270, text: 'TTL 300 (aa)', size: 24, mono: false },
  { name: 'Step 9 line 1', w: 195, text: 'answer', size: 24, mono: false },
  { name: 'Step 9 line 2', w: 195, text: '(cached for', size: 24, mono: false },
  { name: 'Step 9 line 3', w: 195, text: '300 s)', size: 24, mono: false },
  { name: 'Step 10 line 1', w: 150, text: 'address', size: 24, mono: false }
];

let allOk = true;
items.forEach(it => {
  const coeff = it.mono ? 0.62 : 0.6;
  const estW = it.text.length * coeff * it.size;
  const pad = (it.w - estW) / 2;
  if (pad < 16) {
    console.error(`FAIL: ${it.name} "${it.text}" pad = ${pad.toFixed(1)}px < 16px!`);
    allOk = false;
  }
});
if (allOk) {
  console.log("PASS: EVERY SINGLE TEXT LINE HAS >= 16.0px PADDING!");
}
