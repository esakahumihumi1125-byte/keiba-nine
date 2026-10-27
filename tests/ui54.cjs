// Requires jsdom: npm install --prefix /tmp/keiba-ui-check jsdom
// NODE_PATH=/tmp/keiba-ui-check/node_modules node tests/ui54.cjs
const {JSDOM,VirtualConsole}=require('jsdom'),fs=require('node:fs'),assert=require('node:assert/strict');
const errors=[],vc=new VirtualConsole();vc.on('jsdomError',e=>{if(e.type==='unhandled-exception')errors.push(e)});
const html=fs.readFileSync('keiba-nine-beta51-feed-record.html','utf8');
const dom=new JSDOM(html,{url:'https://example.com/',runScripts:'dangerously',pretendToBeVisual:true,virtualConsole:vc,beforeParse(w){w.alert=()=>{};w.confirm=()=>true;w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=()=>{};w.fetch=async()=>({ok:true,json:async()=>({schema:1,generatedAt:new Date().toISOString(),forecasts:[]})});}});
(async()=>{try{
 const w=dom.window,d=w.document;await new Promise(r=>setTimeout(r,100));assert.deepEqual(errors.map(e=>e.message),[]);
 let checks=0;const ok=x=>{assert(x);checks++};
 ok(d.querySelectorAll('.tabs button').length===3);ok(d.getElementById('simple52Body').textContent.includes('データ待ち'));
 const date=new Date(Date.now()+86400000).toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'});
 const row={date,track:'京都',race:1,off:'23:59',recordType:'live',status:'final',intent:'購入推奨',ranking:[1,2,3,4,5,6,7,8],rankS:[1,2],rankA:[3,4],rankB:[5,6,7,8],first:[1,2],second:[1,2,3,4],third:[1,2,3,4,5,6,7,8],evidence:{references:['synthetic UI test only']}};
 w.receiveFeed51({schema:1,generatedAt:new Date(Date.now()-60000).toISOString(),forecasts:[row,{...row,race:2},{...row,track:'東京'}]});
 d.getElementById('raceTrack54').value='京都';d.getElementById('raceTrack54').dispatchEvent(new w.Event('change'));
 ok(d.getElementById('raceDate54').value===date);ok(d.getElementById('raceTrack54').options.length===2);ok(d.getElementById('simple52Pick').options.length===2);
 ok(d.querySelectorAll('.s52-rank-B .s52-horse').length===4);ok(!d.getElementById('saveRecommendation54').disabled);
 d.getElementById('saveRecommendation54').click();ok(d.getElementById('saveRecommendation54').disabled);ok(d.getElementById('saveNotice54').textContent.includes('保存しました'));
 let ledger=JSON.parse(w.localStorage.getItem('keiba_nine_beta23_local_v1'));const chosen=ledger.forecasts.find(f=>f.recommendation54);ok(chosen.tri.length===36);ok(chosen.trio.length===0);
 d.getElementById('nextRace54').click();ok(d.getElementById('simple52Body').textContent.includes('京都2レース'));ok(d.getElementById('nextRace54').disabled);ok(!d.getElementById('saveRecommendation54').disabled);
 d.getElementById('raceTrack54').value='東京';d.getElementById('raceTrack54').dispatchEvent(new w.Event('change'));ok(d.getElementById('simple52Pick').options.length===1);ok(d.getElementById('simple52Body').textContent.includes('東京1レース'));
 d.querySelector('[data-screen="live"]').click();ok(d.getElementById('live').classList.contains('active'));ok(d.getElementById('finance54').textContent.includes('購入想定額'));
 const purchase=d.getElementById('purchasePick54');purchase.value=chosen.id;purchase.dispatchEvent(new w.Event('change'));ok(d.getElementById('purchaseBets54').textContent.includes('3,600円'));
 d.getElementById('purchaseSave54').click();ok(d.getElementById('purchaseNotice54').textContent.includes('確認してください'));
 d.getElementById('purchaseConfirm54').checked=true;d.getElementById('purchaseSave54').click();ok(d.getElementById('purchaseNotice54').textContent.includes('保存しました'));
 d.getElementById('financeMode54').value='actual';d.getElementById('financeMode54').dispatchEvent(new w.Event('change'));ok(d.getElementById('financeNote54').textContent.includes('結果待ち 3,600円'));
 w.show('results');const form=[...d.querySelectorAll('.real-result-entry')].find(f=>f.dataset.race===date+'|京都|1|live');const b=chosen.tri[0];for(const [name,v] of Object.entries({one:b[0],two:b[1],three:b[2],triDividend:5000,trioDividend:0}))form.elements.namedItem(name).value=v;form.elements.namedItem('confirmed').checked=true;form.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
 w.show('live');ok(d.getElementById('financeStake54').textContent==='3,600円');ok(d.getElementById('financeReturn54').textContent==='5,000円');ok(d.getElementById('financeNet54').textContent==='1,400円');
 const beforeFilter=w.localStorage.getItem('keiba_nine_beta23_local_v1');
 ok(d.getElementById('recordKind56').value==='live');
 const kind=d.getElementById('recordKind56');kind.value='test';kind.dispatchEvent(new w.Event('change'));
 ok([...d.querySelectorAll('#realForecastList > [data-key56]')].every(r=>r.hidden));
 ok(!d.getElementById('recordEmpty56').hidden);
 kind.value='live';kind.dispatchEvent(new w.Event('change'));
 const card=[...d.querySelectorAll('#realForecastList > [data-key56]')].find(r=>r.dataset.key56===date+'|京都|1|live');
 ok(!card.hidden);ok(card.querySelector('.r56-state').textContent==='結果確認済み');
 ok(!card.querySelector('details').open);card.querySelector('[data-result56]').click();
 ok(d.getElementById('results').classList.contains('active'));
 ok(d.getElementById('resultPick56').value===date+'|京都|1|live');
 ok([...d.querySelectorAll('#realResultForms > details')].filter(r=>!r.hidden).length===1);
 ok(!d.getElementById('resultsAdvanced56').open);
 ok(w.localStorage.getItem('keiba_nine_beta23_local_v1')===beforeFilter);
 w.show('live');d.getElementById('purchaseOpen56').click();ok(d.getElementById('purchaseDetail56').open);

 ok(d.getElementById('realForecastList').textContent.includes(chosen.tri[0].join('→')));
 ok(errors.length===0);console.log(checks+' full-page DOM interaction checks passed');
 }finally{dom.window.close()}})().catch(e=>{console.error(e);process.exitCode=1});
