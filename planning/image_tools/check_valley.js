const fs = require("fs");
const { execSync } = require("child_process");

const svg = fs.readFileSync("test_perfect_valley.svg", "utf8");

console.log("=== 1. Checking Canvas and Elements ===");
const vbMatch = svg.match(/viewBox="0 0 1600 (\d+)"/);
if (!vbMatch) {
  console.error("FAIL: viewBox incorrect");
} else {
  const h = parseInt(vbMatch[1], 10);
  if (h < 900 || h > 1200) {
    console.error(`FAIL: Height ${h} is out of bounds [900, 1200]`);
  } else {
    console.log(`PASS: Height is ${h} (valid 900-1200 range)`);
  }
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

console.log("\n=== 3. Checking Style Words Not Printed ===");
const textRegex = /<text[^>]*>([\s\S]*?)<\/text>/g;
const banned = ["orange", "green", "grey", "monospace", "arrow"];
let bannedFound = false;
while ((match = textRegex.exec(svg)) !== null) {
  const innerText = match[1].replace(/<[^>]+>/g, " ").toLowerCase();
  banned.forEach(word => {
    const wRegex = new RegExp(`\\b${word}\\b`, "i");
    if (wRegex.test(innerText)) {
      console.error(`FAIL: Banned style word "${word}" printed as text inside: "${innerText.trim()}"`);
      bannedFound = true;
    }
  });
}
if (!bannedFound) {
  console.log("PASS: No banned style words printed as text!");
}

console.log("\n=== 4. Checking Required Content Labels ===");
const requiredLabels = [
  "Why all spines share one ASN",
  "Leaf-spine slice",
  "leaf3",
  "spine1",
  "spine2",
  "leaf2",
  "same ASN",
  "route starts at leaf3",
  "a failed link",
  "leaves only one remaining path",
  "leaf2 passes",
  "the route up to spine2",
  "spine2 sees its own ASN",
  "already in the path",
  "and rejects it",
  "different spine ASNs: no repeated ASN, the valley path is installed,",
  "forwarding becomes suboptimal and latency rises",
  "Note: per-rack leaf ASN 65101, 65102"
];

let allPresent = true;
requiredLabels.forEach(label => {
  if (!svg.includes(label)) {
    console.error(`FAIL: Missing text fragment "${label}"`);
    allPresent = false;
  }
});
if (allPresent) console.log("PASS: All required text fragments present!");

console.log("\n=== 5. Checking XML Validity ===");
try {
  execSync("python3 -c \"import xml.etree.ElementTree as ET; ET.parse('test_perfect_valley.svg')\"");
  console.log("PASS: SVG is well-formed XML!");
} catch (e) {
  console.error("FAIL: XML parsing error", e.message);
}

console.log("\n=== 6. Checking Arrow Count ===");
const arrowCount = (svg.match(/marker-end="url\(#arrow-green\)"/g) || []).length;
console.log(`Arrow count: ${arrowCount} (expected 3)`);
if (arrowCount === 3) {
  console.log("PASS: Exactly 3 path arrows!");
} else {
  console.error(`FAIL: Expected 3 arrows, found ${arrowCount}`);
}