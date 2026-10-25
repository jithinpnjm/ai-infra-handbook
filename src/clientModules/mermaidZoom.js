// Click any Mermaid diagram or article image to view it full-screen;
// click again, click Close, or press Esc to close.
if (typeof window !== 'undefined') {
  const closeZoomModal = () => {
    const existing = document.getElementById('diagram-zoom-overlay');
    if (existing) {
      existing.remove();
    }
    document.querySelectorAll('.mermaid-zoomed').forEach((n) => n.classList.remove('mermaid-zoomed'));
    document.body.classList.remove('diagram-zoom-open');
  };

  const openZoomModal = (sourceEl) => {
    closeZoomModal();

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const cardBg = isDark ? '#18191a' : '#ffffff';
    const borderCol = isDark ? '#334155' : '#cbd5e1';
    const textCol = isDark ? '#f8fafc' : '#0f172a';

    const overlay = document.createElement('div');
    overlay.id = 'diagram-zoom-overlay';
    overlay.className = 'diagram-zoom-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.style.cssText = [
      'position: fixed',
      'inset: 0',
      'z-index: 99999',
      'margin: 0',
      'padding: 2vh 2vw',
      'background: rgba(15, 23, 42, 0.9)',
      'display: flex',
      'align-items: center',
      'justify-content: center',
      'cursor: zoom-out',
      'box-sizing: border-box',
    ].join(';');

    const card = document.createElement('div');
    card.className = 'diagram-zoom-card';
    card.style.cssText = [
      'position: relative',
      'width: 94vw',
      'height: 92vh',
      `background-color: ${cardBg}`,
      `border: 1px solid ${borderCol}`,
      'border-radius: 12px',
      'padding: 3.5rem 2rem 1.5rem',
      'box-sizing: border-box',
      'display: flex',
      'flex-direction: column',
      'align-items: center',
      'justify-content: center',
      'overflow: auto',
      'box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6)',
    ].join(';');

    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'diagram-zoom-close';
    closeBtn.setAttribute('aria-label', 'Close zoomed view');
    closeBtn.textContent = 'Close (Esc)';
    closeBtn.style.cssText = [
      'position: absolute',
      'top: 0.75rem',
      'right: 1rem',
      'padding: 0.4rem 0.9rem',
      'font-size: 0.875rem',
      'font-weight: 600',
      `color: ${textCol}`,
      `background-color: ${cardBg}`,
      `border: 1px solid ${borderCol}`,
      'border-radius: 6px',
      'cursor: pointer',
      'z-index: 10',
    ].join(';');

    const content = document.createElement('div');
    content.className = 'diagram-zoom-content';
    content.style.cssText = [
      'width: 100%',
      'height: 100%',
      'display: flex',
      'align-items: center',
      'justify-content: center',
      'overflow: auto',
      `background-color: ${cardBg}`,
    ].join(';');

    if (sourceEl.tagName && sourceEl.tagName.toLowerCase() === 'img') {
      const clonedImg = sourceEl.cloneNode(true);
      clonedImg.removeAttribute('width');
      clonedImg.removeAttribute('height');
      clonedImg.style.cssText = [
        'display: block',
        'width: 88vw',
        'height: 82vh',
        'max-width: 88vw',
        'max-height: 82vh',
        'object-fit: contain',
      ].join(';');
      content.appendChild(clonedImg);
    } else {
      const svg = sourceEl.querySelector('svg');
      if (svg) {
        const clonedSvg = svg.cloneNode(true);
        clonedSvg.removeAttribute('width');
        clonedSvg.removeAttribute('height');
        clonedSvg.removeAttribute('style');
        clonedSvg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
        clonedSvg.style.cssText = [
          'display: block',
          'width: 88vw !important',
          'height: 82vh !important',
          'max-width: 88vw !important',
          'max-height: 82vh !important',
          `background-color: ${cardBg}`,
        ].join(';');
        content.appendChild(clonedSvg);
      } else {
        content.appendChild(sourceEl.cloneNode(true));
      }
    }

    card.appendChild(closeBtn);
    card.appendChild(content);
    overlay.appendChild(card);
    document.body.appendChild(overlay);
    document.body.classList.add('diagram-zoom-open');
  };

  document.addEventListener('click', (e) => {
    const target = e.target;
    if (!target || !target.closest) return;

    if (target.closest('#diagram-zoom-overlay')) {
      closeZoomModal();
      return;
    }

    const mermaidBox = target.closest('.docusaurus-mermaid-container');
    if (mermaidBox) {
      openZoomModal(mermaidBox);
      return;
    }

    const markdownImg = target.closest('.theme-doc-markdown img, article img');
    if (markdownImg) {
      openZoomModal(markdownImg);
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeZoomModal();
    }
  });
}
