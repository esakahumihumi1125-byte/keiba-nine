/* Offline UI contract: official JRA PDF index is only requested on click. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const code=fs.readFileSync('/tmp/keiba-jra-official-pdf-ui.js','utf8');
function makeResponse(date='2026-11-07',links=[
 {track:'東京',url:'https://www.jra.go.jp/keiba/rpdf/2026/sample.pdf'}
]){
 return {version:'jra-official-pdf-link-discovery-1',date,
  indexUrl:'https://www.jra.go.jp/keiba/rpdf/',links,linkFound:links.length>0,
  pdfContentsRead:false,officialRunnerNumbersVerified:false,
  entryChangeVerified:false,predictionReady:false,bettingReady:false};
}
function boot(fetch){
 const nodes=new Map(),calls=[];
 function element(tag='div'){
  return {tag,children:[],value:'',textContent:'',disabled:false,href:'',target:'',rel:'',
   onclick:null,onchange:null,append(...xs){this.children.push(...xs)},
   replaceChildren(...xs){this.children=[...xs]}};
 }
 const $=id=>{if(!nodes.has(id))nodes.set(id,element());return nodes.get(id);};
 const ctx={document:{getElementById:$,createElement:element},URL,encodeURIComponent,
  fetch:(...args)=>{calls.push(args);return fetch(...args);}};
 $('chooseMeeting').value='';
 vm.runInNewContext(code,ctx);
 return {$,calls};
}
const good=async()=>{
 let count=0;
 const {$,calls}=boot(async()=>{count++;return {ok:true,json:async()=>makeResponse()}});
 assert.equal(calls.length,0,'No auto-fetch on page load');
 await $('checkOfficialPdf').onclick();
 assert.equal(calls.length,0,'No fetch without a date');
 assert.match($('officialPdfMessage').textContent,/開催日/);
 $('chooseMeeting').value='2026-11-07|東京';$('chooseMeeting').onchange();
 await $('checkOfficialPdf').onclick();
 assert.equal(count,1,'One explicit click makes one official index fetch');
 assert.equal(calls[0][0],'/api/jra/official-pdf-links?date=2026-11-07');
 assert.equal(calls[0][1].credentials,'same-origin');
 assert.equal(calls[0][1].cache,'no-store');
 assert.equal(calls[0][1].headers['X-Keiba-Request'],'private');
 const children=$('officialPdfLinks').children;
 assert.equal(children.length,2);
 assert.equal(children[1].tag,'a');
 assert.equal(children[1].href,'https://www.jra.go.jp/keiba/rpdf/2026/sample.pdf');
 assert.equal(children[1].target,'_blank');
 assert.equal(children[1].rel,'noopener noreferrer');
 assert.match($('officialPdfMessage').textContent,/馬番・取消・馬場の自動照合は未実施/);
 $('chooseMeeting').value='2026-11-08|東京';$('chooseMeeting').onchange();
 assert.equal($('officialPdfLinks').children.length,0,'Reset after date change');
 assert.equal(calls.length,1,'Changing date does not auto-fetch');
};
const invalid=async()=>{
 for(const bad of [
  makeResponse('2026-11-07',[{track:'東京',url:'http://www.jra.go.jp/keiba/rpdf/wrong.pdf'}]),
  makeResponse('2026-11-07',[{track:'東京',url:'https://jra.jp.evil.test/keiba/rpdf/wrong.pdf'}]),
  makeResponse('2026-11-07',[{track:'東京',url:'https://www.jra.go.jp/keiba/rpdf/test.pdf?leak=1'}]),
  makeResponse('2026-11-07',[{track:'東京',url:'https://www.jra.go.jp/keiba/rpdf/test.html'}]),
  makeResponse('2026-11-08'),
  {...makeResponse(),predictionReady:true},
  {...makeResponse(),officialRunnerNumbersVerified:true},
  {...makeResponse(),links:[{track:'京都',url:'https://www.jra.go.jp/keiba/rpdf/2026/a.pdf'},
                              {track:'京都',url:'https://jra.jp/keiba/rpdf/2026/b.pdf'}],linkFound:true},
 ]){
  const {$}=boot(async()=>({ok:true,json:async()=>bad}));
  $('chooseMeeting').value='2026-11-07|東京';
  await $('checkOfficialPdf').onclick();
  assert.equal($('officialPdfLinks').children.length,0,'Untrusted links or claims must be rejected');
  assert.match($('officialPdfMessage').textContent,/不正|公式PDFリンクの応答|確認できませんでした/);
 }
};
const stale=async()=>{
 let resolveFetch;
 const {$,calls}=boot(()=>new Promise(resolve=>{resolveFetch=resolve}));
 $('chooseMeeting').value='2026-11-07|東京';
 const pending=$('checkOfficialPdf').onclick();
 assert.equal(calls.length,1);
 $('chooseMeeting').value='2026-11-08|京都';$('chooseMeeting').onchange();
 resolveFetch({ok:true,json:async()=>makeResponse()});
 await pending;
 assert.equal($('officialPdfLinks').children.length,0,'Never paint old-day links');
 assert.match($('officialPdfMessage').textContent,/まだ確認してへん/);
};
const noLink=async()=>{
 const {$}=boot(async()=>({ok:true,json:async()=>makeResponse('2026-11-07',[])}));
 $('chooseMeeting').value='2026-11-07|東京';
 await $('checkOfficialPdf').onclick();
 assert.equal($('officialPdfLinks').children.length,1);
 assert.match($('officialPdfLinks').children[0].textContent,/形式変更・取得遅延/);
};
(async()=>{await good();await invalid();await stale();await noLink();
 console.log('JRA official PDF link UI: click-only, source-bound, no race prediction, stale handling and no-link states PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
