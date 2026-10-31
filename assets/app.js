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
  function toggleState(id, key) { const x=states[key].indexOf(id); x<0?states[key].push(id):states[key].splice(x,1);persist();render(); const button=[...document.querySelectorAll('[data-action]')].find(b=>b.dataset.id===id&&b.dataset.action===(key==='saved'?'save':'read'));button?.focus(); }
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
      return !q || [i.title,i.summary,i.why,i.try,i.product,JSON.stringify(i.details||{}),...(i.tags||[])].join(' ').toLocaleLowerCase().includes(q);
    });
    const mode=$('sortSelect').value;
    list.sort((a,b)=>mode==='score'?(b.score-a.score||b.date.localeCompare(a.date)):(b.date.localeCompare(a.date)||b.score-a.score));
    return list;
  }
  const openDetails = new Set();
  const sourceLink = (url, label) => `<a href="${esc(link(url))}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`;
  function detailPanel(i, index) {
    const d=i.details||{}, c=d.community||{}, panelId=`release-detail-${index}`;
    const searches=(c.searches||[]).map(s=>{
      const status={found:'投稿候補あり',not_found:'確認できた事例なし',unavailable:'検索不可・未取得',not_searched:'未検索',not_applicable:'対象未特定'}[s.status]||s.status;
      return `<li>${esc(s.platform)}：${esc(status)}${s.reason?` — ${esc(s.reason)}`:''}</li>`;
    }).join('');
    const reports=(c.sources||[]).map(r=>`<li class="community-report"><div>${sourceLink(r.url,r.title)} <span class="evidence-kind">${esc(({user_report:'利用者の報告',developer_report:'開発者の検証',official_demo:'公式の実演'})[r.kind]||'未分類の投稿')}</span></div><small>投稿日：${esc(dateJP(r.publishedAt))} JST · ${esc(r.platform)}</small><p>${esc(r.summary)}</p><p class="small-muted">関連性・限界：${esc(r.relation||'未確認')}</p>${r.excerpt?`<details class="original"><summary>取得原文の抜粋</summary><p lang="en">${esc(r.excerpt)}</p></details>`:''}</li>`).join('');
    const section=(title,body)=>`<section class="detail-section"><h4>${title}</h4>${body}</section>`;
    return `<details class="release-details" data-detail-id="${esc(i.id)}" ${openDetails.has(i.id)?'open':''}>
      <summary aria-controls="${panelId}"><span>具体的な使い方・変更前後・活用事例</span><span class="expand-hint" aria-hidden="true">＋</span></summary>
      <div class="detail-content" id="${panelId}"><p class="evidence-note">${esc(d.basis||'既存の説明を表示しています。')} ${d.mode==='ai'?`（モデル：${esc(d.model)}）`:''}</p>
      ${section('何が変わった？ <span class="evidence-kind">公式資料に基づく解説</span>',`<p>${esc(d.change||i.summary)}</p><p class="evidence-source">出典：${sourceLink(i.sourceUrl,i.sourceName||'公式資料')} · 公開日：${esc(dateJP(i.sourcePublishedAt||i.date))} JST</p>${(d.officialSources||[]).map(r=>`<p class="evidence-source">${sourceLink(r.url,r.title)} · 公開日：${esc(dateJP(r.publishedAt))} JST</p>`).join('')}`)}
      ${section('変更前と後',`<div class="comparison"><div><span>変更前</span><p>${esc(d.before||'旧版の挙動は未確認です。')}</p></div><div><span>変更後</span><p>${esc(d.after||i.summary)}</p></div></div>`)}
      ${section('具体的にどう使う？ <span class="evidence-kind proposal">本人向けの提案・未実測</span>',`<p>${esc(d.workflow||i.try)}</p>`)}
      ${section('試す手順・コマンド',`<ol>${(d.steps||[i.try]).map(t=>`<li>${esc(t)}</li>`).join('')}</ol>${(d.commands||[]).map(cmd=>`<div class="command"><strong>${esc(cmd.label)}</strong><small>${esc(cmd.platform)}</small><pre><code>${esc(cmd.command)}</code></pre></div>`).join('')}`)}
      ${section('ユーザーへの効果 / 制約',`<p><strong>期待できる効果：</strong>${esc(d.benefit||i.why)}</p><p><strong>使える環境・プラン：</strong>${esc(d.environment||i.availability)}</p><p><strong>前提・注意点：</strong>${esc(d.limitations||'公式の提供条件を確認してください。')}</p>`)}
      ${section('Xやコミュニティの活用事例・反応',`<p class="evidence-note">個別の投稿は公式仕様や改善効果の証明ではありません。実際の環境・バージョン・投稿日を確認してください。</p>${reports?`<ul class="community-list">${reports}</ul>`:'<p>確認できた事例なし。</p>'}${c.checkedAt?`<p class="evidence-source">調査日：${esc(dateJP(c.checkedAt))} JST</p>`:'<p class="evidence-source">このリリースのコミュニティ検索は未実施です。未検索は「投稿が存在しない」という意味ではありません。</p>'}<ul class="search-status">${searches||'<li>X：未検索 / GitHub・Reddit・Hacker News：未検索</li>'}</ul>`)}
      </div></details>`;
  }
  document.addEventListener('toggle',e=>{
    if(!e.target.matches?.('.release-details'))return;
    const node=e.target, id=node.dataset.detailId;
    if(node.open)openDetails.add(id);else openDetails.delete(id);
    node.querySelector('summary')?.setAttribute('aria-expanded',String(node.open));
  },true);
  function renderFeed() {
    const list=filtered();
    $('resultsLabel').textContent=`${list.length} 件`;
    $('emptyState').hidden=list.length>0;
    $('feedCards').innerHTML=list.map((i,index)=>{
      const st=i.status==='要確認'?'notice':i.reviewed?'reviewed':'machine';
      const stLabel=i.status==='要確認'?'! 更新検知・要確認':i.reviewed?'✓ 公式確認済み':'● 自動取得・機械評価';
      return `<article class="release-card ${isRead(i.id)?'':'unread'}" data-item="${esc(i.id)}"><div class="card-head"><div><div class="card-meta"><span>${esc(dateJP(i.date))}</span><span class="category">${esc(i.category)}</span><span>${esc(i.product)}</span><span class="${st}">${stLabel}</span>${i.channel==='preview'?'<span class="notice">PREVIEW</span>':''}</div><h3>${esc(i.title)}</h3><p class="summary">${esc(cut(i.summary,130))}</p></div><div class="score-wrap ${scoreClass(i.score)}"><small>あなたへの有用度</small><div class="score">${Number(i.score)||0}<span>/ 5</span></div><div class="score-dots">${scoreDots(i.score)}</div></div></div>
      <p class="personal-benefit"><strong>あなたの作業では：</strong>${esc(cut(i.details?.benefit||i.why,100))}</p>${detailPanel(i,index)}
      <div class="card-bottom"><a class="source-link" href="${esc(link(i.sourceUrl))}" target="_blank" rel="noopener noreferrer">公式ソースを確認 ↗</a><button class="mini-btn ${isSaved(i.id)?'active':''}" aria-pressed="${isSaved(i.id)}" data-action="save" data-id="${esc(i.id)}">${isSaved(i.id)?'★ 保存済み':'☆ 保存'}</button><button class="mini-btn ${isRead(i.id)?'active':''}" aria-pressed="${isRead(i.id)}" data-action="read" data-id="${esc(i.id)}">${isRead(i.id)?'✓ 既読':'○ 既読にする'}</button><div class="taglist">${(i.tags||[]).slice(0,4).map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div></div></article>`;
    }).join('');
    document.querySelectorAll('.release-details').forEach(node=>node.querySelector('summary').setAttribute('aria-expanded',String(node.open)));
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
