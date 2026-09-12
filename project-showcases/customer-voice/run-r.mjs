import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.dirname(fileURLToPath(import.meta.url));
const moduleUrl=process.env.WEBR_MODULE || import.meta.resolve('webr');
const {WebR}=await import(moduleUrl);
const r=new WebR({interactive:false});
try {
  await r.init();
  await r.FS.mkdir('/work');
  await r.FS.mkdir('/work/data');
  await r.FS.mkdir('/work/results');
  for(const name of ['responses.csv','customers.csv','assignments.csv','invitations.csv']) {
    await r.FS.writeFile('/work/data/'+name,new Uint8Array(await fs.readFile(path.join(root,'data',name))));
  }
  await r.FS.writeFile('/work/analysis.R',new Uint8Array(await fs.readFile(path.join(root,'analysis.R'))));
  await r.evalRVoid('setwd("/work"); source("analysis.R")');
  for(const name of ['theme-summary.csv','response-rates.csv','r-summary.csv','r-environment.txt']) {
    await fs.writeFile(path.join(root,'results',name),await r.FS.readFile('/work/results/'+name));
  }
  console.log(await fs.readFile(path.join(root,'results','r-summary.csv'),'utf8'));
} finally {r.close();}
