(() => {
  'use strict';
  const data = window.DESPORTES;
  const dialog = document.getElementById('reader');
  const buttons = [...document.querySelectorAll('[data-language]')];
  let selected = null;
  function render(language) {
    if (!selected) return;
    buttons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.language === language)));
    const target = document.getElementById('reader-text');
    target.replaceChildren();
    target.lang = language === 'french' ? 'fr' : 'en';
    if (language === 'french') {
      const pre = document.createElement('pre');
      pre.textContent = selected.french;
      target.append(pre);
    } else {
      const paragraph = document.createElement('p');
      paragraph.textContent = selected.english;
      target.append(paragraph);
    }
    target.scrollTop = 0;
  }
  document.querySelectorAll('[data-letter]').forEach(button => button.addEventListener('click', () => {
    selected = data.letters.find(letter => letter.id === button.dataset.letter);
    if (!selected) return;
    document.getElementById('reader-title').textContent = 'To ' + selected.recipient;
    document.getElementById('reader-folio').textContent = 'Folio ' + selected.folio + ' · Paris, 22 July 1593';
    for (const [id, field] of [['reader-source', 'source'], ['reader-published', 'published'], ['reader-archive', 'archive']]) {
      document.getElementById(id).href = selected[field];
    }
    render('english');
    dialog.showModal();
  }));
  buttons.forEach(button => button.addEventListener('click', () => render(button.dataset.language)));
  document.getElementById('close-reader').addEventListener('click', () => dialog.close());
})();
