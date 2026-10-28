const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const h=fs.readFileSync('keiba-nine-beta51-feed-record.html','utf8'),c={};vm.createContext(c);
function part(a,b){return h.slice(h.indexOf(a),h.indexOf(b));}
vm.runInContext(part('/* REVIEW58_START */','/* REVIEW58_END */')+part('/* SIMPLE54_LOGIC_START */','/* SIMPLE54_LOGIC_END */'),c);
const f={version:2,tri:[[1,2,3]]},r={confirmed:true,one:1,two:2,three:3};
assert.match(c.review58(f,r),/的中/);assert.match(c.review58(f,{...r,two:3,three:2}),/着順が違い/);
assert.match(c.review58(f,{...r,three:4}),/2・3着/);assert.match(c.review58(f,{...r,one:4}),/1着が/);
assert.match(c.review58(f,{...r,confirmed:false}),/確認・保存/);assert.match(c.review58(null,r),/対象外/);
assert.match(c.review58({...f,tri:[]},r),/ありません/);assert.match(c.review58(f,null),/確認・保存/);
const q=c.quality58({rankS:[1,2],horses:[{number:1,name:'テスト'}]});assert.equal(q.named,1);assert.equal(q.total,2);assert.equal(q.source,false);assert.equal(q.training,false);
assert.equal(JSON.stringify(f),JSON.stringify({version:2,tri:[[1,2,3]]}));
console.log('13 quality and saved-ticket review checks passed');
