'use strict';
const $=id=>document.getElementById(id);const money=c=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(c/100);const pct=n=>(n*100).toFixed(1)+'%';const safe=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let baseline,jobs,costChanged=false;
const API='https://cleaning-intake-31-220-90-233.sslip.io';
const RECEIPT_STORAGE='cleaning-live-receipt-v1';
let receiptSession=null,submissionBody=null,busy=false;
function record(label,text){const el=document.createElement('div');el.className='record';el.innerHTML='<span>'+safe(label)+'</span><strong>'+safe(text)+'</strong>';$('record-trail').append(el);}
function message(text,error=false){$('workflow-status').textContent=text;$('workflow-status').classList.toggle('error',error);}
function remember(){try{localStorage.setItem(RECEIPT_STORAGE,JSON.stringify(receiptSession));}catch{/* Receipt still works for this tab when storage is unavailable. */}}
function newSession(){const bytes=crypto.getRandomValues(new Uint8Array(32));receiptSession={submission_id:crypto.randomUUID(),receipt_token:Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('')};remember();}
function buttons(items){$('action-buttons').replaceChildren();for(const [title,fn] of items){const b=document.createElement('button');b.className='secondary';b.textContent=title;b.disabled=busy;b.addEventListener('click',fn);$('action-buttons').append(b);}}
function refreshButtons(){buttons([['Refresh Salesforce receipt',checkReceipt],...(submissionBody?[['Replay same submission',()=>sendEnquiry(true)]]:[])]);}
function renderReceipt(data){
  $('intake').hidden=true;$('actions').hidden=false;$('record-trail').replaceChildren();
  $('action-title').textContent=data.status==='handoff_confirmed'?'Salesforce handoff confirmed':'Waiting for Salesforce confirmation';
  $('action-text').textContent='Reference: '+data.reference+'. Quote review and customer acceptance take place inside Salesforce. Refresh this receipt to check progress.';
  record('ENQUIRY REFERENCE',data.reference);
  record('SALESFORCE ENQUIRY',data.enquiry_confirmed?'Confirmed':'Awaiting confirmation');
  record('CRM CONTACT',data.contact_confirmed?'Linked contact confirmed':'Awaiting confirmation');
  record('ESTIMATOR TASK',data.estimator_task_confirmed?'Correct enquiry and contact links confirmed · '+data.task_status:'Awaiting confirmation');
  record('QUOTE REVIEW',data.quote_status||'Awaiting confirmation');
  record('CUSTOMER ACCEPTANCE',data.customer_accepted?'Recorded in Salesforce':'Not recorded');
  record('JOB',data.job_created?'Created in Salesforce · '+data.job_status:'No job created');
  if(data.checked_at)record('LAST VERIFIED',new Date(data.checked_at).toLocaleString('en-US',{timeZone:'America/Los_Angeles'})+' Pacific time'+' · Salesforce REST read-back');
  const step=data.job_created?3:(data.contact_confirmed&&data.estimator_task_confirmed?2:1);
  document.querySelectorAll('.steps li').forEach((el,i)=>el.classList.toggle('active',i===step));
  refreshButtons();
}
async function request(path,options={}){
  const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),45000);
  try{
    const response=await fetch(API+path,{...options,signal:controller.signal,cache:'no-store'});
    const data=await response.json();
    if(!response.ok)throw Error(data.error||'Salesforce could not confirm the request.');
    return data;
  }catch(error){if(error.name==='AbortError')throw Error('Confirmation took too long. Keep this reference and retry the same submission.');throw error;}
  finally{clearTimeout(timeout);}
}
async function sendEnquiry(replay=false){
  if(busy||!submissionBody)return;busy=true;$('intake').querySelector('button').disabled=true;refreshButtons();
  message(replay?'Replaying the same source reference in Salesforce…':'Sending your enquiry to Salesforce and checking the handoff…');
  try{const data=await request('/v1/enquiries',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(submissionBody)});renderReceipt(data);message(data.status==='handoff_confirmed'?(data.replayed?'Replay confirmed: the existing enquiry and handoff were reused.':'Salesforce confirmed the enquiry, linked contact and estimator task.'):'The enquiry is being checked. Refresh the receipt; no handoff success has been assumed.');}
  catch(error){message(error.message||'Connection unavailable. Retry the same submission.',true);}
  finally{busy=false;$('intake').querySelector('button').disabled=false;refreshButtons();}
}
async function checkReceipt(){
  if(busy||!receiptSession)return;busy=true;refreshButtons();message('Reading the current records from Salesforce…');
  try{const data=await request('/v1/receipts/'+receiptSession.submission_id,{headers:{Authorization:'Bearer '+receiptSession.receipt_token}});renderReceipt(data);message(data.status==='handoff_confirmed'?'Receipt refreshed from Salesforce.':'Salesforce confirmation is still pending.');}
  catch(error){message(error.message||'Could not refresh the receipt. Please retry.',true);}
  finally{busy=false;refreshButtons();}
}
$('intake').addEventListener('submit',e=>{
  e.preventDefault();if(busy)return;
  if(!submissionBody){const form=new FormData(e.currentTarget);if(!receiptSession)newSession();submissionBody={...receiptSession,customer:form.get('customer').trim(),email:form.get('email').trim(),address:form.get('address').trim(),service:form.get('service'),website:form.get('website')||''};for(const field of e.currentTarget.querySelectorAll('input,select'))field.disabled=true;e.currentTarget.querySelector('button').textContent='Retry same enquiry';}
  sendEnquiry();
});
$('reset-workflow').addEventListener('click',()=>{
  if(busy)return;receiptSession=null;submissionBody=null;try{localStorage.removeItem(RECEIPT_STORAGE);}catch{}
  $('intake').hidden=false;$('actions').hidden=true;$('intake').reset();for(const field of $('intake').querySelectorAll('input,select'))field.disabled=false;$('intake').querySelector('button').textContent='Send to Salesforce';
  $('intake').elements.email.value='alex+'+crypto.randomUUID().slice(0,8)+'@example.test';
  $('record-trail').innerHTML='<p class="empty">Submit an enquiry to see its Salesforce record, linked contact and estimator task.</p>';
  document.querySelectorAll('.steps li').forEach((el,i)=>el.classList.toggle('active',i===0));message('Ready for a new enquiry. Previous Salesforce records are kept.');
});
try{const saved=JSON.parse(localStorage.getItem(RECEIPT_STORAGE));if(saved&&/^[a-f0-9-]{36}$/.test(saved.submission_id)&&/^[a-f0-9]{64}$/.test(saved.receipt_token))receiptSession=saved;}catch{}
if(receiptSession){$('intake').hidden=true;$('actions').hidden=false;$('action-title').textContent='Your saved enquiry receipt';$('action-text').textContent='Check your previous submission directly in Salesforce, or start a new enquiry. Your private receipt key stays in this browser.';refreshButtons();}
else $('intake').elements.email.value='alex+'+crypto.randomUUID().slice(0,8)+'@example.test';

function selectedJobs(){return jobs.filter(j=>j.status==='Completed'&&($('period').value==='all'||j.completed_date===$('period').value));}
function metrics(list){const verified=list.filter(j=>j.verified),revenue=list.reduce((a,j)=>a+j.revenue_cents,0),vr=verified.reduce((a,j)=>a+j.revenue_cents,0),hours=verified.reduce((a,j)=>a+j.person_hours,0),cost=verified.reduce((a,j)=>a+j.direct_cost_cents,0);return {revenue,vr,hours,cost,verified:verified.length,count:list.length,margin:vr?(vr-cost)/vr:null,rpph:hours?vr/100/hours:null};}
function summaryText(){const m=metrics(selectedJobs()),period=$('period').value==='all'?'6–11 October 2026':$('period').selectedOptions[0].textContent;const ex=jobs.filter(j=>j.status==='Completed'&&!j.verified);return 'OWNER BRIEFING · '+period+'\nUSD'+(costChanged?' · browser what-if':' · reconciled snapshot')+'\n\n'+m.count+' completed jobs · '+money(m.revenue)+' revenue\n'+m.verified+'/'+m.count+' have verified costs\nDirect margin: '+(m.margin===null?'unavailable':pct(m.margin))+'\nRevenue/person-hour: '+(m.rpph===null?'unavailable':'$'+m.rpph.toFixed(2))+'\n\nEnquiry cohort · 5–7 October 2026\n15 won / 21 decided · '+pct(baseline.cohort.close_rate)+' close rate\n\nCOHORT EXCEPTIONS\n'+(ex.length?ex.map(j=>j.job_id+': '+j.review_status).join('\n'):'All completed-job costs verified in this what-if view.');}
function render(){const m=metrics(selectedJobs());$('revenue').textContent=money(m.revenue);$('job-count').textContent=m.count+' completed · '+m.verified+' verified';$('rpph').textContent=m.rpph===null?'Unavailable':'$'+m.rpph.toFixed(2);$('margin').textContent=m.margin===null?'Unavailable':pct(m.margin);$('close-rate').textContent=pct(baseline.cohort.close_rate);$('snapshot-state').textContent=costChanged?'What-if scenario · original snapshot unchanged':'Reconciled snapshot · 6–11 Oct 2026';$('summary').textContent=summaryText();$('jobs').innerHTML=jobs.map(j=>'<tr><td>'+safe(j.job_id)+'</td><td>'+(j.completed_date||'—')+'</td><td>'+(j.revenue_cents===null?'—':(j.revenue_cents/100).toFixed(2))+'</td><td>'+(j.person_hours??'—')+'</td><td>'+(j.materials_cents===null?'Missing':(j.materials_cents/100).toFixed(2))+'</td><td>'+(j.other_direct_cents===null?'Missing':(j.other_direct_cents/100).toFixed(2))+'</td><td>'+safe(j.review_status)+'</td></tr>').join('');
$('exceptions').replaceChildren();const ex=jobs.filter(j=>j.status==='Completed'&&!j.verified);if(!ex.length){$('exceptions').innerHTML='<p>Both missing costs resolved in your what-if scenario.</p>';return;}for(const j of ex){const box=document.createElement('div');box.className='exception';const expected=j.job_id==='JOB-011'?180:120;box.innerHTML='<h3>'+safe(j.job_id)+' · '+money(j.revenue_cents)+' revenue</h3><p class="flag">'+safe(j.review_status)+'</p><p>Owner: Demo Operations Manager · 11 Oct 2026</p><form><label>Supply missing cost (USD)<input type="number" min="0" step="0.01" required value="'+expected+'" aria-label="Missing cost for '+safe(j.job_id)+'"></label><button class="secondary" type="submit">Confirm cost</button></form>';box.querySelector('form').addEventListener('submit',e=>{e.preventDefault();const val=Number(box.querySelector('input').value);if(!Number.isFinite(val)||val<0)return;if(j.materials_cents===null)j.materials_cents=Math.round(val*100);else j.other_direct_cents=Math.round(val*100);j.direct_cost_cents=j.person_hours*j.loaded_hourly_cents+j.materials_cents+j.other_direct_cents;j.verified=1;j.review_status='Verified (browser what-if)';costChanged=true;render();});$('exceptions').append(box);}}
$('period').addEventListener('change',()=>{if(baseline)render();});$('reset-costs').addEventListener('click',()=>{jobs=structuredClone(baseline.jobs);costChanged=false;render();});$('download-summary').addEventListener('click',()=>{const blob=new Blob([summaryText()],{type:'text/plain'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='owner-briefing.txt';a.click();URL.revokeObjectURL(url);});
fetch('verified-reporting.json').then(r=>{if(!r.ok)throw Error('Snapshot unavailable');return r.json();}).then(data=>{baseline=data;jobs=structuredClone(data.jobs);$('provenance').textContent='Snapshot extracted '+new Date(data.extracted_at).toLocaleString('en-GB',{timeZone:'UTC'})+' UTC. Source: '+data.source+'.';render();}).catch(()=>{$('snapshot-state').textContent='Reporting snapshot could not load. Please refresh.';});

