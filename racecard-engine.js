/* KEIBA NINE racecard evidence gate: offline, no remote data and no bets placed. */
(function(root){
'use strict';
function validateRacecard(x){
  const tracks=['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉'];
  const axes=['recent','training','course','pedigree','pace'];
  if(!x||typeof x!=='object'||Array.isArray(x))throw Error('JSONオブジェクトを入力してください');
  if(typeof x.source!=='string'||!x.source.trim()||x.source.length>120||x.licenseConfirmed!==true)throw Error('提供元と利用許諾の確認が必要です（自己申告であり許諾の証明ではありません）');
  if(typeof x.date!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(x.date)||!Number.isFinite(Date.parse(x.date+'T00:00:00Z'))||new Date(x.date+'T00:00:00Z').toISOString().slice(0,10)!==x.date)throw Error('開催日が不正です');
  if(!tracks.includes(x.track)||!Number.isInteger(x.race)||x.race<1||x.race>12)throw Error('競馬場・レース番号が不正です');
  if(!Array.isArray(x.horses)||x.horses.length<1||x.horses.length>18)throw Error('出走馬は1〜18頭で指定してください');
  const seen=new Set();
  for(const h of x.horses){
    if(!h||typeof h!=='object'||Array.isArray(h)||!Number.isInteger(h.number)||h.number<1||h.number>18||seen.has(h.number))throw Error('馬番が重複または不正です');
    seen.add(h.number);
    if(typeof h.name!=='string'||!h.name.trim()||h.name.length>100)throw Error('馬名が不正です');
    if(h.scratched!==undefined&&typeof h.scratched!=='boolean')throw Error('取消情報はtrue/falseで指定してください');
    if(h.evaluations!==undefined){
      if(!h.evaluations||typeof h.evaluations!=='object'||Array.isArray(h.evaluations))throw Error(h.number+'番の評価形式が不正です');
      for(const [axis,val] of Object.entries(h.evaluations)){
        if(!axes.includes(axis))throw Error(h.number+'番に未対応の評価項目 '+axis+' があります');
        if(!val||typeof val!=='object'||Array.isArray(val)||!['S','A','B','C'].includes(val.grade)||typeof val.note!=='string'||val.note.trim().length<8||val.note.length>500)throw Error(h.number+'番 '+axis+' はS/A/B/C評価と8文字以上の根拠が必要です');
      }
    }
  }
  return x;
}
function analyzeRacecard(input){
  const x=validateRacecard(input);
  const axes=[{key:'recent',label:'近走',weight:25},{key:'training',label:'調教',weight:25},{key:'course',label:'コース適性',weight:20},{key:'pedigree',label:'血統',weight:15},{key:'pace',label:'展開',weight:15}];
  const points={S:4,A:3,B:2,C:1};
  const active=x.horses.filter(h=>h.scratched!==true).sort((a,b)=>a.number-b.number);
  const missing=active.map(h=>({number:h.number,name:h.name,missing:axes.filter(a=>!h.evaluations?.[a.key]).map(a=>a.label)})).filter(h=>h.missing.length);
  const reasons=[];
  if(active.length<5)reasons.push('出走候補が5頭未満のため、参考フォーメーションは作りません');
  if(missing.length)reasons.push('すべての出走候補に近走・調教・適性・血統・展開の根拠付き評価が必要です');
  if(reasons.length)return {ready:false,active,missing,reasons,ranked:[],formation:null,combinations:[]};
  const ranked=active.map(h=>{
    const score=axes.reduce((sum,a)=>sum+points[h.evaluations[a.key].grade]*a.weight,0)/100;
    const overall=score>=3.55?'S':score>=2.75?'A':score>=1.9?'B':'C';
    return {number:h.number,name:h.name,score:Math.round(score*100)/100,overall,evaluations:h.evaluations};
  }).sort((a,b)=>b.score-a.score||a.number-b.number);
  if(ranked[0].score-ranked[ranked.length-1].score<0.35){
    return {ready:false,active,missing:[],reasons:['全馬の評価差が小さく、馬番順の便宜的な順位で買い目を作らないため見送り'],ranked,formation:null,combinations:[]};
  }
  const first=ranked.slice(0,2).map(h=>h.number);
  const second=ranked.slice(0,5).map(h=>h.number);
  const third=ranked.slice(0,7).map(h=>h.number);
  const combinations=[];
  for(const a of first)for(const b of second)for(const c of third){
    if(a!==b&&b!==c&&a!==c)combinations.push([a,b,c]);
  }
  if(combinations.length>48)throw Error('3連単の上限48点を超えています');
  return {ready:true,active,missing:[],reasons:[],ranked,formation:{first,second,third},combinations};
}
root.KeibaNineRacecard={validateRacecard,analyzeRacecard};
})(window);
