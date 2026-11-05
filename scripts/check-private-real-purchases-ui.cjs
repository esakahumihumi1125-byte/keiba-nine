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
assert.equal($('realDayInvest').textContent,'0円');
assert.equal($('realDayROI').textContent,'—');
assert.match($('realDayPending').textContent,/7,200円/);
assert.equal($('realMonthSummary').children.length,1);
assert.equal($('realTrackSummary').children.length,1);
assert.match($('realMonthSummary').children[0].children[1].textContent,/回収率 —/,'unsettled only must have no ROI');
assert.match($('realMonthSummary').children[0].children[1].textContent,/未確定 1件・投資 7,200円/);
$('realPendingOnly').checked=true;$('realPendingOnly').onchange();
assert.equal($('realList').children.length,1,'Pending-only shows unsettled records');
$('realPendingOnly').checked=false;$('realPendingOnly').onchange();
assert.match($('realPending').textContent,/7,200円/);
assert.equal($('realROI').textContent,'—');
assert.equal($('realList').children.length,1);
const row=$('realList').children[0];
assert.match(row.children[1].textContent,/未確定/);
assert.match($('realReviewSummary').textContent,/結果を入力した購入記録：0件/);
assert.equal(row.children[4].textContent,'実際の1〜3着を入力');
promptValue='1-1-2';row.children[4].onclick();
assert.match($('realMessage').textContent,/異なる3頭/);
assert.equal(JSON.parse(storage.get(ledgerKey))[0].result,null);
promptValue='①②③';approve=false;row.children[4].onclick();approve=true;
assert.equal(JSON.parse(storage.get(ledgerKey))[0].result,null,'review confirmation cancellation');
promptValue='①②③';row.children[4].onclick();
assert.deepEqual(JSON.parse(storage.get(ledgerKey))[0].result,[1,2,3]);
assert.match($('realReviewSummary').textContent,/3連単買い目に一致：1件/);
assert.match($('realList').children[0].children[1].textContent,/買い目に一致/);
assert.equal($('realDayROI').textContent,'—','manual result never settles payout');
promptValue='9-2-3';$('realList').children[0].children[4].onclick();
assert.match($('realReviewSummary').textContent,/1着候補の取りこぼし：1件/);
assert.match($('realList').children[0].children[1].textContent,/1着馬が1着候補外/);
assert.equal($('realInvest').textContent,'0円','result is not used as payment proof');
promptValue='1-2-3';$('realList').children[0].children[4].onclick();
assert.match($('realReviewSummary').textContent,/3連単買い目に一致：1件/);
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
assert.equal($('realDayROI').textContent,'0.0%');
$('realPendingOnly').checked=true;$('realPendingOnly').onchange();
assert.match($('realList').children[0].textContent,/払戻待ちの馬券はありません/);
$('realPendingOnly').checked=false;$('realPendingOnly').onchange();
assert.equal($('realProfit').textContent,'-7,200円');
promptValue='12000';$('realList').children[0].children[2].onclick();
assert.equal($('realReturn').textContent,'12,000円');
assert.equal($('realROI').textContent,'166.7%');
assert.equal($('realProfit').textContent,'+4,800円');
assert.equal($('realDayInvest').textContent,'7,200円');
assert.equal($('realDayReturn').textContent,'12,000円');
assert.equal($('realDayROI').textContent,'166.7%');
assert.equal($('realDayProfit').textContent,'+4,800円');
assert.match($('realMonthSummary').children[0].children[1].textContent,/166.7%/);
assert.match($('realTrackSummary').children[0].children[1].textContent,/確定 1件/);
$('mDate').value='2026-11-08';$('mDate').onchange();
assert.equal($('realList').children.length,1);
assert.match($('realList').children[0].textContent,/ありません/);
assert.equal($('realROI').textContent,'166.7%','ROI covers settled entries across dates');
assert.equal($('realDayROI').textContent,'—','No settled entries on selected date');
assert.equal($('realDayInvest').textContent,'0円');
assert.equal($('realDayReturn').textContent,'0円');
$('mDate').value='2026-11-07';$('mDate').onchange();
assert.equal($('realList').children.length,1);
assert.equal($('realDayROI').textContent,'166.7%','Changing date back restores daily ROI');
$('realExport').onclick();
assert.equal(first.files.length,2,'export backup created and URL revoked');
const second=boot(),get=second.$;
get('mDate').value='2026-11-07';get('mDate').onchange();
get('mTrack').value='東京';get('mTrack').onchange();
get('mRace').value='1';get('mRace').onchange();
assert.equal(get('realROI').textContent,'166.7%','ledger persists after reload');
assert.match(get('realReviewSummary').textContent,/3連単買い目に一致：1件/);
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

(async()=>{
 const draftKey='keiba-nine-owner-ticket-drafts-v1';
 const originalDrafts=storage.get(draftKey),originalPurchases=storage.get(ledgerKey);
 const base=JSON.parse(originalDrafts)[0];
 const secondDay={...base,date:'2026-11-08',track:'京都',race:3};
 const draftBackup={format:'keiba-nine-owner-drafts-1',
  exportedAt:'2026-11-05T00:00:00.000Z',records:[base,secondDay]};
 const mkFile=x=>{
  const content=typeof x==='string'?x:JSON.stringify(x);
  return {size:content.length,text:async()=>content};
 };
 const useFile=async(id,value)=>{
  get(id).files=[mkFile(value)];
  return get(id).onchange();
 };
 await useFile('mImport',{...draftBackup,format:'keiba-nine-real-3rentan-v1'});
 assert.equal(storage.get(draftKey),originalDrafts,'wrong backup type must not replace drafts');
 assert.match(get('mMsg').textContent,/復元できません/);
 await useFile('mImport',{...draftBackup,records:[{...base,first:[1,1]}]});
 assert.equal(storage.get(draftKey),originalDrafts,'bad form must not replace drafts');
 await useFile('mImport',{...draftBackup,records:[base,base]});
 assert.equal(storage.get(draftKey),originalDrafts,'duplicate race must be rejected');
 approve=false;await useFile('mImport',draftBackup);approve=true;
 assert.equal(storage.get(draftKey),originalDrafts,'cancelled restore must not overwrite');
 await useFile('mImport',draftBackup);
 assert.equal(JSON.parse(storage.get(draftKey)).length,2);
 assert.equal(get('mCount').textContent,'36点');
 assert.equal(get('realAdd').disabled,false,'real purchase button refreshes after draft restore');
 assert.match(get('mMsg').textContent,/2件を復元/);
 assert.equal(get('mImport').value,'','reselecting same file must be allowed');
 await useFile('realImport',draftBackup);
 assert.equal(storage.get(ledgerKey),originalPurchases,'drafts file cannot be used as purchase file');
 const restoredPurchase={...base,id:'purchase-restore-test',unit:200,stake:7200,
  payout:12000,purchasedAt:'2026-11-05T00:00:00.000Z',result:[1,2,3]};
 const realBackup={format:'keiba-nine-real-3rentan-v1',
  exportedAt:'2026-11-05T00:00:00.000Z',records:[restoredPurchase]};
 await useFile('realImport',{...realBackup,records:[{...restoredPurchase,stake:999}]});
  await useFile('realImport',{...realBackup,records:[{...restoredPurchase,result:[1,1,2]}]});
  assert.equal(storage.get(ledgerKey),originalPurchases,'invalid 3-horse result must not import');
 assert.equal(storage.get(ledgerKey),originalPurchases,'tampered stake must be rejected');
 await useFile('realImport',{...realBackup,records:[restoredPurchase,restoredPurchase]});
 assert.equal(storage.get(ledgerKey),originalPurchases,'duplicate purchase id must be rejected');
 get('realImport').files=[{size:1024*1024+1,text:async()=>JSON.stringify(realBackup)}];
 await get('realImport').onchange();
 assert.equal(storage.get(ledgerKey),originalPurchases,'oversized files must be rejected');
 approve=false;await useFile('realImport',realBackup);approve=true;
 assert.equal(storage.get(ledgerKey),originalPurchases,'cancelled purchase restore must not overwrite');
 await useFile('realImport',realBackup);
 const imported=JSON.parse(storage.get(ledgerKey));
 assert.equal(imported.length,1);
 assert.equal(imported[0].payout,12000);
  assert.deepEqual(imported[0].result,[1,2,3],'restore keeps finishing order');
 assert.equal(get('realInvest').textContent,'7,200円');
 assert.equal(get('realReturn').textContent,'12,000円');
 assert.equal(get('realROI').textContent,'166.7%');
 assert.match(get('realMessage').textContent,/1件を復元/);
 assert.equal(get('realImport').value,'');
 const reload=boot(),r=reload.$;
 assert.equal(r('realROI').textContent,'166.7%','restored purchase persists across reload');
  assert.match(r('realReviewSummary').textContent,/3連単買い目に一致：1件/);
 r('mDate').value='2026-11-08';r('mDate').onchange();
 r('mTrack').value='京都';r('mTrack').onchange();
 r('mRace').value='3';r('mRace').onchange();
 assert.equal(r('mCount').textContent,'36点','draft for another date restores');
  const settled=JSON.parse(storage.get(ledgerKey))[0];
  const mixData=[settled,
    {...settled,id:'pending-kyoto',date:'2026-11-08',track:'京都',race:3,payout:null},
    {...settled,id:'loss-tokyo',date:'2026-12-05',track:'東京',race:5,payout:0}];
  storage.set(ledgerKey,JSON.stringify(mixData));
  const mixed=boot(),show=mixed.$;
  assert.equal(show('realInvest').textContent,'14,400円','exclude pending stake globally');
  assert.equal(show('realReturn').textContent,'12,000円');
  assert.equal(show('realROI').textContent,'83.3%','zero payout is settled loss');
  const months=show('realMonthSummary').children;
  assert.equal(months.length,2,'group 2 months');
  assert.equal(months[0].children[0].textContent,'2026-12','latest month first');
  assert.match(months[0].children[1].textContent,/回収率 0.0%/);
  assert.match(months[1].children[1].textContent,/回収率 166.7%/);
  assert.match(months[1].children[1].textContent,/未確定 1件・投資 7,200円/);
  const tracks=show('realTrackSummary').children;
  assert.equal(tracks.length,2,'group by track');
  const tokyo=tracks.find(row=>row.children[0].textContent==='東京');
  const kyoto=tracks.find(row=>row.children[0].textContent==='京都');
  assert.match(tokyo.children[1].textContent,/回収率 83.3%/);
  assert.match(kyoto.children[1].textContent,/回収率 —/,'pending-only track is not assigned zero ROI');
  assert.match(kyoto.children[1].textContent,/未確定 1件・投資 7,200円/);

 assert.ok(!manual.includes('fetch(')&&!ledger.includes('fetch('));
 console.log('Private owner JSON restore: validated drafts and purchases, cancellation, duplicates, wrong type, reload, ROI passed');
})().catch(err=>{console.error(err);process.exitCode=1});

