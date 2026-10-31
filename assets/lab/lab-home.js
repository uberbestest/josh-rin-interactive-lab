/* Decorative homepage controls only. No telemetry, storage, model calls or experiments. */
(function () {
  'use strict';
  const group = document.getElementById('labFilters');
  const cards = Array.from(document.querySelectorAll('#experiments .card'));
  const status = document.getElementById('labFilterStatus');
  if (group && cards.length && status) {
    group.hidden = false;
    status.hidden = false;
    const buttons = Array.from(group.querySelectorAll('button[data-filter]'));
    for (const button of buttons) {
      button.addEventListener('click', function () {
        const filter = button.dataset.filter;
        let shown = 0;
        for (const card of cards) {
          const visible = filter === 'all' || card.dataset.topic === filter;
          card.hidden = !visible;
          if (visible) shown += 1;
        }
        for (const other of buttons) other.setAttribute('aria-pressed', String(other === button));
        status.textContent = filter === 'all'
          ? 'Showing all ' + cards.length + ' instruments.'
          : 'Showing ' + shown + ' of ' + cards.length + ' instruments · ' + button.textContent + '.';
      });
    }
    status.textContent = 'Showing all ' + cards.length + ' instruments.';
  }
  const button = document.getElementById('puddleHello');
  const message = document.getElementById('puddleMessage');
  if (button && message) {
    button.hidden = false;
    const lines = [
      'Puddle: “Please keep the receipts. And the crumbs.”',
      'Puddle: “A green checkmark is not a peer review.”',
      'Puddle: “The goblins have requested a second candy audit.”',
      'Mote keeps the light on. Puddle keeps an eye on the snacks.'
    ];
    let next = 0;
    button.addEventListener('click', function () {
      message.textContent = lines[next % lines.length];
      next += 1;
    });
  }
})();
