"""Confirmed Monday JRA holidays reuse the guarded weekend auto-read only."""
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_auto_forecast_ui import JS, HTML


class ConfirmedHolidayJraDayTests(unittest.TestCase):
    def test_page_discloses_billable_on_open_for_confirmed_holidays(self):
        self.assertIn("JRA公表済みの2026年開催月曜", HTML)
        self.assertIn("2026-11-23", JS)
        self.assertIn("confirmedHoliday", JS)
        self.assertIn("if(normalWeekend||confirmedHoliday)", JS)
        self.assertIn("JRA開催の月祝当日", JS)
        self.assertNotIn("Special weekday races are explicit manual reads", JS)

    @unittest.skipUnless(shutil.which("node"), "Node unavailable")
    def test_limited_to_exact_2026_scheduled_monday_and_explicit_eve_label(self):
        node = r"""
const fs=require('node:fs'),assert=require('node:assert/strict');
const vm=require('node:vm');
const source=fs.readFileSync(0,'utf8');
const decl=source.match(/const CONFIRMED_MONDAY_RACEDAYS=new Set\(\[[\s\S]*?\]\);/);
assert(decl,'explicit list is required');
const autoStart=source.indexOf('function autoFetchOnRegularRaceDay(){');
const autoEnd=source.indexOf("\nif(typeof document.addEventListener",autoStart);
const hiliteStart=source.indexOf('function highlightSelectedWeekend(){');
const hiliteEnd=source.indexOf("\n$('autoDay').value=jstToday();",hiliteStart);
assert(autoStart>=0&&autoEnd>autoStart);
assert(hiliteStart>=0&&hiliteEnd>hiliteStart);
const autoCode=decl[0]+'\n'+source.slice(autoStart,autoEnd);
const highlightCode=decl[0]+'\n'+source.slice(hiliteStart,hiliteEnd);
function dayTest(day,expectCall){
 let calls=0,seen=[];
 const el=new Map([['autoDay',{value:day}]]);
 const $=id=>{
  if(!el.has(id))el.set(id,{textContent:'',onclick:()=>{if(id==='autoRun')calls++;}});
  return el.get(id);
 };
 vm.runInNewContext(autoCode+"\n;autoFetchOnRegularRaceDay();",{
  $,Date,Set,Number,Array,
  recentWeekendEmptyRead:()=>false,
  showRecentlyFixedWithoutProvider:(day,label)=>{seen.push(label);return false;},
  jstToday:()=>day,nearestJstWeekday:()=> '2026-11-28'
 },{timeout:800});
 assert.equal(calls,expectCall,day+' unexpected provider request');
 if(day==='2026-11-23')assert.equal(seen[0],'JRA開催の月祝当日');
}
dayTest('2026-11-22',1);
dayTest('2026-11-23',1);
dayTest('2026-11-30',0);
dayTest('2026-11-24',0);
dayTest('2026-11-21',1);
// Older published 2026 holiday is explicit but the actual scheduled racing
// date is only selected when the current day matches.
dayTest('2026-10-12',1);
function highlight(today){
 const el=new Map([['autoDay',{value:today}]]);
 const $=id=>{
  if(!el.has(id))el.set(id,{dataset:{},hidden:false,disabled:false,textContent:''});
  return el.get(id);
 };
 const day=new Date(today+'T12:00:00Z');
 const nearest=target=>{
  const d=new Date(day.valueOf());
  d.setUTCDate(d.getUTCDate()+(target-d.getUTCDay()+7)%7);
  return d.toISOString().slice(0,10);
 };
 vm.runInNewContext(highlightCode+"\n;highlightSelectedWeekend();",{
  $,Date,Set,Number,jstToday:()=>today,nearestJstWeekday:nearest
 },{timeout:800});
 return $;
}
const sun=highlight('2026-11-22');
assert.equal(sun('autoMondayQuick').hidden,false);
assert.equal(sun('autoMondayQuick').disabled,false);
assert(sun('autoMondayQuick').textContent.includes('明日11/23（月祝）'));
const ordinary=highlight('2026-11-29');
assert.equal(ordinary('autoMondayQuick').hidden,true);
assert.equal(ordinary('autoMondayQuick').disabled,true);
console.log('2026 holiday auto-read: ONLY confirmed Monday or weekends; Sunday next-day shortcut PASS');
"""
        run = subprocess.run(["node", "-e", node], input=JS, text=True,
                             capture_output=True, timeout=15, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("ONLY confirmed Monday", run.stdout)


if __name__ == "__main__":
    unittest.main()
