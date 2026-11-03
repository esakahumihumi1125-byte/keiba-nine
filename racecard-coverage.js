/* KEIBA NINE offline program coverage audit.
   The stated program is user/provider-supplied: NEVER infer official fixtures. */
(function(root){
'use strict';
const tracks=['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉'];
const key=(date,track,race)=>[date,track,race].join('|');
function validDate(s){
 return typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&
   Number.isFinite(Date.parse(s+'T00:00:00Z'))&&
   new Date(s+'T00:00:00Z').toISOString().slice(0,10)===s;
}
function validateProgram(program){
 if(!program||typeof program!=='object'||Array.isArray(program))throw Error('開催予定programはオブジェクトが必要です');
 if(typeof program.source!=='string'||!program.source.trim()||program.source.length>120)throw Error('開催予定には確認元sourceが必要です');
 if(typeof program.checkedAt!=='string'||!/(Z|[+-]\d{2}:\d{2})$/.test(program.checkedAt)||!Number.isFinite(Date.parse(program.checkedAt)))throw Error('開催予定にはタイムゾーン付きの確認日時checkedAtが必要です');
 if(!Array.isArray(program.sessions)||!program.sessions.length||program.sessions.length>120)throw Error('開催予定sessionsは1〜120件で指定してください');
 const sessions=new Set(),expected=new Set(),normalized=[];
 for(const s of program.sessions){
  if(!s||typeof s!=='object'||Array.isArray(s)||!validDate(s.date)||!tracks.includes(s.track))throw Error('開催予定の日付・競馬場が不正です');
  const label=s.date+' '+s.track;
  if(sessions.has(label))throw Error('開催予定に同じ日付・競馬場が重複しています：'+label);
  sessions.add(label);
  if(!Array.isArray(s.races)||!s.races.length||s.races.length>12)throw Error(label+'の対象レースは1〜12個です');
  const list=new Set();
  for(const n of s.races){
   if(!Number.isInteger(n)||n<1||n>12||list.has(n))throw Error(label+'のレース番号に重複・不正があります');
   list.add(n);
   expected.add(key(s.date,s.track,n));
  }
  normalized.push({date:s.date,track:s.track,races:[...list].sort((a,b)=>a-b)});
 }
 if(expected.size>120)throw Error('開催予定は最大120レースまでです');
 return {source:program.source.trim(),checkedAt:program.checkedAt,sessions:normalized,expected:[...expected]};
}
function auditCoverage(bundle){
 if(!root.KeibaNineBatch)throw Error('一括検証エンジンを先に読み込んでください');
 const analysed=root.KeibaNineBatch.analyzeBundle(bundle);
 if(bundle.program===undefined)return {
  declared:false,allCardsPresent:false,allPreviewsReady:false,
  expected:0,received:analysed.total,ready:analysed.ready,
  missing:[],unexpected:[],unready:[],sessions:[],
  notice:'開催予定programが未指定です。全場全Rがそろったか判定できません。'
 };
 const program=validateProgram(bundle.program);
 const expected=new Set(program.expected);
 const got=new Map(analysed.entries.map(e=>[key(e.date,e.track,e.race),e]));
 const missing=program.expected.filter(k=>!got.has(k));
 const unexpected=[...got.keys()].filter(k=>!expected.has(k));
 const unready=program.expected.filter(k=>got.has(k)&&!got.get(k).analysis.ready);
 const sessions=program.sessions.map(s=>{
  const keys=s.races.map(n=>key(s.date,s.track,n));
  const missingRaces=s.races.filter((n,i)=>!got.has(keys[i]));
  const unreadyRaces=s.races.filter((n,i)=>got.has(keys[i])&&!got.get(keys[i]).analysis.ready);
  return {date:s.date,track:s.track,expected:s.races.length,received:s.races.length-missingRaces.length,
    ready:s.races.length-missingRaces.length-unreadyRaces.length,missingRaces,unreadyRaces};
 });
 const complete=missing.length===0&&unexpected.length===0;
 return {
  declared:true,source:program.source,checkedAt:program.checkedAt,
  expected:program.expected.length,received:analysed.total,
  ready:program.expected.filter(k=>got.has(k)&&got.get(k).analysis.ready).length,
  allCardsPresent:complete,allPreviewsReady:complete&&unready.length===0,
  missing,unexpected,unready,sessions,
  notice:'開催予定・出馬表とも入力データです。JRA公式の日程との照合や取得データの利用権限を保証しません。'
 };
}
root.KeibaNineCoverage={validateProgram,auditCoverage};
})(window);
