const fs = require('fs');

// Build SVG for "How a lookup actually works"
// Canvas: 1600 x 1200
// ViewBox: 0 0 1600 1200
// Background: #f5f8f5
// Text: #303a36
// Main green: #207448
// Light green panels: #e8f1ea
// Orange: #db8129 (only on step 8!)

const c = [155, 460, 765, 1025, 1220, 1445];
const W = [230, 280, 200, 140, 140, 230];

// Header cards Y
const cardY = 80;
const cardH = 175;

// Participant Header details
const participants = [
  {
    id: "App",
    name: "Application",
    w: W[0],
    c: c[0],
    icon: 'window',
    titleLines: [
      { text: "Application", size: 30, bold: true, y: 205 }
    ]
  },
  {
    id: "Stub",
    name: "Stub resolver (libc / systemd-resolved)",
    w: W[1],
    c: c[1],
    icon: 'gear',
    titleLines: [
      { text: "Stub resolver", size: 30, bold: true, y: 172 },
      { text: "(libc /", size: 24, bold: false, y: 204 },
      { text: "systemd-resolved)", size: 24, bold: false, y: 234 }
    ]
  },
  {
    id: "Rec",
    name: "Recursive resolver (cache)",
    w: W[2],
    c: c[2],
    icon: 'cache',
    titleLines: [
      { text: "Recursive", size: 30, bold: true, y: 172 },
      { text: "resolver", size: 30, bold: true, y: 204 },
      { text: "(cache)", size: 24, bold: false, y: 234 }
    ]
  },
  {
    id: "Root",
    name: "Root server",
    w: W[3],
    c: c[3],
    icon: 'globe',
    titleLines: [
      { text: "Root", size: 30, bold: true, y: 188 },
      { text: "server", size: 30, bold: true, y: 224 }
    ]
  },
  {
    id: "TLD",
    name: ".com TLD server",
    w: W[4],
    c: c[4],
    icon: 'server',
    titleLines: [
      { text: ".com", size: 30, bold: true, y: 172 },
      { text: "TLD", size: 30, bold: true, y: 204 },
      { text: "server", size: 30, bold: true, y: 234 }
    ]
  },
  {
    id: "Auth",
    name: "example.com authoritative",
    w: W[5],
    c: c[5],
    icon: 'shield',
    titleLines: [
      { text: "example.com", size: 30, bold: true, y: 188 },
      { text: "authoritative", size: 24, bold: false, y: 224 }
    ]
  }
];

// Events
const events = [
  {
    step: 1,
    from: c[0], to: c[1],
    type: 'solid',
    badgeTop: 270, badgeH: 74, arrowY: 352,
    badgeW: 220,
    badgeX: 205, // between 179 and 442
    lines: [
      { text: 'getaddrinfo(', dy: 0 },
      { text: '"www.example', dy: 24 },
      { text: '.com")', dy: 24 }
    ],
    mono: true,
    startY: 295
  },
  {
    step: 2,
    from: c[1], to: c[2],
    type: 'solid',
    badgeTop: 374, badgeH: 98, arrowY: 480,
    badgeW: 248,
    badgeX: 494, // between 484 and 747
    lines: [
      { text: 'query', dy: 0 },
      { text: 'www.example.com', dy: 24 },
      { text: 'A (recursion', dy: 24 },
      { text: 'desired)', dy: 24 }
    ],
    mono: false,
    startY: 397
  },
  {
    step: 'note',
    lane: c[2],
    boxTop: 504, boxH: 42, boxW: 180,
    lines: [
      { text: 'cache miss', dy: 0 }
    ],
    mono: false,
    textY: 532
  },
  {
    step: 3,
    from: c[2], to: c[3],
    type: 'solid',
    badgeTop: 566, badgeH: 74, arrowY: 648,
    badgeW: 195,
    badgeX: 795, // between 789 and 1007
    lines: [
      { text: 'www.', dy: 0 },
      { text: 'example.com', dy: 24 },
      { text: 'A ?', dy: 24 }
    ],
    mono: false,
    startY: 591
  },
  {
    step: 4,
    from: c[3], to: c[2],
    type: 'dashed',
    badgeTop: 670, badgeH: 74, arrowY: 752,
    badgeW: 180,
    badgeX: 800, // between 783 and 1001
    lines: [
      { text: 'referral:', dy: 0 },
      { text: 'NS for com', dy: 24 },
      { text: '(+ glue)', dy: 24 }
    ],
    mono: false,
    startY: 695
  },
  {
    step: 5,
    from: c[2], to: c[4],
    type: 'solid',
    badgeTop: 774, badgeH: 42, arrowY: 824,
    badgeW: 310,
    badgeX: 840,
    lines: [
      { text: 'www.example.com A ?', dy: 0 }
    ],
    mono: false,
    startY: 803
  },
  {
    step: 6,
    from: c[4], to: c[2],
    type: 'dashed',
    badgeTop: 844, badgeH: 56, arrowY: 908,
    badgeW: 325,
    badgeX: 830,
    lines: [
      { text: 'referral: NS for', dy: 0 },
      { text: 'example.com (+ glue)', dy: 24 }
    ],
    mono: false,
    startY: 869
  },
  {
    step: 7,
    from: c[2], to: c[5],
    type: 'solid',
    badgeTop: 928, badgeH: 42, arrowY: 978,
    badgeW: 310,
    badgeX: 950,
    lines: [
      { text: 'www.example.com A ?', dy: 0 }
    ],
    mono: false,
    startY: 957
  },
  {
    step: 8,
    from: c[5], to: c[2],
    type: 'dashed',
    orange: true,
    badgeTop: 998, badgeH: 56, arrowY: 1062,
    badgeW: 270,
    badgeX: 970,
    lines: [
      { text: 'A 93.184.216.34,', dy: 0 },
      { text: 'TTL 300 (aa)', dy: 24 }
    ],
    mono: false,
    startY: 1023
  },
  {
    step: 9,
    from: c[2], to: c[1],
    type: 'dashed',
    badgeTop: 1082, badgeH: 74, arrowY: 1164,
    badgeW: 195,
    badgeX: 520,
    lines: [
      { text: 'answer', dy: 0 },
      { text: '(cached for', dy: 24 },
      { text: '300 s)', dy: 24 }
    ],
    mono: false,
    startY: 1107
  },
  {
    step: 10,
    from: c[1], to: c[0],
    type: 'dashed',
    badgeTop: 1120, // Wait, step 9 arrow is at 1164, step 10 arrow must be below step 9!
    badgeH: 42, arrowY: 1210
  }
];

console.log("Check step 9 and 10 Y coords...");
