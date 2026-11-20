const events = [
  {
    step: 1,
    from: 155, to: 470, dir: 1,
    lines: ['getaddrinfo(', '"www.example', '.com")'],
    mono: true
  },
  {
    step: 2,
    from: 470, to: 770, dir: 1,
    lines: ['query', 'www.example.com', 'A (recursion', 'desired)'],
    mono: false
  },
  {
    step: 3,
    from: 770, to: 1000, dir: 1,
    lines: ['www.', 'example.com', 'A ?'],
    mono: false
  },
  {
    step: 4,
    from: 1000, to: 770, dir: -1,
    lines: ['referral:', 'NS for com', '(+ glue)'],
    mono: false
  },
  {
    step: 5,
    from: 770, to: 1200, dir: 1,
    lines: ['www.example.com A ?'],
    mono: false
  },
  {
    step: 6,
    from: 1200, to: 770, dir: -1,
    lines: ['referral: NS for', 'example.com (+ glue)'],
    mono: false
  },
  {
    step: 7,
    from: 770, to: 1445, dir: 1,
    lines: ['www.example.com A ?'],
    mono: false
  },
  {
    step: 8,
    from: 1445, to: 770, dir: -1,
    lines: ['A 93.184.216.34,', 'TTL 300 (aa)'],
    mono: false
  },
  {
    step: 9,
    from: 770, to: 470, dir: -1,
    lines: ['answer', '(cached for', '300 s)'],
    mono: false
  },
  {
    step: 10,
    from: 470, to: 155, dir: -1,
    lines: ['address'],
    mono: false
  }
];

events.forEach(e => {
  const coeff = e.mono ? 0.62 : 0.6;
  const maxW = Math.max(...e.lines.map(l => l.length * coeff * 24));
  const badgeW = maxW + 36; // at least 18px pad on each side
  const span = Math.abs(e.to - e.from);
  
  // Circle at e.from, radius 24.
  // Arrowhead at e.to, length 18.
  // Space available between circle edge and arrowhead edge:
  const avail = span - 24 - 18;
  const margin = avail - badgeW;
  console.log(`Step ${e.step}: span=${span}px | badgeW=${badgeW.toFixed(1)}px | avail=${avail}px | remainingMargin=${margin.toFixed(1)}px (ok? ${margin >= 10})`);
});
