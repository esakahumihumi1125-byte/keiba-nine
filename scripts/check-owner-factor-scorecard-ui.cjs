/* Five-factor scorecard: user-entered grades only, no network or persistent data. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('/tmp/keiba-owner-scorecard.js','utf8');
function boot(decision=true,saved={}){
 const nodes=new Map(),links=[],alerts=[],writes=[];
 const store=new Map(Object.entries(saved).map(([k,v])=>[k,JSON.stringify(v)]));
 const localStorage={getItem:k=>store.get(k)||null,setItem:(k,v)=>{writes.push(k);throw Error('Unexpected write: '+k)}};
 function element(tag='div'){
  return {tag,value:'',textContent:'',className:'',disabled:false,children:[],
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
    location:{assign:url=>links.push(url)}
  },
  Date,JSON,Set,Map,Object,String,Number,Error,URLSearchParams,localStorage,
  confirm:()=>decision,console
 };
 vm.runInNewContext(source,ctx);
 return {el:get,links,alerts,writes,store};
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
assert.ok(!source.includes('localStorage.setItem'),'never save manual evaluation or member data to browser');
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
assert.deepEqual(owned.writes,[],'roster intake never writes member data or picks');
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

console.log('Owner manual 5-factor scoring: 36-point ranks, validation, cancel, no-network handoff PASS');
