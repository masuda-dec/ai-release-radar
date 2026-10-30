(() => {
  'use strict';
  const data = window.RADAR_DATA || {items:[],checks:[],generatedAt:null,failures:[]};
  const items = Array.isArray(data.items) ? data.items : [];
  const states = getStorage('airadar:v1', {read:[],saved:[]});
  states.read = Array.isArray(states.read) ? states.read : [];
  states.saved = Array.isArray(states.saved) ? states.saved : [];
  let view = 'feed';
  let category = 'all';
  let toastTimer = null;
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const link = url => /^https:\/\//i.test(String(url || '')) ? String(url) : '#';
  const dateJP = s => {
    const d = new Date(String(s).includes('T') ? s : `${s}T12:00:00+09:00`);
    return Number.isNaN(d.getTime()) ? s : new Intl.DateTimeFormat('ja-JP',{timeZone:'Asia/Tokyo',month:'short',day:'numeric',year:'numeric'}).format(d);
  };
  const scoreClass = n => n >= 4 ? '' : n === 3 ? 'score-mid' : 'score-low';
  const isRead = id => states.read.includes(id);
  const isSaved = id => states.saved.includes(id);
  const scoreDots = n => Array.from({length:5},(_,i)=>`<i class="${i<n?'on':''}"></i>`).join('');
  function getStorage(key, fallback) { try { return JSON.parse(localStorage.getItem(key)) || fallback; } catch { return fallback; } }
  function persist() { try { localStorage.setItem('airadar:v1', JSON.stringify(states)); } catch {} }
  function toast(message) { const node=$('toast');node.textContent=message;node.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>node.classList.remove('show'),2600); }
  function toggleState(id, key) { const x=states[key].indexOf(id); x<0?states[key].push(id):states[key].splice(x,1);persist();render(); }
  const cut = (text, limit) => String(text||'').length>limit ? String(text).slice(0,limit-1)+'…':String(text||'');
  const sorted = list => [...list].sort((a,b) => b.score-a.score || b.date.localeCompare(a.date));

  function renderPriority() {
    const top=sorted(items.filter(i=>i.status==='公式確認済み' && i.score>=4)).slice(0,3);
    $('priorityCards').innerHTML = top.map((i,n)=>`<article class="priority-card"><span class="priority-num">0${n+1} / RECOMMENDED</span><h3>${esc(i.title)}</h3><p>${esc(cut(i.why,112))}</p><div class="priority-footer"><span class="pill">有用度 ${Number(i.score)||0} / 5</span><a href="${esc(link(i.sourceUrl))}" target="_blank" rel="noopener noreferrer">公式情報 ↗</a></div></article>`).join('') || '<p class="section-sub">新しい重要項目はありません。</p>';
  }
  function filtered() {
    const q=$('searchInput').value.trim().toLocaleLowerCase();
    const days=$('periodSelect').value;
    const minHigh=$('onlyHigh').checked;
    // News lookback is relative to the newest fetched date, so archived snapshots still work.
    const maxDate=items.reduce((m,i)=>i.date>m?i.date:m,'1970-01-01');
    const since=new Date(`${maxDate}T12:00:00+09:00`);
    if(days!=='all') since.setUTCDate(since.getUTCDate()-Number(days));
    const minDate=since.toISOString().slice(0,10);
    const list=items.filter(i=>{
      if(view==='saved'&&!isSaved(i.id)) return false;
      if(category!=='all'&&i.category!==category)return false;
      if(minHigh&&i.score<4)return false;
      if(days!=='all'&&i.date<minDate)return false;
      return !q || [i.title,i.summary,i.why,i.try,i.product,...(i.tags||[])].join(' ').toLocaleLowerCase().includes(q);
    });
    const mode=$('sortSelect').value;
    list.sort((a,b)=>mode==='score'?(b.score-a.score||b.date.localeCompare(a.date)):(b.date.localeCompare(a.date)||b.score-a.score));
    return list;
  }
  function renderFeed() {
    const list=filtered();
    $('resultsLabel').textContent=`${list.length} 件`;
    $('emptyState').hidden=list.length>0;
    $('feedCards').innerHTML=list.map(i=>{
      const st=i.status==='要確認'?'notice':i.reviewed?'reviewed':'machine';
      const stLabel=i.status==='要確認'?'! 更新検知・要確認':i.reviewed?'✓ 公式確認済み':'● 自動取得・機械評価';
      return `<article class="release-card ${isRead(i.id)?'':'unread'}" data-item="${esc(i.id)}"><div class="card-head"><div><div class="card-meta"><span>${esc(dateJP(i.date))}</span><span class="category">${esc(i.category)}</span><span>${esc(i.product)}</span><span class="${st}">${stLabel}</span>${i.channel==='preview'?'<span class="notice">PREVIEW</span>':''}</div><h3>${esc(i.title)}</h3><p class="summary">${esc(i.summary)}</p></div><div class="score-wrap ${scoreClass(i.score)}"><small>あなたへの有用度</small><div class="score">${Number(i.score)||0}<span>/ 5</span></div><div class="score-dots">${scoreDots(i.score)}</div></div></div>
      <div class="details"><div class="detail"><div class="detail-label">✳ なぜあなたに役立つ？</div><p>${esc(i.why)}</p></div><div class="detail"><div class="detail-label">↗ 具体的にどう使う？</div><p>${esc(i.try)}</p></div></div><p class="availability"><strong>利用条件：</strong> ${esc(i.availability)}</p>
      <div class="card-bottom"><a class="source-link" href="${esc(link(i.sourceUrl))}" target="_blank" rel="noopener noreferrer">公式ソースを確認 ↗</a><button class="mini-btn ${isSaved(i.id)?'active':''}" data-action="save" data-id="${esc(i.id)}">${isSaved(i.id)?'★ 保存済み':'☆ 保存'}</button><button class="mini-btn ${isRead(i.id)?'active':''}" data-action="read" data-id="${esc(i.id)}">${isRead(i.id)?'✓ 既読':'○ 既読にする'}</button><div class="taglist">${(i.tags||[]).slice(0,4).map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div></div></article>`;
    }).join('');
  }
  function renderSources() {
    $('sourceList').innerHTML=(data.checks||[]).map(s=>`<div class="source-row"><div class="source-row-head"><strong>${esc(s.name)}</strong><span class="source-status ${s.automatic?'':'off'}">${s.automatic?'● 収集対象':'! 未監視'}</span></div><p>${esc(s.method)}</p>${s.url?`<a href="${esc(link(s.url))}" target="_blank" rel="noopener noreferrer">公式情報を見る ↗</a>`:''}</div>`).join('');
    if((data.failures||[]).length) $('sourceList').insertAdjacentHTML('afterbegin', `<div class="source-row" style="border-color:#b67d54"><strong>一部の取得に失敗しました</strong><p>${(data.failures||[]).map(f=>esc(`${f.source}: ${f.message}`)).join(' / ')}</p></div>`);
  }
  function renderNav() {
    document.querySelectorAll('[data-nav]').forEach(b=>b.classList.toggle('active',b.dataset.nav===view));
    $('feedSection').hidden=view==='sources';$('sourcesSection').hidden=view!=='sources';
    $('priorityPanel').hidden=view!=='feed';$('hero').hidden=view==='sources';
    $('savedCount').textContent=states.saved.length;$('navCount').textContent=items.length;
  }
  function renderStats() {
    $('totalStat').textContent=items.length;
    $('priorityStat').textContent=items.filter(i=>i.score===5).length;
    $('unreadStat').textContent=items.filter(i=>!isRead(i.id)).length;
    $('sourceStat').textContent=(data.checks||[]).filter(s=>s.automatic).length;
  }
  function render() {renderNav();renderStats();renderPriority();renderFeed();renderSources();}
  document.addEventListener('click',e=>{
    const nav=e.target.closest('[data-nav]');
    if(nav){view=nav.dataset.nav;render();window.scrollTo({top:0,behavior:'smooth'});return;}
    const action=e.target.closest('[data-action]');
    if(action){toggleState(action.dataset.id,action.dataset.action==='save'?'saved':'read');return;}
    const c=e.target.closest('[data-category]');
    if(c){category=c.dataset.category;document.querySelectorAll('[data-category]').forEach(b=>b.classList.toggle('active',b.dataset.category===category));renderFeed();}
  });
  ['searchInput','sortSelect','periodSelect','onlyHigh'].forEach(id=>$(id).addEventListener(id==='searchInput'?'input':'change',renderFeed));
  $('copyBtn').addEventListener('click',async()=>{
    const text='AI Release Radar の優先更新\n'+sorted(items.filter(i=>i.score>=4)).slice(0,5).map(i=>`${i.date}｜${i.title}（${i.score}/5）\n使い道: ${i.try}\n${i.sourceUrl}`).join('\n\n');
    try{await navigator.clipboard.writeText(text);toast('重要項目をコピーしました');}
    catch{const temp=document.createElement('textarea');temp.value=text;document.body.appendChild(temp);temp.select();const ok=document.execCommand('copy');temp.remove();toast(ok?'重要項目をコピーしました':'コピーできませんでした');}
  });
  $('syncLabel').textContent=data.generatedAt?`データ更新：${dateJP(data.generatedAt)} JST`:'未取得';
  $('lastFooter').textContent=data.note?` ${data.note}`:'';
  render();
})();
