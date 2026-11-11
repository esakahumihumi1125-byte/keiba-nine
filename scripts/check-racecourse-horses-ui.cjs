// Verify the actual embedded browser logic, using no provider, network or UI runtime.
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('keiba-nine-beta51-feed-record.html','utf8');
const marker='<!-- RACECOURSE58_MINI_HORSES_START:';
const scene=html.split(marker)[1]?.split('<!-- RACECOURSE58_MINI_HORSES_END -->')[0];
assert(scene,'racetrack horses script must exist');
const src=scene.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert(src,'embedded horse animation JavaScript must exist');
new vm.Script(src,{filename:'home-horse-animation-inline.js'}); // syntax check
let banner,field,svg,horseArc,homeActive=true,mediaChange,mutationChange;
let pauseCount=0,resumeCount=0;
class FakeNode {
  constructor(name){this.name=name;this.attrs={};this.children=[];this.parent=null;this.textContent='';}
  setAttribute(k,v){this.attrs[k]=String(v);}
  getAttribute(k){return this.attrs[k]||null;}
  removeAttribute(k){delete this.attrs[k];}
  append(...nodes){for(const node of nodes){node.parent=this;this.children.push(node)}}
  get firstChild(){return this.children[0]||null;}
  insertBefore(node,other){
    const idx=this.children.indexOf(other);node.parent=this;
    this.children.splice(idx<0?this.children.length:idx,0,node);
  }
  querySelector(name){return this.children.find(n=>n.name===name)||null}
  remove(){if(!this.parent)return;const p=this.parent.children,i=p.indexOf(this);
    if(i>=0)p.splice(i,1);this.parent=null}
}
const motionStatus={matches:false,addEventListener:(event,callback)=>{
  assert.equal(event,'change');mediaChange=callback;
}};
const home={classList:{contains:()=>homeActive},prepend:(node)=>{banner=node},
  get className(){return 'active'}};
const doc={
 hidden:false,
 getElementById:(id)=>id==='home'?home:null,
 createElement:(tag)=>{
  assert.equal(tag,'div');
  const el=new FakeNode(tag);
  Object.defineProperty(el,'innerHTML',{set(markup){
   assert(markup.includes('id="kn-thoroughbred"'));
   assert(markup.includes('id="kn-racecourse-arc"'));
   assert(markup.includes('class="kn-far-side-fence"'));
   const d=markup.match(/id="kn-racecourse-arc" d="([^"]+)"/)?.[1];
   assert(d && d.split(' C ').length>=3,'motion path must form an arc');
   field=new FakeNode('g');
   horseArc={
    getAttribute:(key)=>key==='d'?d:null,getTotalLength:()=>1600,
    getPointAtLength:(n)=>({x:-180+n,y:360-Math.sin(n/1600*Math.PI)*45}),
   };
   svg={
    querySelector:(q)=>q==='#kn-racecourse-horse-field'?field:
      q==='#kn-racecourse-arc'?horseArc:null,
    pauseAnimations:()=>{pauseCount++},unpauseAnimations:()=>{resumeCount++},
   };
  }});
  el.querySelector=(q)=>q==='svg'?svg:null;
  return el;
 },
 createElementNS:(ns,tag)=>{
  assert.equal(ns,'http://www.w3.org/2000/svg');
  return new FakeNode(tag);
 },
 addEventListener:(kind,cb)=>{if(kind==='visibilitychange')doc.visibilityChange=cb},
};
const win={
 matchMedia:(query)=>{
  assert.equal(query,'(prefers-reduced-motion: reduce)');return motionStatus},
 addEventListener:(event,callback)=>{if(event==='pageshow')win.pageshow=callback}
};
class FakeObserver{
 constructor(cb){mutationChange=cb}
 observe(target,opts){
  assert.equal(target,home);
  assert.deepEqual([...opts.attributeFilter],['class']);
 }
}
vm.runInNewContext(src,{
 document:doc,window:win,MutationObserver:FakeObserver,
 fetch:()=>{throw Error('background must not request external data')},
 localStorage:{getItem:()=>{throw Error('must not read records')}},
 sessionStorage:{setItem:()=>{throw Error('must not write records')}},
});
assert(banner,'banner should prepend to home');
assert.equal(field.children.length,18);
const horses=field.children;
for(let i=0;i<18;i++){
 const horse=horses[i];
 assert.equal(horse.getAttribute('data-horse'),String(i+1));
 const motion=horse.querySelector('animateMotion');
 assert(motion,'every horse follows the turf track');
 assert.equal(motion.getAttribute('path'),horseArc.getAttribute('d'));
 assert.equal(motion.getAttribute('dur'),'28s');
 assert.equal(motion.getAttribute('rotate'),'auto');
 assert.equal(motion.getAttribute('repeatCount'),'indefinite');
 const bob=horse.children.find(x=>x.name==='g');
 const shape=bob.children[0];
 assert.equal(shape.getAttribute('transform'),'scale(.66)');
 assert.equal(shape.children[0].getAttribute('href'),'#kn-thoroughbred');
 assert.equal(shape.children[1].textContent,String(i+1));
}
assert(resumeCount>0,'home should play the motion when visible');
homeActive=false;mutationChange();assert(pauseCount>0,'other tabs must pause animation');
homeActive=true;mutationChange();assert(resumeCount>1,'home tab must resume');
doc.hidden=true;doc.visibilityChange();assert(pauseCount>1,'hidden PWA must pause');
doc.hidden=false;doc.visibilityChange();
motionStatus.matches=true;mediaChange();
for(const horse of horses){
 assert.equal(horse.querySelector('animateMotion'),null);
 assert(horse.getAttribute('transform')?.startsWith('translate('));
}
motionStatus.matches=false;mediaChange();
for(const horse of horses)assert(horse.querySelector('animateMotion'));
console.log('18 curved horse motions, saddlecloths, tab pause and reduced-motion smoke passed');
