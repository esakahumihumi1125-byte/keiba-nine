/* Offline test: JRDB member's provisional email is parsed only inside the owner browser. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const script=fs.readFileSync('/tmp/keiba-jrdb-mail-local.js','utf8');
const storage=new Map(),requests=[],navigation=[];
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
  localStorage,window:{location:{assign:url=>navigation.push(url)}},URLSearchParams,Date,JSON,Set,String,Number,Array,Error,confirm:()=>approve,
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
// 12R mail pattern; named 9R–11R match the real structural heading format.
function titledTwelveRaceMail(date,venue){
 const body=['■想定確定',''];
 for(let n=1;n<=12;n++){
  body.push(date+'　5回'+venue+'1日目　09:55発走');
  body.push(n+'Ｒ'+([9,10,11].includes(n)?' 特別サンプル'+n:''));
  body.push('２歳・未勝利(馬齢)[指]　芝・左1600M　2頭');
  body.push('前評 B 馬名 性 齢 騎手 斤量 IDM 厩舎');
  const grade=['','◎ ','○ ','▲ ','△ ','注 ','B ◎ ','◎ B ','☆ ','× ','B △ ','△ B '][n-1];
  body.push(' '+grade+'テストサクラ 牝 2 架空騎手 55 架空厩舎');
  body.push(' B テストナイン 牡 2 架空騎手 56 架空厩舎');
  body.push('');
 }
 body.push("All Rights Reserved By 'JRDB.'");
 return body.join('\n');
}
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
// Named stakes/race headers must not silently skip 9R–11R or drop their horses.
const full=titledTwelveRaceMail('2099年1月9日（土）','福島');
e('mailText').value=full;e('importMail').onclick();
let titledMeeting=JSON.parse(storage.get(key)).find(x=>x.date==='2099-01-09'&&x.track==='福島');
assert.equal(titledMeeting.races.length,12,'full mail with titled 9R–11R must import 12 races');
assert.deepEqual(Array.from(titledMeeting.races.map(x=>x.race)),[1,2,3,4,5,6,7,8,9,10,11,12]);
assert.equal(titledMeeting.races[8].expected,2,'named 9R count retained');
assert.equal(titledMeeting.races[10].horses.length,2,'named 11R horse entries retained');
assert.ok(!storage.get(key).includes('特別サンプル'),'race titles are not saved');
const preservedTitled=storage.get(key);
e('mailText').value=full.replace('9Ｒ 特別サンプル9','9Ｒ特別サンプル9');
e('importMail').onclick();
assert.match(e('message').textContent,/取り込めません/);
assert.equal(storage.get(key),preservedTitled,'unrecognized named heading fails all-or-nothing');
e('mailText').value=full.replace('◎ テストサクラ','未確認印 テストサクラ');
e('importMail').onclick();
assert.match(e('message').textContent,/取り込めません/);
assert.equal(storage.get(key),preservedTitled,'unsupported grade marker must fail closed');
e('clearAll').onclick();
assert.equal(storage.has(key),false);
assert.equal(e('raceList').children.length,0);
const next=loadPage();
assert.equal(next('raceList').children.length,0,'Deleted calendar stays deleted');
assert.equal(requests.length,0,'Never issue a network request');
assert.ok(!script.includes('fetch('));
assert.ok(!script.includes('innerHTML'));
assert.ok(!script.includes('XMLHttpRequest'));

// Synthetic JRDB 前日情報: actual horse-numbered structure without licensed data.
function predayFixture(date,venue,count=12){
 const lines=['■前日情報',''];
 for(let race=1;race<=count;race++){
  lines.push(date+'　5回'+venue+'1日目　09:55発走');
  lines.push(race+'Ｒ'+(race===11?' 合成特別競走':''));
  lines.push('２歳・未勝利(馬齢)　ダ・左1600M　3頭立','');
  lines.push('騎情ID前 B馬名 性齢 騎手 斤量 脚 前評IDM 情 騎 基オ(人)');
  lines.push('◎◎◎◎ 1 合成サクラ'+race+' 牝2 架空騎手55'+(race===6?'':' 先')+' 25: 21 1 0: 8.0( 1)');
  lines.push('△△ 2 B合成ナイン'+race+' 牡3 架空騎手56 逃 12: 12 0 0: 30.0( 7)');
  lines.push(' 3 合成ドリーム'+race+' セ4 架空騎手57 差 11: 10 1 0: 99.0(12)');
  lines.push('','≪推奨買い目≫');
  lines.push('1-2( 1.0)　1-3( 99.0)','');
 }
 lines.push('このメールに掲載された内容は転載禁止');
 return lines.join('\n');
}
const PRE='keiba-nine-jrdb-preday-runners-v1';
const previewPreday=loadPage();
const predayTriple=[
 predayFixture('2099年11月7日（土）','東京'),
 predayFixture('2099年11月7日（土）','京都'),
 predayFixture('2099年11月7日（土）','福島')
].join('\n\n');
const savedBeforePreday=storage.get(key);
previewPreday('predayText').value=predayTriple;
previewPreday('predayImport').onclick();
assert.match(previewPreday('predayStatus').textContent,/3通の前日情報から36R/);
assert.equal(previewPreday('predayText').value,'');
const pre=JSON.parse(storage.get(PRE));
assert.equal(pre.length,3);
assert.ok(pre.every(x=>x.date==='2099-11-07'&&x.races.length===12));
assert.equal(pre.find(x=>x.track==='東京').races[0].runners.length,3);
assert.equal(pre.find(x=>x.track==='東京').races[5].runners[0].style,'未確認','debut race unknown running style is not fabricated');
assert.deepEqual(pre.find(x=>x.track==='東京').races[0].runners[1],{
 number:2,name:'合成ナイン1',style:'逃'
});
assert.ok(!storage.get(PRE).includes('騎手'),'private local store excludes other licensed metadata');
assert.ok(!storage.get(PRE).includes('99.0'),'private local store excludes odds');
assert.ok(!storage.get(PRE).includes('前評'),'private local store excludes provider ratings');
assert.equal(storage.get(key),savedBeforePreday,'existing 想確 mail unaffected');
previewPreday('predayMeeting').value='2099-11-07|東京';
previewPreday('predayMeeting').onchange();
assert.equal(previewPreday('predayRaces').children.length,12);
assert.match(previewPreday('predayRaces').children[0].children[1].children[0].textContent,/1番 合成サクラ1（先）/);
previewPreday('predayRaces').children[0].children[2].onclick();
assert.match(navigation[0],/\/my-scorecard#select=v1&date=2099-11-07&track=/);
assert.ok(!navigation[0].includes('合成'),'names do not enter URL');
const preSaved=storage.get(PRE);
previewPreday('predayText').value=predayFixture('2099年11月8日（日）','東京')+'\n\n'+
 predayFixture('2099年11月8日（日）','京都').replace('3頭立','4頭立');
previewPreday('predayImport').onclick();
assert.match(previewPreday('predayStatus').textContent,/取り込めません/);
assert.equal(storage.get(PRE),preSaved,'invalid second email aborts entire update');
previewPreday('predayText').value=predayFixture('2099年11月7日（土）','東京',11);
previewPreday('predayImport').onclick();
assert.match(previewPreday('predayStatus').textContent,/旧Rが欠けています/);
assert.equal(storage.get(PRE),preSaved,'incomplete later update cannot delete an existing R');
previewPreday('predayText').value=predayTriple;
previewPreday('predayImport').onclick();
assert.equal(storage.get(PRE),preSaved,'idempotent re-import does not alter records');
assert.equal(requests.length,0,'no email contents sent to network');

console.log('JRDB personal mail importer: local-only 2099 fixture, two venues, replacement, bad email block, clear and no network OK');

// iPhone import: a single UTF-8 text file containing two provisional emails.
// Choosing it only populates the preview textbox; never saves automatically.
(async()=>{
 const ui=loadPage(),payload=mail('2099年1月12日（月）','東京')+
  '\n\n'+mail('2099年1月12日（月）','京都');
 const imported={name:'jrdb-two-courses.txt',size:Buffer.byteLength(payload,'utf8'),text:async()=>payload};
 const before=storage.get(key);
 ui('mailTextFile').files=[imported];
 await ui('mailTextFile').onchange();
 assert.match(ui('mailFileStatus').textContent,/2開催分を検査できました/);
 assert.match(ui('mailFileStatus').textContent,/まだ未保存/);
 assert.equal(ui('mailText').value,payload);
 assert.equal(storage.get(key),before,'file preview never mutates browser records');
 ui('importMail').onclick();
 const now=JSON.parse(storage.get(key));
 assert.equal(now.filter(x=>x.date==='2099-01-12').length,2);
 assert.equal(ui('mailText').value,'','saved file contents cleared from textarea');
 const saved=storage.get(key);
 ui('mailText').value='do-not-overwrite';
 const bad={name:'unexpected.txt',size:500,text:async()=>('invalid example.').repeat(20)};
 ui('mailTextFile').files=[bad];await ui('mailTextFile').onchange();
 assert.match(ui('mailFileStatus').textContent,/ファイルを読み込めません/);
 assert.equal(ui('mailText').value,'do-not-overwrite','invalid import preserves pasted text');
 assert.equal(storage.get(key),saved);
 const wrong={name:'source.json',size:500,text:async()=>payload};
 ui('mailTextFile').files=[wrong];await ui('mailTextFile').onchange();
 assert.match(ui('mailFileStatus').textContent,/\.txt/);
 assert.equal(storage.get(key),saved);
 const huge={name:'oversize.txt',size:192001,text:async()=>{throw Error('should not read')}};
 ui('mailTextFile').files=[huge];await ui('mailTextFile').onchange();
 assert.match(ui('mailFileStatus').textContent,/192KB/);
 assert.equal(storage.get(key),saved);
 approve=false;
 ui('mailTextFile').files=[imported];await ui('mailTextFile').onchange();
 assert.equal(ui('mailText').value,'do-not-overwrite','declined file preview preserves other text');
 approve=true;
 ui('mailText').value='';
 let resolveFirst;
 const older={name:'older.txt',size:Buffer.byteLength(payload,'utf8'),text:()=>new Promise(r=>{resolveFirst=r})};
 ui('mailTextFile').files=[older];
 const pending=ui('mailTextFile').onchange();
 const nextBody=mail('2099年1月13日（火）','福島');
 const newer={name:'newer.txt',size:Buffer.byteLength(nextBody,'utf8'),text:async()=>nextBody};
 ui('mailTextFile').files=[newer];
 await ui('mailTextFile').onchange();
 resolveFirst(payload);await pending;
 assert.equal(ui('mailText').value,nextBody,'stale earlier file read cannot override latest selection');
 assert.equal(storage.get(key),saved,'file loading cannot save without explicit click');
 assert.equal(requests.length,0);
 console.log('JRDB single-file manual preview: 2 venues, invalid file, cancel, and stale file read PASS');
})().catch(error=>{console.error(error);process.exitCode=1});

