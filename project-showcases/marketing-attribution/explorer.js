/* Local display of saved analysis results. No network requests or model fitting. */
(() => {
  'use strict';
  const el = id => document.getElementById(id);
  const data = JSON.parse(el('case-data').textContent);
  const pct = value => `${(100 * value).toFixed(1)}%`;
  const number = value => value.toLocaleString('en-US');
  function node(tag, text, className) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (className) element.className = className;
    return element;
  }
  const descriptions = {
    'First touch': 'All credit goes to the first recorded event. It may not be the true acquisition touch.',
    'Last touch': "All credit goes to the final event's channel. These are recorded events, not click records.",
    'Linear': 'Each recorded event receives the same credit. Repeated channel appearances receive repeated shares.',
    'Position based': 'The first and final events receive 40% each; the middle events share 20%. One- and two-event paths use special cases.',
    'Time decay': 'Credit halves for every seven days farther from conversion, then the weights are normalized within this path.'
  };
  for (const path of data.examples) {
    const option = node('option', `${path.id}: ${path.channels.length} events`);
    option.value = path.id;
    el('path-picker').append(option);
  }
  function renderPath() {
    const path = data.examples.find(p => p.id === el('path-picker').value);
    const model = el('path-model').value;
    const events = path.channels.map((channel, i) => {
      const li = node('li');
      const label = node('span', channel);
      const time = new Date(path.times[i]).toLocaleDateString('en-GB', {day:'numeric', month:'short',timeZone:'UTC'});
      li.append(label,node('small',`${time} · ${i === path.channels.length - 1 ? 'Conversion' : 'Impression'}`));
      return li;
    });
    el('event-path').replaceChildren(...events);
    const credit = new Map();
    path.channels.forEach((channel, i) => credit.set(channel, (credit.get(channel) || 0) + path.weights[model][i]));
    const rows = [...credit].sort((a,b) => b[1]-a[1]).map(([channel,share]) => {
      const row = node('div',undefined,'allocation-row');
      row.append(node('span',channel),node('strong',pct(share)));
      return row;
    });
    el('path-allocation').replaceChildren(...rows);
    el('path-source').textContent = `${path.id}. Source CSV rows ${path.source_rows.join(', ')}. UTC dates.`;
    el('path-description').textContent = descriptions[model];
  }
  for (const spec of data.specifications) {
    const option = node('option',spec.scenario);
    option.value = spec.scenario;
    el('aggregate-spec').append(option);
  }
  function renderAggregate() {
    const scenario = el('aggregate-spec').value;
    const model = el('aggregate-model').value;
    const specification = data.specifications.find(s => s.scenario === scenario);
    const selected = data.comparison.filter(r => r.scenario === scenario && r.model === model).sort((a,b) => a.rank-b.rank);
    const baseline = data.comparison.filter(r => r.scenario === scenario && r.model === 'Last touch');
    el('credit-title').textContent = `${model} versus last touch`;
    el('credit-base').textContent = `${number(specification.eligible_conversions)} eligible conversions · ${number(specification.journeys)} paths · ${scenario.toLowerCase()}`;
    const rows = selected.map(r => {
      const last = baseline.find(b => b.channel === r.channel);
      const row = node('div',undefined,'credit-row');
      const label = node('div',undefined,'credit-label');
      label.append(node('span',r.channel),node('span',`${pct(r.share)} | last ${pct(last.share)}`));
      const line = node('div',undefined,'credit-line');
      line.setAttribute('aria-hidden','true');
      const bar=node('i'), dot=node('b');
      bar.style.width=`${r.share/.4*100}%`;
      dot.style.left=`${last.share/.4*100}%`;
      line.append(bar,dot);row.append(label,line);
      return row;
    });
    el('credit-rows').replaceChildren(...rows);
    let message = model === 'Markov'
      ? 'Markov shares are normalized removal scores. They allocate observed credit; they are not incremental conversion estimates.'
      : descriptions[model];
    if (specification.unassigned_conversions) message += ` ${number(specification.unassigned_conversions)} conversions with no earlier recorded impression are unassigned; this is a different eligible population.`;
    if (scenario === 'First seen July 8 onward') message += ' This cohort has a different population and follow-up duration.';
    if (scenario === '30-day lookback') message += ' The extract spans only July, so 30 days equals the full observed path.';
    el('credit-message').textContent = message;
  }
  function renderClock() {
    const scenario = el('window-picker').value;
    const rows = data.comparison.filter(r => r.scenario === scenario && r.model === 'Markov');
    const insta=rows.find(r => r.channel === 'Instagram'),video=rows.find(r => r.channel === 'Online Video');
    const children=[insta,video].map(r => {
      const div=node('div');div.append(node('span',r.channel),node('strong',pct(r.share)));return div;
    });
    const leader = insta.share > video.share ? 'Instagram' : 'Online Video';
    const note = `${scenario}: ${leader} ranks third. Both shares use all ${number(insta.eligible_conversions)} conversions.`;
    children.push(node('p',note+(scenario === '30-day lookback' ? ' Thirty days covers the entire source extract.' : '')));
    el('clock-result').replaceChildren(...children);
  }
  el('path-picker').addEventListener('change',renderPath);
  el('path-model').addEventListener('change',renderPath);
  el('aggregate-model').addEventListener('change',renderAggregate);
  el('aggregate-spec').addEventListener('change',renderAggregate);
  el('window-picker').addEventListener('change',renderClock);
  renderPath();renderAggregate();renderClock();
  el('path-controls').hidden=false;
  el('aggregate-controls').hidden=false;
  el('window-control').hidden=false;
  const theme = el('theme-toggle');
  function setTheme(dark) {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    theme.textContent = dark ? 'Light view' : 'Dark view';
    theme.setAttribute('aria-label',dark ? 'Switch to light appearance' : 'Switch to dark appearance');
  }
  theme.addEventListener('click',() => setTheme(document.documentElement.dataset.theme !== 'dark'));
  setTheme(window.matchMedia('(prefers-color-scheme: dark)').matches);
  theme.hidden=false;
  const links=[...document.querySelectorAll('.contents a')];
  const observer=new IntersectionObserver(entries => {
    const visible=entries.filter(e => e.isIntersecting).sort((a,b) => a.boundingClientRect.top-b.boundingClientRect.top);
    if (!visible.length) return;
    for (const link of links) {
      if (link.hash === `#${visible[0].target.id}`) link.setAttribute('aria-current','location');
      else link.removeAttribute('aria-current');
    }
  },{rootMargin:'-100px 0px -50% 0px',threshold:0});
  document.querySelectorAll('.chapter').forEach(chapter => observer.observe(chapter));
})();
