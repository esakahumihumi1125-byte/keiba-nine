/* JRDB provisional -> manual numbered racecard comparison, private offline only. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const provisional=fs.readFileSync('/tmp/keiba-jrdb-mail-local.js','utf8');
const mapping=fs.readFileSync('/tmp/keiba-jrdb-manual-numbers.js','utf8');
const MAIL='keiba-nine-jrdb-personal-mail-v1';
const NUMBERS='keiba-nine-owner-manual-numbers-v1';
const DRAFT='keiba-nine-owner-ticket-drafts-v1',REAL='keiba-nine-owner-real-purchases-v1';
const storage=new Map([[DRAFT,'draft-marker'],[REAL,'purchase-marker']]);
let approve=true,network=0;
const localStorage={
 getItem:k=>storage.get(k)||null,
 setItem(k,v){storage.set(k,v)},
 removeItem:k=>storage.delete(k)
};
function boot(){
 const nodes=new Map();
 function el(tag='div'){
  return {tag,children:[],value:'',textContent:'',disabled:false,onclick:null,onchange:null,oninput:null,
   append(...x){this.children.push(...x)},
   replaceChildren(...x){this.children=[...x]}
  };
 }
 function $(id){if(!nodes.has(id))nodes.set(id,el());return nodes.get(id);}
 const scope={document:{getElementById:$,createElement:el},localStorage,Date,
  JSON,Set,Map,Number,String,Array,Error,console,
  confirm:()=>approve,fetch:()=>{network++;throw Error('network disabled');}};
 vm.runInNewContext(provisional,scope);
 vm.runInNewContext(mapping,scope);
 return $;
}
const mail=(horseA='テストサクラ',horseB='テストナイン')=>[
 '■想定確定','','2099年1月1日（木）　5回東京1日目　09:55発走',
 '1Ｒ','２歳・未勝利(馬齢)　芝1600M　2頭',
 '前評 B 馬名 性 齢 騎手 斤量 IDM 厩舎',
 '　 '+horseA+' 牝 2 架空 55 架空',
 '　 '+horseB+' 牡 2 架空 56 架空','',
 "All Rights Reserved By 'JRDB.'"
].join('\n');
const $=boot();
assert.equal($('numberRace').value,'');
assert.equal($('saveNumbers').disabled,true);
$('mailText').value=mail();$('importMail').onclick();
assert.equal($('numberRace').value,'1');
assert.equal($('storedNumberRows').children.length,0);
assert.equal(storage.has(NUMBERS),false);
$('numberPaste').value='① テストサクラ\n② テストナイン';
$('compareNumbers').onclick();
assert.match($('numberPreview').children[0].textContent,/馬名一致2頭/);
assert.equal($('saveNumbers').disabled,false);
assert.equal(storage.has(NUMBERS),false,'Comparing never auto-saves');
approve=false;$('saveNumbers').onclick();
assert.equal(storage.has(NUMBERS),false,'Declined save is never stored');
approve=true;$('saveNumbers').onclick();
let values=JSON.parse(storage.get(NUMBERS));
assert.equal(values.length,1);
assert.equal(values[0].rows.length,2);
assert.deepEqual(values[0].rows.map(x=>x.number),[1,2]);
assert.match($('storedNumberMessage').textContent,/本人の手入力/);
assert.equal(storage.get(DRAFT),'draft-marker');
assert.equal(storage.get(REAL),'purchase-marker');
const before=storage.get(NUMBERS);
for(const bad of ['1 テストサクラ\n1 テストナイン',
 '19 テストサクラ\n2 テストナイン',
 '1 テストサクラ\n2 テストサクラ',
 '1 テストサクラ\n2 テストナイン\n3 x\n4 y\n5 z\n6 zz\n7 zz2\n8 zz3\n9 zz4\n10 zz5\n11 zz6\n12 zz7\n13 zz8\n14 zz9\n15 zz10\n16 zz11\n17 zz12\n18 zz13\n19 zz14',
 '1 テストサクラ\n二 テストナイン']){
 $('numberPaste').value=bad;$('compareNumbers').onclick();
 assert.match($('numberMessage').textContent,/照合できません/);
 assert.equal(storage.get(NUMBERS),before);
}
$('numberPaste').value='1 テストサクラ\n3 新出走馬';
$('compareNumbers').onclick();
assert.match($('numberPreview').children[0].textContent,/馬名一致1頭/);
assert.ok($('numberPreview').children.some(x=>/想定にあるが貼付にない/.test(x.textContent)));
assert.ok($('numberPreview').children.some(x=>/想定にないが貼付にある/.test(x.textContent)));
assert.equal(storage.get(NUMBERS),before);
$('saveNumbers').onclick();
values=JSON.parse(storage.get(NUMBERS));
assert.equal(values.length,1,'Resaving one race replaces it, never duplicates');
assert.equal(values[0].rows[1].number,3);
assert.equal(values[0].rows[1].name,'新出走馬');
// Underlying JRDB provisional content changes: saved manual numbers are stale,
// and pending unsaved comparison may not overwrite the new snapshot.
$('numberPaste').value='1 テストサクラ\n2 テストナイン';
$('compareNumbers').onclick();
$('mailText').value=mail('改訂テストサクラ','テストナイン');
$('importMail').onclick();
assert.match($('storedNumberMessage').textContent,/再照合が必要/);
const staleRecord=storage.get(NUMBERS);
$('saveNumbers').onclick();
assert.equal(storage.get(NUMBERS),staleRecord);
assert.match($('numberMessage').textContent,/もう一度照合/);
$('numberPaste').value='1 改訂テストサクラ\n2 テストナイン';
$('compareNumbers').onclick();
$('saveNumbers').onclick();
assert.match($('storedNumberMessage').textContent,/本人の手入力/);
const reloaded=boot();
assert.equal(reloaded('numberRace').value,'1','Saved meeting selection restored');
assert.match(reloaded('storedNumberMessage').textContent,/本人の手入力/);
assert.equal(reloaded('storedNumberRows').children.length,2);
approve=false;reloaded('deleteNumbers').onclick();
assert.equal(JSON.parse(storage.get(NUMBERS)).length,1);
approve=true;reloaded('deleteNumbers').onclick();
assert.equal(JSON.parse(storage.get(NUMBERS)).length,0);
assert.equal(storage.get(DRAFT),'draft-marker');
assert.equal(storage.get(REAL),'purchase-marker');

// Bulk mapping: two venues, strictly matched to imported provisional horse names.
const secondVenue=mail().replace('2099年1月1日（木）','2099年1月2日（金）')
 .replace('東京','京都');
reloaded('mailText').value=secondVenue;
reloaded('importMail').onclick();
assert.equal(JSON.parse(storage.get(MAIL)).length,2);
const allRaceText='2099-01-01 東京1R\n1 改訂テストサクラ\n2 テストナイン\n\n'+
 '2099-01-02 京都1R\n① テストサクラ\n② テストナイン';
reloaded('bulkNumberPaste').value=allRaceText;
assert.equal(reloaded('bulkNumberSave').disabled,true,'batch-save begins locked');
const originalMappings=storage.get(NUMBERS),writes=[];
reloaded('bulkNumberReview').onclick();
assert.equal(reloaded('bulkNumberPreview').children.length,2);
assert.match(reloaded('bulkNumberStatus').textContent,/2R一致/);
assert.equal(reloaded('bulkNumberSave').disabled,false);
assert.equal(storage.get(NUMBERS),originalMappings,'preview never persists');
approve=false;
reloaded('bulkNumberSave').onclick();
assert.equal(storage.get(NUMBERS),originalMappings,'bulk save canceled');
approve=true;
reloaded('bulkNumberSave').onclick();
let batchMappings=JSON.parse(storage.get(NUMBERS));
assert.equal(batchMappings.length,2);
assert.deepEqual(batchMappings.map(x=>x.track).sort(),['京都','東京']);
assert.equal(batchMappings.find(x=>x.track==='京都').rows.length,2);
assert.match(reloaded('bulkNumberStatus').textContent,/2Rの馬番・馬名メモを端末内に保存/);
assert.equal(reloaded('bulkNumberPaste').value,'');
assert.equal(reloaded('bulkNumberSave').disabled,true);
assert.equal(storage.get(DRAFT),'draft-marker','batch does not alter ticket drafts');
assert.equal(storage.get(REAL),'purchase-marker','batch does not alter actual purchases');
const batchSaved=storage.get(NUMBERS);
for(const text of [
 allRaceText+'\n2099-01-01 東京1R\n1 改訂テストサクラ\n2 テストナイン',
 '2099-01-01 東京1R\n1 改訂テストサクラ\n2 別の馬',
 '2099-01-01 東京1R\n1 改訂テストサクラ',
 '2099-01-01 東京1R\n1 改訂テストサクラ\n1 テストナイン',
 '2099-01-33 東京1R\n1 改訂テストサクラ\n2 テストナイン',
 '2099-01-01 福島1R\n1 改訂テストサクラ\n2 テストナイン',
 '2099-01-01 東京1R\n1 改訂テストサクラ\n2 テストナイン\n2099-01-01 東京13R\n1 x'
]){
 reloaded('bulkNumberPaste').value=text;
 reloaded('bulkNumberReview').onclick();
 assert.equal(reloaded('bulkNumberSave').disabled,true,'invalid batch blocked');
 assert.match(reloaded('bulkNumberStatus').textContent,/一括照合できません/);
 assert.equal(storage.get(NUMBERS),batchSaved,'invalid batch cannot mutate records');
}
reloaded('bulkNumberPaste').value=allRaceText;
reloaded('bulkNumberReview').onclick();
assert.equal(reloaded('bulkNumberSave').disabled,false);
reloaded('bulkNumberPaste').value=allRaceText+'\n';
reloaded('bulkNumberSave').onclick();
assert.match(reloaded('bulkNumberStatus').textContent,/貼付内容または元資料が変わりました/);
assert.equal(storage.get(NUMBERS),batchSaved,'modified reviewed input rejected');
reloaded('bulkNumberPaste').value=allRaceText;
reloaded('bulkNumberReview').onclick();
const savedMailSnapshot=storage.get(MAIL);
storage.set(MAIL,savedMailSnapshot+' ');
reloaded('bulkNumberSave').onclick();
assert.equal(storage.get(NUMBERS),batchSaved,'changed source mail snapshot blocks save');
assert.equal(reloaded('bulkNumberSave').disabled,true);
storage.set(MAIL,savedMailSnapshot);
reloaded('bulkNumberPaste').value=allRaceText;
reloaded('bulkNumberReview').onclick();
storage.set(NUMBERS,batchSaved+' ');
reloaded('bulkNumberSave').onclick();
assert.equal(storage.get(NUMBERS),batchSaved+' ','intervening memo modification blocks overwrite');
storage.set(NUMBERS,batchSaved);
assert.equal(network,0,'bulk mapping performs no network requests');
assert.ok(!mapping.includes('fetch('));

reloaded('clearAll').onclick();
assert.equal(storage.has(MAIL),false);
assert.equal(reloaded('numberRace').value,'');
assert.equal(network,0,'All workflows must stay local/offline');
assert.ok(!mapping.includes('fetch('));
assert.ok(!mapping.includes('innerHTML'));
assert.ok(!mapping.includes('XMLHttpRequest'));

// Maximum 36R: three synthetic venues, each with exactly 12 complete race rosters.
function fullSyntheticMeeting(venue){
 const text=['■想定確定',''];
 for(let n=1;n<=12;n++){
  text.push('2099年1月9日（土）　5回'+venue+'1日目　09:55発走');
  text.push(n+'Ｒ'+(n===11?' 架空ステークス':''));
  text.push('2歳・未勝利(馬齢) 芝1600M 2頭');
  text.push('前評 B 馬名 性 齢 騎手 斤量 IDM 厩舎');
  text.push(' テストサクラ 牝 2 架空 55 架空');
  text.push(' テストナイン 牡 2 架空 56 架空');
  text.push('');
 }
 text.push("All Rights Reserved By 'JRDB.'");
 return text.join('\n');
}
const three=boot();
three('mailText').value=['東京','京都','福島'].map(fullSyntheticMeeting).join('\n\n');
three('importMail').onclick();
assert.match(three('message').textContent,/3通を確認/);
const maxBatch=['東京','京都','福島'].flatMap(venue=>
 Array.from({length:12},(_,idx)=>'2099-01-09 '+venue+(idx+1)+'R\n1 テストサクラ\n2 テストナイン')
).join('\n\n');
three('bulkNumberPaste').value=maxBatch;
three('bulkNumberReview').onclick();
assert.equal(three('bulkNumberPreview').children.length,36,'all 36 race previews are displayed');
assert.match(three('bulkNumberStatus').textContent,/36R一致/);
assert.equal(three('bulkNumberSave').disabled,false);
three('bulkNumberSave').onclick();
const allMapped=JSON.parse(storage.get(NUMBERS));
assert.equal(allMapped.filter(r=>r.date==='2099-01-09').length,36,'all 36 race mappings stored atomically');
assert.equal(storage.get(DRAFT),'draft-marker');
assert.equal(storage.get(REAL),'purchase-marker');
const allMappedSaved=storage.get(NUMBERS);
three('bulkNumberPaste').value=maxBatch+'\n\n2099-01-10 東京1R\n1 テストサクラ\n2 テストナイン';
three('bulkNumberReview').onclick();
assert.equal(three('bulkNumberSave').disabled,true,'a 37th race is rejected');
assert.equal(storage.get(NUMBERS),allMappedSaved);

console.log('JRDB provisional vs manual numbered JRA racecard: mapping, mismatch, overwrite guard, stale after mail changes, owner confirmation, isolation PASS');
