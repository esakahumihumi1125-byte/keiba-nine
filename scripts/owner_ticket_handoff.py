"""Client-only recipient for explicit 3連単 handoff. No API, secrets or automatic save."""

JS = r"""
(function(){
  'use strict';
  // URL fragments are not transmitted to Render. Remove immediately, whether
  // accepted or declined, so a later reload never silently repeats the import.
  if(typeof window==='undefined'||!window.location)return;
  const fragment=window.location.hash||'';
  if(!fragment.startsWith('#import=v1'))return;
  function clearFragment(){
    try{window.history.replaceState(null,'',window.location.pathname+window.location.search);}
    catch(_){}
  }
  try{
    if(fragment.length>450)throw Error('受け取りデータが長すぎます。');
    const p=new URLSearchParams(fragment.slice(1));
    const keys=['import','date','track','race','first','second','third'];
    if([...p.keys()].length!==keys.length||keys.some(k=>p.getAll(k).length!==1))
      throw Error('受け取り内容の形式が正しくありません。');
    if(p.get('import')!=='v1')throw Error('未対応の引き継ぎ形式です。');
    const date=p.get('date'),track=p.get('track'),race=Number(p.get('race'));
    if(!validDate(date)||!TRACKS.includes(track)||!Number.isInteger(race)||
       race<1||race>12)throw Error('開催日・競馬場・レースを確認してください。');
    function parseHorseList(value){
      if(!/^(?:[1-9]|1[0-8])(?:,(?:[1-9]|1[0-8]))*$/.test(value||''))
        throw Error('馬番は1〜18、カンマ区切りで確認してください。');
      const numbers=value.split(',').map(Number);
      if(!validNums(numbers)||numbers.length<1)throw Error('馬番が重複しています。');
      return numbers;
    }
    const incomingFirst=parseHorseList(p.get('first'));
    const incomingSecond=parseHorseList(p.get('second'));
    const incomingThird=parseHorseList(p.get('third'));
    const count=ticketsFor(incomingFirst,incomingSecond,incomingThird).length;
    if(!count||count>LIMIT)throw Error(count+'点です。1〜48点の買い目だけ受け取れます。');
    clearFragment();
    if(!window.confirm(date+' '+track+race+'R の3連単'+count+
       '点を未保存の下書きとして反映する？\\n既に作成中の候補は置き換えられます。購入・保存はしません。')){
      message('取り込みをキャンセルしました。保存済みの記録は変更していません。');
      return;
    }
    $('mDate').value=date;
    $('mTrack').value=track;
    $('mRace').value=String(race);
    first=new Set(incomingFirst);
    second=new Set(incomingSecond);
    third=new Set(incomingThird);
    render();
    showDay();
    message('予想から3連単 '+count+'点を反映したで。買い目を確認して「下書きを保存」を押してな。購入記録には追加されません。');
  }catch(error){
    clearFragment();
    message('予想を受け取れませんでした：'+(error instanceof Error?error.message:'入力を確認してください。'));
  }
})();
"""
