const {context,section}=require('./feed-record.cjs');
const vm=require('node:vm'),assert=require('node:assert/strict');
let checks=0;const ok=v=>{assert(v);checks++},throws=fn=>{assert.throws(fn);checks++};
function setup(initial){const h=context(initial),c=h.c;vm.runInContext(section('/* SIMPLE52_LOGIC_START */','/* SIMPLE52_LOGIC_END */')+section('/* SIMPLE54_LOGIC_START */','/* SIMPLE54_LOGIC_END */')+section('const getAllRaces=','function adjudicate(')+section('window.sourceRecommendation54=','function render40(){')+'\nwindow.batch54=()=>latest40();window.result54=r=>R23.results.push(r);window.eligible54=()=>eligibleRecord(R23.forecasts);',c);return h;}
const h=setup(),c=h.c,date=new Date(Date.now()+86400000).toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'}),r={date,track:'京都',race:1,off:'23:59',recordType:'live',status:'final',intent:'購入推奨',ranking:[1,2,3,4,5,6,7,8],rankS:[1,2],rankA:[3,4],rankB:[5,6,7,8],first:[1,2],second:[1,2,3,4],third:[1,2,3,4,5,6,7,8],raceCard:{date,track:'京都',race:1,complete:true,source:'synthetic roster only',checkedAt:new Date(Date.now()-120000).toISOString(),runners:Array.from({length:8},(_,i)=>({number:i+1,name:i===0?'テスト馬':'架空馬'+(i+1),status:'active'}))},evidence:{references:['synthetic test only']}};
const feed={schema:1,generatedAt:new Date(Date.now()-60000).toISOString(),forecasts:[r]};c.receiveFeed51(feed);
const source=c.batch54()[0],key=c.identity54(source),expected=JSON.stringify(c.recommend52(source));
ok(c.state54(source).canSave);for(const change of [{off:''},{off:'25:00'},{status:'draft'},{status:'skip'},{intent:'見送り'},{recordType:'test'},{rankB:[]}])ok(!c.state54({...source,...change}).canSave);
ok(!c.state54(source,Date.parse(date+'T23:59:00+09:00')).canSave);
throws(()=>c.saveRecommendation54(source.id,'stale'));
const saved=c.saveRecommendation54(source.id,key);ok(JSON.stringify(saved.tri)===expected);ok(saved.tri.length===36);ok(saved.trio.length===0);ok(saved.first.length===0);ok(!saved.feedIdentity51);ok(c.getRaces().length===2);
ok(c.saveRecommendation54(source.id,key).id===saved.id);ok(c.getRaces().length===2);ok(c.eligible54().id===saved.id);
// Later automatic delivery cannot replace the user's exact chosen ticket snapshot.
c.receiveFeed51({...feed,generatedAt:new Date(Date.now()-10000).toISOString(),forecasts:[{...r,rankA:[4,3]}]});ok(c.eligible54().id===saved.id);
ok(c.financeSummary54('actual').pending===0);c.recordPurchase54(saved.id);ok(c.financeSummary54('actual').pending===3600);c.recordPurchase54(saved.id);ok(c.financeSummary54('actual').pending===3600);
const bet=saved.tri[0];c.result54({date,track:'京都',race:1,recordType:'live',savedAt:new Date().toISOString(),confirmed:true,one:bet[0],two:bet[1],three:bet[2],triDividend:5000,trioDividend:0});
for(const mode of ['simulation','actual']){const st=c.financeSummary54(mode);ok(st.stake===3600&&st.returned===5000&&st.net===1400&&st.pending===0);}
// Failed write must not leave an in-memory save or a purchase marker.
const source2=c.batch54()[0],key2=c.identity54(source2);h.fail('keiba_nine_beta23_local_v1');const n=c.getRaces().length;throws(()=>c.saveRecommendation54(source2.id,key2));ok(c.getRaces().length===n);h.fail(null);
const second=c.saveRecommendation54(source2.id,key2);throws(()=>c.recordPurchase54(second.id));
const reloaded=setup({'keiba_nine_beta23_local_v1':h.storage.get('keiba_nine_beta23_local_v1')});ok(reloaded.c.savedRecommendation54(key).tri.length===36);ok(reloaded.c.financeSummary54('actual').stake===3600); // the next successful save persisted the injected result too
const bad=setup({'keiba_nine_beta23_local_v1':'broken'});throws(()=>bad.c.saveRecommendation54(source.id,key));
// A truncated 40-ticket recommendation stays a list, not an expanded formation.
ok(c.recommend52({...r,first:[1,2,3],second:[1,2,3,4,5]}).length===40);
console.log(checks+' recommendation/save/settlement/purchase checks passed');
