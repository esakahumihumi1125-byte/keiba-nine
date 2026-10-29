// NODE_PATH=/tmp/keiba-ui-check/node_modules node tests/real-result-flow.cjs
// Separate, disposable browser storage. Never connects to user accounts or feeds.
const {JSDOM,VirtualConsole}=require('jsdom'),fs=require('node:fs'),assert=require('node:assert/strict');
const actual=JSON.parse(fs.readFileSync('tests/fixtures/derby2025-result.json','utf8'));
const html=fs.readFileSync('keiba-nine-beta51-feed-record.html','utf8');
const key='keiba_nine_beta23_local_v1',errors=[];let checks=0;
const ok=v=>{assert(v);checks++};
function browser(saved){const vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));return new JSDOM(html,{url:'https://example.com/',runScripts:'dangerously',virtualConsole:vc,beforeParse(w){w.alert=()=>{};w.confirm=()=>true;w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=()=>{};w.fetch=async()=>({ok:true,json:async()=>({schema:1,generatedAt:new Date().toISOString(),forecasts:[]})});if(saved)w.localStorage.setItem(key,saved);}});}
const wait=()=>new Promise(r=>setTimeout(r,100));
(async()=>{let dom=browser();try{
 await wait();let w=dom.window,d=w.document;
 // Ticket deliberately chosen after the outcome. Its timestamp must never be backdated.
 const f={id:'post-race-ui-check',version:1,date:actual.date,track:actual.track,race:actual.race,off:actual.off,recordType:'live',savedAt:new Date().toISOString(),intent:'購入推奨',recommendation54:true,tri:[[13,17,2],[13,2,17]],trio:[],first:[],second:[],third:[],reason:actual.purpose};
 const backup=JSON.stringify({schema:1,forecasts:[f],results:[]});
 const input=d.getElementById('rpImport');Object.defineProperty(input,'files',{value:[{size:backup.length,text:async()=>backup}]});input.dispatchEvent(new w.Event('change'));await wait();
 w.show('live');ok(w.KEIBA_NINE_23_TEST.getRaces().length===1);ok(d.getElementById('realForecastList').textContent.includes('発走後の記録・検証対象外'));
 w.show('results');const form=d.querySelector('.real-result-entry');ok(!!form);
 for(const field of ['one','two','three','triDividend','trioDividend','sourceUrl'])form.elements.namedItem(field).value=actual[field];
 form.elements.namedItem('confirmed').checked=true;form.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
 const result=w.KEIBA_NINE_23_TEST.getResults()[0];ok(result.one===13&&result.two===17&&result.three===2);ok(result.triDividend===8460);ok(result.sourceUrl===actual.sourceUrl);
 const computed=w.KEIBA_NINE_23_TEST.adjudicate(f,result);ok(computed.stake===200&&computed.returned===8460&&computed.net===8260);
 const miss=w.KEIBA_NINE_23_TEST.adjudicate({...f,tri:[[13,2,17]]},result);ok(miss.returned===0&&miss.net===-100);
 // Successful arithmetic is NOT successful prediction performance.
 for(const mode of ['simulation','actual']){const stats=w.financeSummary54(mode);ok(stats.stake===0&&stats.returned===0&&stats.count===0);}
 assert.throws(()=>w.recordPurchase54(f.id));checks++;
 const saved=w.localStorage.getItem(key);dom.window.close();dom=browser(saved);await wait();w=dom.window;d=w.document;w.show('live');
 ok(w.KEIBA_NINE_23_TEST.getResults()[0].sourceUrl===actual.sourceUrl);ok(d.getElementById('realForecastList').textContent.includes('結果確認済み'));ok(w.financeSummary54().count===0);
 d.getElementById('financePeriod62').value='day';d.getElementById('financePeriod62').dispatchEvent(new w.Event('change'));d.getElementById('recordDate56').value=actual.date;d.getElementById('recordDate56').dispatchEvent(new w.Event('change'));
 ok(d.getElementById('financeNet54').textContent==='0円');ok(d.getElementById('recordsCount56').textContent.includes('表示 1レース'));ok(errors.length===0);
 console.log(checks+' real-result import, entry, reload, arithmetic and exclusion checks passed');
}finally{dom.window.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
