export function wilson(k,n){
  if(!n)return [0,0];
  const z=1.959963984540054,p=k/n,d=1+z*z/n,c=(p+z*z/(2*n))/d,h=z*Math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;
  return [Math.max(0,c-h),Math.min(1,c+h)];
}
export function eligibleResponses(data,group,segment){
  return data.responses.filter(r=>r.text.trim()&&(group==='all'||r.reason==='Too expensive')&&(segment==='All'||r.schedule===segment));
}
export function summarize(data,rows,excluded=new Set()){
  return data.themes.map(theme=>{
    const count=rows.filter(r=>r.assignments.some(a=>a.theme_id===theme.id&&a.sentiment==='negative'&&!excluded.has(r.response_id+':'+a.theme_id))).length;
    const [lower,upper]=wilson(count,rows.length);
    return {...theme,count,n:rows.length,share:rows.length?count/rows.length:0,lower,upper};
  }).sort((a,b)=>b.count-a.count||a.id.localeCompare(b.id));
}
const patterns={affordability:/\b(budget|afford|expensive|price)\b/i,value:/\b(worth|value|waste)\b/i,delivery_flexibility:/\b(switch|slot|rota|schedule|thursday|evening)\b/i,pause_control:/\b(skip|pause|restart|away)\b/i,delivery_reliability:/\b(late|promised|reliable|never came)\b/i,billing_clarity:/\b(charge|fee|invoice|checkout)\b/i,food_quality:/\b(taste|tasted|fresh|soggy|bland|dry|quality)\b/i,portion_size:/\b(portions|small|serving|amount of food)\b/i,support:/\b(support|help|replied|reply)\b/i,packaging:/\b(lid|plastic|trays|container|packaging|wrapping)\b/i};
export function keywordMatches(text){return Object.entries(patterns).filter(([,pattern])=>pattern.test(text)).map(([id])=>id);}

if(typeof document!=='undefined'){
  const data=JSON.parse(document.getElementById('case-data').textContent);
  const el=id=>document.getElementById(id);
  const make=(tag,text,className)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(className)node.className=className;return node;};
  const labels=Object.fromEntries(data.themes.map(t=>[t.id,t]));
  const excluded=new Set();
  let rows=[],selected='R005';
  const pct=n=>(n*100).toFixed(1)+'%';
  function showQuote(response,assignment){
    const target=el('source-text');target.replaceChildren();
    if(!assignment){target.textContent=response.text;return;}
    const start=response.text.indexOf(assignment.evidence_quote);
    if(start<0){target.textContent=response.text;return;}
    target.append(document.createTextNode(response.text.slice(0,start)),make('mark',assignment.evidence_quote),document.createTextNode(response.text.slice(start+assignment.evidence_quote.length)));
    el('theme-definition').textContent=labels[assignment.theme_id].definition;
    el('quote-help').textContent='Highlighted: '+labels[assignment.theme_id].label+' · '+assignment.sentiment+' mention.';
  }
  function renderResponse(){
    const response=rows.find(r=>r.response_id===selected);
    el('theme-controls').replaceChildren();el('theme-definition').textContent='';
    if(!response){el('source-text').textContent='No written responses in this selection.';el('response-meta').textContent='Empty selection';return;}
    el('response-meta').textContent=response.response_id+' · '+response.schedule+' · '+response.reason;
    el('quote-help').textContent='Select a theme to highlight its source passage.';
    showQuote(response,null);
    for(const assignment of response.assignments){
      const row=make('div',undefined,'theme-row');
      const button=make('button',labels[assignment.theme_id].label,'theme-inspect');button.type='button';button.addEventListener('click',()=>showQuote(response,assignment));row.append(button);
      if(assignment.sentiment==='negative'){
        const label=make('label',undefined,'theme-include');const input=make('input');input.type='checkbox';input.checked=!excluded.has(response.response_id+':'+assignment.theme_id);
        input.setAttribute('aria-label','Include '+labels[assignment.theme_id].label+' from '+response.response_id+' in the count');
        input.addEventListener('change',()=>{const key=response.response_id+':'+assignment.theme_id;if(input.checked)excluded.delete(key);else excluded.add(key);renderChart();});
        label.append(input,document.createTextNode('Include this issue in the count'));row.append(label);
        const aggregate=summarize(data,rows,excluded).find(s=>s.id===assignment.theme_id);
        const countLabel=make('p','In this selection: '+aggregate.count+' of '+aggregate.n+' responses.','small theme-count');countLabel.dataset.theme=assignment.theme_id;row.append(countLabel);
      }else{row.append(make('p','Positive mention · not counted as an issue','positive-tag'));}
      el('theme-controls').append(row);
    }
  }
  function renderChart(){
    const summary=summarize(data,rows,excluded),group=el('answer-group').value,segment=el('segment').value;
    el('chart-title').textContent=group==='price'?'Issues inside “Too expensive”':'Issues across written feedback';
    el('chart-subtitle').textContent=rows.length+' written responses · '+(segment==='All'?'all schedules':segment.toLowerCase())+' · negative mentions';
    el('chart-rows').replaceChildren();el('chart-table').replaceChildren();
    for(const s of summary){
      const row=make('div',undefined,'bar-row'),label=make('div',undefined,'bar-label');
      label.append(make('span',s.label),make('span',s.count+'/'+s.n+' · '+pct(s.share)));
      const track=make('div',undefined,'bar-track');track.setAttribute('aria-hidden','true');const bar=make('i'),interval=make('b');bar.style.width=pct(s.share);interval.style.left=(s.lower*100)+'%';interval.style.width=((s.upper-s.lower)*100)+'%';track.append(bar,interval);row.append(label,track);el('chart-rows').append(row);
      const tr=make('tr'),th=make('th',s.label);th.scope='row';tr.append(th,...[s.count,s.n,pct(s.share),pct(s.lower)+'–'+pct(s.upper)].map(v=>make('td',String(v))));el('chart-table').append(tr);
    }
    el('table-caption').textContent='Negative themes in '+rows.length+' written responses, '+(group==='price'?'price-related':'all answer groups')+', '+segment.toLowerCase()+'.';
    el('edit-status').textContent=excluded.size?excluded.size+' coding decision'+(excluded.size===1?'':'s')+' excluded locally. Published findings above remain unchanged.':'Reference coding. Changes stay in this browser.';
    document.querySelectorAll('.theme-count').forEach(node=>{const s=summary.find(s=>s.id===node.dataset.theme);node.textContent='In this selection: '+s.count+' of '+s.n+' responses.';});
    el('reset').disabled=excluded.size===0;
  }
  function updateFilters(){
    rows=eligibleResponses(data,el('answer-group').value,el('segment').value);
    if(!rows.some(r=>r.response_id===selected))selected=rows[0]?.response_id||'';
    el('response-picker').replaceChildren(...rows.map(r=>{const option=make('option',r.response_id+' · '+r.text.slice(0,75)+(r.text.length>75?'…':''));option.value=r.response_id;return option;}));
    el('response-picker').value=selected;renderResponse();renderChart();
  }
  el('answer-group').addEventListener('change',updateFilters);el('segment').addEventListener('change',updateFilters);
  el('response-picker').addEventListener('change',()=>{selected=el('response-picker').value;renderResponse();});
  el('reset').addEventListener('click',()=>{excluded.clear();renderResponse();renderChart();});
  el('baseline-run').addEventListener('click',()=>{
    const text=el('baseline-text').value.trim(),matches=keywordMatches(text);el('baseline-result').replaceChildren();
    const title=!text?'No response to code.':matches.length?'Keyword matches: '+matches.map(id=>labels[id].label).join('; ')+'.':'No dictionary match. That does not mean there is no issue.';
    el('baseline-result').append(make('strong',title));
    const explanation=!text?'An empty response must stay unlabelled.':text==='I can afford it; I just do not think it is worth the price.'?'The affordability match misses the negation. This is why a keyword hit is only a candidate for review.':'These are literal pattern matches. Check the whole sentence, its sentiment and the codebook before accepting a theme.';
    el('baseline-result').append(make('p',explanation));
  });
  updateFilters();el('explorer-controls').hidden=false;el('edit-controls').hidden=false;el('baseline-run').hidden=false;
  if(window.matchMedia('(max-width:760px)').matches)document.querySelector('.contents details').open=false;
}
