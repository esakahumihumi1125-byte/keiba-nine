/* KEIBA NINE generic CSV -> offline racecard adapter.
   This is NOT a JRDB/JRA parser. Users must verify source licensing themselves.
   No network, storage, grades inferred, or public data publication. */
(function(root){
'use strict';
const required=['date','track','race','number','name','scratched'];
const axes=['recent','training','course','pedigree','pace'];
const maxChars=2000000,maxRows=2160;
function parseCSV(csv){
 if(typeof csv!=='string'||!csv.trim()||csv.length>maxChars)throw Error('CSVは2MB以内の文字列で指定してください');
 const text=csv.replace(/^\uFEFF/,'');
 const rows=[];let row=[],cell='',quoted=false,afterQuote=false;
 const push=()=>{row.push(cell);rows.push(row);row=[];cell='';afterQuote=false};
 for(let i=0;i<text.length;i++){
  const ch=text[i];
  if(quoted){
   if(ch==='"'){
    if(text[i+1]==='"'){cell+='"';i++}else{quoted=false;afterQuote=true}
   }else cell+=ch;
   continue;
  }
  if(ch==='"'&&!cell&&!afterQuote){quoted=true;continue}
  if(ch==='"')throw Error('CSVの引用符が不正です（'+(rows.length+1)+'行目）');
  if(afterQuote&&ch!==','&&ch!=='\n'&&ch!=='\r')throw Error('CSVの引用符の後に余分な文字があります');
  if(ch===','){row.push(cell);cell='';afterQuote=false}
  else if(ch==='\r'||ch==='\n'){
   push();
   if(ch==='\r'&&text[i+1]==='\n')i++;
   if(rows.length>maxRows+2)throw Error('CSVの行数は2160行までです');
  }else cell+=ch;
 }
 if(quoted)throw Error('CSVの引用符が閉じられていません');
 if(cell!==''||row.length||afterQuote)push();
 const filtered=rows.filter(r=>r.some(v=>v.trim()!==''));
 if(filtered.length<2)throw Error('見出し行とデータ行が必要です');
 return filtered;
}
function convertCSV(csv,{source,licenseConfirmed}={}){
 if(typeof source!=='string'||!source.trim()||source.trim().length>120||licenseConfirmed!==true)
  throw Error('提供元sourceと利用許諾の確認が必要です');
 const rows=parseCSV(csv);
 const header=rows.shift().map(s=>s.trim().toLowerCase());
 if(new Set(header).size!==header.length)throw Error('CSVの列名に重複があります');
 for(const col of required)if(!header.includes(col))throw Error('必須列が不足しています：'+col);
 const known=[...required,...axes.flatMap(a=>[a+'_grade',a+'_note'])];
 for(const col of header)if(!known.includes(col))throw Error('未対応のCSV列名です：'+col);
 if(rows.length>maxRows)throw Error('最大2160頭分までです');
 const lookup=new Map(header.map((h,i)=>[h,i]));
 const get=(r,k)=>r[lookup.get(k)]??'';
 const cards=new Map();
 for(let i=0;i<rows.length;i++){
  const r=rows[i];
  if(r.length!==header.length)throw Error((i+2)+'行目の列数が一致しません');
  const date=get(r,'date').trim(),track=get(r,'track').trim();
  const raceString=get(r,'race').trim(),numberString=get(r,'number').trim();
  if(!/^\d{1,2}$/.test(raceString)||!/^\d{1,2}$/.test(numberString))throw Error((i+2)+'行目のR・馬番が不正です');
  const race=Number(raceString),number=Number(numberString);
  const name=get(r,'name').trim(),status=get(r,'scratched').trim().toLowerCase();
  const flags={'true':true,'false':false,'1':true,'0':false,'取消':true,'出走':false};
  if(!Object.hasOwn(flags,status))throw Error((i+2)+'行目はscratchedにtrue/false（または1/0・出走/取消）が必要です');
  const evaluations={};
  for(const axis of axes){
   const grade=get(r,axis+'_grade').trim().toUpperCase(),note=get(r,axis+'_note').trim();
   if(grade||note){
    if(!grade||!note)throw Error((i+2)+'行目 '+axis+' は評価と根拠を両方入力してください');
    evaluations[axis]={grade,note};
   }
  }
  const key=[date,track,race].join('|');
  if(!cards.has(key))cards.set(key,{date,track,race,horses:[]});
  cards.get(key).horses.push({number,name,scratched:flags[status],...(Object.keys(evaluations).length?{evaluations}:{})});
  if(cards.size>120)throw Error('対象レースは最大120Rまでです');
 }
 const output={kind:'keiba-nine-racecards',schema:1,source:source.trim(),licenseConfirmed:true,racecards:[...cards.values()]};
 if(!root.KeibaNineBatch)throw Error('一括検証エンジンがありません');
 return root.KeibaNineBatch.validateBundle(output);
}
root.KeibaNineCSV={parseCSV,convertCSV,required:[...required],axes:[...axes]};
})(window);
