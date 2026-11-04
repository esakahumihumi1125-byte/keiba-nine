/* No API calls: synthetic, owner-only purchase declarations and settlement. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const manual=fs.readFileSync('/tmp/keiba-private-manual-tickets.js','utf8');
const ledger=fs.readFileSync('/tmp/keiba-private-purchases.js','utf8');
const storage=new Map();
const writes=[];
const localStorage={
 getItem(k){return storage.get(k)||null;},
 setItem(k,v){storage.set(k,v);writes.push(k);}
};
let approve=true,promptValue='0';
const calls=[];
function boot(){
 const nodes=new Map(),files=[];
 function node(tag='div'){
  return {tag,value:'',textContent:'',className:'',children:[],dataset:{},
   disabled:false,onclick:null,onchange:null,style:{},type:'',href:'',download:'',
   append(...n){this.children.push(...n);},
   replaceChildren(...n){this.children=[...n];},
   setAttribute(k,v){this[k]=v;},
   click(){this.clicked=true;}
  };
 }
 function $(id){if(!nodes.has(id))nodes.set(id,node());return nodes.get(id);}
 const URL={createObjectURL(file){files.push(file);return 'blob:test';},
   revokeObjectURL(url){files.push(url);}};
 const scope={
  document:{getElementById:$,createElement:node},localStorage,
  Date,JSON,Set,Number,String,Blob,URL,console,
  confirm(msg){calls.push(['confirm',msg]);return approve;},
  prompt(msg,defaultValue){calls.push(['prompt',msg,defaultValue]);return promptValue;}
 };
 vm.runInNewContext(manual,scope);
 vm.runInNewContext(ledger,scope);
 return {$,files};
}
const first=boot(),$=first.$;
assert.equal($('realAdd').disabled,true,'empty draft cannot be marked purchased');
assert.equal($('realROI').textContent,'—');
assert.equal($('realInvest').textContent,'0円');
$('mDate').value='2026-11-07';$('mDate').onchange();
$('mTrack').value='東京';$('mTrack').onchange();
$('mRace').value='1';$('mRace').onchange();
const choose=(id,n)=>$(id).children[n-1].onclick();
choose('mFirst',1);choose('mFirst',2);
for(let i=1;i<=4;i++)choose('mSecond',i);
for(let i=1;i<=8;i++)choose('mThird',i);
assert.equal($('mCount').textContent,'36点');
assert.equal($('realAdd').disabled,true,'non-saved formation cannot become a purchase');
$('mSave').onclick();
assert.equal($('realAdd').disabled,false,'saved formation now available');
const ledgerKey='keiba-nine-owner-real-purchases-v1';
$('realUnit').value='50';
$('realAdd').onclick();
assert.match($('realMessage').textContent,/100円単位/);
assert.equal(storage.has(ledgerKey),false);
$('realUnit').value='200';
approve=false;$('realAdd').onclick();approve=true;
assert.equal(storage.has(ledgerKey),false,'cancelled confirmation must not save');
$('realAdd').onclick();
let saved=JSON.parse(storage.get(ledgerKey));
assert.equal(saved.length,1);
assert.equal(saved[0].stake,7200);
assert.equal(saved[0].unit,200);
assert.equal(saved[0].payout,null,'payout is unknown, NOT zero');
assert.equal(saved[0].verifiedByJra,undefined);
assert.equal($('realInvest').textContent,'0円','unsettled not counted in ROI');
assert.match($('realPending').textContent,/7,200円/);
assert.equal($('realROI').textContent,'—');
assert.equal($('realList').children.length,1);
const row=$('realList').children[0];
assert.match(row.children[1].textContent,/未確定/);
assert.equal(row.children[2].textContent,'払戻を入力');
promptValue='not a number';row.children[2].onclick();
assert.match($('realMessage').textContent,/整数/);
assert.equal(JSON.parse(storage.get(ledgerKey))[0].payout,null);
promptValue='0';row.children[2].onclick();
saved=JSON.parse(storage.get(ledgerKey));
assert.equal(saved[0].payout,0,'losing tickets can settle for zero');
assert.equal($('realInvest').textContent,'7,200円');
assert.equal($('realReturn').textContent,'0円');
assert.equal($('realROI').textContent,'0.0%');
assert.equal($('realProfit').textContent,'-7,200円');
promptValue='12000';$('realList').children[0].children[2].onclick();
assert.equal($('realReturn').textContent,'12,000円');
assert.equal($('realROI').textContent,'166.7%');
assert.equal($('realProfit').textContent,'+4,800円');
$('mDate').value='2026-11-08';$('mDate').onchange();
assert.equal($('realList').children.length,1);
assert.match($('realList').children[0].textContent,/ありません/);
assert.equal($('realROI').textContent,'166.7%','ROI covers settled entries across dates');
$('mDate').value='2026-11-07';$('mDate').onchange();
assert.equal($('realList').children.length,1);
$('realExport').onclick();
assert.equal(first.files.length,2,'export backup created and URL revoked');
const second=boot(),get=second.$;
get('mDate').value='2026-11-07';get('mDate').onchange();
get('mTrack').value='東京';get('mTrack').onchange();
get('mRace').value='1';get('mRace').onchange();
assert.equal(get('realROI').textContent,'166.7%','ledger persists after reload');
assert.equal(get('realList').children.length,1);
approve=false;get('realList').children[0].children[3].onclick();approve=true;
assert.equal(JSON.parse(storage.get(ledgerKey)).length,1);
get('realList').children[0].children[3].onclick();
assert.equal(JSON.parse(storage.get(ledgerKey)).length,0);
assert.equal(get('realROI').textContent,'—');
assert.equal(get('mCount').textContent,'36点','deleting purchase never deletes draft');
assert.ok(writes.some(x=>x===ledgerKey));
assert.ok(!manual.includes('fetch(')&&!ledger.includes('fetch('));
assert.ok(!ledger.includes('innerHTML'));
console.log('Private 3連単 actual purchase ledger: confirm, ROI, payout, filter, reload, backup passed');
