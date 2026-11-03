/* Private iPhone research UI regression with synthetic, no provider access. */
'use strict';
const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const js=fs.readFileSync('/tmp/keiba-private-console.js','utf8');
const elements=new Map(), requests=[];
function el(id){
 if(!elements.has(id))elements.set(id,{
  value:'',disabled:false,textContent:'',files:[],
  replaceChildren(){},append(){},onclick:null,onchange:null
 });
 return elements.get(id);
}
const sampleResponse={
 recordType:'test',status:'draft',publishable:false,validated:false,
 researchDecision:'simulate',points:1,stake:100,first:[1],
 tri:[[1,2,3]],reason:'架空検証の買い目',
 evaluation:{horses:[{number:1,rank:1,overall:'S',grades:{
  training:'S',recent:'A',course_distance:'A'},coverage:100}]}
};
async function fetchMock(path,options={}){
 requests.push({path,options});
 if(path==='/api/status')return {ok:true,json:async()=>({jrdbConfigured:false})};
 if(path==='/api/research')return {ok:true,json:async()=>sampleResponse};
 throw Error('Unexpected URL '+path);
}
const scope={document:{getElementById:el,createElement:()=>({
 className:'',textContent:'',append(){}})},fetch:fetchMock,
 Date,console,encodeURIComponent,JSON};
vm.runInNewContext(js,scope);
async function flush(){
 await new Promise(resolve=>setImmediate(resolve));
 await new Promise(resolve=>setImmediate(resolve));
}
(async()=>{
 await flush();
 assert.equal(el('load').disabled,true);
 assert.equal(typeof el('researchDemo').onclick,'function');
 assert.equal(typeof el('researchRun').onclick,'function');
 el('researchDemo').onclick();
 await flush();
 const post=requests.find(r=>r.path==='/api/research');
 assert.ok(post,'demo must call private research');
 assert.equal(post.options.method,'POST');
 assert.equal(post.options.credentials,'same-origin');
 assert.equal(post.options.headers['X-Keiba-Request'],'private');
 const body=JSON.parse(post.options.body);
 assert.equal(body.recordType,'test');
 assert.equal(body.track,'架空競馬場');
 assert.equal(body.horses.length,8);
 for(const horse of body.horses){
  assert.equal(Object.keys(horse.assessments).length,10);
  for(const axis of Object.values(horse.assessments))
   assert.equal(axis.evidence[0].sourceId,'synthetic');
 }
 assert.match(el('researchMessage').textContent,/架空テスト/);
 assert.match(el('researchMessage').textContent,/1点/);
 assert.match(el('researchOutput').textContent,/総合評価順/);
 assert.match(el('researchOutput').textContent,/1-2-3/);
 const before=requests.length;
 el('researchInput').value=JSON.stringify({...body,recordType:'live'});
 await el('researchRun').onclick();
 assert.equal(requests.length,before,'live data should not hit research endpoint');
 assert.match(el('researchMessage').textContent,/検証できません/);
 console.log('Private research iPhone DOM mock: 13 key checks passed');
})().catch(e=>{console.error(e);process.exitCode=1});
