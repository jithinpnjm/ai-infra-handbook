const fs = require('fs');

// Canvas: 1600 x 1200
const W = [230, 280, 200, 140, 140, 230];
const c = [155, 460, 765, 1025, 1220, 1445];

// Let's verify card positions:
// Card 0: App: 155 - 115 = 40 to 270 (W=230)
// Card 1: Stub: 460 - 140 = 320 to 600 (W=280) -> gap from Card 0 = 50px (>= 40px)
// Card 2: Rec: 765 - 100 = 665 to 865 (W=200) -> gap from Card 1 = 65px (>= 40px)
// Card 3: Root: 1025 - 70 = 955 to 1095 (W=140) -> gap from Card 2 = 90px (>= 40px)
// Card 4: TLD: 1220 - 70 = 1150 to 1290 (W=140) -> gap from Card 3 = 55px (>= 40px)
// Card 5: Auth: 1445 - 115 = 1330 to 1560 (W=230) -> gap from Card 4 = 40px (>= 40px)
// Margins: Left = 40px, Right = 40px. Perfect!

// Now let's calculate the vertical positions of all events so that:
// 1. Every badge has generous height and line spacing (dy >= 26 for 24px font).
// 2. Every badge has >= 16px padding on all sides.
// 3. No circle overlaps any badge or arrow.
// 4. Everything fits cleanly under H=1200.

const events = [
  {
    step: 1,
    type: 'arrow',
    from: 0, to: 1,
    isMono: true,
    lines: ['getaddrinfo(', '"www.example', '.com")'],
    badgeW: 220, badgeH: 74,
    badgeY: 260,
    badgeX: 202, // centered between 179 and 460 (midpoint 319.5 -> 319.5 - 110 = 209.5)
    arrowY: 346,
    lineDy: 24,
    textStartY: 284
  },
  {
    step: 2,
    type: 'arrow',
    from: 1, to: 2,
    isMono: false,
    lines: ['query', 'www.example.com', 'A (recursion', 'desired)'],
    badgeW: 250, badgeH: 98,
    badgeY: 366,
    badgeX: 492, // centered between 484 and 765 (midpoint 624.5 -> 624.5 - 125 = 499.5)
    arrowY: 476,
    lineDy: 24,
    textStartY: 388
  },
  {
    step: 'note',
    type: 'note',
    lane: 2,
    lines: ['cache miss'],
    badgeW: 180, badgeH: 42,
    badgeY: 494,
    badgeX: c[2] - 90,
    textY: 521
  },
  {
    step: 3,
    type: 'arrow',
    from: 2, to: 3,
    isMono: false,
    lines: ['www.', 'example.com', 'A ?'],
    badgeW: 195, badgeH: 74,
    badgeY: 554,
    badgeX: 796, // between 789 and 1025
    arrowY: 640,
    lineDy: 24,
    textStartY: 578
  },
  {
    step: 4,
    type: 'arrow',
    from: 3, to: 2,
    dashed: true,
    isMono: false,
    lines: ['referral:', 'NS for com', '(+ glue)'],
    badgeW: 180, badgeH: 74,
    badgeY: 658,
    badgeX: 804, // between 765 and 1001
    arrowY: 744,
    lineDy: 24,
    textStartY: 682
  },
  {
    step: 5,
    type: 'arrow',
    from: 2, to: 4,
    isMono: false,
    lines: ['www.example.com A ?'],
    badgeW: 310, badgeH: 44,
    badgeY: 774, // Circle 4 at c[3]=1025, cy=744, bottom=768. 774 > 768! No overlap!
    badgeX: 850,
    arrowY: 830,
    textStartY: 803
  },
  {
    step: 6,
    type: 'arrow',
    from: 4, to: 2,
    dashed: true,
    isMono: false,
    lines: ['referral: NS for', 'example.com (+ glue)'],
    badgeW: 325, badgeH: 58,
    badgeY: 848,
    badgeX: 840,
    arrowY: 918,
    lineDy: 26,
    textStartY: 873
  },
  {
    step: 7,
    type: 'arrow',
    from: 2, to: 5,
    isMono: false,
    lines: ['www.example.com A ?'],
    badgeW: 310, badgeH: 44,
    badgeY: 948, // Circle 6 at c[4]=1220, cy=918, bottom=942. 948 > 942! No overlap!
    badgeX: 960,
    arrowY: 1004,
    textStartY: 977
  },
  {
    step: 8,
    type: 'arrow',
    from: 5, to: 2,
    dashed: true,
    orange: true,
    isMono: false,
    lines: ['A 93.184.216.34,', 'TTL 300 (aa)'],
    badgeW: 270, badgeH: 58,
    badgeY: 1022,
    badgeX: 980,
    arrowY: 1092,
    lineDy: 26,
    textStartY: 1047
  },
  {
    step: 9,
    type: 'arrow',
    from: 2, to: 1,
    dashed: true,
    isMono: false,
    lines: ['answer', '(cached for', '300 s)'],
    badgeW: 195, badgeH: 74,
    badgeY: 1042, // between 460 and 741 (left of Rec). Arrow 8 is right of Rec, so no X collision!
    badgeX: 522,
    arrowY: 1128,
    lineDy: 24,
    textStartY: 1066
  },
  {
    step: 10,
    type: 'arrow',
    from: 1, to: 0,
    dashed: true,
    isMono: false,
    lines: ['address'],
    badgeW: 150, badgeH: 44,
    badgeY: 1122, // between 155 and 436.
    badgeX: 235,
    arrowY: 1176,
    textStartY: 1151
  }
];

// Let's run automated collision detection on this layout!
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

// Circle vs Rect
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

// Arrow vs Rect
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

// Rect vs Rect
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
  console.log("SUCCESS! ZERO COLLISIONS! PERFECT GEOMETRY!");
}
