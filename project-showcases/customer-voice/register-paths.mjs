import {register} from 'node:module';
if(process.platform==='win32') register('./windows-path-loader.mjs',import.meta.url);
