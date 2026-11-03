/* KEIBA NINE personal-use, offline batch preview bridge.
   Converts verified-format input grades to an explicit test/draft preview.
   Does not publish, bet, or write any persistent records. */
(function(root){
'use strict';
function toDraftRows(bundle){
 if(!root.KeibaNineBatch)throw Error('一括分析エンジンを先に読み込んでください');
 const analyzed=root.KeibaNineBatch.analyzeBundle(bundle);
 return analyzed.entries.map(entry=>{
   const a=entry.analysis,ready=a.ready;
   const ranked=a.ranked||[];
   const intro='入力された評価の暫定計算。公式出馬表・取消・馬場の照合は未実施。購入推奨ではありません。';
   const reason=ready?intro:(intro+' 見送り理由：'+a.reasons.join('／'));
   const horses=(ready?ranked:a.active.map(h=>({number:h.number,name:h.name,overall:'未検証'}))).map(h=>({
     number:h.number,name:h.name,overall:h.overall||'未検証',
     training:h.evaluations?.training?.grade||'未検証',
     course:h.evaluations?.course?.grade||'未検証',
     pedigree:h.evaluations?.pedigree?.grade||'未検証',
     pace:h.evaluations?.pace?.grade||'未検証',
     reason:ready?Object.entries(h.evaluations).map(([k,v])=>k+': '+v.note).join('／').slice(0,1200):'評価根拠が不足しているため見送り'
   }));
   return {
     date:entry.date,track:entry.track,race:entry.race,off:'',
     recordType:'test',status:ready?'draft':'skip',
     intent:ready?'参考':'見送り',confidence:'C',
     ranking:ranked.map(h=>h.number),
     first:ready?a.formation.first:[],
     second:ready?a.formation.second:[],
     third:ready?a.formation.third:[],
     trioMode:'ボックス',trioPool:[],
     triPoints:ready?a.combinations.length:0,trioPoints:0,
     rankS:ranked.filter(h=>h.overall==='S').map(h=>h.number),
     rankA:ranked.filter(h=>h.overall==='A').map(h=>h.number),
     rankB:ranked.filter(h=>h.overall==='B').map(h=>h.number),
     reason, horses
   };
 });
}
root.KeibaNinePreviewBridge={toDraftRows,sessionKey:'kn_batch_preview_transfer_v1'};
})(window);
