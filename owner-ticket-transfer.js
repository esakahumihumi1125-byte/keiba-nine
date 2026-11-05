/* KEIBA NINE: explicit, no-save transfer of a manually reviewed 3連単 draft. */
(function(root, factory){
  'use strict';
  const api=factory();
  if(typeof module==='object' && module.exports)module.exports=api;
  if(root && root.document)api.install(root);
})(typeof window!=='undefined'?window:null,function(){
  'use strict';
  const TRACKS=new Set(['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉']);
  const DEST='https://keiba-nine-owner-preview.onrender.com/my-tickets';
  function validDate(s){
    if(typeof s!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(s))return false;
    const d=new Date(s+'T12:00:00Z');
    return Number.isFinite(d.valueOf())&&d.toISOString().slice(0,10)===s;
  }
  function numbers(s){
    if(typeof s!=='string'||!s.trim()||!/^[0-9,、，\s]+$/.test(s))throw Error('馬番は1〜18の数字で入力してな。');
    const raw=s.trim().split(/[,、，\s]+/).filter(Boolean);
    const nums=raw.map(n=>Number(n));
    if(!raw.length||raw.length>18||nums.some(n=>!Number.isInteger(n)||n<1||n>18)||new Set(nums).size!==nums.length)
      throw Error('馬番の重複や1〜18以外の番号を確認してな。');
    return nums;
  }
  function build(data){
    if(!data||data.recordType!=='live')throw Error('架空テストは送れません。実戦・個人検証を選んでな。');
    if(!data.useTri)throw Error('3連単の登録チェックを入れてな。');
    if(data.intent==='見送り')throw Error('見送りのレースは馬券下書きへ反映しません。');
    if(!validDate(data.date)||!TRACKS.has(data.track))throw Error('開催日・競馬場を確認してな。');
    const race=Number(data.race);
    if(!Number.isInteger(race)||race<1||race>12)throw Error('レースは1〜12Rを選んでな。');
    const first=numbers(data.first),second=numbers(data.second),third=numbers(data.third);
    const unique=new Set();
    for(const a of first)for(const b of second)for(const c of third)
      if(a!==b&&a!==c&&b!==c)unique.add(a+'-'+b+'-'+c);
    if(unique.size<1||unique.size>48)throw Error(unique.size+'点です。1〜48点になるよう候補を調整してな。');
    const fragment=new URLSearchParams({
      import:'v1',date:data.date,track:data.track,race:String(race),
      first:first.join(','),second:second.join(','),third:third.join(',')
    });
    // URL fragment is never sent to Render as an HTTP query or server log.
    return {url:DEST+'#'+fragment.toString(),points:unique.size,date:data.date,
            track:data.track,race};
  }
  function install(win){
    const doc=win.document,btn=doc.getElementById('ownerTicketTransfer'),
          note=doc.getElementById('ownerTicketTransferStatus');
    if(!btn||!note)return;
    btn.addEventListener('click',()=>{
      const val=id=>doc.getElementById(id)?.value||'';
      try{
        const draft=build({
          date:val('rpDate'),track:val('rpTrack'),race:val('rpRace'),
          first:val('rpFirst'),second:val('rpSecond'),third:val('rpThird'),
          recordType:val('rpRecordType'),intent:val('rpIntent'),
          useTri:!!doc.getElementById('rpUseTri')?.checked
        });
        if(!win.confirm(draft.date+' '+draft.track+draft.race+'Rの3連単 '+
          draft.points+'点を本人用の下書き画面に反映する？\\n保存・購入はされません。'))return;
        note.textContent='本人用へ移動します。引き継ぎ後に内容を確認して保存してな。';
        win.location.assign(draft.url);
      }catch(err){
        note.textContent=err instanceof Error?err.message:'3連単の入力を確認してな。';
      }
    });
  }
  return {build,numbers,install};
});
