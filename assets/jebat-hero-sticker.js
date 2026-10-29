import { play, brand } from './fun.js';
import { commandToken } from './jebat-sticker.js';

const canvas = document.getElementById('command-sticker');
if (canvas) {
  const player = play(canvas, commandToken, {
    palette: brand('#C97A40', '#2F6F55'),
    loop: false,
    label: 'Isometric orchestration token',
  });
  document.getElementById('replay-run')?.addEventListener('click', () => player.replay());
  canvas.addEventListener('click', () => player.replay());
  canvas.style.cursor = 'pointer';
}
