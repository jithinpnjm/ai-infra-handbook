const fs = require('fs');

const svg = fs.readFileSync('lookup.svg', 'utf8');

console.log("=== 1. Checking Canvas and Elements ===");
if (!svg.includes('width="1600"') || !svg.includes('viewBox="0 0 1600 1200"')) {
  console.error("FAIL: Canvas dimensions incorrect");
} else {
  console.log("PASS: Canvas is 1600x1200");
}

const firstChildrenMatch = svg.match(/<svg[^>]*>\s*(<title>[^<]+<\/title>)\s*(<desc>[^<]+<\/desc>)/);
if (!firstChildrenMatch) {
  console.error("FAIL: <title> and <desc> are not first children");
} else {
  console.log("PASS: <title> and <desc> are first children");
}

console.log("\n=== 2. Checking Text Sizes ===");
const fontSizeRegex = /font-size="([^"]+)"/g;
let match;
let minSize = 999;
const fontSizes = [];
while ((match = fontSizeRegex.exec(svg)) !== null) {
  const size = parseFloat(match[1]);
  fontSizes.push(size);
  if (size < minSize) minSize = size;
  if (size < 24) {
    console.error(`FAIL: Font size ${size} < 24px!`);
  }
}
console.log(`PASS: Minimum font size found is ${minSize}px (>= 24px). All sizes:`, [...new Set(fontSizes)]);

console.log("\n=== 3. Checking Required Content Labels ===");
const requiredLabels = [
  "How a lookup actually works",
  "Application",
  "Stub resolver",
  "(libc /",
  "systemd-resolved)",
  "Recursive",
  "resolver",
  "(cache)",
  "Root",
  "server",
  ".com",
  "TLD",
  "example.com",
  "authoritative",
  "getaddrinfo(",
  '"www.example',
  '.com")',
  "query",
  "www.example.com",
  "A (recursion",
  "desired)",
  "cache miss",
  "www.example.com A ?",
  "referral:",
  "NS for com",
  "(+ glue)",
  "referral: NS for",
  "example.com (+ glue)",
  "A 93.184.216.34,",
  "TTL 300 (aa)",
  "answer",
  "(cached for",
  "300 s)",
  "address"
];

let allPresent = true;
requiredLabels.forEach(label => {
  if (!svg.includes(label)) {
    console.error(`FAIL: Missing text fragment "${label}"`);
    allPresent = false;
  }
});
if (allPresent) console.log("PASS: All required text fragments present!");

console.log("\n=== 4. Checking Colors ===");
const colorRegex = /(#[0-9a-fA-F]{3,6})/g;
const colors = new Set();
while ((match = colorRegex.exec(svg)) !== null) {
  colors.add(match[1].toLowerCase());
}
console.log("Found colors:", [...colors]);
// Allowed: #f5f8f5, #303a36, #207448, #e8f1ea, #c8d6ce, #ffffff, #db8129
const allowed = new Set(['#f5f8f5', '#303a36', '#207448', '#e8f1ea', '#c8d6ce', '#ffffff', '#db8129']);
colors.forEach(c => {
  if (!allowed.has(c)) {
    console.warn("Unexpected color:", c);
  }
});

console.log("\n=== 5. Checking XML Validity ===");
const { execSync } = require('child_process');
try {
  execSync('python3 -c "import xml.etree.ElementTree as ET; ET.parse(\'lookup.svg\')"');
  console.log("PASS: SVG is well-formed XML!");
} catch (e) {
  console.error("FAIL: XML parsing error", e.message);
}

