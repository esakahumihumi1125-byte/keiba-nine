"""4 signed + 13 unsigned + 7 excluded: a safe, useful 24R phone view."""
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_auto_forecast_ui import HTML, JS


class OwnerCombinedPrestartStudyTests(unittest.TestCase):
    def test_visible_homepage_shortlist_and_separate_result_types(self):
        for id_ in ("autoCombinedResearchPanel", "autoCombinedResearchRows",
                    "autoCombinedResearchStatus", "autoCombinedNoPickPanel",
                    "autoCombinedNoPickRows", "autoCombinedNoPickTitle"):
            self.assertIn('id="' + id_ + '"', HTML)
        self.assertIn("研究用下書きと署名なし参考例", HTML)
        self.assertIn("正式10項目", HTML)
        self.assertIn("renderCombinedResearchRows(data,day,displayableDrafts,quickRows)", JS)

    @unittest.skipUnless(shutil.which("node"), "Node unavailable")
    def test_24r_combined_never_promotes_bounded_unsigned_references(self):
        node = r"""
const assert=require('node:assert/strict'),vm=require('node:vm');
const js=require('node:fs').readFileSync(0,'utf8');
const from=js.indexOf('function combinedResearchIndex(');
const end=js.indexOf('function render(input,day){',from);
assert(from>0&&end>from);
let documentWrites=0,networkCalls=0,receiptWrites=0;
class Element{
 constructor(tag){this.tag=tag;this.children=[];this.textContent='';
  this.open=false;this.className='';}
 append(...nodes){this.children.push(...nodes);}
 replaceChildren(...nodes){this.children=nodes;}
}
const elements=new Map([
 'autoCombinedResearchRows','autoCombinedResearchStatus',
 'autoCombinedNoPickTitle','autoCombinedNoPickRows',
 'autoCombinedResearchPanel','autoCombinedNoPickPanel',
 'autoCombinedResearchExport','autoCombinedResearchExportStatus'
].map(key=>[key,new Element(key)]));
const sandbox={
 Set,Map,Object,Array,String,Number,Error,
 REASONS:{missing_factors:'資料不足',ambiguous_equal_grade_boundary:'同点判定保留'},
 $:key=>elements.get(key),
 dom:(tag,value,className)=>{
  const out=new Element(tag);
  if(value!==undefined)out.textContent=String(value);
  out.className=className||'';
  documentWrites++;return out;
 },
 draftExpiredOnDevice:(day,time)=>time==='23:55',
 fetch:()=>{networkCalls++;throw Error('unexpected_provider_call')},
 localStorage:{setItem:()=>{receiptWrites++}},
};
vm.createContext(sandbox);
vm.runInContext(js.slice(from,end)+
 '\nglobalThis.study=combinedResearchIndex;'+
 'globalThis.renderCombined=renderCombinedResearchRows;',sandbox);
const R=[];
for(const track of ['東京','福島'])
 for(let race=1;race<=12;race++){
  const n=R.length;
  R.push({track,race,postTime:'1'+String(Math.floor(n/6))+
    ':'+String((n%6)*10).padStart(2,'0'),
   status:n<4?'provisional_draft':'hold',
   points:n<4?36:0,first:n<4?[1,2]:[],second:n<4?[1,2,3,4]:[],
   third:n<4?[1,2,3,4,5]:[]});
 }
const day='20261123';
const data={raceCount:24,draftCount:4,holdCount:20,races:R};
const drafts=R.slice(0,4).map(r=>({
 key:r.track+'|'+r.race,draft:true,postTime:r.postTime
}));
const references=R.slice(4,17).map(r=>({
 race:r,panel:{label:'近走不足'},
 picks:['1着候補 1・2','2着候補 1・2・3','3着候補 1・2・3・4']
}));
const result=sandbox.study(data,day,drafts,references);
assert.equal(result.signed,4);
assert.equal(result.unsigned,13);
assert.equal(result.excluded.length,7);
assert.equal(result.picks.length,17);
assert.equal(new Set(result.picks.map(x=>x.key)).size,17);
assert.equal(result.picks.filter(x=>x.type==='unsigned_reference').length,13);
assert(result.picks.every(x=>x.lines.length>=1));
assert(result.picks.slice(0,4).every(x=>x.title.includes('36点')));
assert(!JSON.stringify(result).includes('"actualPurchase":true'));
const rendered=sandbox.renderCombined(data,day,drafts,references);
assert.equal(rendered.picks.length,17);
assert.match(elements.get('autoCombinedResearchStatus').textContent,
 /全24R｜発走前研究用下書き 4R｜署名なし追加参考 13R｜新しい買い目・参考候補なし 7R/);
const [venues,cards]=elements.get('autoCombinedResearchRows').children;
assert.deepEqual(venues.children.map(b=>b.textContent),['東京','福島']);
assert.equal(cards.children.length,12);
assert.equal(cards.children[0].children[0].textContent,'東京 1R');
venues.children[1].onclick();
assert.equal(cards.children.length,12,'all 12 Fukushima races remain discoverable');
assert.equal(cards.children[0].children[0].textContent,'福島 1R');
assert.equal(cards.children[5].children[0].textContent,'福島 6R');
assert.match(cards.children[5].children[1].textContent,/見送り・参考候補なし/);
assert.match(cards.children[5].className,/owner-research-hold/);
assert.equal(venues.children[1].ariaPressed,'true');
assert.equal(elements.get('autoCombinedNoPickRows').children.length,7);
assert.equal(elements.get('autoCombinedResearchPanel').open,true);
assert.equal(elements.get('autoCombinedNoPickPanel').open,false);
assert.equal(networkCalls,0);
assert.equal(receiptWrites,0);
assert(documentWrites>10);
const counterfeit=references.slice();
counterfeit[0]={...counterfeit[0],race:R[0]};
assert.throws(()=>sandbox.study(data,day,drafts,counterfeit));
const fake=references.slice();
fake[0]={...fake[0],panel:{label:'JRA公式照合済'}};
assert.throws(()=>sandbox.study(data,day,drafts,fake));
const duplicated=references.slice();
duplicated.push(references[0]);
assert.throws(()=>sandbox.study(data,day,drafts,duplicated));
const invalid={...data,raceCount:25};
assert.throws(()=>sandbox.study(invalid,day,drafts,references));
const lateDraft=structuredClone(data);
lateDraft.races[0].postTime='23:55';
const lateDrafts=[{...drafts[0]},...drafts.slice(1)];
const late= sandbox.study(lateDraft,day,lateDrafts,[]);
assert.equal(late.signed,3);
assert.equal(late.excluded.length,21);
const lateReference=structuredClone(data);
lateReference.races[4].postTime='23:55';
const oldRefs=[{...references[0],race:lateReference.races[4]},
 ...references.slice(1).map(item=>({
  ...item,race:lateReference.races.find(r=>
   r.track===item.race.track&&r.race===item.race.race)
 }))];
const lateData={...lateReference};
const lateResult=sandbox.study(lateData,day,[],oldRefs);
assert.equal(lateResult.unsigned,12);
assert.equal(lateResult.excluded.length,12);
console.log('24R combined forecast: 4 signed drafts + 13 unsigned references + 7 unshown, stale safety, no extra provider or receipt writes PASS');
"""
        completed=subprocess.run(
            ["node", "-e", node], input=JS, capture_output=True,
            text=True, timeout=15, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("4 signed drafts + 13 unsigned references", completed.stdout)


if __name__ == "__main__":
    unittest.main()
