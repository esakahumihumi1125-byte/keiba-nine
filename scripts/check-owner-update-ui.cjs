/* Owner home-screen update check: no network, paid data or browser dependency. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('/tmp/keiba-owner-update.js','utf8');
function page({path='/',loaded='iphone-login-recovery-20261105-v9|aaaaaaaaaaaa',
               version='iphone-login-recovery-20261105-v9',sha='bbbbbbbbbbbb',
               status=200,failed=false}={}){
 const winEvents={},docEvents={},messages=[],requests=[],reloads=[];
 const makeElement=tag=>({
  tag,textContent:'',type:'',className:'',onclick:null,children:[],attributes:{},
  setAttribute(k,v){this.attributes[k]=v},
  append(...children){this.children.push(...children)}
 });
 const document={
  visibilityState:'visible',
  querySelector:q=>q==='meta[name="keiba-owner-release"]'?{content:loaded}:null,
  addEventListener:(type,fn)=>{docEvents[type]=fn},
  createElement:makeElement,
  body:{prepend:e=>messages.push(e)}
 };
 const location={pathname:path,reload:()=>reloads.push('reload')};
 const window={addEventListener:(type,fn)=>{winEvents[type]=fn}};
 const fetch=async(url,options)=>{
  requests.push({url,options});
  if(failed)throw Error('network outage');
  return {ok:status===200,text:async()=>'KEIBA NINE\nuiVersion='+version+'\nrenderCommit='+sha+'\nnote=owner-only'};
 };
 vm.runInNewContext(source,{document,window,location,fetch});
 return {document,window,location,winEvents,docEvents,messages,requests,reloads};
}
const flush=async()=>{
 await Promise.resolve();await Promise.resolve();
 await new Promise(resolve=>setImmediate(resolve));
};
(async()=>{
 const root=page();
 root.winEvents.pageshow();await flush();
 assert.equal(root.reloads.length,1,'clean landing auto-updates on new deploy');
 assert.equal(root.messages.length,0,'clean landing never asks for manual refresh');
 assert.equal(root.requests[0].url,'/ui-version');
 assert.equal(root.requests[0].options.cache,'no-store');
 assert.equal(root.requests[0].options.credentials,'same-origin');
 assert.equal(root.requests[0].options.redirect,'manual');
 const unchanged=page({sha:'aaaaaaaaaaaa'});
 unchanged.winEvents.pageshow();await flush();
 assert.equal(unchanged.reloads.length,0,'same deployed version does not reload');
 assert.equal(unchanged.messages.length,0);
 const editor=page({path:'/my-tickets'});
 editor.winEvents.pageshow();await flush();
 assert.equal(editor.reloads.length,0,'never auto-reload notebook while editing might occur');
 assert.equal(editor.messages.length,1,'show a non-destructive update notice');
 assert.match(editor.messages[0].children[0].textContent,/編集中の入力/);
 editor.winEvents.pageshow();await flush();
 assert.equal(editor.messages.length,1,'at most one update banner');
 editor.messages[0].children[1].onclick();
 assert.equal(editor.reloads.length,1,'explicit update tap may reload notebook');
 const dirtyRoot=page();
 dirtyRoot.docEvents.input();dirtyRoot.winEvents.pageshow();await flush();
 assert.equal(dirtyRoot.reloads.length,0,'never auto-reload edited landing');
 assert.equal(dirtyRoot.messages.length,1);
 const resumed=page();
 resumed.document.visibilityState='hidden';
 resumed.docEvents.visibilitychange();await flush();
 assert.equal(resumed.requests.length,0,'no background polling while hidden');
 resumed.document.visibilityState='visible';
 resumed.docEvents.visibilitychange();await flush();
 assert.equal(resumed.reloads.length,1,'resuming visible app checks deploy');
 const unauth=page({status:401});unauth.winEvents.pageshow();await flush();
 assert.equal(unauth.reloads.length,0,'auth failure cannot reload-loop');
 assert.equal(unauth.messages.length,0);
 const offline=page({failed:true});offline.winEvents.pageshow();await flush();
 assert.equal(offline.reloads.length,0,'offline session preserves current UI');
 const malformed=page({sha:'bad'});malformed.winEvents.pageshow();await flush();
 assert.equal(malformed.reloads.length,0,'invalid revision cannot trigger reload');
 assert.ok(!source.includes('localStorage.setItem('),'release check must never change drafts');
 assert.ok(!source.includes('innerHTML'),'release notice must not render untrusted HTML');
 console.log('Owner iPhone update on resume: 9 DOM, no-data-loss and auth checks passed');
})().catch(e=>{console.error(e);process.exitCode=1});
