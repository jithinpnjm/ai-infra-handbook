const fs = require('fs');

const events = [
  {
    step: 1,
    from: 155, to: 455,
    type: "solid",
    textLines: ['getaddrinfo(', '"www.example.com")'],
    mono: true,
    y: 340,
    badgeW: 280,
    badgeH: 60
  },
  {
    step: 2,
    from: 455, to: 750,
    type: "solid",
    textLines: ['query', 'www.example.com', 'A (recursion', 'desired)'],
    mono: false,
    y: 450,
    badgeW: 240,
    badgeH: 104
  },
  {
    step: "note",
    lane: 750,
    textLines: ['cache miss'],
    mono: false,
    y: 535,
    boxW: 180,
    boxH: 46
  },
  {
    step: 3,
    from: 750, to: 1000,
    type: "solid",
    textLines: ['www.example.com', 'A ?'],
    mono: false,
    y: 615,
    badgeW: 240,
    badgeH: 58
  },
  {
    step: 4,
    from: 1000, to: 750,
    type: "dashed",
    textLines: ['referral:', 'NS for com', '(+ glue)'],
    mono: false,
    y: 710,
    badgeW: 200,
    badgeH: 80
  },
  {
    step: 5,
    from: 750, to: 1200,
    type: "solid",
    textLines: ['www.example.com A ?'],
    mono: false,
    y: 790,
    badgeW: 300,
    badgeH: 46
  },
  {
    step: 6,
    from: 1200, to: 750,
    type: "dashed",
    textLines: ['referral: NS for', 'example.com (+ glue)'],
    mono: false,
    y: 870,
    badgeW: 340,
    badgeH: 60
  },
  {
    step: 7,
    from: 750, to: 1445,
    type: "solid",
    textLines: ['www.example.com A ?'],
    mono: false,
    y: 950,
    badgeW: 300,
    badgeH: 46
  },
  {
    step: 8,
    from: 1445, to: 750,
    type: "dashed",
    orange: true,
    textLines: ['A 93.184.216.34, TTL 300 (aa)'],
    mono: false,
    y: 1020,
    badgeW: 440,
    badgeH: 46
  },
  {
    step: 9,
    from: 750, to: 455,
    type: "dashed",
    textLines: ['answer', '(cached for', '300 s)'],
    mono: false,
    y: 1105,
    badgeW: 200,
    badgeH: 80
  },
  {
    step: 10,
    from: 455, to: 155,
    type: "dashed",
    textLines: ['address'],
    mono: false,
    y: 1165,
    badgeW: 160,
    badgeH: 46
  }
];

// Check vertical gaps between consecutive events
for (let i = 0; i < events.length - 1; i++) {
  const e1 = events[i];
  const e2 = events[i+1];
  const y1_bottom = e1.step === 'note' ? e1.y + e1.boxH/2 : e1.y;
  const y2_top = e2.step === 'note' ? e2.y - e2.boxH/2 : e2.y - e2.badgeH;
  console.log(`Gap between event ${e1.step} and ${e2.step}: ${y2_top - y1_bottom} px`);
}
