"""One-tap owner-only research export: 24R index, no purchases or paid calls."""
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_auto_forecast_ui import HTML, JS


class ResearchExportTests(unittest.TestCase):
    def test_action_is_visible_and_explains_separate_signed_backup(self):
        self.assertIn('id="autoCombinedResearchExport"', HTML)
        self.assertIn('id="autoCombinedResearchExportStatus"', HTML)
        self.assertIn("発走前署名やサーバー永続保存の代わりにはなりません", HTML)
        self.assertIn("combinedResearchDownloadText(fresh,day", JS)
        self.assertIn("link.download='arc-race-'+day+'-research-view.txt'", JS)
        self.assertIn("URL.revokeObjectURL(url)", JS)
        self.assertIn("発走前固定", JS)

    @unittest.skipUnless(shutil.which("node"), "Node unavailable")
    def test_24r_download_rechecks_races_date_without_second_fetch(self):
        node = r"""
const assert=require('node:assert/strict'),vm=require('node:vm');
const src=require('node:fs').readFileSync(0,'utf8');
const start=src.indexOf('function combinedResearchIndex(');
const end=src.indexOf('function render(input,day){',start);
assert(start>=0&&end>start);
const source=src.slice(start,end);
const dates=['東京','福島'];const races=[];
for(const track of dates)
 for(let i=1;i<=12;i++){
  const n=races.length;
  races.push({track,race:i,postTime:'1'+Math.floor(n/6)+
   ':'+String(n%6*10).padStart(2,'0'),
   status:n<4?'provisional_draft':'hold',
   points:n<4?36:0,first:n<4?[1,2]:[],
   second:n<4?[1,2,3,4]:[],
   third:n<4?[1,2,3,4,5]:[]});
 }
const day='20261123';
const report={raceCount:24,draftCount:4,holdCount:20,races};
const drafts=races.slice(0,4).map(r=>({
 key:r.track+'|'+r.race,draft:true,postTime:r.postTime
}));
const references=races.slice(4,17).map(r=>({
 race:r,panel:{label:'近走不足'},
 picks:['1着候補 1・2','2着候補 1・2・3','3着候補 1・2・3・4']
}));
class Elem {
 constructor(tag){this.tag=tag;this.children=[];this.disabled=false;
  this.textContent='';this.open=false;this.onclick=null;this.value='';}
 append(...children){this.children.push(...children)}
 replaceChildren(...children){this.children=children}
}
const nodes=new Map([
 'autoCombinedResearchRows','autoCombinedNoPickRows',
 'autoCombinedResearchStatus','autoCombinedNoPickTitle',
 'autoCombinedResearchPanel','autoCombinedNoPickPanel',
 'autoCombinedResearchExport','autoCombinedResearchExportStatus',
 'autoDay'
].map(id=>[id,new Elem(id)]));
nodes.get('autoDay').value='2026-11-23';
let requests=0,writes=0,downloads=0,revoked=0,created=0;
let lastFile='',lastName='';
const doc={
 body:{append(x){x.attached=true}},
 createElement:tag=>{
  if(tag==='a')return {
   href:'',download:'',hidden:false,
   click(){downloads++;lastName=this.download},
   remove(){this.attached=false}
  };
  return new Elem(tag);
 }
};
const sandbox={
 Set,Map,Object,Array,Number,String,Error,Date,document:doc,
 $:key=>nodes.get(key),
 dom:(tag,value)=>{const x=new Elem(tag);
  x.textContent=value===undefined?'':String(value);return x;},
 draftExpiredOnDevice:(day,postTime)=>postTime==='23:55',
 Blob:class {
  constructor(data,options){
   created++;lastFile=data.join('');this.type=options.type;
  }
 },
 URL:{
  createObjectURL:()=> 'blob:private-research-1',
  revokeObjectURL:()=>{revoked++}
 },
 setTimeout:fn=>fn(),
 fetch:()=>{requests++;throw Error('paid request prohibited')},
 localStorage:{setItem:()=>{writes++}},
 report,day
};
vm.createContext(sandbox);
vm.runInContext('let latestDisplayedReport,latestDisplayedDay;\n'+source+
 '\nglobalThis.combined=combinedResearchIndex;'+
 'globalThis.format=combinedResearchDownloadText;'+
 'globalThis.renderAll=renderCombinedResearchRows;',sandbox);
vm.runInContext('latestDisplayedReport=report;latestDisplayedDay=day;',sandbox);
const summary=sandbox.combined(report,day,drafts,references);
assert.equal(summary.signed,4);
assert.equal(summary.unsigned,13);
assert.equal(summary.excluded.length,7);
const formatted=sandbox.format(summary,day,'2026-11-22T08:40:00.000Z');
assert.match(formatted,/全R研究参考・閲覧専用/);
assert.match(formatted,/JRDB2項目の研究下書き：4R/);
assert.match(formatted,/署名なし参考例：13R/);
assert.match(formatted,/新しい候補表示なし：7R/);
assert.match(formatted,/独立検証なし/);
assert.match(formatted,/発走前保存の署名を持たず/);
assert.equal((formatted.match(/予定（JRDB）｜/g)||[]).length,24);
assert(!formatted.includes('officialJraVerified:true'));
assert(!formatted.includes('actualPurchase:true'));
assert(!formatted.includes('rawIndex'));
sandbox.renderAll(report,day,drafts,references);
const button=nodes.get('autoCombinedResearchExport');
assert.equal(button.disabled,false);
button.onclick();
assert.equal(downloads,1);
assert.equal(created,1);
assert.equal(revoked,1);
assert.equal(lastName,'arc-race-20261123-research-view.txt');
assert.equal(lastFile.split('\n')[0],formatted.split('\n')[0]);
assert.equal(lastFile.split('\n')[1],formatted.split('\n')[1]);
assert.match(lastFile,/研究下書き：4R/);
assert.match(lastFile,/署名なし参考例：13R/);
assert.match(nodes.get('autoCombinedResearchExportStatus').textContent,
 /iPhoneの「ファイル」/);
assert.equal(requests,0);
assert.equal(writes,0);
nodes.get('autoDay').value='2026-11-22';
button.onclick();
assert.equal(downloads,1,'old day cannot be downloaded');
assert.match(nodes.get('autoCombinedResearchExportStatus').textContent,/取得日が変わりました/);
nodes.get('autoDay').value='2026-11-23';
races[0].postTime='23:55';  // onset of provisional off, at next explicit tap
button.onclick();
assert.equal(downloads,2);
assert.match(lastFile,/JRDB2項目の研究下書き：3R/);
assert.match(lastFile,/新しい候補表示なし：8R/);
assert.equal(requests,0);
assert.equal(writes,0);
const invalid={...summary,picks:[...summary.picks,summary.picks[0]]};
assert.throws(()=>sandbox.format(invalid,day,'2026-11-22T08:40:00Z'));
assert.throws(()=>sandbox.format(summary,day,'invalid_timestamp'));
console.log('24R read-only file export: 4+13+7, no paid request, no receipt mutation, date and off recheck PASS');
"""
        completed = subprocess.run(
            ["node", "-e", node], input=JS, text=True,
            capture_output=True, check=False, timeout=15,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("off recheck PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()
