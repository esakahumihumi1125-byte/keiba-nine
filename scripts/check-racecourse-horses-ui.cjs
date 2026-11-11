// Smoke-check the public ARC RACE static banner without browser or network access.
'use strict';
const fs = require('node:fs');
const assert = require('node:assert/strict');
const html = fs.readFileSync('keiba-nine-beta51-feed-record.html', 'utf8');
const start = '<!-- ARC_RACE_STATIC_HERO_STYLE:';
const end = '<!-- ARC_RACE_STATIC_HERO_STYLE_END -->';
assert(html.includes(start) && html.includes(end), 'Static hero styles must exist');
const css = html.split(start)[1].split(end)[0];
const match = html.match(/<div class="arc-race-static-hero" id="arc-race-static-hero"[\s\S]*?<\/div>/);
assert(match, 'Static home banner must be present exactly once');
assert.equal((html.match(/id="arc-race-static-hero"/g) || []).length, 1);
const hero = match[0];
for (const copy of ['ARC RACE · NIGHT TRACK', '勝負を描く、予想のアーク。',
  'AI競馬予想・データ分析', '3連単', 'WIN5', '実戦記録']) {
  assert(hero.includes(copy), 'Missing hero text: ' + copy);
}
assert(css.includes('#d8ab59a3'), 'Gold race arc missing');
assert(css.includes('#4898c5a1'), 'Blue race arc missing');
assert(css.includes('min-height:142px'), 'Compact home layout missing');
for (const forbidden of ['<script', '<animateMotion', 'animation:', '@keyframes',
  'fetch(', 'localStorage', 'sessionStorage', 'setInterval(',
  'requestAnimationFrame']) {
  assert(!hero.includes(forbidden) && !css.includes(forbidden),
    'Static hero may not use ' + forbidden);
}
assert(!html.includes('RACECOURSE58_MINI_HORSES_START'));
assert(!html.includes('kn-thoroughbred-gallop'));
assert(!html.includes('const numHorses=18;'));
assert(html.includes('id="knOwnerForecastLaunch"'));
assert(html.includes('data-screen="win5"'));
console.log('ARC RACE public static banner, gold/blue arcs and zero motion passed');
