const {JSDOM,VirtualConsole}=require('jsdom'),fs=require('fs'),assert=require('node:assert/strict');
const feed=JSON.parse(fs.readFileSync('keiba-nine-auto-feed.json','utf8'));
// Keep the source's live/draft distinction while making deadline checks reproducible.
feed.date=new Date(Date.now()+86400000).toISOString().slice(0,10);feed.generatedAt=new Date(Date.now()-60000).toISOString();
feed.forecasts[0].date=feed.date;feed.forecasts[0].off='23:59';
const errors=[],vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e));
const dom=new JSDOM(fs.readFileSync('keiba-nine-beta51-feed-record.html','utf8'),{url:'https://example.com',runScripts:'dangerously',virtualConsole:vc,beforeParse(w){w.alert=()=>{};w.confirm=()=>true;w.scrollTo=()=>{};w.fetch=async()=>({ok:true,json:async()=>({schema:1,generatedAt:feed.generatedAt,forecasts:[]})});}});
setTimeout(()=>{try{const w=dom.window,d=w.document;const before=w.localStorage.getItem('keiba_nine_beta23_local_v1');
assert.equal(w.receiveFeed51(feed),0);
assert(d.getElementById('simple52Body').textContent.includes('マルモリマイベスト'));
assert(d.getElementById('simple52Body').textContent.includes('暫定'));
assert(d.getElementById('simple52Body').textContent.includes('主要候補'));
assert(d.getElementById('saveRecommendation54').disabled);assert(d.getElementById('copyTicket63').disabled);
assert.equal(w.localStorage.getItem('keiba_nine_beta23_local_v1'),before);
w.receiveFeed51(feed);assert.equal(w.localStorage.getItem('keiba_nine_beta23_local_v1'),before);
const bad=JSON.parse(JSON.stringify(feed));bad.forecasts[0].status='unknown';assert.throws(()=>w.receiveFeed51(bad));
assert.equal(errors.length,0);console.log('Draft feed displayed; purchase/save blocked; personal ledger unchanged; invalid draft rejected.');
}finally{dom.window.close()}},150);
