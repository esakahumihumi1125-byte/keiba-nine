/* KEIBA NINE offline batch racecard adapter. No fetch, writes, publishing or betting. */
(function(root){
'use strict';
const allowedTracks=['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉'];
const maxRaces=120;
function validateBundle(input){
 if(!input||typeof input!=='object'||Array.isArray(input))throw Error('JSONオブジェクトを指定してください');
 if(input.kind!=='keiba-nine-racecards'||input.schema!==1)throw Error('kind: keiba-nine-racecards / schema: 1 が必要です');
 if(typeof input.source!=='string'||!input.source.trim()||input.source.length>120||input.licenseConfirmed!==true)throw Error('提供元と利用許諾確認が必要です（自己申告であり許諾の証明ではありません）');
 if(!Array.isArray(input.racecards)||input.racecards.length<1||input.racecards.length>maxRaces)throw Error('1ファイルのレース数は1〜120です');
 if(!root.KeibaNineRacecard)throw Error('出馬表の検証エンジンが見つかりません');
 const seen=new Set();
 const cards=input.racecards.map((row,i)=>{
   if(!row||typeof row!=='object'||Array.isArray(row))throw Error((i+1)+'番目のレースが不正です');
   if(Object.hasOwn(row,'source')&&row.source!==input.source)throw Error((i+1)+'番目の提供元が一括ファイルと一致しません');
   if(Object.hasOwn(row,'licenseConfirmed')&&row.licenseConfirmed!==true)throw Error((i+1)+'番目の利用許諾確認が不足しています');
   const card=root.KeibaNineRacecard.validateRacecard({...row,source:input.source,licenseConfirmed:true});
   const key=card.date+'|'+card.track+'|'+card.race;
   if(seen.has(key))throw Error('同じ開催日・競馬場・レース番号が重複しています：'+key);
   seen.add(key);
   return card;
 });
 return {kind:'keiba-nine-racecards',schema:1,source:input.source,licenseConfirmed:true,racecards:cards};
}
function analyzeBundle(input){
 const bundle=validateBundle(input);
 const entries=bundle.racecards.map(card=>({
   date:card.date,track:card.track,race:card.race,source:bundle.source,
   analysis:root.KeibaNineRacecard.analyzeRacecard(card)
 }));
 entries.sort((a,b)=>a.date.localeCompare(b.date)||allowedTracks.indexOf(a.track)-allowedTracks.indexOf(b.track)||a.race-b.race);
 const ready=entries.filter(x=>x.analysis.ready).length;
 const dates=[...new Set(entries.map(x=>x.date))].sort();
 const tracks=[...new Set(entries.map(x=>x.track))].sort((a,b)=>allowedTracks.indexOf(a)-allowedTracks.indexOf(b));
 return {source:bundle.source,entries,dates,tracks,total:entries.length,ready,skipped:entries.length-ready};
}
root.KeibaNineBatch={validateBundle,analyzeBundle,maxRaces};
})(window);
