const events = [
  { step: 1, text: 'getaddrinfo("www.example.com")', lines: ['getaddrinfo(', '"www.example.com")'], h: 58, from: 155, to: 470, type: 'solid' },
  { step: 2, text: 'query www.example.com A (recursion desired)', lines: ['query', 'www.example.com', 'A (recursion', 'desired)'], h: 96, from: 470, to: 770, type: 'solid' },
  { step: 'note', text: 'cache miss', lines: ['cache miss'], h: 42, lane: 770 },
  { step: 3, text: 'www.example.com A ?', lines: ['www.', 'example.com', 'A ?'], h: 72, from: 770, to: 1000, type: 'solid' },
  { step: 4, text: 'referral: NS for com (+ glue)', lines: ['referral:', 'NS for com', '(+ glue)'], h: 72, from: 1000, to: 770, type: 'dashed' },
  { step: 5, text: 'www.example.com A ?', lines: ['www.example.com A ?'], h: 42, from: 770, to: 1200, type: 'solid' },
  { step: 6, text: 'referral: NS for example.com (+ glue)', lines: ['referral: NS for', 'example.com (+ glue)'], h: 58, from: 1200, to: 770, type: 'dashed' },
  { step: 7, text: 'www.example.com A ?', lines: ['www.example.com A ?'], h: 42, from: 770, to: 1445, type: 'solid' },
  { step: 8, text: 'A 93.184.216.34, TTL 300 (aa)', lines: ['A 93.184.216.34, TTL 300 (aa)'], h: 42, from: 1445, to: 770, type: 'dashed', orange: true },
  { step: 9, text: 'answer (cached for 300 s)', lines: ['answer', '(cached for', '300 s)'], h: 72, from: 770, to: 470, type: 'dashed' },
  { step: 10, text: 'address', lines: ['address'], h: 42, from: 470, to: 155, type: 'dashed' }
];

let curY = 280;
events.forEach(e => {
  e.badgeTop = curY;
  e.badgeBottom = curY + e.h;
  e.arrowY = curY + e.h + 8; // Arrow is 8px below badge
  if (e.step === 'note') {
    e.arrowY = null;
    curY += e.h + 24;
  } else {
    curY = e.arrowY + 20; // 20px gap to next badge top
  }
  console.log(`Event ${e.step}: badgeTop=${e.badgeTop}, badgeBottom=${e.badgeBottom}, arrowY=${e.arrowY}`);
});
console.log("Final curY:", curY);
