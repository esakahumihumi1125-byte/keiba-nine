/* JRA web racecard prestart guidance and owner-only matching progress (offline). */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const code=fs.readFileSync('/tmp/keiba-jra-web-card.js','utf8');
const MAIL='keiba-nine-jrdb-personal-mail-v1';
const MANUAL='keiba-nine-owner-manual-numbers-v1';
const m={date:'2099-01-01',track:'東京',kind:'jrdb-provisional',
 races:[
  {race:1,postTime:'09:55',expected:2,horses:['架空ホースA','架空ホースB']},
  {race:2,postTime:'10:25',expected:2,horses:['架空ホースC','架空ホースD']},
  {race:3,postTime:'11:25',expected:2,horses:['架空ホースE','架空ホースF']},
  {race:4,postTime:'12:25',expected:2,horses:['架空ホースG','架空ホースH']},
 ]};
const mark=r=>JSON.stringify([r.postTime,r.expected,r.horses]);
const matches=[
 {date:m.date,track:m.track,race:1,sourceMark:mark(m.races[0]),
  rows:[{number:1,name:'架空ホースA'},{number:2,name:'架空ホースB'}]},
 {date:m.date,track:m.track,race:2,sourceMark:'old-snapshot',
  rows:[{number:1,name:'架空ホースC'},{number:2,name:'架空ホースD'}]},
 {date:m.date,track:m.track,race:3,sourceMark:mark(m.races[2]),
  rows:[{number:1,name:'架空ホースE'},{number:2,name:'新出走馬'}]},
];
const storage=new Map([[MAIL,JSON.stringify([m])],[MANUAL,JSON.stringify(matches)]]);
const events=[],calls=[];
function element(tag='div'){
 return {tag,value:'',textContent:'',children:[],type:'',className:'',disabled:false,
  onclick:null,onchange:null,
  append(...nodes){this.children.push(...nodes)},
  replaceChildren(...nodes){this.children=[...nodes]},
  scrollIntoView(v){events.push(v)}
 };
}
function boot(){
 const nodes=new Map();
 const $=id=>{if(!nodes.has(id))nodes.set(id,element());return nodes.get(id);};
 $('chooseMeeting').value='2099-01-01|東京';
 $('numberRace').value='1';
 $('numberRace').onchange=()=>events.push('selected');
 for(const id of ['importMail','deleteMeeting','clearAll','saveNumbers','deleteNumbers'])
  $(id).onclick=()=>events.push(id);
 const env={document:{getElementById:$,createElement:element},
  localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},
  JSON,Date,Set,Number,Array,String,
  fetch:()=>{calls.push('network');throw Error('Never call network');}};
 vm.runInNewContext(code,env);
 return $;
}
const $=boot();
assert.equal(calls.length,0,'UI load must not fetch JRA website or paid provider');
assert.match($('jraPublishTiming').textContent,/発表目安/);
assert.match($('jraPublishTiming').textContent,/PDF一覧は主に開催当日以降/);
assert.match($('jraNumberProgress').textContent,/全4R/);
assert.match($('jraNumberProgress').textContent,/1R馬名一致、1R未入力、1R再照合、1R差異あり/);
assert.equal($('jraRaceChecklist').children.length,4);
const buttons=$('jraRaceChecklist').children;
assert.match(buttons[0].textContent,/1R 馬名一致/);
assert.match(buttons[1].textContent,/2R 想定更新/);
assert.match(buttons[2].textContent,/3R 馬名差異/);
assert.match(buttons[3].textContent,/4R 馬番未入力/);
buttons[2].onclick();
assert.equal($('numberRace').value,'3','One tap selects race in manual mapping UI');
assert.deepEqual(events.slice(0,2),['selected',{behavior:'smooth',block:'start'}]);
const before=JSON.stringify([...storage]);
$('chooseMeeting').value='2099-01-02|京都';
$('chooseMeeting').onchange();
assert.match($('jraNumberProgress').textContent,/まだ取り込んでへん/);
assert.equal($('jraRaceChecklist').children.length,0);
$('chooseMeeting').value='2099-01-01|東京';$('chooseMeeting').onchange();
const updated=JSON.parse(storage.get(MANUAL));
updated[0].rows=[{number:1,name:'架空ホースA'},{number:2,name:'別の馬'}];
storage.set(MANUAL,JSON.stringify(updated));
$('saveNumbers').onclick();
assert.match($('jraNumberProgress').textContent,/0R馬名一致、1R未入力、1R再照合、2R差異あり/);
assert.equal(events.includes('saveNumbers'),true);
assert.equal(calls.length,0);
assert.ok(!code.includes('fetch('));
assert.ok(!code.includes('innerHTML'));
console.log('JRA web release guidance and private per-race match checklist: no network/official verification, stale/unmatched classification and tap-to-race PASS');
