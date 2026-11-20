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
  // 1: App -> Stub
  { step: 1, type: "arrow", from: 0, to: 1, badgeX: 184, badgeW: 300, badgeY: 226, badgeH: 62, arrowY: 294, lines: ['getaddrinfo(', '"www.example.com")'], isMono: true },
  
  // 2: Stub -> Rec
  { step: 2, type: "arrow", from: 1, to: 2, badgeX: 518, badgeW: 244, badgeY: 312, badgeH: 96, arrowY: 414, lines: ['query', 'www.example.com', 'A (recursion', 'desired)'], isMono: false },
  
  // note: over Rec
  { step: "note", type: "note", center: c[2], badgeX: c[2] - 88, badgeW: 176, badgeY: 432, badgeH: 48, lines: ['cache miss'], isMono: false },
  
  // 3: Rec -> Root
  { step: 3, type: "arrow", from: 2, to: 3, badgeX: 808, badgeW: 192, badgeY: 498, badgeH: 78, arrowY: 582, lines: ['www.', 'example.com', 'A ?'], isMono: false },
  
  // 4: Root -> Rec
  { step: 4, type: "arrow", from: 3, to: 2, badgeX: 804, badgeW: 180, badgeY: 602, badgeH: 78, arrowY: 686, lines: ['referral:', 'NS for com', '(+ glue)'], isMono: false },
  
  // 5: Rec -> TLD
  { step: 5, type: "arrow", from: 2, to: 4, badgeX: 838, badgeW: 310, badgeY: 712, badgeH: 48, arrowY: 766, lines: ['www.example.com A ?'], isMono: false },
  
  // 6: TLD -> Rec
  { step: 6, type: "arrow", from: 4, to: 2, badgeX: 830, badgeW: 324, badgeY: 786, badgeH: 62, arrowY: 854, lines: ['referral: NS for', 'example.com (+ glue)'], isMono: false },
  
  // 7: Rec -> Auth
  { step: 7, type: "arrow", from: 2, to: 5, badgeX: 955, badgeW: 310, badgeY: 882, badgeH: 48, arrowY: 936, lines: ['www.example.com A ?'], isMono: false },
  
  // 8: Auth -> Rec (Orange)
  { step: 8, type: "arrow", from: 5, to: 2, badgeX: 876, badgeW: 468, badgeY: 954, badgeH: 48, arrowY: 1008, lines: ['A 93.184.216.34, TTL 300 (aa)'], isMono: false, orange: true },
  
  // 9: Rec -> Stub
  { step: 9, type: "arrow", from: 2, to: 1, badgeX: 516, badgeW: 195, badgeY: 1026, badgeH: 78, arrowY: 1110, lines: ['answer', '(cached for', '300 s)'], isMono: false },
  
  // 10: Stub -> App
  { step: 10, type: "arrow", from: 1, to: 0, badgeX: 235, badgeW: 140, badgeY: 1122, badgeH: 48, arrowY: 1176, lines: ['address'], isMono: false }
];

items.forEach(e => {
  if (e.type === "arrow") {
    e.circle = { cx: c[e.from], cy: e.arrowY, r: 24 };
  }
});

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
    const xOverlap = Math.max(0, Math.min(b1.right, b2.right) - Math.max(b1.left, b2.left));
    const yOverlap = Math.max(0, Math.min(b1.bottom, b2.bottom) - Math.max(b1.top, b2.top));
    if (xOverlap > 0 && yOverlap > 0) {
      console.log(`OVERLAP between ${b1.id} and ${b2.id}: dx=${xOverlap}, dy=${yOverlap}`);
      overlaps++;
    }
  }
}
console.log(`Total overlaps found: ${overlaps}`);
console.log("Final arrow y:", items[items.length - 1].arrowY);
