/* Local-only factor notes: persistence permitted only for private score drafts. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('/tmp/keiba-owner-scorecard.js','utf8');
function boot(decision=true,saved={},hash='',researchHandoff=null,stagedUnsavedResearch=false){
 const nodes=new Map(),links=[],alerts=[],writes=[],cleared=[],tempWrites=[];
 const tempStore=new Map(researchHandoff?[[
  'keiba-nine-owner-research-scorecard-handoff-v1',JSON.stringify(researchHandoff)
 ]]:[]);
 const store=new Map(Object.entries(saved).map(([k,v])=>[k,JSON.stringify(v)]));
 const NOTE='keiba-nine-owner-factor-notes-v1';
 const storageBehavior={failWrites:false};
 const localStorage={getItem:k=>store.get(k)||null,setItem:(k,v)=>{if(k!==NOTE)throw Error('Unexpected write: '+k);if(storageBehavior.failWrites)throw Error('Storage quota exceeded');writes.push(k);store.set(k,v)}};
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
 const runSource=stagedUnsavedResearch?source.replace('receiveResearchPrefill();',
  "$('scoreDate').value='2026-11-07';$('scoreTrack').value='京都';"+
  "$('scoreRace').value='1';changeScoreRace();"+
  "$('scoreInput').value='1 UNSAVED ? ? ? ? ?';receiveResearchPrefill();"):source;
 vm.runInNewContext(runSource,ctx);
 return {el:get,links,alerts,writes,store,cleared,tempStore,tempWrites,storageBehavior};
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
assert.equal(me('scoreWinnerReview').children[0].children.length,5,'3-runner race offers only rank 3 (plus reset)');
me('scoreWinnerReview').children[0].children[3].onclick();
assert.match(me('scoreFormation').textContent,/6点／100円なら600円/,'3 heads are 6 permutations, not padded to 30');
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
// Independently override a selected day-batch first candidate (5th place).
// Existing saved grades and tickets must remain unchanged until later explicit save.
const custom=boot(true,{[NOTES]:dayNotes}),bc=custom.el;
bc('scoreDate').value='2026-11-07';bc('scoreTrack').value='東京';
bc('scoreDayBuild').onclick();
const Tokyo=bc('scoreDayBatchPreview').children[0];
assert.equal(Tokyo.children[4].children.length,5,'summary, default and ranks 3–5');
assert.equal(Tokyo.children[4].children[1].attributes['aria-pressed'],'true');
assert.match(Tokyo.children[4].children[4].textContent,/総合5位 5番を1着に追加/);
Tokyo.children[4].children[4].onclick();
assert.match(bc('scoreDayBatchText').value,/東京11R\n1着：1・2・5\n2着：1・2・3・4\n3着：1・2・3・4・5・6/);
assert.match(bc('scoreDayBatchStatus').textContent,/44点、100円換算4,400円/);
assert.match(bc('scoreDayBatchPreview').children[0].children[0].textContent,/東京11R｜40点/);
assert.equal(bc('scoreDayBatchPreview').children[0].children[4].children[4].attributes['aria-pressed'],'true');
assert.equal(custom.writes.length,0,'reviewing winner did not save grade or actual ticket');
bc('scoreDayTransfer').onclick();
assert.equal(custom.links.length,1,'custom batch can safely transfer after source revalidation');
const customPayload=JSON.parse(custom.tempStore.get(transferKey));
assert.equal(customPayload.points,44);
assert.match(customPayload.text,/東京11R\n1着：1・2・5/);
assert.ok(!JSON.stringify(customPayload).includes('架空馬'),'personal private names excluded');
assert.ok(!JSON.stringify(customPayload).includes('調教'));
const changedDay=boot(true,{[NOTES]:dayNotes}),dy=changedDay.el;
dy('scoreDate').value='2026-11-07';dy('scoreDayBuild').onclick();
changedDay.store.set(NOTES,JSON.stringify(dayNotes.map(n=>
 n.race===11?{...n,text:n.text.replace('架空馬A S S','架空馬A C C')}:n)));
dy('scoreDayBatchPreview').children[0].children[4].children[4].onclick();
assert.equal(dy('scoreDayTransfer').disabled,true,'changed note blocks old winner choice');
assert.match(dy('scoreDayBatchStatus').textContent,/元データが変更/);
assert.equal(changedDay.tempWrites.length,0);
const resetDay=boot(true,{[NOTES]:dayNotes}),rd=resetDay.el;
rd('scoreDate').value='2026-11-07';rd('scoreDayBuild').onclick();
rd('scoreDayBatchPreview').children[0].children[4].children[4].onclick();
rd('scoreDayBatchPreview').children[0].children[4].children[1].onclick();
assert.match(rd('scoreDayBatchStatus').textContent,/40点、100円換算4,000円/);
assert.match(rd('scoreDayBatchText').value,/東京11R\n1着：1・2\n2着：1・2・3・4\n3着：1・2・3・4・5・6・7・8/);

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


// Two JRDB-derived *provisional* grades may be copied into an incomplete
// manual scorecard after a deliberate owner action. Never infer the other 3.
const researchPayload={
 version:'jrdb-research-to-scorecard-v1',createdAt:new Date().toISOString(),
 date:'2026-11-07',track:'東京',race:6,researchOnly:true,
 officialJraVerified:false,predictionReady:false,
 runners:[
  {number:1,training:'S',recent:'A'},
  {number:2,training:'A',recent:'未評価'},
  {number:3,training:'未評価',recent:'B'},
 ],
};
const research=boot(true,{},'#research=v1',researchPayload),re=research.el;
assert.equal(re('scoreDate').value,'2026-11-07');
assert.equal(re('scoreTrack').value,'東京');
assert.equal(re('scoreRace').value,'6');
assert.equal(re('scoreMemoGrid').children.length,3);
assert.equal(re('scoreInput').value,
 '1  S A ? ? ?\n2  A ? ? ? ?\n3  ? B ? ? ?');
assert.match(re('scoreMemoStatus').textContent,/JRDB研究用・未検証/);
assert.equal(re('scoreHandoff').disabled,true,'incomplete research grades cannot propose any ticket');
re('scoreReview').onclick();
assert.equal(re('scoreHandoff').disabled,true,'three blank factors block ranking');
assert.match(re('scoreStatus').textContent,/計算できません/);
assert.equal(research.tempStore.size,0,'one-time provisional data consumed and deleted');
assert.deepEqual(research.cleared,['/my-scorecard'],'clear one-time URL token');
const researchNote=JSON.parse(research.store.get(NOTES));
assert.equal(researchNote.length,1,'consented incomplete draft is saved only to score notes');
assert.match(researchNote[0].text,/1  S A \? \? \?/);
assert.equal(researchNote[0].sourceMark,null);
assert.equal(researchNote[0].researchSource,'jrdb-two-factor-research-v1','unverified research provenance persists in note');
assert.ok(research.writes.every(k=>k===NOTES),'never write actual ticket or purchased ledgers');
assert.equal(research.links.length,0);
// A research transfer to Tokyo 6R must NOT erase an unsaved edit in Kyoto
// 1R. The target-replacement confirmation is not consent to lose source work.
const blockedResearch=boot(true,{},'#research=v1',researchPayload,true),brr=blockedResearch.el;
assert.equal(brr('scoreTrack').value,'京都');
assert.equal(brr('scoreRace').value,'1');
assert.equal(brr('scoreInput').value,'1 UNSAVED ? ? ? ? ?');
assert.equal(blockedResearch.writes.length,0,'no cross-race write when source input is unsaved');
assert.match(brr('scoreMemoStatus').textContent,/未保存の評価/);
assert.equal(blockedResearch.tempStore.size,0,'failed handoff never lingers in one-use session storage');
const afterResearch=boot(true,{[NOTES]:researchNote}),ar=afterResearch.el;
ar('scoreDate').value='2026-11-07';ar('scoreTrack').value='東京';
ar('scoreRace').value='6';ar('scoreRace').onchange();
assert.equal(ar('scoreMemoGrid').children.length,3,
 'research-derived incomplete grades reopen editable dropdowns after iPhone relaunch');
assert.equal(ar('scoreMemoGrid').children[0].children[1].children[0].children[0].value,'S');
assert.equal(ar('scoreMemoGrid').children[0].children[1].children[1].children[0].value,'A');
assert.equal(ar('scoreMemoGrid').children[0].children[1].children[2].children[0].value,'');
assert.match(ar('scoreInput').value,/\? \? \?/);
assert.equal(ar('scoreHandoff').disabled,true);
assert.match(ar('scoreDraftStatus').textContent,/JRDB研究用の未検証2項目/);

for(const [title,bad] of [
 ['injected names',{...researchPayload,runners:[{...researchPayload.runners[0],name:'SECRET'},...researchPayload.runners.slice(1)]}],
 ['false official verification',{...researchPayload,officialJraVerified:true}],
 ['finished prediction',{...researchPayload,predictionReady:true}],
 ['unknown grade',{...researchPayload,runners:[{...researchPayload.runners[0],training:'Z'},...researchPayload.runners.slice(1)]}],
 ['duplicate number',{...researchPayload,runners:[researchPayload.runners[0],researchPayload.runners[0],researchPayload.runners[2]]}],
 ['expired',{...researchPayload,createdAt:'2020-01-01T00:00:00Z'}],
 ['no assessed factors',{...researchPayload,runners:researchPayload.runners.map(x=>({...x,training:'未評価',recent:'未評価'}))}],
]){
 const x=boot(true,{},'#research=v1',bad),q=x.el;
 assert.equal(x.writes.length,0,title+' must not save anything');
 assert.equal(q('scoreMemoGrid').children.length,0,title+' must not render untrusted horse grades');
 assert.match(q('scoreMemoStatus').textContent,/受け取れません/,title+' must explain refusal');
 assert.equal(x.tempStore.size,0,title+' must delete one-time data');
}
const badResearchTag=boot(true,{[NOTES]:[{
 ...researchNote[0],researchSource:'fake-published-verified'
}]}),br=badResearchTag.el;
br('scoreDate').value='2026-11-07';br('scoreTrack').value='東京';
br('scoreRace').value='6';br('scoreRace').onchange();
assert.match(br('scoreDraftStatus').textContent,/復元できません/,'unknown research status rejected');
assert.equal(br('scoreInput').value,'');
const savedResearch={
 date:'2026-11-07',track:'東京',race:6,
 text:'1 C C C C C\n2 C C C C C\n3 C C C C C',
 sourceMark:null,savedAt:new Date().toISOString(),
};
const declinedResearch=boot(false,{[NOTES]:[savedResearch]},'#research=v1',researchPayload),dr=declinedResearch.el;
assert.equal(declinedResearch.writes.length,0,'operator declines to replace existing assessments');
assert.equal(JSON.parse(declinedResearch.store.get(NOTES))[0].text,savedResearch.text);
assert.equal(declinedResearch.tempStore.size,0);
assert.equal(dr('scoreMemoGrid').children.length,0);


{
// The three Saturday venues can be seeded with numbered JRDB pre-day
// rosters in ONE owner action. These remain five-factor UNKNOWN drafts.
const PREDAY='keiba-nine-jrdb-preday-runners-v1';
const fakeRace=(race)=>({race,postTime:'10:00',expected:3,runners:[
 {number:1,name:'架空サクラ'+race,style:'先'},
 {number:2,name:'架空ナイン'+race,style:'逃'},
 {number:3,name:'架空ドリーム'+race,style:'差'}
]});
const predayMeetings=['東京','京都','福島'].map(track=>({
 kind:'jrdb-preday-provisional',date:'2026-11-07',track,
 races:Array.from({length:12},(_,i)=>fakeRace(i+1))
}));
const pd=boot(true,{[PREDAY]:predayMeetings}),pe=pd.el;
assert.equal(pe('scoreDate').value,'2026-11-07',
 'opening manual scorecard chooses upcoming imported meeting date');
assert.equal(pe('scoreTrack').value,'福島',
 'first saved upcoming venue is selected without requiring manual picker');
assert.equal(pe('scoreRace').value,'1');
assert.match(pe('scorePredayStatus').textContent,/自動選択したで/);
assert.equal(pd.writes.length,0,'opening scorecard never seeds or writes notes');
pe('scoreTrialJump').onclick();
assert.equal(pd.links.length,1);
assert.ok(pd.links[0].startsWith('/owner-auto-trial#select=v1&'));
const pilotCoords=new URLSearchParams(pd.links[0].split('#')[1]);
assert.equal(pilotCoords.get('date'),'2026-11-07');
assert.equal(pilotCoords.get('track'),'福島');
assert.equal(pilotCoords.get('race'),'1');
assert.equal(pilotCoords.size,4);
assert.equal(pd.writes.length,0);

assert.equal(pe('scoreHandoff').disabled,true,'no auto-grade or ticket on page open');
pe('scoreDate').value='2026-11-07';pe('scoreTrack').value='東京';pe('scoreRace').value='1';
pe('scoreSeedPredayDay').onclick();
assert.match(pe('scorePredayStatus').textContent,/36Rを馬番だけ仮登録/);
assert.equal(pd.writes.length,1,'all 36R seeded in one atomic note write');
const seeded=JSON.parse(pd.store.get(NOTES));
assert.equal(seeded.length,36);
assert.equal(new Set(seeded.map(n=>n.date+'|'+n.track+'|'+n.race)).size,36);
assert.ok(seeded.every(n=>n.researchSource==='jrdb-preday-roster-v1'&&
 n.sourceMark===null&&typeof n.predaySourceMark==='string'&&
 n.text.split('\n').length===3&&n.text.includes(' ? ? ? ? ?')));
assert.equal(pe('scoreRaceGrid').children.length,12);
assert.match(pe('scoreDayStatus').textContent,/途中12R/);
assert.equal(pe('scoreHandoff').disabled,true,'no grade or ticket invented');
assert.equal(pd.links.length,0,'never transfer tickets on source import');
const guardSeed=boot(true,{[PREDAY]:predayMeetings}),gs=guardSeed.el;
gs('scoreDate').value='2026-11-07';gs('scoreTrack').value='東京';gs('scoreRace').value='1';
gs('scoreRace').onchange();
gs('scoreInput').value=fixture; // failed storage write left this draft only in the editor
gs('scoreSeedPredayDay').onclick();
assert.match(gs('scorePredayStatus').textContent,/未保存の評価/);
assert.equal(guardSeed.store.has(NOTES),false,'bulk pre-day seed must not discard unsaved editor');
assert.equal(gs('scoreInput').value,fixture);
assert.equal(pe('scoreMemoGrid').children.length,3,'loaded race has editable five-factor selectors');
assert.match(pe('scoreMemoGrid').children[0].children[0].textContent,/脚質 先（前日資料）/);
assert.match(pe('scorePaceStatus').textContent,/逃1・先1・差1・追0・未確認0/);
assert.match(pe('scorePaceStatus').textContent,/これだけで展開S\/A\/B\/Cは付けません/);
pe('scoreReview').onclick();
assert.equal(pe('scoreHandoff').disabled,true,'no rank from all unknown factors');
pe('scoreSeedPredayDay').onclick();
assert.equal(pd.writes.length,1,'repeated seeding preserves current notes');

// Explicit cross-screen jump may request the same one-confirmation seed.
// Cancelling must never write notes, and malformed URL params cannot bypass it.
const brokenPreday=JSON.parse(JSON.stringify(predayMeetings));
brokenPreday[0].races[0].race=99;
const badStartup=boot(true,{[PREDAY]:brokenPreday});
assert.equal(badStartup.el('scoreTrack').value,'',
 'invalid imported data must not be auto-selected');
assert.match(badStartup.el('scorePredayStatus').textContent,/保存形式に問題/);
assert.equal(badStartup.writes.length,0,'invalid source cannot create any score note');
const seedHash='#select=v1&date=2026-11-07&track='+encodeURIComponent('東京')+'&race=1&seed=day-v1';
const oneClick=boot(true,{[PREDAY]:predayMeetings},seedHash);
assert.equal(oneClick.el('scoreDate').value,'2026-11-07');
assert.equal(oneClick.el('scoreTrack').value,'東京',
 'explicit URL deep-link overrides suggested saved venue');
assert.equal(oneClick.el('scoreTrack').value,'東京');
assert.equal(JSON.parse(oneClick.store.get(NOTES)).length,36,'confirmed link seeds 36R once');
assert.equal(oneClick.writes.length,1,'one-confirmation link makes only one atomic note write');
assert.equal(oneClick.cleared.length,1,'used request fragment cleared from address');
assert.equal(oneClick.links.length,0,'not a purchase or betting handoff');
const cancelledSeed=boot(false,{[PREDAY]:predayMeetings},seedHash);
assert.equal(cancelledSeed.writes.length,0,'declined one-click seed leaves notes untouched');
assert.equal(cancelledSeed.store.has(NOTES),false,'no saved notes after cancellation');
assert.equal(cancelledSeed.cleared.length,1,'declined link is one-use too');
for(const malformed of [seedHash.replace('day-v1','invalid'),seedHash+'&seed=day-v1']){
 const invalidLink=boot(true,{[PREDAY]:predayMeetings},malformed);
 assert.equal(invalidLink.writes.length,0,'malformed seed must not write');
 assert.match(invalidLink.el('scoreStatus').textContent,/受け取れませんでした/);
}

// Full-day owner navigation must never confuse 36 saved entry placeholders with
// 36 completed real AI predictions. It only selects incomplete saved notes.
const unfinished=boot(true,{[PREDAY]:predayMeetings,[NOTES]:seeded}),uf=unfinished.el;
uf('scoreDate').value='2026-11-07';
uf('scoreTrack').value='東京';uf('scoreRace').value='1';uf('scoreRace').onchange();
assert.match(uf('scoreAllDayStatus').textContent,/36R登録／採点済0R／途中36R／要再確認0R/);
assert.equal(uf('scoreNextPending').disabled,false);
assert.equal(uf('scoreVenueGrid').children.length,3,'three venue cards for saved 36R only');
assert.ok(uf('scoreVenueGrid').children.some(x=>/東京.*12\/12R｜採点済0・途中12/.test(x.textContent)),
 'Tokyo venue card reports 12 incomplete notes');
assert.ok(uf('scoreVenueGrid').children.some(x=>/京都.*12\/12R｜採点済0・途中12/.test(x.textContent)),
 'Kyoto venue card reports 12 incomplete notes');
const venueWrites=unfinished.writes.length;
uf('scoreVenueGrid').children.find(x=>x.textContent.startsWith('京都')).onclick();
assert.equal(uf('scoreTrack').value,'京都','venue tap jumps across tracks');
assert.equal(uf('scoreRace').value,'1','venue tap opens first unfinished R');
assert.equal(unfinished.writes.length,venueWrites,'venue tap cannot change stored scores or tickets');
assert.match(uf('scoreVenueStatus').textContent,/京都1Rを開きました/);
const venueOld=uf('scoreTrack').value+'|'+uf('scoreRace').value;
uf('scoreInput').value+=' not saved';
uf('scoreVenueGrid').children.find(x=>x.textContent.startsWith('福島')).onclick();
assert.equal(uf('scoreTrack').value+'|'+uf('scoreRace').value,venueOld,
 'venue switching blocks unsaved input');
assert.match(uf('scoreVenueStatus').textContent,/移動せず入力を確認/);
uf('scoreRace').onchange(); // Restore stored text for next button tests.

const beforeNextWrites=unfinished.writes.length;
const initial=uf('scoreTrack').value+'|'+uf('scoreRace').value;
uf('scoreNextPending').onclick();
assert.notEqual(uf('scoreTrack').value+'|'+uf('scoreRace').value,initial);
assert.equal(unfinished.writes.length,beforeNextWrites,'navigation must not save, score, or overwrite');
assert.equal(unfinished.links.length,0,'navigation does not initiate ticket handoff');
assert.match(uf('scoreNextPendingStatus').textContent,/前日資料に基づく手動評価/);
const beforeUnsaved=uf('scoreTrack').value+'|'+uf('scoreRace').value;
uf('scoreInput').value+=' changed without save';
uf('scoreNextPending').onclick();
assert.equal(uf('scoreTrack').value+'|'+uf('scoreRace').value,beforeUnsaved,
 'unsaved edit must stop navigation');
assert.match(uf('scoreNextPendingStatus').textContent,/入力が保存済みメモと違います/);

// Graded notes are skipped, and source mismatches are counted as stale rather
// than silently converted into valid grades.
const complete=seeded.map(x=>({...x}));
complete[0].text=complete[0].text.replaceAll(' ? ? ? ? ?',' S A A B S');
const graded=boot(true,{[PREDAY]:predayMeetings,[NOTES]:complete}),ge=graded.el;
ge('scoreDate').value='2026-11-07';ge('scoreTrack').value='東京';ge('scoreRace').value='1';
ge('scoreRace').onchange();
assert.match(ge('scoreAllDayStatus').textContent,/採点済1R／途中35R/);
ge('scoreNextPending').onclick();
assert.notEqual(ge('scoreTrack').value+'|'+ge('scoreRace').value,'東京|1',
 'completed score must not be chosen');
const staleRoster=JSON.parse(JSON.stringify(predayMeetings));
staleRoster[0].races[0].runners[0].name='架空サクラ訂正';
const modified=boot(true,{[PREDAY]:staleRoster,[NOTES]:complete}),me=modified.el;
me('scoreDate').value='2026-11-07';me('scoreTrack').value='東京';me('scoreRace').value='1';
me('scoreRace').onchange();
assert.match(me('scoreAllDayStatus').textContent,/要再確認1R/);
assert.equal(me('scoreNextPending').disabled,false);

// A day without any imported notes is not silently treated as 0/36 complete.
const absent=boot(),ae=absent.el;
ae('scoreDate').value='2026-11-07';ae('scoreTrack').value='東京';ae('scoreRace').value='1';ae('scoreRace').onchange();
assert.match(ae('scoreAllDayStatus').textContent,/0R登録/);
assert.match(ae('scoreAllDayStatus').textContent,/未登録の開催・Rは集計対象外/);
assert.equal(ae('scoreNextPending').disabled,true);
assert.equal(ae('scoreVenueGrid').children.length,0,'unknown venues must not appear as 0/12 completed');

const existingNote={date:'2026-11-07',track:'東京',race:1,
 text:'1 以前の評価 S A A A A\n2 別の評価 A A A A A\n3 既存の記録 B B B B B',
 sourceMark:null,savedAt:new Date().toISOString()};
const keep=boot(true,{[PREDAY]:predayMeetings,[NOTES]:[existingNote]}),ke=keep.el;
ke('scoreDate').value='2026-11-07';ke('scoreTrack').value='京都';
ke('scoreSeedPredayDay').onclick();
assert.equal(JSON.parse(keep.store.get(NOTES)).length,36);
assert.equal(JSON.parse(keep.store.get(NOTES)).find(x=>x.track==='東京'&&x.race===1).text,
 existingNote.text,'existing owner assessment never overwritten');

const single=boot(true,{[PREDAY]:predayMeetings}),se=single.el;
se('scoreDate').value='2026-11-07';se('scoreTrack').value='福島';se('scoreRace').value='4';
se('scoreFromPreday').onclick();
assert.match(se('scorePredayStatus').textContent,/3頭を仮入力/);
assert.match(se('scoreInput').value,/架空サクラ4 \? \? \? \? \?/);
assert.equal(se('scoreMemoGrid').children.length,3);
assert.equal(se('scoreHandoff').disabled,true);
const preNotes=JSON.parse(single.store.get(NOTES));
// Users can type all five grades directly into the textarea without losing
// the original pre-day provenance or silently breaking the saved-note schema.
const rawBeforeScore=se('scoreInput').value;
se('scoreInput').value=rawBeforeScore.replaceAll(' ? ? ? ? ?',' S A A B S');
se('scoreInput').oninput();
const withEnteredGrades=JSON.parse(single.store.get(NOTES));
assert.equal(withEnteredGrades[0].researchSource,'jrdb-preday-roster-v1');
assert.equal(typeof withEnteredGrades[0].predaySourceMark,'string');
se('scoreReview').onclick();
assert.equal(se('scoreHandoff').disabled,false,'manually completed grades may produce review-only formation');
assert.match(se('scoreStatus').textContent,/JRDB前日資料の仮馬番/);
se('scoreInput').value=se('scoreInput').value.replace('架空サクラ4','架空馬名変更');
se('scoreInput').oninput();
se('scoreReview').onclick();
assert.equal(se('scoreHandoff').disabled,true,'renamed provider horse cannot be ranked using stale source');
assert.match(se('scoreStatus').textContent,/計算できません.*馬番・馬名/);
const afterBadRaw=JSON.parse(single.store.get(NOTES));
assert.equal(afterBadRaw[0].researchSource,'jrdb-preday-roster-v1','tampering never strips source provenance');
assert.equal(afterBadRaw[0].predaySourceMark,withEnteredGrades[0].predaySourceMark);

assert.equal(preNotes.length,1);
assert.equal(preNotes[0].predaySourceMark,JSON.stringify([
 predayMeetings[2].races[3].postTime,
 3,predayMeetings[2].races[3].runners]));
const resumed=boot(true,{[PREDAY]:predayMeetings,[NOTES]:preNotes}),re= resumed.el;
re('scoreDate').value='2026-11-07';re('scoreTrack').value='福島';re('scoreRace').value='4';
re('scoreRace').onchange();
assert.equal(re('scoreMemoGrid').children.length,3,'iPhone relaunch restores row selectors');
assert.match(re('scoreMemoGrid').children[0].children[0].textContent,/脚質 先（前日資料）/,'style persists as provider observation after re-open');
assert.match(re('scorePaceStatus').textContent,/逃1・先1・差1/);
assert.match(re('scoreInput').value,/架空サクラ4/);
assert.equal(re('scoreHandoff').disabled,true);
const beforeChange=JSON.stringify(predayMeetings);
const changedPreday=JSON.parse(beforeChange);
changedPreday[2].races[3].runners[0].name='架空サクラ変更';
const stale=boot(true,{[PREDAY]:changedPreday,[NOTES]:[...preNotes,seeded.find(n=>n.track==='東京'&&n.race===1)]}),st=stale.el;
st('scoreDate').value='2026-11-07';st('scoreTrack').value='福島';st('scoreRace').value='4';
st('scoreRace').onchange();
assert.match(st('scoreDraftStatus').textContent,/復元できません/);
assert.equal(st('scoreInput').value,'','stale source cannot silently restore old horse number associations');
assert.match(st('scoreDayStatus').textContent,/要再確認1R/);
// A stale pre-day source is deliberately blank on restore, but typing
// fresh notes makes it unsaved and blocks both queue and venue shortcuts.
st('scoreInput').value='1 手入力 ? ? ? ? ?';
const staleBefore=st('scoreTrack').value+'|'+st('scoreRace').value;
st('scoreNextPending').onclick();
assert.equal(st('scoreTrack').value+'|'+st('scoreRace').value,staleBefore);
assert.match(st('scoreNextPendingStatus').textContent,/保存済みメモと違います/);
st('scoreVenueGrid').children.find(x=>x.textContent.startsWith('東京')).onclick();
assert.equal(st('scoreTrack').value+'|'+st('scoreRace').value,staleBefore);
assert.match(st('scoreVenueStatus').textContent,/移動せず入力を確認/);
st('scoreInput').value='';
st('scoreDayBuild').onclick();
assert.equal(st('scoreDayTransfer').disabled,true,'stale pre-day note never enters 36R betting batch');
const missingSource=boot(true,{[NOTES]:preNotes}),ms=missingSource.el;
ms('scoreDate').value='2026-11-07';ms('scoreTrack').value='福島';ms('scoreRace').value='4';
ms('scoreRace').onchange();
assert.equal(ms('scoreInput').value,'','deleted pre-day mail is not interpreted as verified');
assert.match(ms('scoreDraftStatus').textContent,/復元できません/);
const refused=boot(false,{[PREDAY]:predayMeetings,[NOTES]:[existingNote]}),rf=refused.el;
rf('scoreDate').value='2026-11-07';rf('scoreTrack').value='東京';rf('scoreRace').value='1';
rf('scoreRace').onchange();
rf('scoreFromPreday').onclick();
assert.equal(refused.writes.length,0,'existing manual grades cannot be overwritten without consent');
assert.equal(JSON.parse(refused.store.get(NOTES))[0].text,existingNote.text);

}
// A failed Safari/localStorage write must never silently erase unsaved
// factor edits when switching 1R -> 2R, venue or date.
const quota=boot(),qe=quota.el;
qe('scoreDate').value='2026-11-07';qe('scoreTrack').value='東京';qe('scoreRace').value='1';
qe('scoreRace').onchange();
quota.storageBehavior.failWrites=true;
qe('scoreInput').value=fixture;qe('scoreInput').oninput();
assert.match(qe('scoreDraftStatus').textContent,/保存に失敗/);
assert.equal(quota.store.has(NOTES),false,'storage failure must not create a phantom note');
qe('scoreRaceGrid').children[1].onclick();
assert.equal(qe('scoreRace').value,'1','race card blocked until draft persisted');
assert.equal(qe('scoreInput').value,fixture,'draft text stays visible after failed navigation');
assert.match(qe('scoreNavigationStatus').textContent,/未保存の評価/);
qe('scoreTrack').value='京都';qe('scoreTrack').onchange();
assert.equal(qe('scoreTrack').value,'東京','venue selector must restore previous value');
qe('scoreDate').value='2026-11-08';qe('scoreDate').onchange();
assert.equal(qe('scoreDate').value,'2026-11-07','date selector must restore previous value');
assert.equal(qe('scoreInput').value,fixture);
quota.storageBehavior.failWrites=false;
qe('scoreRetryDraft').onclick();
assert.equal(JSON.parse(quota.store.get(NOTES))[0].text,fixture);
assert.match(qe('scoreDraftStatus').textContent,/保存しました/);
qe('scoreRaceGrid').children[1].onclick();
assert.equal(qe('scoreRace').value,'2','after successful retry next race is available');
assert.equal(qe('scoreInput').value,'','other race does not inherit previous 1R scores');
qe('scoreRaceGrid').children[0].onclick();
assert.equal(qe('scoreInput').value,fixture,'saved 1R scores can be reopened safely');
// Even without an oninput event, edited DOM text must block navigation.
qe('scoreInput').value=fixture+' unsaved';
qe('scoreRace').value='3';qe('scoreRace').onchange();
assert.equal(qe('scoreRace').value,'1');
assert.equal(qe('scoreInput').value,fixture+' unsaved');
assert.equal(JSON.parse(quota.store.get(NOTES))[0].text,fixture);
const firstDeepLink=boot(true,{},'#select=v1&date=2026-11-07&track='+encodeURIComponent('東京')+'&race=1');
const de=firstDeepLink.el;
firstDeepLink.storageBehavior.failWrites=true;
de('scoreInput').value=fixture;
de('scoreInput').oninput();
de('scoreRaceGrid').children[1].onclick();
assert.equal(de('scoreRace').value,'1','first deep-link navigation must protect unsaved score');
assert.equal(de('scoreInput').value,fixture);
assert.match(de('scoreNavigationStatus').textContent,/未保存の評価/);
assert.equal(firstDeepLink.store.has(NOTES),false);
console.log('Owner scorecard storage-error retry and unsaved navigation guards PASS');

console.log('Owner manual 5-factor scoring: 36-point ranks, validation, cancel, no-network handoff PASS');
