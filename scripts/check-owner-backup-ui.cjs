/* Browser-only 4-section backup import/export safety tests; synthetic horse names. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const js=fs.readFileSync('/tmp/keiba-owner-backup.js','utf8');
const keys=[
 'keiba-nine-owner-ticket-drafts-v1',
 'keiba-nine-owner-real-purchases-v1',
 'keiba-nine-jrdb-personal-mail-v1',
 'keiba-nine-owner-manual-numbers-v1'
],format='keiba-nine-owner-local-all-v1';
const source={race:1,postTime:'09:55',expected:3,horses:['架空A','架空B','架空C']};
const first={date:'2099-01-09',track:'東京',race:1,first:[1],second:[2],third:[3],savedAt:'2099-01-08T12:00:00+09:00'};
const purchase={...first,id:'draft-001',unit:100,stake:100,payout:null,purchasedAt:'2099-01-09T09:00:00+09:00'};
const mail={kind:'jrdb-provisional',date:'2099-01-09',track:'東京',races:[source]};
const memo={date:'2099-01-09',track:'東京',race:1,
 sourceMark:JSON.stringify([source.postTime,source.expected,source.horses]),
 rows:[{number:1,name:'架空A'},{number:2,name:'架空B'},{number:3,name:'架空C'}]};
const fixture=()=>({
 [keys[0]]:[first],[keys[1]]:[purchase],[keys[2]]:[mail],[keys[3]]:[memo]
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
 e('backupDownload').onclick();
 assert.equal(page.downloads.length,1,'one file download only');
 assert.match(page.downloads[0].name,/^keiba-nine-private-backup-\d{4}-\d{2}-\d{2}\.json$/);
 assert.equal(page.urls[0],'blob:test');
 assert.equal(page.urls[1],'revoked:blob:test');
 const before=[...page.storage.entries()];
 const goodBackup={format,exportedAt:'2099-01-08T23:00:00Z',sections:{
  ...fixture(),[keys[0]]:[],[keys[1]]:[],[keys[2]]:[],[keys[3]]:[]
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
 // Storage failure during restore must roll back all four keys.
 e('backupFile').files=[file];await e('backupFile').onchange();await flush();
 page.failOnWrite(keys[2]);
 const original=[...page.storage.entries()];
 e('backupRestore').onclick();
 assert.deepEqual([...page.storage.entries()],original,'quota failure rolls back all 4 sections');
 assert.match(e('backupPreview').textContent,/元の4種類の記録へ戻しました/);
 assert.equal(e('backupRestore').disabled,true);
 // A corrupted local section blocks export until the user resolves it.
 const corrupted=boot({...fixture(),[keys[1]]:[{...purchase,payout:-1}]});
 assert.equal(corrupted.el('backupDownload').disabled,true);
 assert.match(corrupted.el('backupSummary').textContent,/不正な形式/);
 assert.ok(!js.includes('fetch('),'backup code must not transmit provider or betting data');
 assert.ok(!js.includes('XMLHttpRequest'),'backup must remain local');
 assert.ok(!js.includes('innerHTML'),'do not inject imported content as HTML');
 console.log('Owner local 4-part backup: export, restore, consent, schema, quota rollback and no upload PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
