/* Offline test: JRDB member's provisional email is parsed only inside the owner browser. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const script=fs.readFileSync('/tmp/keiba-jrdb-mail-local.js','utf8');
const storage=new Map(),requests=[];
let approve=true;
const localStorage={
 getItem:key=>storage.get(key)||null,
 setItem(key,value){storage.set(key,value);},
 removeItem:key=>storage.delete(key)
};
function element(tag='div'){
 return {tag,children:[],value:'',textContent:'',onclick:null,onchange:null,
  append(...nodes){this.children.push(...nodes)},
  replaceChildren(...nodes){this.children=[...nodes]}
 };
}
function loadPage(){
 const nodes=new Map();
 const get=id=>{if(!nodes.has(id))nodes.set(id,element());return nodes.get(id);};
 vm.runInNewContext(script,{document:{getElementById:get,createElement:element},
  localStorage,Date,JSON,Set,String,Number,Array,Error,confirm:()=>approve,
  fetch:()=>{requests.push('network');throw Error('Never network');}});
 return get;
}
const mail=(date,venue,number=1)=>[
 '■想定確定','',
 date+'　5回'+venue+'1日目　09:55発走',
 number+'Ｒ',
 '２歳・未勝利(馬齢)[指]　芝・左1600M　2頭',
 '前評 B 馬名 性 齢 騎手 斤量 IDM 厩舎',
 '　 テストサクラ 牝 2 架空騎手　55 架空厩舎',
 '　 B テストナイン 牡 2 架空騎手　56 架空厩舎','',
 "All Rights Reserved By 'JRDB.'"
].join('\n');
const key='keiba-nine-jrdb-personal-mail-v1';
const e=loadPage();
assert.equal(storage.size,0);
assert.equal(e('raceList').children.length,0);
e('mailText').value=mail('2099年1月1日（木）','東京',1);
e('importMail').onclick();
assert.match(e('message').textContent,/1通を確認/);
assert.equal(e('mailText').value,'','Raw email cleared from DOM after successful ingest');
let state=JSON.parse(storage.get(key));
assert.equal(state.length,1);
assert.equal(state[0].date,'2099-01-01');
assert.equal(state[0].track,'東京');
assert.equal(state[0].kind,'jrdb-provisional');
assert.equal(state[0].races[0].expected,2);
assert.equal(state[0].races[0].postTime,'09:55');
assert.deepEqual(Array.from(state[0].races[0].horses),['テストサクラ','テストナイン']);
assert.ok(!storage.get(key).includes('All Rights Reserved'));
assert.ok(!storage.get(key).includes('架空騎手'));
assert.ok(!storage.get(key).includes('API'));
assert.equal(e('raceList').children.length,1);
assert.equal(e('raceList').children[0].tag,'details');
assert.match(e('raceList').children[0].children[1].textContent,/馬番/);
const before=storage.get(key);
e('mailText').value=mail('2099年1月1日（木）','東京',2).replace('2頭','3頭');
e('importMail').onclick();
assert.match(e('message').textContent,/頭数が一致/);
assert.equal(storage.get(key),before,'Truncated email never overwrites existing data');
approve=false; // A brand-new venue must not require a replacement confirmation.
e('mailText').value=mail('2099年1月1日（木）','京都',1);
e('importMail').onclick();
approve=true;
assert.equal(JSON.parse(storage.get(key)).length,2,'Other venue saved without confirmation');
e('mailText').value=mail('2099年1月1日（木）','東京',1).replace('テストサクラ','改訂テストサクラ');
e('importMail').onclick();
state=JSON.parse(storage.get(key));
assert.equal(state.length,2,'Same venue/date replaces not duplicates');
assert.match(e('message').textContent,/変更1R/);
assert.equal(state.find(x=>x.track==='東京').races[0].horses[0],'改訂テストサクラ');
assert.ok(e('raceList').children.length===1);
e('chooseMeeting').value='2099-01-01|京都';
e('chooseMeeting').onchange();
assert.match(e('meetingInfo').textContent,/京都/);
assert.ok(e('raceList').children[0].children[2].children.length===2);
// Tomorrow: import multiple JRDB messages at once. An invalid final mail must
// fail the entire batch without replacing the already imported calendar.
const two=mail('2099年1月2日（金）','東京',1)+'\n\n'+
 mail('2099年1月2日（金）','京都',1);
e('mailText').value=two;
e('importMail').onclick();
assert.equal(JSON.parse(storage.get(key)).length,4);
assert.match(e('message').textContent,/2通を確認/);
assert.match(e('message').textContent,/2開催を追加/);
let kept=storage.get(key);
e('mailText').value=mail('2099年1月3日（土）','東京',1)+'\n\n'+
 mail('2099年1月3日（土）','京都',1).replace('2頭','3頭');
e('importMail').onclick();
assert.match(e('message').textContent,/取り込めません/);
assert.equal(storage.get(key),kept,'Batch parsing must be all or nothing');
e('mailText').value=two;
e('importMail').onclick();
assert.match(e('message').textContent,/2開催は変更なし/);
assert.equal(storage.get(key),kept,'Reimporting identical mail must not write');
e('mailText').value=mail('2099年1月2日（金）','東京',1)+'\n\n'+
 mail('2099年1月2日（金）','東京',1);
e('importMail').onclick();
assert.match(e('message').textContent,/重複/);
assert.equal(storage.get(key),kept);
approve=false;
e('mailText').value=mail('2099年1月2日（金）','東京',1)
 .replace('テストサクラ','新テストサクラ');
e('importMail').onclick();
assert.equal(storage.get(key),kept,'Declining corrected mail must preserve all meetings');
approve=true;
e('importMail').onclick();
assert.match(e('message').textContent,/変更1R/);
kept=storage.get(key);
assert.equal(JSON.parse(kept).find(x=>x.date==='2099-01-02'&&x.track==='東京')
 .races[0].horses[0],'新テストサクラ');
// User should be able to delete an old meeting without losing other venues.
e('chooseMeeting').value='2099-01-01|京都';
e('deleteMeeting').onclick();
assert.equal(JSON.parse(storage.get(key)).length,3);
assert.ok(!JSON.parse(storage.get(key)).some(x=>x.date==='2099-01-01'&&x.track==='京都'));
const snapshot=storage.get(key);
e('mailText').value='Random unauthorized content';
e('importMail').onclick();
assert.match(e('message').textContent,/取り込めません/);
assert.equal(storage.get(key),snapshot);
e('clearAll').onclick();
assert.equal(storage.has(key),false);
assert.equal(e('raceList').children.length,0);
const next=loadPage();
assert.equal(next('raceList').children.length,0,'Deleted calendar stays deleted');
assert.equal(requests.length,0,'Never issue a network request');
assert.ok(!script.includes('fetch('));
assert.ok(!script.includes('innerHTML'));
assert.ok(!script.includes('XMLHttpRequest'));
console.log('JRDB personal mail importer: local-only 2099 fixture, two venues, replacement, bad email block, clear and no network OK');
