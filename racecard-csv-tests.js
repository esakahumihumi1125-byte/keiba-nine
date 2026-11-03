/* Generic CSV ingestion regressions; all examples are invented. */
(function(root){
'use strict';
const axes=['recent','training','course','pedigree','pace'];
const header=['date','track','race','number','name','scratched',
 ...axes.flatMap(a=>[a+'_grade',a+'_note'])].join(',');
function csvCell(x){const s=String(x);return /[",\r\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s}
const g=[
 ['S','S','S','S','S'],['S','S','S','S','A'],['S','S','S','A','B'],
 ['S','A','S','B','B'],['A','A','A','B','B'],['A','B','A','B','C'],['B','B','B','C','C']
];
const row=(i,track='京都',race=1,mode='full')=>[
 '2026-11-07',track,String(race),String(i+1),i===0?'架空の馬, 一号':'架空の馬'+i,
 'false',...axes.flatMap((a,j)=>mode==='blank'?['','']:[g[i][j],i===0&&j===0?'「根拠」\n時計, 練習':'架空のテスト根拠になる文字列'])
].map(csvCell).join(',');
const raw=header+'\r\n'+Array.from({length:7},(_,i)=>row(i)).join('\r\n')+'\r\n';
const opts={source:'許諾済みのテスト資料',licenseConfirmed:true};
function ok(x,name){if(!x)throw Error(name);checks++}
function reject(input,name,options=opts){let failed=false;try{root.KeibaNineCSV.convertCSV(input,options)}catch(_){failed=true}ok(failed,name)}
let checks=0;
const out=root.KeibaNineCSV.convertCSV('\uFEFF'+raw,opts);
ok(out.racecards.length===1&&out.racecards[0].horses.length===7,'BOM and seven horses');
ok(out.racecards[0].horses[0].name==='架空の馬, 一号','comma in quoted horse name');
ok(out.racecards[0].horses[0].evaluations.recent.note.includes('\n'),'quoted newline preserved');
ok(out.racecards[0].horses[0].evaluations.recent.note.includes('時計, 練習'),'quoted comma preserved');
ok(root.KeibaNineBatch.analyzeBundle(out).ready===1,'complete scoring ready');
const blank=header+'\n'+Array.from({length:7},(_,i)=>row(i,'京都',1,'blank')).join('\n');
const noGrades=root.KeibaNineCSV.convertCSV(blank,opts);
ok(root.KeibaNineBatch.analyzeBundle(noGrades).skipped===1,'no input grades -> skip');
const partial=raw.replace('架空のテスト根拠になる文字列','');
reject(partial,'grade without note rejected');
const multi=header+'\n'+Array.from({length:7},(_,i)=>row(i,'京都',1)).join('\n')+'\n'+Array.from({length:7},(_,i)=>row(i,'東京',2)).join('\n');
ok(root.KeibaNineCSV.convertCSV(multi,opts).racecards.length===2,'two races');
reject(raw,'license acknowledgement required',{source:'dummy',licenseConfirmed:false});
reject(raw,'provider name required',{source:'',licenseConfirmed:true});
reject(raw.replace('false,','unknown,'),'bad withdrawal status rejected');
reject(raw.replace(',1,1,',',1,19,'),'horse 19 rejected');
reject(raw.replace(',1,2,',',1,1,'),'duplicate horse number rejected');
reject(raw.replace('2026-11-07','2026-02-30'),'bad calendar date rejected');
reject(raw.replace('京都','未知の競馬場'),'unknown venue rejected');
reject(raw.replace(header,header+',recent_grade'),'duplicated header rejected');
reject(raw.replace(header,header+',unsupported'),'unknown header rejected');
reject(raw.replace('"架空の馬, 一号"','"架空の馬, 一号'),'unclosed quote rejected');
reject(raw.replace('"架空の馬, 一号"','"架空の馬, 一号"X'),'junk after quote rejected');
reject(raw.replace(',false,',',,'),'unknown scratched rejected');
reject(header+'\n','empty rows rejected');
reject(raw.replace('date,',''), 'missing required date header rejected');
const tooMany=header+'\n'+Array.from({length:121},(_,n)=>row(0,'京都',n%12+1).replace('2026-11-07','2026-11-'+String(7+Math.floor(n/12)).padStart(2,'0'))).join('\n');
reject(tooMany,'over 120 distinct races rejected');
ok(root.KeibaNineCSV.parseCSV('"a","b"\n"1","2"').length===2,'two quoted rows parsed');
const noNewline=header+'\n'+row(0,'京都',1,'blank');
ok(root.KeibaNineCSV.convertCSV(noNewline,opts).racecards.length===1,'last line without newline');
root.KeibaNineCSVTests={passed:checks};
})(window);
