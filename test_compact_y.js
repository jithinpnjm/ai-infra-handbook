const events = [
  { step: 1, badgeTop: 265, badgeH: 68, arrowY: 340 },
  { step: 2, badgeTop: 356, badgeH: 92, arrowY: 454 },
  { step: 'note', boxTop: 472, boxH: 40 },
  { step: 3, badgeTop: 526, badgeH: 68, arrowY: 600 },
  { step: 4, badgeTop: 618, badgeH: 68, arrowY: 692 },
  { step: 5, badgeTop: 710, badgeH: 40, arrowY: 756 },
  { step: 6, badgeTop: 774, badgeH: 54, arrowY: 834 },
  { step: 7, badgeTop: 852, badgeH: 40, arrowY: 898 },
  { step: 8, badgeTop: 916, badgeH: 54, arrowY: 976 },
  { step: 9, badgeTop: 994, badgeH: 68, arrowY: 1068 },
  { step: 10, badgeTop: 1086, badgeH: 40, arrowY: 1132 }
];

for (let i = 0; i < events.length - 1; i++) {
  const e1 = events[i];
  const e2 = events[i+1];
  const y1 = e1.step === 'note' ? e1.boxTop + e1.boxH : e1.arrowY;
  const y2 = e2.step === 'note' ? e2.boxTop : e2.badgeTop;
  console.log(`Gap between event ${e1.step} and ${e2.step}: ${y2 - y1}px`);
}
