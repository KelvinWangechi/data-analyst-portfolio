import assert from 'node:assert/strict';
import fs from 'node:fs';
import {eligibleResponses,summarize,keywordMatches,wilson} from './app.js';
const data=JSON.parse(fs.readFileSync(new URL('./results/explorer.json',import.meta.url)));
const rows=eligibleResponses(data,'price','All');
assert.equal(rows.length,152);
const base=summarize(data,rows);
for(const row of base)assert.equal(row.count,data.summary.price_issue_counts[row.id]);
const changed=summarize(data,rows,new Set(['R005:pause_control']));
assert.equal(changed.find(r=>r.id==='pause_control').count,17);
assert.equal(changed.find(r=>r.id==='value').count,44);
assert.equal(changed.find(r=>r.id==='pause_control').n,152);
assert.equal(summarize(data,rows).find(r=>r.id==='pause_control').count,18);
assert.equal(eligibleResponses(data,'all','All').length,280);
assert.deepEqual(wilson(0,0),[0,0]);
assert.equal(eligibleResponses(data,'price','No such group').length,0);
const rRows=fs.readFileSync(new URL('./results/theme-summary.csv',import.meta.url),'utf8').trim().split(/\r?\n/).slice(1).map(line=>line.replaceAll('"','').split(','));
for(const [segment,theme,count,n,share,lower,upper] of rRows){
  const computed=summarize(data,eligibleResponses(data,'price',segment)).find(r=>r.id===theme);
  assert.equal(computed.count,Number(count));assert.equal(computed.n,Number(n));
  for(const [actual,expected] of [[computed.share,share],[computed.lower,lower],[computed.upper,upper]])assert.ok(Math.abs(actual-Number(expected))<1e-10);
}
assert.deepEqual(keywordMatches(''),[]);
assert.ok(keywordMatches('I can afford it.').includes('affordability'));
console.log('Browser math matches R in every segment; exclusion, reset and empty states passed.');
