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
        self.assertIn("renderCombinedResearchRows(data,day,displayableDrafts,quickRows,agreement)", JS)
        self.assertIn("validatedDraftFirstAgreement(", JS)

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
 'globalThis.renderCombined=renderCombinedResearchRows;'+
 '\nglobalThis.heldWorkout=safeHeldWorkoutEvidence;'+
 '\nglobalThis.draftAgreement=validatedDraftFirstAgreement;',sandbox);
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
// A real held race with partial JRDB workout evidence, but no known recent
// grade; its appearance must never increase the signed/unsigned pick count.
R[18].reason='missing_factors';
R[18].horseCount=4;
R[18].runners=[
 {number:3,training:'S',recent:'未評価'},
 {number:1,training:'A',recent:'未評価'},
 {number:6,training:'B',recent:'未評価'},
 {number:9,training:'未評価',recent:'未評価'},
];
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
// Only an independently validated and already rendered multi-factor card
// may annotate an existing 2-factor draft. No new prediction is created.
const source={children:[{children:[
 {textContent:'東京 1R｜研究用 36点（共通配点64点分）'},
 {textContent:'1着 1・2番／2着 1・2・3番／3着 1・2・3・4番'}
]}]};
const agreement=sandbox.draftAgreement(data,day,source);
assert.match(agreement.get('東京|1'),/1着候補比較：一致/);
const rendered=sandbox.renderCombined(data,day,drafts,references,agreement);
assert.equal(rendered.picks.length,17);
assert.match(elements.get('autoCombinedResearchStatus').textContent,
 /全24R｜発走前研究用下書き 4R｜署名なし追加参考 13R｜新しい買い目・参考候補なし 7R/);
const [venues,kinds,jumps,cards]=elements.get('autoCombinedResearchRows').children;
assert.deepEqual(venues.children.map(b=>b.textContent),['東京','福島']);
assert.equal(kinds.children.length,4,'safe research type filters');
assert.deepEqual(kinds.children.map(x=>x.textContent),[
 '全R 12R','買い目あり 4R','参考 8R','見送り 0R']);
assert.equal(kinds.children[3].disabled,true,'0 holds disabled in Tokyo');
assert.equal(jumps.children.length,13,'all 12R and all-races selector');
assert.equal(jumps.children[0].textContent,'全R');
assert.equal(cards.children.length,12);
assert.equal(cards.children[0].children[0].textContent,'東京 1R');
assert.match(cards.children[0].children[5].textContent,/1着候補比較：一致/);
kinds.children[1].onclick(); // Tokyo signed/unsigned never mix.
assert.equal(cards.children.filter(c=>!c.hidden).length,4);
assert.equal(kinds.children[1].ariaPressed,'true');
assert.equal(cards.children[3].hidden,false);
assert.equal(cards.children[4].hidden,true,'unsigned reference not in signed tab');
kinds.children[2].onclick(); // unsigned references only
assert.equal(cards.children.filter(c=>!c.hidden).length,8);
assert.equal(kinds.children[2].ariaPressed,'true');
assert.equal(cards.children[0].hidden,true,'signed draft not in reference tab');
jumps.children[5].onclick(); // 東京5R only
assert.equal(cards.children.filter(c=>!c.hidden).length,1);
assert.equal(cards.children[4].hidden,false);
assert.equal(jumps.children[5].ariaPressed,'true');
assert.equal(kinds.children[0].ariaPressed,'true','race number resets category');
jumps.children[0].onclick();
assert.equal(cards.children.filter(c=>!c.hidden).length,12);
assert.equal(jumps.children[0].ariaPressed,'true');
venues.children[1].onclick();
assert.equal(jumps.children.length,13,'venue switch resets 12R picker');
assert.equal(kinds.children.length,4,'venue switch resets research categories');
assert.deepEqual(kinds.children.map(x=>x.textContent),[
 '全R 12R','買い目あり 0R','参考 5R','見送り 7R']);
assert.equal(kinds.children[1].disabled,true);
assert.equal(cards.children.length,12,'all 12 Fukushima races remain discoverable');
assert.equal(cards.children.filter(c=>!c.hidden).length,12);
kinds.children[3].onclick();
assert.equal(cards.children.filter(c=>!c.hidden).length,7,
 'Fukushima held races have no new tickets');
assert.equal(cards.children[5].hidden,false,'held no-pick visible');
assert.equal(cards.children[0].hidden,true,'reference not a held no-pick');
kinds.children[2].onclick();
assert.equal(cards.children.filter(c=>!c.hidden).length,5,
 'Fukushima unsigned references are separate');
kinds.children[0].onclick();
assert.equal(cards.children.filter(c=>!c.hidden).length,12);
assert.equal(cards.children[0].children[0].textContent,'福島 1R');
assert.equal(cards.children[5].children[0].textContent,'福島 6R');
assert.match(cards.children[5].children[1].textContent,/見送り・参考候補なし/);
assert.match(cards.children[5].className,/owner-research-hold/);
const partial=cards.children[6]; // 福島7R: workout present, recent missing
assert.equal(partial.children[0].textContent,'福島 7R');
assert.match(partial.children[1].textContent,/見送り・参考候補なし/);
assert.match(partial.children[2].textContent,/調教S：3番/);
assert.match(partial.children[3].textContent,/調教A：1番/);
assert.match(partial.children[4].textContent,/調教B：6番/);
assert.match(partial.children[5].textContent,/近走未評価4頭/);
assert.match(partial.children[5].textContent,/3連単の買い目なし/);
assert(!partial.children.some(node=>/^[123]着 /.test(node.textContent)));
assert.equal(venues.children[1].ariaPressed,'true');
assert.equal(elements.get('autoCombinedNoPickRows').children.length,7);
assert.equal(elements.get('autoCombinedResearchPanel').open,true);
assert.equal(elements.get('autoCombinedNoPickPanel').open,false);
assert.equal(networkCalls,0);
assert.equal(receiptWrites,0);
assert(documentWrites>10);
// Malformed source numbers or all-missing workout must not produce bands.
const duplicate={...R[18],runners:[
 {...R[18].runners[0]}, {...R[18].runners[0]},
 ...R[18].runners.slice(2)
]};
assert.equal(sandbox.heldWorkout(duplicate),null);
const zero={...R[18],runners:R[18].runners.map(h=>({...h,training:'未評価'}))};
assert.equal(sandbox.heldWorkout(zero),null);
assert.equal(sandbox.heldWorkout({...R[18],status:'provisional_draft'}),null);
const past={raceCount:1,draftCount:0,holdCount:1,races:[
 {...R[18],postTime:'23:55'}
]};
sandbox.renderCombined(past,day,[],[]);
const expiredCard=elements.get('autoCombinedResearchRows').children[3].children[0];
assert(!expiredCard.children.some(n=>/調教[SA]/.test(n.textContent)),
 'past-off races must not show a fresh workout ranking');
assert.equal(networkCalls,0);
assert.equal(receiptWrites,0);
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
