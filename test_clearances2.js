const c = [155, 465, 765, 1025, 1220, 1445];

const events = [
  {
    step: 1,
    from: c[0], to: c[1],
    lines: ['getaddrinfo(', '"www.example', '.com")'],
    mono: true
  },
  {
    step: 2,
    from: c[1], to: c[2],
    lines: ['query', 'www.example.com', 'A (recursion', 'desired)'],
    mono: false
  },
  {
    step: 3,
    from: c[2], to: c[3],
    lines: ['www.', 'example.com', 'A ?'],
    mono: false
  },
  {
    step: 4,
    from: c[3], to: c[2],
    lines: ['referral:', 'NS for com', '(+ glue)'],
    mono: false
  },
  {
    step: 5,
    from: c[2], to: c[4],
    lines: ['www.example.com A ?'],
    mono: false
  },
  {
    step: 6,
    from: c[4], to: c[2],
    lines: ['referral: NS for', 'example.com (+ glue)'],
    mono: false
  },
  {
    step: 7,
    from: c[2], to: c[5],
    lines: ['www.example.com A ?'],
    mono: false
  },
  {
    step: 8,
    from: c[5], to: c[2],
    lines: ['A 93.184.216.34,', 'TTL 300 (aa)'],
    mono: false
  },
  {
    step: 9,
    from: c[2], to: c[1],
    lines: ['answer', '(cached for', '300 s)'],
    mono: false
  },
  {
    step: 10,
    from: c[1], to: c[0],
    lines: ['address'],
    mono: false
  }
];

events.forEach(e => {
  const coeff = e.mono ? 0.62 : 0.6;
  const maxW = Math.max(...e.lines.map(l => l.length * coeff * 24));
  const badgeW = maxW + 36;
  const span = Math.abs(e.to - e.from);
  const avail = span - 24 - 18;
  const margin = avail - badgeW;
  console.log(`Step ${e.step}: span=${span}px | badgeW=${badgeW.toFixed(1)}px | avail=${avail}px | remainingMargin=${margin.toFixed(1)}px (ok? ${margin >= 10})`);
});
