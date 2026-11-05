/* Five-factor scorecard: user-entered grades only, no network or persistent data. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('/tmp/keiba-owner-scorecard.js','utf8');
function boot(decision=true){
 const nodes=new Map(),links=[],alerts=[];
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
  Date,JSON,Set,Map,Object,String,Number,Error,URLSearchParams,
  confirm:()=>decision,console
 };
 vm.runInNewContext(source,ctx);
 return {el:get,links,alerts};
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
assert.ok(!source.includes('localStorage'),'never save fake evaluation as confirmed actual data');
assert.ok(!source.includes('innerHTML'),'render only safe textContent');
console.log('Owner manual 5-factor scoring: 36-point ranks, validation, cancel, no-network handoff PASS');
