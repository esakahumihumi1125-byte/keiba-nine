'use strict';
// No network, paid sources, real account or ticket purchasing.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const bridge=require('../owner-ticket-transfer.js');
const receiver=fs.readFileSync('/tmp/keiba-private-owner-handoff.js','utf8');
const standard={date:'2026-11-07',track:'東京',race:'1',
 first:'1',second:'2,3,4,5,6,7',third:'2,3,4,5,6,7',
 recordType:'live',intent:'購入推奨',useTri:true};
const built=bridge.build(standard);
assert.equal(built.points,30);
assert.ok(built.url.startsWith('https://keiba-nine-owner-preview.onrender.com/my-tickets#import=v1&'));
assert.ok(!built.url.includes('?'),'Only fragment may contain the selected horse numbers');
const fragment='#'+built.url.split('#')[1];
function receiverRun(hash,accepted=true){
 const nodes=Object.fromEntries(['mDate','mTrack','mRace'].map(id=>[id,{value:''}]));
 const logs=[];
 let clearCount=0,renderCount=0,dayCount=0;
 const win={location:{hash,pathname:'/my-tickets',search:''},
   history:{replaceState(){clearCount++}},
   confirm:()=>accepted};
 const c={window:win,URLSearchParams,Date,Set,Number,Error,
  TRACKS:['東京','京都'],LIMIT:48,
  validDate:x=>x==='2026-11-07',
  validNums:a=>Array.isArray(a)&&a.length>=1&&a.length<=18&&
    a.every(n=>Number.isInteger(n)&&n>=1&&n<=18)&&new Set(a).size===a.length,
  ticketsFor(first,second,third){
    const set=new Set();
    for(const a of first)for(const b of second)for(const d of third)
      if(a!==b&&a!==d&&b!==d)set.add(a+'-'+b+'-'+d);
    return Array.from(set);
  },
  first:new Set([10]),second:new Set([11]),third:new Set([12]),
  $:id=>nodes[id],render:()=>renderCount++,showDay:()=>dayCount++,
  message:t=>logs.push(t)
 };
 vm.runInNewContext(receiver,c);
 return {c,nodes,logs,clearCount,renderCount,dayCount};
}
let result=receiverRun(fragment);
assert.equal(result.clearCount,1);
assert.equal(result.nodes.mDate.value,'2026-11-07');
assert.equal(result.nodes.mTrack.value,'東京');
assert.equal(result.nodes.mRace.value,'1');
assert.deepEqual([...result.c.first],[1]);
assert.deepEqual([...result.c.second],[2,3,4,5,6,7]);
assert.deepEqual([...result.c.third],[2,3,4,5,6,7]);
assert.equal(result.renderCount,1);
assert.equal(result.dayCount,1);
assert.match(result.logs.at(-1),/購入記録には追加されません/);
result=receiverRun(fragment,false);
assert.equal(result.clearCount,1);
assert.deepEqual([...result.c.first],[10], 'Decline must keep current selection');
assert.equal(result.renderCount,0);
const bads=[
 '#import=v1&date=2026-11-07&track=%E6%9D%B1%E4%BA%AC&race=1&first=1&second=2&third=3&third=4',
 '#import=v1&date=2026-11-07&track=%E6%9D%B1%E4%BA%AC&race=1&first=1&second=1&third=1',
 '#import=v1&date=2026-11-07&track=%E6%9D%B1%E4%BA%AC&race=1&first=1&second=2&third=2,2',
 '#import=v1&date=2026-11-07&track=%E6%9D%B1%E4%BA%AC&race=1&first=1&second=2&third=19'
];
for(const bad of bads){
 const o=receiverRun(bad);
 assert.equal(o.renderCount,0,'Invalid formation must not be applied');
 assert.equal(o.clearCount,1,'Invalid fragment must still be stripped');
 assert.deepEqual([...o.c.first],[10]);
}
for(const patch of [
 {recordType:'test'},{intent:'見送り'},{useTri:false},
 {first:'1,1'},{track:'大阪'},{date:'2026-11-31'},
 {first:'1',second:'2,3,4,5,6,7,8,9',third:'2,3,4,5,6,7,8,9,10'}
])assert.throws(()=>bridge.build({...standard,...patch}));
assert.equal(bridge.build({...standard,first:'1,2',second:'1,2,3,4,5',third:'1,2,3,4,5,6,7,8'}).points,48);
let nav='',status='',click;
const values={rpDate:standard.date,rpTrack:standard.track,rpRace:standard.race,
  rpFirst:standard.first,rpSecond:standard.second,rpThird:standard.third,
  rpRecordType:standard.recordType,rpIntent:standard.intent};
const win={document:{getElementById(id){
  if(id==='ownerTicketTransfer')return {addEventListener(type,cb){assert.equal(type,'click');click=cb}};
  if(id==='ownerTicketTransferStatus')return {set textContent(x){status=x}};
  if(id==='rpUseTri')return {checked:true};
  return {value:values[id]||''};
 }},confirm:()=>true,location:{assign:url=>nav=url}};
bridge.install(win);click();
assert.ok(nav.startsWith('https://keiba-nine-owner-preview.onrender.com/my-tickets#import=v1'));
assert.match(status,/本人用へ移動/);
assert.ok(!receiver.includes('localStorage.setItem'));
assert.ok(!receiver.includes('fetch('));
console.log('Owner ticket handoff: validated formation, safe fragment, no automatic save/purchase, invalid/declined cases passed');
