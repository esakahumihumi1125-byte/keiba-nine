/* KEIBA NINE racecard comparison against a separately supplied reference file.
   No network calls, provider authentication, official claims, betting or storage. */
(function(root){
'use strict';
const allowedTracks=new Set(['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉']);
const key=r=>r.date+'|'+r.track+'|'+r.race;
function validDay(value){
 return typeof value==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(value)&&Number.isFinite(Date.parse(value+'T00:00:00Z'))&&new Date(value+'T00:00:00Z').toISOString().slice(0,10)===value;
}
function validateReference(input){
 if(!input||typeof input!=='object'||Array.isArray(input)||input.kind!=='keiba-nine-racecard-reference'||input.schema!==1)throw Error('照合ファイルはkind: keiba-nine-racecard-reference、schema: 1が必要です');
 if(typeof input.source!=='string'||!input.source.trim()||input.source.length>120)throw Error('照合元の出典名が必要です');
 if(typeof input.checkedAt!=='string'||!/(Z|[+-]\d{2}:\d{2})$/.test(input.checkedAt)||!Number.isFinite(Date.parse(input.checkedAt)))throw Error('照合元にはタイムゾーン付き確認日時が必要です');
 if(!Array.isArray(input.races)||input.races.length<1||input.races.length>120)throw Error('照合対象は1〜120レースです');
 const seen=new Set();
 const races=input.races.map((r,i)=>{
  const tag='照合元'+(i+1)+'R目：';
  if(!r||typeof r!=='object'||Array.isArray(r)||!validDay(r.date)||!allowedTracks.has(r.track)||!Number.isInteger(r.race)||r.race<1||r.race>12)throw Error(tag+'開催日・競馬場・レース番号が不正です');
  if(r.complete!==true)throw Error(tag+'全頭確認フラグcomplete:trueが必要です');
  if(r.off!==undefined&&(typeof r.off!=='string'||!/^([01]\d|2[0-3]):[0-5]\d$/.test(r.off)))throw Error(tag+'発走時刻はHH:MMで指定してください');
  if(!Array.isArray(r.horses)||r.horses.length<1||r.horses.length>18)throw Error(tag+'登録馬は1〜18頭です');
  const k=key(r);if(seen.has(k))throw Error(tag+'開催日・競馬場・Rが重複しています');
  seen.add(k);
  const numbers=new Set();
  const horses=r.horses.map(h=>{
   if(!h||typeof h!=='object'||Array.isArray(h)||!Number.isInteger(h.number)||h.number<1||h.number>18||numbers.has(h.number))throw Error(tag+'馬番に重複・不正があります');
   numbers.add(h.number);
   if(typeof h.name!=='string'||!h.name.trim()||h.name.length>100)throw Error(tag+'馬名が不正です');
   if(typeof h.scratched!=='boolean')throw Error(tag+'全馬に取消情報true/falseが必要です');
   return {number:h.number,name:h.name.trim().normalize('NFKC'),scratched:h.scratched};
  });
  return {date:r.date,track:r.track,race:r.race,complete:true,off:r.off, horses};
 });
 return {source:input.source.trim(),checkedAt:input.checkedAt,races};
}
function compareBundle(bundle,reference){
 if(!root.KeibaNineBatch)throw Error('一括分析エンジンを読み込んでください');
 const input=root.KeibaNineBatch.validateBundle(bundle),ref=validateReference(reference);
 const refMap=new Map(ref.races.map(r=>[key(r),r]));
 const issues=[],raceChecks=[];
 for(const card of input.racecards){
  const label=card.date+' '+card.track+card.race+'R';
  const target=refMap.get(key(card)),problem=[];
  if(!target)problem.push('照合元に該当レースがありません');
  else{
   const known=new Map(target.horses.map(h=>[h.number,h]));
   const from=new Map(card.horses.map(h=>[h.number,h]));
   for(const horse of card.horses){
    const expected=known.get(horse.number);
    if(!expected){problem.push(horse.number+'番 '+horse.name+'：照合元にありません');continue}
    if(horse.name.trim().normalize('NFKC')!==expected.name)problem.push(horse.number+'番：馬名が不一致（入力 '+horse.name+'／照合元 '+expected.name+'）');
    if(typeof horse.scratched!=='boolean')problem.push(horse.number+'番：入力側の取消情報が未確認');
    else if(horse.scratched!==expected.scratched)problem.push(horse.number+'番：取消状態が不一致');
   }
   for(const h of target.horses)if(!from.has(h.number))problem.push(h.number+'番：照合元にいる馬が入力側にありません');
   if(target.off!==undefined&&card.off!==undefined&&target.off!==card.off)problem.push('発走時刻が不一致');
  }
  raceChecks.push({date:card.date,track:card.track,race:card.race,matched:problem.length===0,issues:problem});
  for(const reason of problem)issues.push(label+'｜'+reason);
 }
 return {matched:issues.length===0,compared:input.racecards.length,passed:raceChecks.filter(x=>x.matched).length,failed:raceChecks.filter(x=>!x.matched).length,referenceSource:ref.source,checkedAt:ref.checkedAt,referenceCount:ref.races.length,issues,raceChecks,notice:'入力された別ファイル同士の一致のみ確認。提供元の真正性・JRA公式との照合を保証しません。'};
}
root.KeibaNineReference={validateReference,compareBundle};
})(window);
