// Click a Mermaid diagram to view it full screen; click again or press Esc to close.
if (typeof window !== 'undefined') {
  document.addEventListener('click', (e) => {
    const box = e.target.closest && e.target.closest('.docusaurus-mermaid-container');
    if (box) box.classList.toggle('mermaid-zoomed');
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') document.querySelectorAll('.mermaid-zoomed').forEach((n) => n.classList.remove('mermaid-zoomed'));
  });
}
