/* Private iPhone research UI regression with synthetic, no provider access. */
'use strict';
const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const {spawnSync}=require('node:child_process');
const js=fs.readFileSync('/tmp/keiba-private-console.js','utf8');
const elements=new Map(), requests=[];
function makeElement(){
 return {value:'',disabled:false,textContent:'',className:'',files:[],children:[],
  replaceChildren(...nodes){this.children=[...nodes];},
  append(...nodes){this.children.push(...nodes);},
  onclick:null,onchange:null};
}
function el(id){
 if(!elements.has(id))elements.set(id,makeElement());
 return elements.get(id);
}
function collect(node){return [node,...(node.children||[]).flatMap(collect)];}
function screenText(node){return collect(node).map(n=>n.textContent||'').join(' ');}
let forceBadResult=false;
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
 if(path==='/api/research')return {ok:true,json:async()=>
  forceBadResult?{...sampleResponse,points:2}:sampleResponse};
 throw Error('Unexpected URL '+path);
}
const scope={document:{getElementById:el,createElement:()=>makeElement()},fetch:fetchMock,
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
 const actual=spawnSync('python',['-c', [
  'import sys,json',
  "sys.path.insert(0,'scripts')",
  'from research_planner import plan_race',
  'plan=plan_race(json.load(sys.stdin))',
  "assert plan['recordType']=='test' and plan['publishable'] is False",
  "assert plan['researchDecision']=='simulate'",
  "assert set(plan['first'])=={1,2}",
  "assert 0<plan['points']<=40 and plan['points']==len(plan['tri'])",
  "print('Synthetic JS fixture -> Python planner:',plan['points'],'tickets')",
  'print(json.dumps(plan,ensure_ascii=False))',
 ].join(';')],{input:JSON.stringify(body),encoding:'utf8'});
 assert.equal(actual.status,0,actual.stderr);
 assert.match(actual.stdout,/Synthetic JS fixture -> Python planner/);
 const fullPlan=JSON.parse(actual.stdout.trim().split('\\n').pop());
 assert.equal(fullPlan.points,36,'synthetic eight-horse fixture yields 36 tickets');
 assert.equal(fullPlan.stake,3600);
 assert.equal(typeof scope.renderResearchSummary,'function');
 scope.renderResearchSummary(fullPlan,body);
 const realSummary=screenText(host);
 assert.match(realSummary,/36点/);
 assert.match(realSummary,/3,600円/);
 assert.equal(collect(host).filter(x=>x.className==='horse-row').length,8);
 assert.equal(collect(host).filter(x=>x.className==='grade-tag grade-a').length,2,
   'A class is red and shown for synthetic A-tier runners');
 for(const horse of body.horses){
  assert.equal(Object.keys(horse.assessments).length,10);
  for(const axis of Object.values(horse.assessments))
   assert.equal(axis.evidence[0].sourceId,'synthetic');
 }
 assert.match(el('researchMessage').textContent,/架空テスト/);
 assert.match(el('researchMessage').textContent,/1点/);
 assert.match(el('researchOutput').textContent,/総合評価順/);
 assert.match(el('researchOutput').textContent,/1-2-3/);
 const host=el('researchSummary');
 assert.equal(host.children.length,4,'summary shows four sections with no raw JSON');
 const prose=screenText(host);
 assert.match(prose,/架空テスト/);
 assert.match(prose,/1点/);
 assert.match(prose,/100円/);
 assert.match(prose,/総合評価順/);
 assert.match(prose,/1番/);
 assert.match(prose,/各着順の候補/);
 assert.match(prose,/全組み合わせが買い目とは限りません/);
 const badges=collect(host).filter(n=>n.className.includes('grade-tag'));
 assert.equal(badges.length,1);
 assert.equal(badges[0].className,'grade-tag grade-s');
 assert.equal(el('researchOutput').textContent.includes('1-2-3'),true);

 const before=requests.length;
 el('researchInput').value=JSON.stringify({...body,recordType:'live'});
 await el('researchRun').onclick();
 assert.equal(requests.length,before,'live data should not hit research endpoint');
 assert.match(el('researchMessage').textContent,/検証できません/);
 assert.equal(host.children.length,0,'invalid input clears stale prior result');
 forceBadResult=true;
 el('researchInput').value=JSON.stringify(body);
 await el('researchRun').onclick();
 assert.match(el('researchMessage').textContent,/検証できません/);
 assert.equal(host.children.length,0,'malformed returned ticket counts must not display');
 console.log('Private research iPhone DOM mock: ranking cards, summary and safety checks passed');
})().catch(e=>{console.error(e);process.exitCode=1});
