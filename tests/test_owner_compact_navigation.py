"""Compact ARC RACE owner screen remains read-only and easy to navigate."""
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_auto_forecast_ui import HTML, CSS, JS


class OwnerCompactNavigationTests(unittest.TestCase):
    def test_simple_primary_workflow_keeps_original_tools_accessible(self):
        self.assertLess(HTML.index('id="autoDailyStart"'),
                        HTML.index('class="owner-preday-recovery"'))
        self.assertLess(HTML.index('class="owner-preday-recovery"'),
                        HTML.index('id="forecastRacesSection"'))
        for element in ("ownerPredayMode", "ownerJrdbMode",
                        "ownerDetailToggle", "autoPredayInlineRaces",
                        "autoCombinedResearchRows", "autoHistory",
                        "autoAdvancedResearch", "autoRun", "autoSaturdayQuick"):
            self.assertEqual(HTML.count('id="' + element + '"'), 1, element)
        all_ids = re.findall(r'id="([^"]+)"', HTML)
        self.assertEqual(len(all_ids), len(set(all_ids)))
        self.assertIn('class="owner-simple owner-preday-view"', HTML)
        self.assertIn("body.owner-simple:not(.owner-detailed)", CSS)
        self.assertIn("owner-jrdb-view .owner-preday-recovery", CSS)
        self.assertIn("owner-preday-view #forecastRacesSection", CSS)
        self.assertIn("owner-view-switch button[aria-pressed", CSS)
        self.assertIn('href="#fixedHistorySection"', HTML)
        self.assertIn('正式10項目の予想とJRA公式照合は未完成', HTML)

    @unittest.skipUnless(shutil.which("node"), "Node not available")
    def test_source_switches_and_details_do_not_fetch_or_write(self):
        node = r"""
const vm=require('node:vm'),assert=require('node:assert/strict');
const code=require('node:fs').readFileSync(0,'utf8');
const marker=";(()=>{'use strict';\nconst preday=document.getElementById('ownerPredayMode');";
const start=code.lastIndexOf(marker);
assert(start>=0,'isolated compact navigation script');
const names=['ownerPredayMode','ownerJrdbMode','ownerDetailToggle',
 'forecastRacesSection','autoPredayInlineRaces',
 'autoSaturdayQuick','autoSundayQuick','autoMondayQuick','autoRun',
 'autoPredayInlineLoad'];
const attrs=new Map(),controlListeners=new Map();
const els=new Map(names.map(n=>[n,{
 textContent:'',onclick:null,scrolls:0,
 setAttribute(k,v){attrs.set(n+':'+k,v)},
 addEventListener(type,fn){controlListeners.set(n+':'+type,fn)},
 scrollIntoView(){this.scrolls++}
}]));
const classes=new Set(['owner-simple','owner-preday-view']);
const body={classList:{
 toggle(name,state){
  const value=state===undefined?!classes.has(name):state;
  if(value)classes.add(name);else classes.delete(name);
  return value;
 },
 contains:name=>classes.has(name)
}};
const listeners=new Map(),links=new Map(
 ['.arc-main-tabs a[href="#forecastRacesSection"]',
  '.arc-main-tabs a[href="#fixedHistorySection"]'].map(name=>[name,{
   addEventListener(type,fn){listeners.set(name+':'+type,fn)}
 }]));
const document={body,getElementById:id=>els.get(id),
 querySelector:name=>links.get(name)};
vm.runInNewContext(code.slice(start),{document,String},
 {timeout:1000});
assert(classes.has('owner-preday-view')&&!classes.has('owner-jrdb-view'));
assert.equal(attrs.get('ownerPredayMode:aria-pressed'),'true');
els.get('ownerJrdbMode').onclick();
assert(classes.has('owner-jrdb-view')&&!classes.has('owner-preday-view'));
assert.equal(els.get('forecastRacesSection').scrolls,1);
assert.equal(attrs.get('ownerJrdbMode:aria-pressed'),'true');
els.get('ownerPredayMode').onclick();
assert(classes.has('owner-preday-view'));
assert.equal(els.get('autoPredayInlineRaces').scrolls,1);
els.get('ownerDetailToggle').onclick();
assert(classes.has('owner-detailed'));
assert.equal(els.get('ownerDetailToggle').textContent,'簡単表示に戻す');
els.get('ownerDetailToggle').onclick();
assert(!classes.has('owner-detailed'));
listeners.get('.arc-main-tabs a[href="#fixedHistorySection"]:click')();
assert(classes.has('owner-detailed'),'record navigation reveals history');
listeners.get('.arc-main-tabs a[href="#forecastRacesSection"]:click')();
assert(classes.has('owner-jrdb-view'),'race navigation reveals JRDB');
// The existing authenticated paid fetch handler runs exactly once per tap;
// the additive navigation listener must not replace it or call it again.
let paidCalls=0;
for(const id of ['autoSaturdayQuick','autoSundayQuick','autoMondayQuick','autoRun'])
 els.get(id).onclick=()=>{paidCalls++};
function browserTap(id){
 const element=els.get(id);
 if(typeof element.onclick==='function')element.onclick();
 const listener=controlListeners.get(id+':click');
 assert.equal(typeof listener,'function',id+' must have a view listener');
 listener();
}
for(const id of ['autoSaturdayQuick','autoSundayQuick','autoMondayQuick','autoRun']){
 els.get('ownerPredayMode').onclick();
 assert(classes.has('owner-preday-view'));
 browserTap(id);
 assert(classes.has('owner-jrdb-view'),'one tap must reveal the fetched predictions');
}
assert.equal(paidCalls,4,'all existing source gestures remain exactly once');
browserTap('autoPredayInlineLoad');
assert(classes.has('owner-preday-view'),'free reference refresh reveals preday');
assert.equal(paidCalls,4,'view changes must not add a paid source request');
console.log('Compact owner view switch: one-tap JRDB reveal, no duplicate API/storage PASS');
"""
        result = subprocess.run(["node", "-e", node], input=JS, text=True,
                                capture_output=True, timeout=15, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no duplicate API/storage", result.stdout)


if __name__ == "__main__":
    unittest.main()
