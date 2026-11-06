/* Local-only factor notes: persistence permitted only for private score drafts. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('/tmp/keiba-owner-scorecard.js','utf8');
function boot(decision=true,saved={},hash=''){
 const nodes=new Map(),links=[],alerts=[],writes=[],cleared=[],tempWrites=[];
 const tempStore=new Map();
 const store=new Map(Object.entries(saved).map(([k,v])=>[k,JSON.stringify(v)]));
 const NOTE='keiba-nine-owner-factor-notes-v1';
 const localStorage={getItem:k=>store.get(k)||null,setItem:(k,v)=>{if(k!==NOTE)throw Error('Unexpected write: '+k);writes.push(k);store.set(k,v)}};
 const sessionStorage={getItem:k=>tempStore.get(k)||null,setItem:(k,v)=>{tempWrites.push(k);tempStore.set(k,v)},removeItem:k=>tempStore.delete(k)};
 function element(tag='div'){
  return {tag,value:'',textContent:'',className:'',disabled:false,children:[],
   attributes:{},setAttribute(k,v){this.attributes[k]=v},
   onclick:null,onchange:null,oninput:null,append(...c){this.children.push(...c)},
   replaceChildren(...c){this.children=[...c]}};
 }
 function get(id){
  if(!nodes.has(id)){
   const el=element();
   if(id==='scoreHandoff')el.disabled=true;
   nodes.set(id,el);
  }
  return nodes.get(id);
 }
 const ctx={
  document:{getElementById:get,createElement:element},window:{
    location:{hash,pathname:'/my-scorecard',search:'',assign:url=>links.push(url)},
    history:{replaceState:(...args)=>cleared.push(args[2])}
  },
  Date,JSON,Set,Map,Object,String,Number,Error,URLSearchParams,localStorage,sessionStorage,
  confirm:()=>decision,console
 };
 vm.runInNewContext(source,ctx);
 return {el:get,links,alerts,writes,store,cleared,tempStore,tempWrites};
}
const fixture=[
 '① 架空馬A S S A A S',
 '② 架空馬B A S S B A',
 '③ 架空馬C A A S A B',
 '④ 架空馬D A B A S A',
 '⑤ 架空馬E B A A B A',
 '⑥ 架空馬F B B B A A',
 '⑦ 架空馬G B B B B B',
 '⑧ 架空馬H C B B B C'
].join('\n');
const a=boot(),e=a.el;
assert.equal(e('scoreHandoff').disabled,true);
e('scoreDate').value='2099-01-09';e('scoreTrack').value='東京';e('scoreRace').value='11';
e('scoreInput').value=fixture;e('scoreReview').onclick();
assert.equal(e('scoreRanks').children.length,8,'all 8 scored and ranked');
assert.match(e('scoreRanks').children[0].children[0].textContent,/位.*番.*総合[SABC].*点/);
assert.ok(e('scoreRanks').children.every(r=>r.children[1].textContent.includes('調教')));
assert.match(e('scoreFormation').textContent,/36点／100円なら3,600円/);
assert.equal(e('scoreHandoff').disabled,false);
assert.equal(e('scoreWinnerReview').children.length,1,'winner-review controls appear after valid 5-factor calculation');
assert.match(e('scoreWinnerReview').children[0].children[5].textContent,/総合5位・5番/);
assert.match(e('scoreWinnerReview').children[0].children[5].textContent,/A以上の材料/);
const validated=e('scoreFormation').textContent;
e('scoreHandoff').onclick();
assert.equal(a.links.length,1,'explicit handoff only');
assert.ok(a.links[0].startsWith('/my-tickets#import=v1&'));
const params=new URLSearchParams(a.links[0].split('#')[1]);
assert.equal(params.get('date'),'2099-01-09');
assert.equal(params.get('track'),'東京');
assert.equal(params.get('race'),'11');
for(const k of ['first','second','third']){
 assert.match(params.get(k),/^(?:[1-9]|1[0-8])(?:,(?:[1-9]|1[0-8]))*$/);
}
assert.equal(params.get('first').split(',').length,2);
assert.equal(params.get('second').split(',').length,4);
assert.equal(params.get('third').split(',').length,8);
assert.ok(!a.links[0].includes('架空馬'),'source member/horse text excluded from URL');
assert.ok(!a.links[0].includes('調教'));
for(const [name,invalid] of [
 ['duplicate horse number',fixture.replace('⑧ 架空馬H','① 架空馬H')],
 ['invalid grade',fixture.replace('架空馬B A S S','架空馬B Z S S')],
 ['less than three',fixture.split('\n').slice(0,2).join('\n')],
 ['19th horse',fixture.replace('⑧ 架空馬H','19 架空馬H')],
 ['wrong columns',fixture.replace('架空馬F B B B A A','架空馬F B B A A')],
 ['duplicate horse name',fixture.replace('架空馬H C B','架空馬A C B')],
 ['HTML tokens',fixture.replace('架空馬A S S','<img> S S')]
]){
 e('scoreInput').value=invalid;
 e('scoreReview').onclick();
 assert.equal(e('scoreHandoff').disabled,true,name+' cannot handoff');
 assert.equal(e('scoreRanks').children.length,0,name+' cannot render partial ranks');
 assert.equal(e('scoreWinnerReview').children.length,0,name+' cannot leave stale win buttons');
 assert.match(e('scoreStatus').textContent,/計算できません/,name+' must explain failure');
}
e('scoreInput').value=fixture;e('scoreReview').onclick();
assert.equal(e('scoreHandoff').disabled,false);
e('scoreInput').value=fixture+' ';
e('scoreHandoff').onclick();
assert.equal(a.links.length,1,'modified input cannot reuse stale scoring');
assert.equal(e('scoreHandoff').disabled,true);
e('scoreInput').value=fixture;e('scoreReview').onclick();
e('scoreRace').value='12';e('scoreRace').onchange();
assert.equal(e('scoreHandoff').disabled,true,'venue selection changes invalidate review');
const decline=boot(false),d=decline.el;
d('scoreDate').value='2099-01-09';d('scoreTrack').value='東京';d('scoreRace').value='11';
d('scoreInput').value=fixture;d('scoreReview').onclick();d('scoreHandoff').onclick();
assert.equal(decline.links.length,0,'cancel does not navigate');
const tiny=boot(),t=tiny.el;
t('scoreDate').value='2099-01-09';t('scoreTrack').value='京都';t('scoreRace').value='2';
t('scoreInput').value=[
 '1 C C C C C','2 C C C C C','3 C C C C C'].join('\n');
t('scoreReview').onclick();
assert.match(t('scoreFormation').textContent,/4点/,'3 competitors do not pad to 30-40');
assert.match(t('scoreFormation').textContent,/70点未満/,'weak top score is explicitly flagged');
assert.match(t('scoreRanks').children[0].children[0].textContent,/1位　1番/,'ties use number order');
assert.ok(!source.includes('fetch('),'never transmit grades or horse data');
assert.ok(!source.includes('localStorage.setItem(MAIL'),'never overwrite imported mail');
assert.ok(!source.includes('localStorage.setItem(MEMO'),'never overwrite mapped numbers');
assert.ok(!source.includes('innerHTML'),'render only safe textContent');

// JRDB provisional mail + owner-typed number mapping are read-only references.
const roster=[
 '架空馬A','架空馬B','架空馬C','架空馬D',
 '架空馬E','架空馬F','架空馬G','架空馬H'
];
const sourceRace={race:11,postTime:'15:35',expected:8,horses:roster};
const snapshot=JSON.stringify([sourceRace.postTime,sourceRace.expected,sourceRace.horses]);
const numbered=roster.map((name,index)=>({number:index+1,name}));
const meeting={kind:'jrdb-provisional',date:'2099-01-09',track:'東京',races:[sourceRace]};
const memo={date:'2099-01-09',track:'東京',race:11,sourceMark:snapshot,rows:numbered};
const MAIL='keiba-nine-jrdb-personal-mail-v1',MEMO='keiba-nine-owner-manual-numbers-v1';
const owned=boot(true,{[MAIL]:[meeting],[MEMO]:[memo]}),o=owned.el;
o('scoreDate').value='2099-01-09';o('scoreTrack').value='東京';o('scoreRace').value='11';
o('scoreFromMemo').onclick();
assert.equal(o('scoreMemoGrid').children.length,8,'render exactly 8 mapped horses');
assert.match(o('scoreMemoStatus').textContent,/未評価40項目/);
assert.match(o('scoreInput').value,/^1 架空馬A \? \? \? \? \?/);
o('scoreReview').onclick();
assert.equal(o('scoreHandoff').disabled,true,'no artificial grades for unassessed horses');
assert.match(o('scoreStatus').textContent,/計算できません/);
const exampleGrades=[
 ['S','S','A','A','S'],['A','S','S','B','A'],
 ['A','A','S','A','B'],['A','B','A','S','A'],
 ['B','A','A','B','A'],['B','B','B','A','A'],
 ['B','B','B','B','B'],['C','B','B','B','C']
];
for(let i=0;i<8;i++)for(let j=0;j<5;j++){
 const menu=o('scoreMemoGrid').children[i].children[1].children[j].children[0];
 menu.value=exampleGrades[i][j];menu.onchange();
}
assert.match(o('scoreMemoStatus').textContent,/未評価0項目/);
assert.ok(!o('scoreInput').value.includes('?'));
o('scoreReview').onclick();
assert.equal(o('scoreRanks').children.length,8);
assert.match(o('scoreFormation').textContent,/36点／100円なら3,600円/);
o('scoreHandoff').onclick();
assert.equal(owned.links.length,1,'owner grades hand off only after explicit confirmation');
assert.ok(!owned.links[0].includes('架空馬'));
assert.ok(owned.writes.length>0,'partial score notes are saved after grade selection');
assert.ok(owned.writes.every(x=>x==='keiba-nine-owner-factor-notes-v1'),'never mutate mail, mapping, draft or actual purchases');
const savedMeeting=owned.store.get(MAIL);
owned.store.set(MAIL,JSON.stringify([{...meeting,races:[{...sourceRace,postTime:'15:36'}]}]));
o('scoreHandoff').onclick();
assert.equal(owned.links.length,1,'changed provisional mail blocks repeat handoff');
assert.equal(o('scoreHandoff').disabled,true);
assert.match(o('scoreStatus').textContent,/引き継ぎ停止/);
o('scoreReview').onclick();
assert.equal(o('scoreHandoff').disabled,true,'changed source blocks recalculation on an imported roster');
assert.match(o('scoreStatus').textContent,/計算できません/);
owned.store.set(MAIL,savedMeeting);
o('scoreReview').onclick();
assert.equal(o('scoreHandoff').disabled,false,'still-valid source may be reviewed again');
o('scoreRace').value='12';o('scoreRace').onchange();
assert.equal(o('scoreMemoGrid').children.length,0,'changing race clears source-specific controls');
assert.equal(o('scoreHandoff').disabled,true);
const stale=boot(true,{[MAIL]:[meeting],[MEMO]:[{...memo,sourceMark:'old-source'}]});
stale.el('scoreDate').value='2099-01-09';
stale.el('scoreTrack').value='東京';stale.el('scoreRace').value='11';
stale.el('scoreFromMemo').onclick();
assert.equal(stale.el('scoreMemoGrid').children.length,0);
assert.match(stale.el('scoreMemoStatus').textContent,/読み込めません/);
const duplicate=boot(true,{[MAIL]:[meeting],[MEMO]:[{...memo,rows:[
 {...numbered[0]}, {...numbered[1],number:1},...numbered.slice(2)
]}]});
duplicate.el('scoreDate').value='2099-01-09';
duplicate.el('scoreTrack').value='東京';duplicate.el('scoreRace').value='11';
duplicate.el('scoreFromMemo').onclick();
assert.equal(duplicate.el('scoreMemoGrid').children.length,0,'duplicate number cannot import');
assert.match(duplicate.el('scoreMemoStatus').textContent,/読み込めません/);
const denied=boot(false,{[MAIL]:[meeting],[MEMO]:[memo]});
denied.el('scoreDate').value='2099-01-09';
denied.el('scoreTrack').value='東京';denied.el('scoreRace').value='11';
denied.el('scoreInput').value=fixture;
denied.el('scoreFromMemo').onclick();
assert.equal(denied.el('scoreInput').value,fixture,'cancel must not erase existing manual grades');
assert.equal(denied.el('scoreMemoGrid').children.length,0);


// Client-only selection deep link from the ticket notebook never carries horse records.
const chosen=boot(true,{},'#select=v1&date=2026-11-07&track=%E4%BA%AC%E9%83%BD&race=9');
assert.equal(chosen.el('scoreDate').value,'2026-11-07');
assert.equal(chosen.el('scoreTrack').value,'京都');
assert.equal(chosen.el('scoreRace').value,'9');
assert.match(chosen.el('scoreStatus').textContent,/選択/);
assert.deepEqual(chosen.cleared,['/my-scorecard'],'remove selection fragment immediately');
const invalidLink=boot(true,{},'#select=v1&date=2026-11-07&track=%E4%BA%AC%E9%83%BD&race=9&horses=secret');
assert.match(invalidLink.el('scoreStatus').textContent,/受け取れませんでした/);
assert.deepEqual(invalidLink.cleared,['/my-scorecard']);
assert.equal(invalidLink.el('scoreTrack').value,'','never trust arbitrary fragments');


// Partial manual assessments auto-save per race and resume after iPhone relaunch.
const NOTES='keiba-nine-owner-factor-notes-v1';
const fresh=boot(),fr=fresh.el;
fr('scoreDate').value='2026-11-07';
fr('scoreTrack').value='京都';fr('scoreRace').value='3';
fr('scoreInput').value='① 架空X A ? B ? S\n② 架空Y ? ? ? ? ?';
fr('scoreInput').oninput();
const savedNotes=JSON.parse(fresh.store.get(NOTES));
assert.equal(savedNotes.length,1);
assert.equal(savedNotes[0].date,'2026-11-07');
assert.equal(savedNotes[0].text,fr('scoreInput').value);
assert.equal(savedNotes[0].sourceMark,null);
assert.ok(fresh.writes.every(k=>k===NOTES));
const restored=boot(true,{[NOTES]:savedNotes}),rs=restored.el;
rs('scoreDate').value='2026-11-07';rs('scoreTrack').value='京都';rs('scoreRace').value='3';
rs('scoreRace').onchange();
assert.equal(rs('scoreInput').value,fr('scoreInput').value);
assert.equal(rs('scoreRaceGrid').children.length,12,'12R buttons for selected venue');
assert.match(rs('scoreDayStatus').textContent,/途中1R／要再確認0R／未着手11R/);
assert.match(rs('scoreRaceGrid').children[2].textContent,/3R　途中/);
assert.equal(rs('scoreRaceGrid').children[2].attributes['aria-pressed'],'true');
assert.match(rs('scoreDraftStatus').textContent,/途中評価を端末から復元/);
rs('scoreRaceGrid').children[3].onclick();
assert.equal(rs('scoreRace').value,'4','grid navigates to chosen R');
assert.equal(rs('scoreInput').value,'','other race cannot inherit previous scores');
assert.match(rs('scoreDayStatus').textContent,/途中1R/);
rs('scoreRace').value='3';rs('scoreRace').onchange();
assert.equal(rs('scoreInput').value,fr('scoreInput').value);
const afterSaved=rs('scoreInput').value;
rs('scoreClearDraft').onclick();
assert.equal(rs('scoreInput').value,'');
assert.equal(JSON.parse(restored.store.get(NOTES)).length,0);
assert.match(rs('scoreDraftStatus').textContent,/削除しました/);
assert.match(rs('scoreRaceGrid').children[2].textContent,/3R　未着手/);
const canDelete=boot(false,{[NOTES]:savedNotes});
canDelete.el('scoreDate').value='2026-11-07';
canDelete.el('scoreTrack').value='京都';canDelete.el('scoreRace').value='3';
canDelete.el('scoreRace').onchange();
canDelete.el('scoreClearDraft').onclick();
assert.equal(canDelete.el('scoreInput').value,afterSaved,'cancel deletion preserves draft');
assert.equal(JSON.parse(canDelete.store.get(NOTES)).length,1);
// Graded memo notes restore selectors with the user's original per-horse values.
const savedMemberNotes=JSON.parse(owned.store.get(NOTES));
assert.equal(savedMemberNotes.length,1);
assert.equal(savedMemberNotes[0].sourceMark,snapshot);
const resumed=boot(true,{[MAIL]:[meeting],[MEMO]:[memo],[NOTES]:savedMemberNotes});
resumed.el('scoreDate').value='2099-01-09';
resumed.el('scoreTrack').value='東京';resumed.el('scoreRace').value='11';
resumed.el('scoreRace').onchange();
assert.equal(resumed.el('scoreMemoGrid').children.length,8);
assert.equal(resumed.el('scoreMemoGrid').children[0].children[1].children[0].children[0].value,'S');
assert.match(resumed.el('scoreDraftStatus').textContent,/復元/);
resumed.el('scoreReview').onclick();
assert.match(resumed.el('scoreFormation').textContent,/36点/);
assert.match(resumed.el('scoreRaceGrid').children[10].textContent,/11R　採点済/);
assert.match(resumed.el('scoreDayStatus').textContent,/採点済1R／途中0R／要再確認0R/);
const changedMeeting={...meeting,races:[{...sourceRace,postTime:'15:36'}]};
const staleDraft=boot(true,{[MAIL]:[changedMeeting],[MEMO]:[memo],[NOTES]:savedMemberNotes});
staleDraft.el('scoreDate').value='2099-01-09';
staleDraft.el('scoreTrack').value='東京';staleDraft.el('scoreRace').value='11';
staleDraft.el('scoreRace').onchange();
assert.equal(staleDraft.el('scoreInput').value,'');
assert.equal(staleDraft.el('scoreMemoGrid').children.length,0);
assert.match(staleDraft.el('scoreDraftStatus').textContent,/復元できません/);
assert.match(staleDraft.el('scoreRaceGrid').children[10].textContent,/11R　要再確認/);
assert.match(staleDraft.el('scoreDayStatus').textContent,/要再確認1R/);
assert.equal(JSON.parse(staleDraft.store.get(NOTES)).length,1,'keep stale draft in storage');
const broken=boot(true,{[NOTES]:[{...savedNotes[0],race:13}]});
broken.el('scoreDate').value='2026-11-07';
broken.el('scoreTrack').value='京都';broken.el('scoreRace').value='3';
broken.el('scoreInput').value='① 仮想馬A A A A A A';
broken.el('scoreInput').oninput();
assert.match(broken.el('scoreDraftStatus').textContent,/保存に失敗/);
assert.equal(JSON.parse(broken.store.get(NOTES))[0].race,13,'invalid storage not overwritten');



// Explicit optional re-review of 3rd–5th place horses never auto-selects
// winners. Added winner replaces no ranked horse; 3rd entries are narrowed
// until the number of distinct permutations is <=40.
const win=boot(),we=win.el;
we('scoreDate').value='2026-11-07';we('scoreTrack').value='東京';we('scoreRace').value='4';
we('scoreInput').value=fixture;we('scoreReview').onclick();
const review=we('scoreWinnerReview').children[0];
assert.equal(review.children.length,7);
assert.equal(review.children[2].attributes['aria-pressed'],'true');
assert.match(review.children[5].textContent,/総合5位・5番/);
assert.match(review.children[5].textContent,/近走・適性・展開/);
review.children[5].onclick();
assert.match(we('scoreStatus').textContent,/5番を1着候補に追加/);
assert.match(we('scoreFormation').textContent,/1着 1・2・5／2着 1・2・3・4／3着 1・2・3・4・5・6/);
assert.match(we('scoreFormation').textContent,/40点／100円なら4,000円/);
assert.equal(we('scoreWinnerReview').children[0].children[5].attributes['aria-pressed'],'true');
assert.equal(we('scoreHandoff').disabled,false);
we('scoreHandoff').onclick();
assert.equal(win.links.length,1,'selected 5th place remains explicit owner decision');
const changedWinner=new URLSearchParams(win.links[0].split('#')[1]);
assert.equal(changedWinner.get('first'),'1,2,5');
assert.equal(changedWinner.get('second'),'1,2,3,4');
assert.equal(changedWinner.get('third'),'1,2,3,4,5,6');
assert.ok(!win.links[0].includes('架空馬'));
assert.equal(win.tempWrites.length,0,'winner-choice selection never changes bulk transfer or saved tickets');
we('scoreWinnerReview').children[0].children[2].onclick();
assert.match(we('scoreFormation').textContent,/1着 1・2／2着 1・2・3・4／3着 1・2・3・4・5・6・7・8/);
assert.match(we('scoreFormation').textContent,/36点／100円なら3,600円/);
we('scoreWinnerReview').children[0].children[3].onclick();
assert.match(we('scoreFormation').textContent,/1着 1・2・3／2着 1・2・3・4/);
assert.match(we('scoreFormation').textContent,/36点／100円なら3,600円/);
we('scoreInput').value=fixture+'\n';
we('scoreInput').oninput();
assert.equal(we('scoreHandoff').disabled,true,'edited grade invalidates selected third winner');
assert.equal(we('scoreWinnerReview').children.length,0,'winner controls cannot persist after source change');
const notEnough=boot(),me=notEnough.el;
me('scoreDate').value='2026-11-07';me('scoreTrack').value='東京';me('scoreRace').value='1';
me('scoreInput').value='1 C C C C C\n2 C C C C C\n3 C C C C C';
me('scoreReview').onclick();
assert.equal(me('scoreWinnerReview').children[0].children.length,4,'3-runner race offers no rank 4 or 5');
me('scoreWinnerReview').children[0].children[3].onclick();
assert.match(me('scoreFormation').textContent,/4点／100円なら400円/,'no padding of short races');
assert.match(me('scoreFormation').textContent,/最高評価でも70点未満/);

// The saved 5-factor notes can now be compiled for an entire meeting date,
// but only complete, non-stale assessments may enter the temporary batch.
const dayNote=(track,race,text,sourceMark=null)=>({
 date:'2026-11-07',track,race,text,sourceMark,savedAt:'2026-11-06T00:00:00.000Z'
});
const dayNotes=[
 dayNote('東京',11,fixture),
 dayNote('京都',2,['1 C C C C C','2 C C C C C','3 C C C C C'].join('\n')),
 dayNote('京都',3,'1 ? ? ? ? ?\n2 ? ? ? ? ?\n3 ? ? ? ? ?'),
 dayNote('京都',4,fixture,'obsolete-provisional-source'),
];
const batch=boot(true,{[NOTES]:dayNotes}),be=batch.el;
be('scoreDate').value='2026-11-07';be('scoreTrack').value='東京';be('scoreRace').value='11';
be('scoreDayBuild').onclick();
assert.equal(be('scoreDayBatchPreview').children.length,2,'partial and stale scores excluded');
assert.equal(be('scoreDayBatchPreview').children[0].children[3].children.length,9,
 'each race exposes all 8 ranked horses when explicitly expanded');
assert.match(be('scoreDayBatchPreview').children[0].children[3].children[0].textContent,/全馬の総合評価順/);
assert.match(be('scoreDayBatchPreview').children[0].children[3].children[1].textContent,/1位.*総合S/);
assert.match(be('scoreDayBatchPreview').children[0].children[3].children[1].className,/score-s/);
assert.ok(be('scoreDayBatchPreview').children[0].children[3].children.some(x=>/score-a/.test(x.className)),
 'A-ranked horses are presented with existing red class');
assert.equal(be('scoreDayTransfer').disabled,false,'complete, saved grades are transferable');
assert.match(be('scoreDayBatchPreview').children[0].children[2].textContent,/1着候補の再点検/);
assert.match(be('scoreDayBatchPreview').children[0].children[2].textContent,/5位5番/);
assert.match(be('scoreDayBatchText').value,/1着：1・2/,'re-review does not automatically override first two in bulk');
assert.match(be('scoreDayBatchStatus').textContent,/2Rの手動採点を一括計算／40点/);
assert.match(be('scoreDayBatchStatus').textContent,/除外：京都3R：途中／京都4R：要再確認/);
assert.match(be('scoreDayBatchText').value,/2026-11-07 東京11R\n1着：/);
assert.match(be('scoreDayBatchText').value,/2026-11-07 京都2R\n1着：/);
assert.equal(be('scoreDayBatchText').value.trim().split(/\n/).filter(x=>x.includes('着：')).length,6);
assert.equal(batch.writes.length,0,'batch must not persist any ticket or rewrite score notes');
be('scoreDayTransfer').onclick();
assert.equal(batch.links.length,1);
assert.equal(batch.links[0],'/my-tickets#scorebatch=v1','never put ranks in URL');
const transferKey='keiba-nine-scorecard-bulk-transfer-v1';
assert.deepEqual(Array.from(batch.tempWrites),[transferKey]);
const transfer=JSON.parse(batch.tempStore.get(transferKey));
assert.equal(transfer.version,'scorecard-bulk-v1');
assert.equal(transfer.date,'2026-11-07');
assert.equal(transfer.count,2);
assert.equal(transfer.points,40);
assert.match(transfer.text,/東京11R/);
assert.ok(!transfer.text.includes('架空馬'),'only numerical formations travel');
assert.ok(!transfer.text.includes('調教'),'no grades in handoff payload');
assert.equal(batch.writes.length,0,'transfer never saves purchased or draft tickets');
const altered=boot(true,{[NOTES]:dayNotes}),ae=altered.el;
ae('scoreDate').value='2026-11-07';ae('scoreDayBuild').onclick();
const changedNotes=dayNotes.map(n=>n.race===11?{...n,text:n.text.replace('架空馬A S S','架空馬A C C')}:n);
altered.store.set(NOTES,JSON.stringify(changedNotes));
ae('scoreDayTransfer').onclick();
assert.equal(altered.links.length,0,'newer score entries block stale preview transfer');
assert.equal(altered.tempWrites.length,0);
assert.equal(ae('scoreDayTransfer').disabled,true);
assert.match(ae('scoreDayBatchStatus').textContent,/更新されています/);
const notApproved=boot(false,{[NOTES]:dayNotes}),ne=notApproved.el;
ne('scoreDate').value='2026-11-07';ne('scoreDayBuild').onclick();ne('scoreDayTransfer').onclick();
assert.equal(notApproved.links.length,0,'user declined navigation');
assert.equal(notApproved.tempWrites.length,0);
const noComplete=boot(true,{[NOTES]:[dayNotes[2],dayNotes[3]]}),nc=noComplete.el;
nc('scoreDate').value='2026-11-07';nc('scoreDayBuild').onclick();
assert.equal(nc('scoreDayTransfer').disabled,true);
assert.match(nc('scoreDayBatchStatus').textContent,/完成したレースはありません/);
const all36=['福島','東京','京都'].flatMap(track=>
 Array.from({length:12},(_,i)=>dayNote(track,i+1,fixture)));
const maxBatch=boot(true,{[NOTES]:all36}),mb=maxBatch.el;
mb('scoreDate').value='2026-11-07';mb('scoreDayBuild').onclick();
assert.equal(mb('scoreDayBatchPreview').children.length,36,'three venues times 12 races');
assert.match(mb('scoreDayBatchStatus').textContent,/36Rの手動採点を一括計算／1296点/);
assert.equal((mb('scoreDayBatchText').value.match(/^2026-11-07 /gm)||[]).length,36);
assert.ok(mb('scoreDayBatchText').value.length<25000);
assert.equal(mb('scoreDayTransfer').disabled,false);
const overflow=boot(true,{[NOTES]:[...all36,dayNote('中山',1,fixture)]}),ov=overflow.el;
ov('scoreDate').value='2026-11-07';ov('scoreDayBuild').onclick();
assert.equal(ov('scoreDayTransfer').disabled,true,'more than 36 must not silently truncate');
assert.match(ov('scoreDayBatchStatus').textContent,/36Rを超えています/);
const invalidateBatch=boot(true,{[NOTES]:dayNotes}),ib=invalidateBatch.el;
ib('scoreDate').value='2026-11-07';ib('scoreDayBuild').onclick();
ib('scoreDate').value='2026-11-08';ib('scoreDate').onchange();
assert.equal(ib('scoreDayTransfer').disabled,true);
assert.equal(ib('scoreDayBatchText').value,'');

console.log('Owner manual 5-factor scoring: 36-point ranks, validation, cancel, no-network handoff PASS');
