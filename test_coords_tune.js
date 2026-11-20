// Let's test shifting all badges/arrows up slightly
// so that the bottom circle ends at <= 1180 (at least 20-30px margin from 1200)

const c = [155, 460, 765, 1025, 1220, 1445];

const events = [
  { step: 1, type: 'arrow', from: 0, to: 1, isMono: true, lines: ['getaddrinfo(', '"www.example', '.com")'], badgeW: 220, badgeH: 74, badgeY: 255, badgeX: 202, arrowY: 341, lineDy: 24, textStartY: 279 },
  { step: 2, type: 'arrow', from: 1, to: 2, isMono: false, lines: ['query', 'www.example.com', 'A (recursion', 'desired)'], badgeW: 250, badgeH: 98, badgeY: 360, badgeX: 492, arrowY: 468, lineDy: 24, textStartY: 382 },
  { step: 'note', type: 'note', lane: 2, lines: ['cache miss'], badgeW: 180, badgeH: 42, badgeY: 486, badgeX: c[2] - 90, textY: 513 },
  { step: 3, type: 'arrow', from: 2, to: 3, isMono: false, lines: ['www.', 'example.com', 'A ?'], badgeW: 195, badgeH: 74, badgeY: 544, badgeX: 796, arrowY: 628, lineDy: 24, textStartY: 568 },
  { step: 4, type: 'arrow', from: 3, to: 2, dashed: true, isMono: false, lines: ['referral:', 'NS for com', '(+ glue)'], badgeW: 180, badgeH: 74, badgeY: 646, badgeX: 804, arrowY: 730, lineDy: 24, textStartY: 670 },
  { step: 5, type: 'arrow', from: 2, to: 4, isMono: false, lines: ['www.example.com A ?'], badgeW: 310, badgeH: 44, badgeY: 760, badgeX: 850, arrowY: 814, textStartY: 789 },
  { step: 6, type: 'arrow', from: 4, to: 2, dashed: true, isMono: false, lines: ['referral: NS for', 'example.com (+ glue)'], badgeW: 325, badgeH: 58, badgeY: 832, badgeX: 840, arrowY: 900, lineDy: 26, textStartY: 857 },
  { step: 7, type: 'arrow', from: 2, to: 5, isMono: false, lines: ['www.example.com A ?'], badgeW: 310, badgeH: 44, badgeY: 928, badgeX: 960, arrowY: 982, textStartY: 957 },
  { step: 8, type: 'arrow', from: 5, to: 2, dashed: true, orange: true, isMono: false, lines: ['A 93.184.216.34,', 'TTL 300 (aa)'], badgeW: 270, badgeH: 58, badgeY: 1000, badgeX: 980, arrowY: 1068, lineDy: 26, textStartY: 1025 },
  { step: 9, type: 'arrow', from: 2, to: 1, dashed: true, isMono: false, lines: ['answer', '(cached for', '300 s)'], badgeW: 195, badgeH: 74, badgeY: 1020, badgeX: 522, arrowY: 1104, lineDy: 24, textStartY: 1044 },
  { step: 10, type: 'arrow', from: 1, to: 0, dashed: true, isMono: false, lines: ['address'], badgeW: 150, badgeH: 44, badgeY: 1098, badgeX: 235, arrowY: 1152, textStartY: 1127 }
];

const rects = [];
const circles = [];
const lines = [];

events.forEach(e => {
  rects.push({ id: `badge-${e.step}`, x1: e.badgeX, y1: e.badgeY, x2: e.badgeX + e.badgeW, y2: e.badgeY + e.badgeH });
  if (e.type === 'arrow') {
    const x1 = c[e.from];
    const x2 = c[e.to];
    const cy = e.arrowY;
    circles.push({ id: `circle-${e.step}`, cx: x1, cy: cy, r: 24, x1: x1 - 24, y1: cy - 24, x2: x1 + 24, y2: cy + 24 });
    const arrowX1 = x1 < x2 ? x1 + 24 : x1 - 24;
    const arrowX2 = x2;
    lines.push({ id: `arrow-${e.step}`, x1: Math.min(arrowX1, arrowX2), x2: Math.max(arrowX1, arrowX2), y: cy });
  }
});

let collisionFound = false;
for (const cir of circles) {
  for (const r of rects) {
    const ox = Math.max(0, Math.min(cir.x2, r.x2) - Math.max(cir.x1, r.x1));
    const oy = Math.max(0, Math.min(cir.y2, r.y2) - Math.max(cir.y1, r.y1));
    if (ox > 0 && oy > 0) {
      console.log(`COLLISION between ${cir.id} and ${r.id}: dx=${ox}, dy=${oy}`);
      collisionFound = true;
    }
  }
}
for (const line of lines) {
  for (const r of rects) {
    if (line.y >= r.y1 && line.y <= r.y2) {
      const ox = Math.max(0, Math.min(line.x2, r.x2) - Math.max(line.x1, r.x1));
      if (ox > 0) {
        console.log(`COLLISION: ${line.id} crosses ${r.id}: dx=${ox}`);
        collisionFound = true;
      }
    }
  }
}
for (let i = 0; i < rects.length; i++) {
  for (let j = i + 1; j < rects.length; j++) {
    const r1 = rects[i];
    const r2 = rects[j];
    const ox = Math.max(0, Math.min(r1.x2, r2.x2) - Math.max(r1.x1, r2.x1));
    const oy = Math.max(0, Math.min(r1.y2, r2.y2) - Math.max(r1.y1, r2.y1));
    if (ox > 0 && oy > 0) {
      console.log(`COLLISION between ${r1.id} and ${r2.id}: dx=${ox}, dy=${oy}`);
      collisionFound = true;
    }
  }
}

if (!collisionFound) {
  console.log("PASS: Tuned coords have ZERO collisions!");
  console.log("Bottom of last circle:", 1152 + 24, "Margin to 1200:", 1200 - (1152 + 24));
}
