/*
 * JEBAT mascot — cursor-tracking head, vanilla JS port of `page-mascot`.
 *
 * Based on page-mascot by Kamran Ahmed (https://kamran.fyi), MIT licensed.
 * https://github.com/nilbuild/page-mascot
 *
 * Each character is two 3x3 sprite sheets: nine head directions and nine
 * expressions. The cell is chosen by moving background-position, so there is
 * no per-frame JavaScript and no animation library.
 *
 * Mounts into any element carrying [data-jebat-mascot]. Options come from
 * data attributes: directions, reactions, size, label.
 */
(function () {
  'use strict';

  var DIRECTIONS = ['up-left', 'up', 'up-right', 'left', 'center', 'right',
                    'down-left', 'down', 'down-right'];

  // Clockwise from the right, matching atan2 with y pointing down.
  var CLOCKWISE = ['right', 'down-right', 'down', 'down-left', 'left',
                   'up-left', 'up', 'up-right'];
  var REACTIONS = ['blink', 'heart', 'sparkle', 'surprised', 'wink',
                   'bashful', 'sleepy', 'dizzy', 'delighted'];

  var SECTOR = (Math.PI * 2) / CLOCKWISE.length;
  var HYSTERESIS = 0.12;
  var DEAD_ZONE = 70;

  var PAYOFFS = ['heart', 'sparkle', 'delighted'];
  var BOOP_PAYOFF = 120;
  var BOOP_END = 560;
  var SQUASH_MS = 420;
  var DIZZY_AFTER = 4;
  var DIZZY_WINDOW = 1600;
  var DIZZY_END = 1100;

  var SQUASH = [
    { transform: 'scale(1, 1)', easing: 'ease-in' },
    { transform: 'scale(1.10, 0.86)', offset: 0.18, easing: 'ease-out' },
    { transform: 'scale(0.95, 1.08)', offset: 0.45, easing: 'ease-in-out' },
    { transform: 'scale(1.03, 0.97)', offset: 0.72, easing: 'ease-in-out' },
    { transform: 'scale(1, 1)' }
  ];

  // background-size 300% makes each cell a clean 0/50/100% step on both axes.
  function cellPosition(index) {
    return ((index % 3) * 50) + '% ' + (Math.floor(index / 3) * 50) + '%';
  }

  function wrapAngle(angle) {
    return Math.atan2(Math.sin(angle), Math.cos(angle));
  }

  function reduceMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function finePointer() {
    return window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  }

  function mount(host) {
    var directions = host.getAttribute('data-directions') ||
      'assets/mascots/pendekar-directions.webp';
    var reactions = host.getAttribute('data-reactions') ||
      'assets/mascots/pendekar-reactions.webp';
    var size = parseInt(host.getAttribute('data-size'), 10) || 140;
    var label = host.getAttribute('data-label') || 'mascot';

    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'jebat-mascot';
    button.setAttribute('aria-label', 'Boop the ' + label);
    button.style.cssText =
      'position:relative;display:block;flex-shrink:0;' +
      'width:' + size + 'px;height:' + size + 'px;padding:0;border:0;' +
      'background:transparent;appearance:none;-webkit-appearance:none;' +
      'cursor:pointer;user-select:none;';

    var squash = document.createElement('span');
    squash.style.cssText =
      'position:relative;display:block;width:100%;height:100%;' +
      'transform-origin:50% 78%;';

    var layerCss = 'position:absolute;inset:0;background-size:300% 300%;' +
      'background-repeat:no-repeat;';

    var dirLayer = document.createElement('span');
    dirLayer.style.cssText = layerCss + 'background-image:url(' + directions + ');' +
      'background-position:' + cellPosition(DIRECTIONS.indexOf('center')) + ';';

    // Always mounted so the sheet is fetched up front, never on first click.
    var reactLayer = document.createElement('span');
    reactLayer.style.cssText = layerCss + 'background-image:url(' + reactions + ');' +
      'background-position:' + cellPosition(0) + ';opacity:0;';

    squash.appendChild(dirLayer);
    squash.appendChild(reactLayer);
    button.appendChild(squash);
    host.appendChild(button);

    var timers = [];
    var boops = { count: 0, at: 0 };

    function setDirection(name) {
      dirLayer.style.backgroundPosition =
        cellPosition(DIRECTIONS.indexOf(name));
    }

    function setReaction(name) {
      if (name) {
        reactLayer.style.backgroundPosition =
          cellPosition(REACTIONS.indexOf(name));
        reactLayer.style.opacity = '1';
        dirLayer.style.opacity = '0';
      } else {
        reactLayer.style.opacity = '0';
        dirLayer.style.opacity = '1';
      }
    }

    function later(ms, name) {
      timers.push(window.setTimeout(function () { setReaction(name); }, ms));
    }

    button.addEventListener('click', function () {
      timers.forEach(window.clearTimeout);
      timers = [];

      var now = Date.now();
      boops.count = (now - boops.at < DIZZY_WINDOW) ? boops.count + 1 : 1;
      boops.at = now;

      if (boops.count >= DIZZY_AFTER) {
        boops.count = 0;
        setReaction('dizzy');
        later(DIZZY_END, null);
      } else {
        setReaction('blink');
        later(BOOP_PAYOFF, PAYOFFS[(boops.count - 1) % PAYOFFS.length]);
        later(BOOP_END, null);
      }

      if (!reduceMotion() && squash.animate) {
        // Per-keyframe easing with the effect itself linear: an easing on the
        // effect would reinterpret every offset and front-load the bounce.
        squash.animate(SQUASH, { duration: SQUASH_MS, easing: 'linear' });
      }
    });

    // Tracking switches off without a fine pointer.
    if (!finePointer()) { return; }

    var sector = -1;
    var pointer = null;

    function aim() {
      if (!pointer) { return; }
      var box = button.getBoundingClientRect();
      var dx = pointer.x - (box.left + box.width / 2);
      var dy = pointer.y - (box.top + box.height / 2);

      if (Math.sqrt(dx * dx + dy * dy) < DEAD_ZONE) {
        sector = -1;
        setDirection('center');
        return;
      }

      // Hold the current sector until the pointer is well past its edge.
      var angle = Math.atan2(dy, dx);
      if (sector !== -1 &&
          Math.abs(wrapAngle(angle - sector * SECTOR)) < SECTOR / 2 + HYSTERESIS) {
        return;
      }
      sector = (Math.round(angle / SECTOR) + CLOCKWISE.length) % CLOCKWISE.length;
      setDirection(CLOCKWISE[sector]);
    }

    window.addEventListener('pointermove', function (event) {
      pointer = { x: event.clientX, y: event.clientY };
      aim();
    }, { passive: true });
    window.addEventListener('scroll', aim, { passive: true });
  }

  function init() {
    document.querySelectorAll('[data-jebat-mascot]').forEach(function (host) {
      if (host.dataset.jebatMascotMounted) { return; }
      host.dataset.jebatMascotMounted = '1';
      mount(host);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
