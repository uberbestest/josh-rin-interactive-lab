'use strict';
const fs=require('node:fs');const {build}=require('./engine.js');
const rows=JSON.parse(fs.readFileSync('results/frontier.json','utf8'));
let cells=0,replays=0;
for(const r of rows){
 const p=build(r),v=p.solve();
 if(v.wins!==r.completions||v.cost!==r.total_ticks||v.action!==r.first_action||p.worlds.length!==r.schedules)throw Error(`JS/Python disagreement: ${r.id}`);
 let wins=0,ticks=0;
 for(let i=0;i<p.worlds.length;i++){const x=p.replay(i);wins+=Number(x.completed);ticks+=x.ticks;replays++;}
 if(wins!==v.wins||ticks!==v.cost)throw Error(`JS replay disagreement: ${r.id}`);
 cells++;
}
console.log(JSON.stringify({status:'PASS',implementation:'JavaScript second implementation; same author',cells,replays}));
