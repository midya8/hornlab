// Independently written set-based engine. No Python report is embedded.
export function validate(value){
 if(!value||Array.isArray(value)||typeof value!=='object'||Object.keys(value).sort().join(',')!=='atoms,facts,rules')throw Error('Expected exactly atoms, facts and rules');
 const {atoms,facts,rules}=value;
 if(!Array.isArray(atoms)||atoms.length>6||atoms.some(a=>typeof a!=='string'||!/^[a-z][a-z0-9_]{0,23}$/.test(a))||new Set(atoms).size!==atoms.length)throw Error('Use at most six unique lowercase atom names, 1-24 characters');
 const subset=xs=>Array.isArray(xs)&&xs.every(x=>typeof x==='string'&&atoms.includes(x))&&new Set(xs).size===xs.length;
 if(!subset(facts))throw Error('facts must be a unique list of declared atoms');
 if(!Array.isArray(rules)||rules.length>8)throw Error('Use at most eight indexed rules');
 for(const r of rules)if(!r||Array.isArray(r)||typeof r!=='object'||Object.keys(r).sort().join(',')!=='if,then'||!subset(r.if)||typeof r.then!=='string'||!atoms.includes(r.then))throw Error('Each rule has exactly if (unique declared atoms) and then (one declared atom)');
 return JSON.parse(JSON.stringify(value));
}
export function analyze(value){
 const input=validate(value),{atoms,facts,rules}=input,order=s=>atoms.filter(a=>s.has(a)),contains=(xs,s)=>xs.every(x=>s.has(x)),members=m=>new Set(atoms.filter((_,i)=>Math.floor(m/2**i)%2)),number=s=>atoms.reduce((n,a,i)=>n+(s.has(a)?2**i:0),0);
 function closure(seed,trace=false){let known=new Set(seed),rounds=[];while(true){const decisions=rules.map((r,i)=>({rule:i,missing:r.if.filter(a=>!known.has(a)).sort((a,b)=>atoms.indexOf(a)-atoms.indexOf(b)),ready:contains(r.if,known),new_head:contains(r.if,known)&&!known.has(r.then)}));const next=new Set(known);decisions.forEach((d,i)=>{if(d.ready)next.add(rules[i].then)});if(trace)rounds.push({round:rounds.length+1,before:order(known),added:order(new Set([...next].filter(a=>!known.has(a)))),after:order(next),rules:decisions});if(next.size===known.size)return {known,rounds};known=next;}}
 const {known:least,rounds}=closure(facts,true),all=Array.from({length:2**atoms.length},(_,i)=>members(i));
 const models=all.filter(s=>contains(facts,s)&&rules.every(r=>!contains(r.if,s)||s.has(r.then))).map(s=>{const immediate=new Set(facts);for(const r of rules)if(contains(r.if,s))immediate.add(r.then);return {mask:number(s),atoms:order(s),supported:immediate.size===s.size&&contains([...immediate],s),least:s.size===least.size&&contains([...least],s)}});
 const seeds=all.filter(s=>[...s].every(a=>facts.includes(a))),clos=new Map(seeds.map(s=>[number(s),closure(s).known]));
 const ablations=seeds.map(s=>({mask:number(s),facts:order(s),closure:order(clos.get(number(s)))}));
 const queries=atoms.map(a=>{const supports=seeds.filter(s=>clos.get(number(s)).has(a)&&[...s].every(f=>!clos.get(number(new Set([...s].filter(x=>x!==f)))).has(a))).map(s=>({mask:number(s),facts:order(s),deletions:order(s).map(f=>{const remaining=new Set([...s].filter(x=>x!==f));return {removed:f,remaining:order(remaining),closure:order(clos.get(number(remaining)))}})}));const first=facts.includes(a)?0:rounds.find(r=>r.added.includes(a))?.round??null;return {atom:a,entailed:least.has(a),first_round:first,first_achievers:first===0||first===null?[]:rounds[first-1].rules.filter(d=>d.new_head&&rules[d.rule].then===a).map(d=>d.rule),countermodel:models.find(m=>!m.atoms.includes(a))?.mask??null,minimal_supports:supports}});
 return {schema:'hornlab-v1',input,rounds,least_model:order(least),models,ablations,queries};
}
