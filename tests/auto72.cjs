const {JSDOM,VirtualConsole}=require('jsdom'),fs=require('fs'),assert=require('node:assert/strict');
const feed=JSON.parse(fs.readFileSync('keiba-nine-auto-feed.json','utf8'));
feed.date=new Date(Date.now()+86400000).toISOString().slice(0,10);feed.generatedAt=new Date(Date.now()-60000).toISOString();feed.forecasts[0].date=feed.date;feed.forecasts[0].off='23:59';
let calls=0,tick,offset=0,fail=false,hidden=false,online=true;const errors=[],vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e));
const dom=new JSDOM(fs.readFileSync('keiba-nine-beta51-feed-record.html','utf8'),{url:'https://example.com',runScripts:'dangerously',pretendToBeVisual:true,virtualConsole:vc,beforeParse(w){
 w.alert=()=>{};w.confirm=()=>true;w.scrollTo=()=>{};const now=w.Date.now.bind(w.Date);w.Date.now=()=>now()+offset;
 Object.defineProperty(w.document,'hidden',{get:()=>hidden});Object.defineProperty(w.navigator,'onLine',{get:()=>online});
 const interval=w.setInterval.bind(w);w.setInterval=(fn,ms)=>{if(ms===300000){tick=fn;return 999;}return interval(fn,ms)};
 w.fetch=async()=>{calls++;if(fail)throw Error('offline');return {ok:true,status:200,text:async()=>JSON.stringify(feed)}};
}});
const pause=()=>new Promise(r=>setTimeout(r,30));
(async()=>{try{await pause();const w=dom.window,d=w.document;assert.equal(calls,1);assert(tick);assert(d.getElementById('feedSync72').textContent.includes('最終確認'));
 const ledger=w.localStorage.getItem('keiba_nine_beta23_local_v1');const receive=w.receiveFeed51;let received=0;w.receiveFeed51=(...args)=>{received++;return receive(...args)};
 offset+=300001;await tick();await pause();assert.equal(calls,2);assert.equal(received,0); // unchanged data does not redraw/persist
 hidden=true;offset+=300001;await tick();assert.equal(calls,2);
 hidden=false;w.document.dispatchEvent(new w.Event('visibilitychange'));await pause();assert.equal(calls,3);
 w.dispatchEvent(new w.Event('pageshow'));await pause();assert.equal(calls,3); // coalesce resume events
 online=false;offset+=300001;await tick();assert.equal(calls,3);
 online=true;fail=true;w.dispatchEvent(new w.Event('online'));await pause();assert.equal(calls,4);assert(d.getElementById('feedSync72').textContent.includes('最新未確認'));
 assert(d.getElementById('simple52Body').textContent.includes('マルモリマイベスト'));assert.equal(w.localStorage.getItem('keiba_nine_beta23_local_v1'),ledger);
 fail=false;offset+=300001;feed.generatedAt=new Date(Date.now()).toISOString();feed.forecasts[0].reason='更新した暫定理由';await tick();await pause();assert.equal(received,1);assert(d.getElementById('simple52Body').textContent.includes('更新した暫定理由'));assert(d.getElementById('saveRecommendation54').disabled);assert.equal(errors.length,0);
 console.log('Auto-refresh: timer, resume, deduplication, offline, recovery and ledger preservation passed.');
}finally{dom.window.close()}})().catch(e=>{console.error(e);process.exitCode=1});
