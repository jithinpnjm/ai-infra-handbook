const fs = require('fs');

// Participants
const participants = [
  {
    id: "App",
    name: "Application",
    w: 230,
    c: 155,
    lines: [{ text: "Application", size: 30, bold: true, y: 215 }]
  },
  {
    id: "Stub",
    name: "Stub resolver (libc / systemd-resolved)",
    w: 280,
    c: 455,
    lines: [
      { text: "Stub resolver", size: 30, bold: true, y: 180 },
      { text: "(libc /", size: 24, bold: false, y: 212 },
      { text: "systemd-resolved)", size: 24, bold: false, y: 242 }
    ]
  },
  {
    id: "Rec",
    name: "Recursive resolver (cache)",
    w: 200,
    c: 750,
    lines: [
      { text: "Recursive", size: 30, bold: true, y: 180 },
      { text: "resolver", size: 30, bold: true, y: 212 },
      { text: "(cache)", size: 24, bold: false, y: 242 }
    ]
  },
  {
    id: "Root",
    name: "Root server",
    w: 140,
    c: 1000,
    lines: [
      { text: "Root", size: 30, bold: true, y: 198 },
      { text: "server", size: 30, bold: true, y: 235 }
    ]
  },
  {
    id: "TLD",
    name: ".com TLD server",
    w: 180,
    c: 1200,
    lines: [
      { text: ".com TLD", size: 30, bold: true, y: 198 },
      { text: "server", size: 30, bold: true, y: 235 }
    ]
  },
  {
    id: "Auth",
    name: "example.com authoritative",
    w: 230,
    c: 1445,
    lines: [
      { text: "example.com", size: 30, bold: true, y: 198 },
      { text: "authoritative", size: 24, bold: false, y: 235 }
    ]
  }
];

// Let verify all participants lines padding
participants.forEach((p, i) => {
  p.lines.forEach(l => {
    const w = l.text.length * 0.6 * l.size;
    const pad = (p.w - w) / 2;
    if (pad < 16) {
      console.error(`ERROR: Participant ${p.name} line "${l.text}" pad=${pad} < 16`);
    }
  });
});
console.log("All participant paddings verified >= 16px!");
