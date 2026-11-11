"""ARC RACE owner home: static premium blue-and-gold course motif.

Presentation only. No moving horses, animation, JavaScript, network calls,
browser storage, authentication, provider calls or betting actions.
"""

SCENE_HTML = """<div class="arc-race-scene arc-race-scene-static" role="img" aria-label="静かなブルーとゴールドの円弧で表現したARC RACEホームバナー">
 <div class="arc-scene-content">
  <span class="arc-scene-eyebrow">ARC RACE · NIGHT TRACK</span>
  <strong class="arc-scene-headline">勝負を描く、予想のアーク。</strong>
  <span class="arc-scene-description">AI競馬予想・データ分析</span>
 </div>
</div>"""

SCENE_CSS = """/* Static owner banner: zero animations and no browser scripts. */
.arc-race-scene{position:relative;isolation:isolate;display:flex;align-items:center;
 min-height:132px;margin:0 0 14px;padding:17px 16px;overflow:hidden;
 border:1px solid #a88a55;border-radius:15px;
 background:radial-gradient(ellipse 105% 120% at 100% 125%,#3178a466,transparent 72%),
 linear-gradient(115deg,#0a2238,#15476c 68%,#0c2b47 100%);
 box-shadow:inset 0 1px 0 #f4d78b33,0 8px 20px #06132140}
.arc-race-scene::before,.arc-race-scene::after{
 content:"";position:absolute;pointer-events:none;z-index:0;
 border-radius:50%;transform:rotate(-14deg)}
.arc-race-scene::before{width:440px;height:220px;right:-125px;top:-94px;
 border:2px solid #dfb56d9e;box-shadow:0 0 28px #d6a45420}
.arc-race-scene::after{width:470px;height:216px;right:-145px;top:-71px;
 border:2px solid #69b8e6a6}
.arc-scene-content{position:relative;z-index:1;display:flex;flex-direction:column;
 align-items:flex-start;gap:5px;max-width:100%}
.arc-scene-eyebrow{font:800 10px/1.4 system-ui,sans-serif;letter-spacing:.11em;
 color:#bed8eb;text-shadow:0 1px 5px #091b30}
.arc-scene-headline{font:800 clamp(17px,4.7vw,21px)/1.35 system-ui,sans-serif;
 color:#ffe0a0;text-shadow:0 2px 9px #061b31}
.arc-scene-description{font-size:11px;color:#e2eef7;
 text-shadow:0 1px 4px #071a2b}
@media(max-width:370px){.arc-race-scene{min-height:125px;padding:13px 11px}
 .arc-race-scene::before{right:-180px}.arc-race-scene::after{right:-197px}}
"""

# Historical name maintained only as an import-compatible constant.
ANIMATED_HORSE_COUNT = 0
