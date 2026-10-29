const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const h=fs.readFileSync('keiba-nine-beta51-feed-record.html','utf8'),c={};vm.createContext(c);
const section=(a,b)=>h.slice(h.indexOf(a),h.indexOf(b));
vm.runInContext(section('/* SIMPLE52_LOGIC_START */','/* SIMPLE52_LOGIC_END */')+section('/* SIMPLE54_LOGIC_START */','/* SIMPLE54_LOGIC_END */')+section('function str41(','const gradeStyle41='),c);
const now=Date.parse('2030-01-01T00:00:00Z'),card={date:'2030-01-02',track:'京都',race:1,complete:true,source:'test only',checkedAt:'2030-01-01T08:00:00+09:00',runners:[1,2,3].map(number=>({number,name:'架空'+number,status:'active'}))};
const r={date:card.date,track:card.track,race:1,off:'12:00',recordType:'live',status:'final',intent:'購入推奨',rankS:[1],rankA:[2],rankB:[3],ranking:[1,2,3],first:[1],second:[2],third:[3],raceCard:card};
let n=0;function ok(v){assert(v);n++;}
ok(c.state54(r,now).canSave);ok(!c.state54({...r,raceCard:undefined},now).canSave);
for(const change of [{complete:false},{track:'東京'},{race:2},{date:'2030-01-03'},{source:''},{checkedAt:'tomorrow'},{checkedAt:'2030-01-01T00:00:00'},{checkedAt:'2030-01-02T00:00:00Z'},{runners:[]},{runners:[card.runners[0],card.runners[0]]},{runners:[...card.runners,{number:19,name:'x',status:'active'}]}])ok(!c.roster60({...r,raceCard:{...card,...change}},now).ok);
for(const status of ['scratched','excluded','unknown'])ok(!c.state54({...r,raceCard:{...card,runners:card.runners.map(x=>x.number===1?{...x,status}:x)}},now).canSave);
ok(!c.roster60({...r,third:[4]},now).ok);ok(!c.roster60({...r,horses:[{number:1,name:'別の馬'}]},now).ok);
ok(c.roster60({...r,horses:[{number:1,name:' 架空１ '}]},now).ok);
ok(c.identity54(r)!==c.identity54({...r,raceCard:{...card,complete:false}}));
const retained=c.extras41(r,'test');ok(retained.raceCard.runners.length===3);
for(const change of [{race:2},{source:''},{checkedAt:'no'},{runners:[card.runners[0],card.runners[0]]}]){assert.throws(()=>c.extras41({...r,raceCard:{...card,...change}},'test'));n++;}
ok(JSON.stringify(r.raceCard)===JSON.stringify(card));
const ticket=c.ticketText63(r,now);ok(ticket.includes('1 → 2 → 3'));ok(ticket.includes('1点 ／ 100円'));
ok(c.ticketText63({...r,intent:'参考'},now).includes('購入推奨ではありません'));
for(const value of [{...r,raceCard:undefined},{...r,intent:'見送り'},r]){
 assert.throws(()=>c.ticketText63(value,value===r?Date.parse('2030-01-03T00:00:00Z'):now));n++;
}
console.log(n+' roster matching, cancellation, identity and normalization checks passed');
