
document.querySelectorAll('.mode-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    document.querySelectorAll('.mode-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
  });
});

document.querySelector('.send-btn').addEventListener('click', () => {
  const textarea = document.querySelector('.composer textarea');
  const value = textarea.value.trim();
  if (!value) return;
  const row = document.createElement('div');
  row.className = 'message-row user';
  row.innerHTML = '<div class="avatar user-avatar">W</div><div class="message-bubble user-bubble"></div>';
  row.querySelector('.user-bubble').textContent = value;
  document.querySelector('.conversation').appendChild(row);
  textarea.value = '';
  row.scrollIntoView({ behavior: 'smooth', block: 'end' });
});
