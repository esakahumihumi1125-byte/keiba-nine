'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('integrations/google_apps_script/Code.gs','utf8');
let now='2026-11-08T00:30:00Z',triggerCount=0;
class TestDate extends Date {
 constructor(...args){super(...(args.length?args:[now]));}
 static now(){return Date.parse(now);}
}
const db=new Map(),props={
 getProperty:k=>db.get(k)||null,
 setProperty:(k,v)=>db.set(k,v),
 deleteProperty:k=>db.delete(k)
};
const msg=(name,id,subject,body)=>({
 getSubject:()=>subject,getPlainBody:()=>body,
 getDate:()=>new Date('2026-11-08T00:27:00Z'),
 getId:()=>id,getFrom:()=>name+' <'+name+'@mailman.jrdb.com>'
});
const hot=msg('jrdb-hotg3','mail-hot','[Jrdb-hotg3 8422] 3回福島2日1R',
 '2026年11月08日 3回福島2日 09:45発走\n１Ｒ\n天候:曇　馬場:稍重');
const mini=msg('jrdb-minig2','mail-mini','[Jrdb-minig2 8401] 福島2日1R',
 '福島 1R\n09:45発走\n総合 パドック点\n◎ 3　◎ 3(3.3)\n○ 4　○ 4(2.3)\n▲ 5　▲ 5(2.2)\nパドック☆\n15');
const ctx={
 Date:TestDate,JSON,Number,Array,String,Set,Map,Object,Error,
 Utilities:{
  formatDate:(d,_tz,pattern)=>{
   const utc=new Date(d.getTime()+9*3600000);
   const y=utc.getUTCFullYear(),m=String(utc.getUTCMonth()+1).padStart(2,'0'),
     day=String(utc.getUTCDate()).padStart(2,'0'),
     hh=String(utc.getUTCHours()).padStart(2,'0'),
     mm=String(utc.getUTCMinutes()).padStart(2,'0');
   return pattern==='HH:mm'?hh+':'+mm:y+'-'+m+'-'+day;
  },
  getUuid:()=> 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'
 },
 PropertiesService:{getScriptProperties:()=>props},
 GmailApp:{search:q=>
  [{getMessages:()=>q.includes('jrdb-minig2')?[mini]:[hot]}]},
 ScriptApp:{
  getProjectTriggers:()=>triggerCount?[{getHandlerFunction:()=> 'syncKeibaMail'}]:[],
  newTrigger:fn=>({timeBased:()=>({everyMinutes:n=>({create:()=>{assert.equal(fn,'syncKeibaMail');assert.equal(n,1);triggerCount++;}})})})
 },
 LockService:{getScriptLock:()=>({tryLock:()=>true,releaseLock:()=>{}})},
 ContentService:{
  MimeType:{JSON:'application/json'},
  createTextOutput:body=>({body,setMimeType(){return this;}})
 }
};
vm.createContext(ctx);
vm.runInContext(source,ctx,{filename:'Code.gs'});
ctx.createKeibaBridgeToken();
const token=db.get('KEIBA_BRIDGE_TOKEN');
assert.equal(token.length,64);
ctx.installKeibaMailTrigger();
ctx.installKeibaMailTrigger();
assert.equal(triggerCount,1,'idempotent timer');
ctx.syncKeibaMail();
const stored=JSON.parse(db.get('KEIBA_MAIL_DAY_20261108'));
assert.equal(Object.keys(stored.records).length,1);
assert.equal(stored.records['福島:1'].ground,'稍重');
assert.equal(JSON.stringify(stored.records['福島:1'].paddock),'[3,4,5]');
assert.equal(JSON.stringify(stored).includes('パドック点'),false,'no paid body');
function post(payload){return JSON.parse(ctx.doPost({postData:{contents:JSON.stringify(payload)}}).body);}
assert.equal(post({action:'read',date:'2026-11-08',token:'wrong'}).ok,false);
const reply=post({action:'read',date:'2026-11-08',token});
assert.equal(reply.schema,'keiba-nine-mail-bridge-v1');
assert.equal(reply.races.length,1);
assert.equal(JSON.stringify(reply.races[0].paddock),'[3,4,5]');
assert.equal(JSON.stringify(reply).includes(token),false);
assert.equal(JSON.stringify(reply).includes('3.3'),false,'no proprietary score');
db.delete('KEIBA_MAIL_DAY_20261108');
now='2026-11-08T00:44:00Z';
ctx.syncKeibaMail();
const late=JSON.parse(db.get('KEIBA_MAIL_DAY_20261108'));
assert.equal(Object.keys(late.records).length,0,'never newly publish after cutoff');
console.log('Gmail bridge synthetic mail parser, secret gate and cutoff PASS');
