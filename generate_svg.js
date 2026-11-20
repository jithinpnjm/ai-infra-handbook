const fs = require('fs');

const nodes = [
  { name: "App", center: 155, w: 230 },
  { name: "Stub", center: 480, w: 280 },
  { name: "Rec", center: 775, w: 210 },
  { name: "Root", center: 1010, w: 150 },
  { name: "TLD", center: 1210, w: 150 },
  { name: "Auth", center: 1445, w: 230 }
];

const c = nodes.map(n => n.center);

// Event schedule
// Let us precisely schedule y-coordinates for all 11 events
const events = [
  {
    step: 1,
    type: "arrow",
    from: 0,
    to: 1,
    arrowType: "solid",
    badgeW: 240,
    badgeH: 80,
    isMono: true,
    lines: ['getaddrinfo(', '"www.example.com")'],
    // Wait, earlier we checked: "www.example.com") is 18 chars * 0.62 * 24 = 267.84px!
    // So if 2 lines, badgeW must be at least 267.84 + 32 = 300px!
    // Let us test 3 lines:
    lines: ['getaddrinfo(', '"www.example.', 'com")'],
    badgeW: 230,
    badgeH: 90
  },
  {
    step: 2,
    type: "arrow",
    from: 1,
    to: 2,
    arrowType: "solid",
    badgeW: 250,
    badgeH: 108,
    isMono: false,
    lines: ['query', 'www.example.com', 'A (recursion', 'desired)']
  },
  {
    step: "note",
    type: "note",
    center: c[2],
    badgeW: 180,
    badgeH: 56,
    isMono: false,
    lines: ['cache miss']
  },
  {
    step: 3,
    type: "arrow",
    from: 2,
    to: 3,
    arrowType: "solid",
    badgeW: 192,
    badgeH: 84,
    isMono: false,
    lines: ['www.', 'example.com', 'A ?']
  },
  {
    step: 4,
    type: "arrow",
    from: 3,
    to: 2,
    arrowType: "dashed",
    badgeW: 180,
    badgeH: 84,
    isMono: false,
    lines: ['referral:', 'NS for com', '(+ glue)']
  },
  {
    step: 5,
    type: "arrow",
    from: 2,
    to: 4,
    arrowType: "solid",
    badgeW: 310,
    badgeH: 56,
    isMono: false,
    lines: ['www.example.com A ?']
  },
  {
    step: 6,
    type: "arrow",
    from: 4,
    to: 2,
    arrowType: "dashed",
    badgeW: 324,
    badgeH: 68,
    isMono: false,
    lines: ['referral: NS for', 'example.com (+ glue)']
  },
  {
    step: 7,
    type: "arrow",
    from: 2,
    to: 5,
    arrowType: "solid",
    badgeW: 310,
    badgeH: 56,
    isMono: false,
    lines: ['www.example.com A ?']
  },
  {
    step: 8,
    type: "arrow",
    from: 5,
    to: 2,
    arrowType: "dashed",
    orange: true,
    badgeW: 268,
    badgeH: 68,
    isMono: false,
    lines: ['A 93.184.216.34,', 'TTL 300 (aa)']
  },
  {
    step: 9,
    type: "arrow",
    from: 2,
    to: 1,
    arrowType: "dashed",
    badgeW: 195,
    badgeH: 84,
    isMono: false,
    lines: ['answer', '(cached for', '300 s)']
  },
  {
    step: 10,
    type: "arrow",
    from: 1,
    to: 0,
    arrowType: "dashed",
    badgeW: 140,
    badgeH: 56,
    isMono: false,
    lines: ['address']
  }
];

let curY = 260;
events.forEach(e => {
  e.badgeY = curY;
  if (e.type === "note") {
    e.badgeX = e.center - e.badgeW / 2;
    curY += e.badgeH + 16;
  } else {
    // Arrow step
    const x1 = c[e.from];
    const x2 = c[e.to];
    // Center badge between sender circle edge and receiver lifeline
    if (x1 < x2) {
      // Left to right
      const startX = x1 + 24;
      const endX = x2;
      e.badgeX = (startX + endX) / 2 - e.badgeW / 2;
    } else {
      // Right to left
      const startX = x1 - 24;
      const endX = x2;
      e.badgeX = (startX + endX) / 2 - e.badgeW / 2;
    }
    e.arrowY = curY + e.badgeH + 8;
    curY = e.arrowY + 16;
  }
});

console.log("Calculated event positions:");
events.forEach(e => {
  console.log(`Step ${e.step}: badge=[${e.badgeX.toFixed(1)}, ${e.badgeY}, w=${e.badgeW}, h=${e.badgeH}], arrowY=${e.arrowY}`);
});
console.log("Final curY:", curY);
