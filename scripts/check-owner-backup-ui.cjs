/* Browser-only 5-section backup import/export safety tests; synthetic horse names. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const js=fs.readFileSync('/tmp/keiba-owner-backup.js','utf8');
const keys=[
 'keiba-nine-owner-ticket-drafts-v1',
 'keiba-nine-owner-real-purchases-v1',
 'keiba-nine-jrdb-personal-mail-v1',
 'keiba-nine-owner-manual-numbers-v1',
 'keiba-nine-owner-factor-notes-v1'
],format='keiba-nine-owner-local-all-v2';
const source={race:1,postTime:'09:55',expected:3,horses:['架空A','架空B','架空C']};
const first={date:'2099-01-09',track:'東京',race:1,first:[1],second:[2],third:[3],savedAt:'2099-01-08T12:00:00+09:00'};
const purchase={...first,id:'draft-001',unit:100,stake:100,payout:null,purchasedAt:'2099-01-09T09:00:00+09:00'};
const mail={kind:'jrdb-provisional',date:'2099-01-09',track:'東京',races:[source]};
const memo={date:'2099-01-09',track:'東京',race:1,
 sourceMark:JSON.stringify([source.postTime,source.expected,source.horses]),
 rows:[{number:1,name:'架空A'},{number:2,name:'架空B'},{number:3,name:'架空C'}]};
const factor={date:'2099-01-09',track:'東京',race:1,text:'1 架空A A ? A B C',sourceMark:memo.sourceMark,savedAt:'2099-01-08T12:00:00+09:00'};
const fixture=()=>({
 [keys[0]]:[first],[keys[1]]:[purchase],[keys[2]]:[mail],[keys[3]]:[memo],[keys[4]]:[factor]
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
  ...fixture(),[keys[0]]:[],[keys[1]]:[],[keys[2]]:[],[keys[3]]:[],[keys[4]]:[]
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
 assert.deepEqual([...page.storage.entries()],original,'quota failure rolls back all 5 sections');
 assert.match(e('backupPreview').textContent,/元の5種類の記録へ戻しました/);
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
 // Previous (four-part) exports remain importable and preserve existing factor notes.
 page.storage.set(keys[4],JSON.stringify([factor]));
 const fourParts=fixture();delete fourParts[keys[4]];
 const legacyFile=fakeFile(JSON.stringify({
  format:'keiba-nine-owner-local-all-v1',exportedAt:'2099-01-08T23:00:00Z',sections:fourParts
 }));
 e('backupFile').files=[legacyFile];await e('backupFile').onchange();await flush();
 assert.equal(e('backupRestore').disabled,false);
 assert.match(e('backupPreview').textContent,/旧4種類のバックアップ/);
 e('backupRestore').onclick();
 assert.deepEqual(JSON.parse(page.storage.get(keys[4])),[factor],
  'legacy restore preserves ongoing factor scoring notes');
 const afterLegacy=[...page.storage.entries()];
 const malformedLegacy={...fourParts,[keys[4]]:[]};
 const extraLegacy=fakeFile(JSON.stringify({format:'keiba-nine-owner-local-all-v1',
  exportedAt:'2099-01-08T23:00:00Z',sections:malformedLegacy}));
 e('backupFile').files=[extraLegacy];await e('backupFile').onchange();await flush();
 assert.equal(e('backupRestore').disabled,true,'old backup must have precisely four sections');
 assert.deepEqual([...page.storage.entries()],afterLegacy);

 console.log('Owner local 5-part backup: export, restore, consent, schema, quota rollback and no upload PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
