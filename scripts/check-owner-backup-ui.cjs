/* Browser-only nine-section backup with legacy 4/5/6/7-section safety tests. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const js=fs.readFileSync('/tmp/keiba-owner-backup.js','utf8');
const keys=[
 'keiba-nine-owner-ticket-drafts-v1',
 'keiba-nine-owner-real-purchases-v1',
 'keiba-nine-jrdb-personal-mail-v1',
 'keiba-nine-owner-manual-numbers-v1',
 'keiba-nine-owner-factor-notes-v1',
 'keiba-nine-jrdb-preday-runners-v1',
 'keiba-nine-owner-server-receipts-v1',
 'keiba-nine-owner-rebound-watch-receipts-v1',
 'keiba-nine-owner-three-core-receipts-v1',
 'keiba-nine-owner-five-core-receipts-v1',
 'keiba-nine-owner-research6-draft-receipts-v1'
],format='keiba-nine-owner-local-all-v8';
const source={race:1,postTime:'09:55',expected:3,horses:['架空A','架空B','架空C']};
const first={date:'2099-01-09',track:'東京',race:1,first:[1],second:[2],third:[3],savedAt:'2099-01-08T12:00:00+09:00'};
const purchase={...first,id:'draft-001',unit:100,stake:100,payout:null,purchasedAt:'2099-01-09T09:00:00+09:00'};
const mail={kind:'jrdb-provisional',date:'2099-01-09',track:'東京',races:[source]};
const memo={date:'2099-01-09',track:'東京',race:1,
 sourceMark:JSON.stringify([source.postTime,source.expected,source.horses]),
 rows:[{number:1,name:'架空A'},{number:2,name:'架空B'},{number:3,name:'架空C'}]};
const factor={date:'2099-01-09',track:'東京',race:1,text:'1 架空A A ? A B C',sourceMark:memo.sourceMark,savedAt:'2099-01-08T12:00:00+09:00'};
const preday={kind:'jrdb-preday-provisional',date:'2099-01-09',track:'東京',races:[
 {race:1,postTime:'09:55',expected:3,runners:[
  {number:1,name:'架空A',style:'逃'},{number:2,name:'架空B',style:'先'},{number:3,name:'架空C',style:'未確認'}
 ]}]};
const signedReceipt={signature:'a'.repeat(64),snapshot:{
 date:'2099-01-09',track:'東京',race:1,
 sourceKind:'prestart-locked',actualPurchase:false,
 lockedAt:'2099-01-08T18:00:00+09:00',
 scheduledOffAt:'2099-01-09T09:55:00+09:00',
 trifectaTickets:[[1,2,3]],trioTickets:[],
 scheduleVerified:false,predictionVerified:false
}};
const reboundWatch={signature:'b'.repeat(64),snapshot:{
 version:'owner-rebound-watch-receipt-1',
 date:'20990109',track:'東京',race:1,
 sourceKind:'server-prestart-research-watch',
 capturedAt:'2099-01-09T07:15:00+09:00',
 scheduledOffAt:'2099-01-09T09:55:00+09:00',
 watch:[{number:4,reviewState:'cross_source_review'},
        {number:9,reviewState:'need_more_evidence'}],
 researchOnly:true,officialJraVerified:false,actualPurchase:false,
 winnerPickReady:false,captureAuditVerified:false
}};
const coreStudy={signature:'c'.repeat(64),snapshot:{
 version:'owner-three-core-receipt-1',
 date:'20990109',track:'東京',race:1,
 sourceKind:'prestart-uncalibrated-70-research',
 capturedAt:'2099-01-09T07:15:00+09:00',
 scheduledOffAt:'2099-01-09T09:55:00+09:00',
 raceRunnerCount:3,observedRunnerCount:1,
 horses:[{number:1,bands:{
  training:'S',course_distance:'A',pace:'B'
 },rawThirdPoints:150}],
 researchOnly:true,officialJraVerified:false,
 sourceHypothesesUncalibrated:true,actualPurchase:false,
 predictionReady:false
}};
const fiveStudy={signature:'d'.repeat(64),snapshot:{
 version:'owner-five-core-receipt-1',
 date:'20990109',track:'東京',race:1,
 sourceKind:'prestart-uncalibrated-85-research',
 capturedAt:'2099-01-09T07:15:00+09:00',
 scheduledOffAt:'2099-01-09T09:55:00+09:00',
 raceRunnerCount:3,observedRunnerCount:1,
 horses:[{number:1,bands:{
  training:'S',course_distance:'A',pace:'B',ground:'A',recent:'C'
 },rawThirdPoints:174}],
 researchOnly:true,officialJraVerified:false,
 sourceHypothesesUncalibrated:true,actualPurchase:false,
 predictionReady:false
}};
const r6First=[1,2],r6Second=[1,2,3,4,5],
 r6Third=[1,2,3,4,5,6,7];
const r6Tickets=[];
for(const a of r6First)for(const b of r6Second)for(const c of r6Third)
 if(a!==b&&a!==c&&b!==c)r6Tickets.push([a,b,c]);
const research6Draft={signature:'e'.repeat(64),snapshot:{
 version:'owner-research6-draft-receipt-1',
 date:'20990109',track:'東京',race:1,
 sourceKind:'prestart-unverified-research6-79-draft',
 capturedAt:'2099-01-09T07:15:00+09:00',
 scheduledOffAt:'2099-01-09T09:55:00+09:00',
 policyVersion:'research-6',researchWeight:79,
 remainingUnassessedWeight:21,runnerCount:7,
 first:r6First,second:r6Second,third:r6Third,
 tickets:r6Tickets,points:40,amountYen:4000,
 researchOnly:true,officialJraVerified:false,
 predictionReady:false,actualPurchase:false
}};
const fixture=()=>({
 [keys[0]]:[first],[keys[1]]:[purchase],[keys[2]]:[mail],
 [keys[3]]:[memo],[keys[4]]:[factor],[keys[5]]:[preday],
 [keys[6]]:[signedReceipt],[keys[7]]:[reboundWatch],
 [keys[8]]:[coreStudy],[keys[9]]:[fiveStudy],
 [keys[10]]:[research6Draft]
});
function boot(initial=fixture()){
 const storage=new Map(Object.entries(initial).map(([k,v])=>[k,JSON.stringify(v)]));
 const nodes=new Map(),urls=[],downloads=[];
 let confirmDecision=true,failWrite=null;
 function element(tag='div'){
  return {tag,value:'',textContent:'',disabled:false,files:[],type:'',
   onclick:null,onchange:null,href:'',download:'',
   append(...a){this.children.push(...a)},children:[],
   click(){downloads.push({href:this.href,name:this.download})},
   remove(){this.removed=true},replaceChildren(){this.children=[]}};
 }
 function $(id){if(!nodes.has(id)){
   const item=element();
   if(id==='backupRestore')item.disabled=true;
   nodes.set(id,item);
  }return nodes.get(id);
 }
 const localStorage={
  getItem:k=>storage.get(k)||null,
  setItem(k,v){if(failWrite===k){failWrite=null;throw Error('quota')}storage.set(k,v)},
  removeItem:k=>storage.delete(k)
 };
 const body={append:el=>{el.parent=body}};
 const URL={createObjectURL:()=>{urls.push('blob:test');return 'blob:test'},revokeObjectURL:x=>urls.push('revoked:'+x)};
 const ctx={document:{getElementById:$,createElement:element,body},localStorage,
  Blob:class Blob{constructor(items,o){this.items=items;this.type=o.type}},
  Date,JSON,Set,Map,Number,String,Array,Error,URL,
  confirm:()=>confirmDecision,setTimeout:fn=>fn(),console};
 vm.runInNewContext(js,ctx);
 return {el:$,storage,urls,downloads,setConfirm:v=>{confirmDecision=v},
   failOnWrite:k=>{failWrite=k}};
}
const flush=async()=>{await Promise.resolve();await Promise.resolve();await new Promise(r=>setImmediate(r))};
const fakeFile=contents=>({size:Buffer.byteLength(contents,'utf8'),text:async()=>contents});
(async()=>{
 const page=boot(),e=page.el;
 assert.match(e('backupSummary').textContent,/下書き1R／購入記録1件／想定メール1開催／馬番メモ1R/);
 assert.equal(e('backupDownload').disabled,false);
 assert.equal(boot({...fixture(),[keys[0]]:[{...first,result:[1,2,3]}]}).el('backupDownload').disabled,false,'reviewed unsold draft remains included in private backup');
 assert.equal(boot({...fixture(),[keys[1]]:[{...purchase,result:[1,2,3]}]}).el('backupDownload').disabled,false,'finished notes remain part of same five-part backup');
 e('backupDownload').onclick();
 assert.equal(page.downloads.length,1,'one file download only');
 assert.match(page.downloads[0].name,/^keiba-nine-private-backup-\d{4}-\d{2}-\d{2}\.json$/);
 assert.equal(page.urls[0],'blob:test');
 assert.equal(page.urls[1],'revoked:blob:test');
 const before=[...page.storage.entries()];
 const goodBackup={format,exportedAt:'2099-01-08T23:00:00Z',sections:{
  ...fixture(),[keys[0]]:[],[keys[1]]:[],[keys[2]]:[],[keys[3]]:[],[keys[4]]:[],[keys[5]]:[],[keys[6]]:[],[keys[7]]:[],[keys[8]]:[],[keys[9]]:[],[keys[10]]:[]
 }};
 let file=fakeFile(JSON.stringify(goodBackup));
 e('backupFile').files=[file];await e('backupFile').onchange();await flush();
 assert.equal(e('backupRestore').disabled,false);
 assert.match(e('backupPreview').textContent,/下書き0R／購入記録0件/);
 page.setConfirm(false);e('backupRestore').onclick();
 assert.deepEqual([...page.storage.entries()],before,'cancel cannot erase purchases');
 page.setConfirm(true);
 e('backupRestore').onclick();
 for(const k of keys)assert.deepEqual(JSON.parse(page.storage.get(k)),[]);
 assert.equal(e('backupRestore').disabled,true);
 assert.match(e('backupPreview').textContent,/復元しました/);
 const afterEmpty=[...page.storage.entries()];
 for(const [label,bad] of [
  ['other-format',{...goodBackup,format:'random-export'}],
  ['missing-ledger',{...goodBackup,sections:{[keys[0]]:[],[keys[2]]:[],[keys[3]]:[]}}],
  ['extra-record',{...goodBackup,sections:{...fixture(),extra:[]}}],
  ['invalid-purchase',{...goodBackup,sections:{...fixture(),[keys[1]]:[{...purchase,stake:123} ]}}],
  ['invalid-draft-result',{...goodBackup,sections:{...fixture(),[keys[0]]:[{...first,result:[1,1,2]}]}}],
  ['invalid-finish',{...goodBackup,sections:{...fixture(),[keys[1]]:[{...purchase,result:[1,1,2]}]}}],
  ['duplicated-horse',{...goodBackup,sections:{...fixture(),[keys[2]]:[{...mail,races:[{...source,horses:['架空A','架空A','架空C']}]}]}}],
  ['duplicate-record',{...goodBackup,sections:{...fixture(),[keys[0]]:[first,first]}}],
  ['37 invalid race',{...goodBackup,sections:{...fixture(),[keys[0]]:[{...first,race:13}]}}]
 ]){
  file=fakeFile(JSON.stringify(bad));e('backupFile').files=[file];
  await e('backupFile').onchange();await flush();
  assert.equal(e('backupRestore').disabled,true,label+' must fail preview');
  assert.match(e('backupPreview').textContent,/読み込めません/);
  assert.deepEqual([...page.storage.entries()],afterEmpty,label+' must not write');
 }
 file={size:2500001,text:async()=>{throw Error('must not read large file')}};
 e('backupFile').files=[file];await e('backupFile').onchange();await flush();
 assert.equal(e('backupRestore').disabled,true);
 assert.match(e('backupPreview').textContent,/2\.5MB/);
 // Pre-reviewed source changed: refuse overwriting data which changed meanwhile.
 file=fakeFile(JSON.stringify({format,exportedAt:'2099-01-08T23:00:00Z',sections:fixture()}));
 e('backupFile').files=[file];await e('backupFile').onchange();await flush();
 assert.equal(e('backupRestore').disabled,false);
 page.storage.set(keys[0],JSON.stringify([first]));
 const changed=[...page.storage.entries()];
 e('backupRestore').onclick();
 assert.equal(e('backupRestore').disabled,true);
 assert.deepEqual([...page.storage.entries()],changed,'stale preview cannot clobber edits');
 // Storage failure during restore must roll back all five keys.
 e('backupFile').files=[file];await e('backupFile').onchange();await flush();
 page.failOnWrite(keys[2]);
 const original=[...page.storage.entries()];
 e('backupRestore').onclick();
 assert.deepEqual([...page.storage.entries()],original,'quota failure rolls back all 6 sections');
 assert.match(e('backupPreview').textContent,/元の11種類の記録へ戻しました/);
 assert.equal(e('backupRestore').disabled,true);
 // A corrupted local section blocks export until the user resolves it.
 const corrupted=boot({...fixture(),[keys[1]]:[{...purchase,payout:-1}]});
 assert.equal(corrupted.el('backupDownload').disabled,true);
 assert.match(corrupted.el('backupSummary').textContent,/不正な形式/);
 assert.ok(!js.includes('fetch('),'backup code must not transmit provider or betting data');
 assert.ok(!js.includes('XMLHttpRequest'),'backup must remain local');
 assert.ok(!js.includes('innerHTML'),'do not inject imported content as HTML');

 // Malformed factor-grade backups must never overwrite valid records.
 for(const badFactor of [
  {...factor,race:13},{...factor,text:''},{...factor,sourceMark:'x'.repeat(1600)},
  {...factor,sourceMark:42},{...factor,savedAt:''}
 ]){
  const current=[...page.storage.entries()];
  const invalidFile=fakeFile(JSON.stringify({format,exportedAt:'2099-01-08T23:00:00Z',
   sections:{...fixture(),[keys[4]]:[badFactor]}}));
  e('backupFile').files=[invalidFile];await e('backupFile').onchange();await flush();
  assert.equal(e('backupRestore').disabled,true,'bad factor note cannot restore');
  assert.deepEqual([...page.storage.entries()],current,'bad factor note has zero writes');
 }
 // The previous full ten-part v7 format must never clear new 79 picks.
 const legacy10=fixture();delete legacy10[keys[10]];
 const old10=fakeFile(JSON.stringify({
  format:'keiba-nine-owner-local-all-v7',
  exportedAt:'2099-01-08T23:00:00Z',sections:legacy10
 }));
 const v7=boot(fixture()),before79=v7.storage.get(keys[10]);
 v7.el('backupFile').files=[old10];await v7.el('backupFile').onchange();await flush();
 assert.equal(v7.el('backupRestore').disabled,false);
 assert.match(v7.el('backupPreview').textContent,/旧10種類のバックアップ/);
 v7.el('backupRestore').onclick();
 assert.equal(v7.storage.get(keys[10]),before79,
  'legacy backup cannot erase signed research6 first-write tickets');
 assert.match(boot(fixture()).el('backupSummary').textContent,/79点研究下書き固定1R/);
 for(const damage of [
  {...research6Draft,signature:'WRONG'},
  {...research6Draft,snapshot:{...research6Draft.snapshot,points:39}},
  {...research6Draft,snapshot:{...research6Draft.snapshot,amountYen:4500}},
  {...research6Draft,snapshot:{...research6Draft.snapshot,officialJraVerified:true}},
  {...research6Draft,snapshot:{...research6Draft.snapshot,first:[2,1]}},
  {...research6Draft,snapshot:{...research6Draft.snapshot,
   capturedAt:'2099-01-09T10:00:00+09:00'}},
 ]){
  const app=boot({...fixture(),[keys[10]]:[damage]});
  assert.equal(app.el('backupDownload').disabled,true,
   'malformed 79-point first-write receipt cannot be exported');
 }
 assert.equal(boot({...fixture(),[keys[10]]:[
  research6Draft,research6Draft]}).el('backupDownload').disabled,true);
 // Old nine-section v6 backup must not remove newly fixed 85-point records.
 const oldNine=fixture();for(const key of keys.slice(9))delete oldNine[key];
 const legacyNine=fakeFile(JSON.stringify({format:'keiba-nine-owner-local-all-v6',
  exportedAt:'2099-01-08T23:00:00Z',sections:oldNine}));
 const current85=boot(fixture()),original85=current85.storage.get(keys[9]);
 current85.el('backupFile').files=[legacyNine];
 await current85.el('backupFile').onchange();await flush();
 assert.equal(current85.el('backupRestore').disabled,false);
 assert.match(current85.el('backupPreview').textContent,/旧9種類のバックアップ/);
 current85.el('backupRestore').onclick();
 assert.equal(current85.storage.get(keys[9]),original85);
 const fakeFive=boot({...fixture(),[keys[9]]:[
  {...fiveStudy,snapshot:{...fiveStudy.snapshot,
   horses:[{...fiveStudy.snapshot.horses[0],rawThirdPoints:255}]}}
 ]});
 assert.equal(fakeFive.el('backupDownload').disabled,true,
  'impossible 85-point arithmetic must block backup export');
 const duplicated=boot({...fixture(),[keys[9]]:[fiveStudy,fiveStudy]});
 assert.equal(duplicated.el('backupDownload').disabled,true);
 // Previous (four-part) exports remain importable and preserve existing factor notes.
 page.storage.set(keys[4],JSON.stringify([factor]));
 const fourParts=fixture();for(const k of keys.slice(4))delete fourParts[k];
 const legacyFile=fakeFile(JSON.stringify({
  format:'keiba-nine-owner-local-all-v1',exportedAt:'2099-01-08T23:00:00Z',sections:fourParts
 }));
 e('backupFile').files=[legacyFile];await e('backupFile').onchange();await flush();
 assert.equal(e('backupRestore').disabled,false);
 assert.match(e('backupPreview').textContent,/旧4種類のバックアップ/);
 e('backupRestore').onclick();
 assert.deepEqual(JSON.parse(page.storage.get(keys[4])),[factor],
  'legacy restore preserves ongoing factor scoring notes');
 assert.deepEqual(JSON.parse(page.storage.get(keys[5])),[],
  'legacy four-part backup preserves the untouched pre-day section');
 const afterLegacy=[...page.storage.entries()];
 const malformedLegacy={...fourParts,[keys[4]]:[]};
 const extraLegacy=fakeFile(JSON.stringify({format:'keiba-nine-owner-local-all-v1',
  exportedAt:'2099-01-08T23:00:00Z',sections:malformedLegacy}));
 e('backupFile').files=[extraLegacy];await e('backupFile').onchange();await flush();
 assert.equal(e('backupRestore').disabled,true,'old backup must have precisely four sections');
 assert.deepEqual([...page.storage.entries()],afterLegacy);

 // Reject malformed or oversize pre-day data: a private file must not bypass
 // the original browser importer validation or overwrite unrelated records.
 for(const broken of [
  {...preday,races:[{...preday.races[0],expected:4}]},
  {...preday,races:[{...preday.races[0],runners:[
   preday.races[0].runners[0],preday.races[0].runners[0],preday.races[0].runners[2]
  ]}]},
  {...preday,races:[{...preday.races[0],runners:[
   {...preday.races[0].runners[0],style:'AI-S'},
   ...preday.races[0].runners.slice(1)
  ]}]},
  {...preday,date:'2099-02-31'}
 ]){
  const current=[...page.storage.entries()];
  const bad=fakeFile(JSON.stringify({format,exportedAt:'2099-01-08T23:00:00Z',
   sections:{...fixture(),[keys[5]]:[broken]}}));
  e('backupFile').files=[bad];await e('backupFile').onchange();await flush();
  assert.equal(e('backupRestore').disabled,true,'invalid pre-day runner file must be rejected');
  assert.deepEqual([...page.storage.entries()],current,'invalid pre-day roster never changes data');
 }
 // Previous five-section exports remain importable without erasing a newer
 // pre-day 36R roster (the extra sixth section is not in the old file).
 const legacyFive=fixture();for(const k of keys.slice(5))delete legacyFive[k];
 page.storage.set(keys[5],JSON.stringify([preday]));
 const older=fakeFile(JSON.stringify({format:'keiba-nine-owner-local-all-v2',
  exportedAt:'2099-01-08T23:00:00Z',sections:legacyFive}));
 e('backupFile').files=[older];await e('backupFile').onchange();await flush();
 assert.equal(e('backupRestore').disabled,false);
 assert.match(e('backupPreview').textContent,/旧5種類のバックアップ/);
 e('backupRestore').onclick();
 assert.deepEqual(JSON.parse(page.storage.get(keys[5])),[preday],
  'restore older 5-part backup preserves the current private pre-day roster');
 // Tamper-evident receipts are backed up but HMAC verification still belongs
 // to the authenticated server when they are used for the 100-yen review.
 const currentSeven=boot(fixture());
 assert.match(currentSeven.el('backupSummary').textContent,/固定記録1R/);
 assert.equal(currentSeven.el('backupDownload').disabled,false);
 for(const tamper of [
  {...signedReceipt,signature:'BAD'},
  {...signedReceipt,snapshot:{...signedReceipt.snapshot,lockedAt:'2099-01-10T10:00:00+09:00'}},
  {...signedReceipt,snapshot:{...signedReceipt.snapshot,trifectaTickets:[[1,1,2]]}}
 ]){
  const invalid=boot({...fixture(),[keys[6]]:[tamper]});
  assert.equal(invalid.el('backupDownload').disabled,true,
   'malformed receipt must not be copied into a new backup');
 }
 // A v3 six-part backup never erases the newer seventh collection.
 const legacySix=fixture();for(const k of keys.slice(6))delete legacySix[k];
 const existing=boot(fixture());
 const oldSix=fakeFile(JSON.stringify({
  format:'keiba-nine-owner-local-all-v3',
  exportedAt:'2099-01-08T23:00:00Z',sections:legacySix
 }));
 existing.el('backupFile').files=[oldSix];
 await existing.el('backupFile').onchange();await flush();
 assert.equal(existing.el('backupRestore').disabled,false);
 existing.el('backupRestore').onclick();
 assert.deepEqual(JSON.parse(existing.storage.get(keys[6])),[signedReceipt],
  'restoring v3 backup must preserve sealed receipts');
 assert.deepEqual(JSON.parse(existing.storage.get(keys[7])),[reboundWatch],
  'restoring v3 backup must preserve protected rebound watches');
 // Version 4 seven-part backup should preserve the eighth (new) watch
 // collection: older backup files cannot erase predictions captured later.
 const legacySeven=fixture();for(const k of keys.slice(7))delete legacySeven[k];
 const v4=boot(fixture());
 const oldSeven=fakeFile(JSON.stringify({
  format:'keiba-nine-owner-local-all-v4',
  exportedAt:'2099-01-08T23:00:00Z',sections:legacySeven
 }));
 v4.el('backupFile').files=[oldSeven];
 await v4.el('backupFile').onchange();await flush();
 assert.equal(v4.el('backupRestore').disabled,false);
 assert.match(v4.el('backupPreview').textContent,/旧7種類のバックアップ/);
 v4.el('backupRestore').onclick();
 assert.deepEqual(JSON.parse(v4.storage.get(keys[7])),[reboundWatch],
  'v4 restore must preserve existing new rebound capture');
 // A v5 eight-part backup must NOT erase the new signed 70-point
 // research snapshot, just as older v3/v4 never erase newer sections.
 const legacyEight=fixture();for(const k of keys.slice(8))delete legacyEight[k];
 const v5=boot(fixture());
 const oldEight=fakeFile(JSON.stringify({
  format:'keiba-nine-owner-local-all-v5',
  exportedAt:'2099-01-08T23:00:00Z',sections:legacyEight
 }));
 v5.el('backupFile').files=[oldEight];
 await v5.el('backupFile').onchange();await flush();
 assert.equal(v5.el('backupRestore').disabled,false);
 assert.match(v5.el('backupPreview').textContent,/旧8種類のバックアップ/);
 v5.el('backupRestore').onclick();
 assert.deepEqual(JSON.parse(v5.storage.get(keys[8])),[coreStudy],
  'v5 restore must not erase first-write prestart 70-point study');
 // A full nine-part file round-trips both kinds of signed research.
 const full=boot(fixture());
 assert.match(full.el('backupSummary').textContent,/巻き返し候補1R/);
 assert.equal(full.el('backupDownload').disabled,false);
 const snapshotFile=fakeFile(JSON.stringify({
  format,exportedAt:'2099-01-08T23:00:00Z',sections:fixture()
 }));
 full.el('backupFile').files=[snapshotFile];
 await full.el('backupFile').onchange();await flush();
 assert.equal(full.el('backupRestore').disabled,false);
 full.el('backupRestore').onclick();
 assert.deepEqual(JSON.parse(full.storage.get(keys[7])),[reboundWatch]);
 assert.deepEqual(JSON.parse(full.storage.get(keys[8])),[coreStudy]);
 assert.match(full.el('backupSummary').textContent,/70点研究固定1R/);
 for(const bad of [
  {...coreStudy,signature:'WRONG'},
  {...coreStudy,snapshot:{...coreStudy.snapshot,actualPurchase:true}},
  {...coreStudy,snapshot:{...coreStudy.snapshot,officialJraVerified:true}},
  {...coreStudy,snapshot:{...coreStudy.snapshot,capturedAt:'2099-01-09T11:00:00+09:00'}},
  {...coreStudy,snapshot:{...coreStudy.snapshot,horses:[{number:1,bands:{
    training:'S',course_distance:'A',pace:'B'
   },rawThirdPoints:200}]}},
  {...coreStudy,snapshot:{...coreStudy.snapshot,horses:[{number:1,bands:{
    training:'未評価',course_distance:'A',pace:'B'
   },rawThirdPoints:150}]}}
 ]){
  const invalid=boot({...fixture(),[keys[8]]:[bad]});
  assert.equal(invalid.el('backupDownload').disabled,true);
  const file=fakeFile(JSON.stringify({
   format,exportedAt:'2099-01-08T23:00:00Z',
   sections:{...fixture(),[keys[8]]:[bad]}
  }));
  full.el('backupFile').files=[file];
  await full.el('backupFile').onchange();await flush();
  assert.equal(full.el('backupRestore').disabled,true);
 }
 assert.equal(boot({...fixture(),[keys[8]]:[coreStudy,coreStudy]})
  .el('backupDownload').disabled,true);
 // Never export or restore malicious/retroactive/colliding watch records.
 for(const damaged of [
  {...reboundWatch,signature:'wrong'},
  {...reboundWatch,snapshot:{...reboundWatch.snapshot,officialJraVerified:true}},
  {...reboundWatch,snapshot:{...reboundWatch.snapshot,capturedAt:'2099-01-09T11:00:00+09:00'}},
  {...reboundWatch,snapshot:{...reboundWatch.snapshot,scheduledOffAt:'2099-01-10T09:55:00+09:00'}},
  {...reboundWatch,snapshot:{...reboundWatch.snapshot,watch:[{number:4,reviewState:'unknown'}]}},
  {...reboundWatch,snapshot:{...reboundWatch.snapshot,watch:[{number:9,reviewState:'need_more_evidence'},{number:4,reviewState:'cross_source_review'}]}},
  {...reboundWatch,snapshot:{...reboundWatch.snapshot,watch:[{number:4,reviewState:'cross_source_review'},{number:4,reviewState:'need_more_evidence'}]}}
 ]){
  const invalid=boot({...fixture(),[keys[7]]:[damaged]});
  assert.equal(invalid.el('backupDownload').disabled,true,
   'corrupt rebound watch cannot be exported');
  const current=[...full.storage.entries()];
  const badFile=fakeFile(JSON.stringify({
   format,exportedAt:'2099-01-08T23:00:00Z',
   sections:{...fixture(),[keys[7]]:[damaged]}
  }));
  full.el('backupFile').files=[badFile];
  await full.el('backupFile').onchange();await flush();
  assert.equal(full.el('backupRestore').disabled,true,
   'corrupt rebound watch cannot be imported');
  assert.deepEqual([...full.storage.entries()],current,
   'invalid restored watch must never mutate current history');
 }
 const double=boot({...fixture(),[keys[7]]:[reboundWatch,reboundWatch]});
 assert.equal(double.el('backupDownload').disabled,true,
  'duplicate sealed race must be rejected');
 assert.ok(!js.includes('fetch('),'all eleven sections must remain browser-local');
 console.log('Owner local nine-part backup: rebound watch preservation, legacy restore, quota rollback PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
