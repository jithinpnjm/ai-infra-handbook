// Header ends at y = 260.
// Footer / lifelines end at y = 1170.
// Available height = 1170 - 270 = 900px.

const events = [
  { step: 1, text: 'getaddrinfo("www.example.com")', lines: ['getaddrinfo(', '"www.example.com")'], h: 58 },
  { step: 2, text: 'query www.example.com A (recursion desired)', lines: ['query', 'www.example.com', 'A (recursion', 'desired)'], h: 96 },
  { step: 'note', text: 'cache miss', lines: ['cache miss'], h: 42 },
  { step: 3, text: 'www.example.com A ?', lines: ['www.', 'example.com', 'A ?'], h: 72 },
  { step: 4, text: 'referral: NS for com (+ glue)', lines: ['referral:', 'NS for com', '(+ glue)'], h: 72 },
  { step: 5, text: 'www.example.com A ?', lines: ['www.example.com A ?'], h: 42 },
  { step: 6, text: 'referral: NS for example.com (+ glue)', lines: ['referral: NS for', 'example.com (+ glue)'], h: 58 },
  { step: 7, text: 'www.example.com A ?', lines: ['www.example.com A ?'], h: 42 },
  { step: 8, text: 'A 93.184.216.34, TTL 300 (aa)', lines: ['A 93.184.216.34, TTL 300 (aa)'], h: 42 },
  { step: 9, text: 'answer (cached for 300 s)', lines: ['answer', '(cached for', '300 s)'], h: 72 },
  { step: 10, text: 'address', lines: ['address'], h: 42 }
];

const totalH = events.reduce((sum, e) => sum + e.h, 0);
console.log("Total badge height:", totalH);
const remaining = 900 - totalH;
console.log("Remaining for 10 gaps:", remaining);
console.log("Average gap:", remaining / 10);
