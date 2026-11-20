const nodes = [
  { name: "App", center: 155, w: 230 },
  { name: "Stub", center: 490, w: 280 },
  { name: "Rec", center: 780, w: 210 },
  { name: "Root", center: 1010, w: 150 },
  { name: "TLD", center: 1210, w: 150 },
  { name: "Auth", center: 1445, w: 230 }
];
const c = nodes.map(n => n.center);

const items = [
  { step: 1, type: "arrow", from: 0, to: 1, badgeW: 300, badgeH: 66, lines: ['getaddrinfo(', '"www.example.com")'], isMono: true },
  { step: 2, type: "arrow", from: 1, to: 2, badgeW: 250, badgeH: 104, lines: ['query', 'www.example.com', 'A (recursion', 'desired)'], isMono: false },
  { step: "note", type: "note", center: c[2], badgeW: 180, badgeH: 52, lines: ['cache miss'], isMono: false },
  { step: 3, type: "arrow", from: 2, to: 3, badgeW: 192, badgeH: 86, lines: ['www.', 'example.com', 'A ?'], isMono: false },
  { step: 4, type: "arrow", from: 3, to: 2, badgeW: 180, badgeH: 86, lines: ['referral:', 'NS for com', '(+ glue)'], isMono: false },
  { step: 5, type: "arrow", from: 2, to: 4, badgeW: 310, badgeH: 52, lines: ['www.example.com A ?'], isMono: false },
  { step: 6, type: "arrow", from: 4, to: 2, badgeW: 324, badgeH: 66, lines: ['referral: NS for', 'example.com (+ glue)'], isMono: false },
  { step: 7, type: "arrow", from: 2, to: 5, badgeW: 310, badgeH: 52, lines: ['www.example.com A ?'], isMono: false },
  { step: 8, type: "arrow", from: 5, to: 2, badgeW: 468, badgeH: 52, lines: ['A 93.184.216.34, TTL 300 (aa)'], isMono: false, orange: true },
  { step: 9, type: "arrow", from: 2, to: 1, badgeW: 195, badgeH: 86, lines: ['answer', '(cached for', '300 s)'], isMono: false },
  { step: 10, type: "arrow", from: 1, to: 0, badgeW: 140, badgeH: 52, lines: ['address'], isMono: false }
];

let curY = 226;
items.forEach(e => {
  e.badgeY = curY;
  if (e.type === "note") {
    e.badgeX = e.center - e.badgeW / 2;
    curY += e.badgeH + 12;
  } else {
    const x1 = c[e.from];
    const x2 = c[e.to];
    if (x1 < x2) {
      const startX = x1 + 24;
      const endX = x2;
      e.badgeX = (startX + endX) / 2 - e.badgeW / 2;
    } else {
      const startX = x1 - 24;
      const endX = x2;
      e.badgeX = (startX + endX) / 2 - e.badgeW / 2;
    }
    e.arrowY = curY + e.badgeH + 6;
    e.circle = { cx: x1, cy: e.arrowY, r: 24 };
    curY = e.arrowY + 12;
  }
});

// Check bounding boxes
const boxes = [];
items.forEach(e => {
  boxes.push({ id: `badge-${e.step}`, left: e.badgeX, right: e.badgeX + e.badgeW, top: e.badgeY, bottom: e.badgeY + e.badgeH });
  if (e.circle) {
    boxes.push({ id: `circle-${e.step}`, left: e.circle.cx - 24, right: e.circle.cx + 24, top: e.circle.cy - 24, bottom: e.circle.cy + 24 });
  }
});

let overlaps = 0;
for (let i = 0; i < boxes.length; i++) {
  for (let j = i + 1; j < boxes.length; j++) {
    const b1 = boxes[i];
    const b2 = boxes[j];
    // Check if overlap
    const xOverlap = Math.max(0, Math.min(b1.right, b2.right) - Math.max(b1.left, b2.left));
    const yOverlap = Math.max(0, Math.min(b1.bottom, b2.bottom) - Math.max(b1.top, b2.top));
    if (xOverlap > 0 && yOverlap > 0) {
      console.log(`OVERLAP between ${b1.id} and ${b2.id}: dx=${xOverlap}, dy=${yOverlap}`);
      overlaps++;
    }
  }
}
console.log(`Total overlaps found: ${overlaps}`);
