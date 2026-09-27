import { createRequire } from 'node:module';
import { mkdirSync, copyFileSync } from 'node:fs';
const require=createRequire(import.meta.url);
mkdirSync('public',{recursive:true});
copyFileSync(require.resolve('echarts/dist/echarts.min.js'),'public/echarts.min.js');
