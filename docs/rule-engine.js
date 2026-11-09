import {validate} from './engine.js';
export function auditRules(input){
 const data=validate(input),{atoms,facts,rules}=data,all=2**rules.length-1;
 const ids=m=>rules.map((_,i)=>i).filter(i=>m&2**i),names=s=>atoms.filter(a=>s.has(a));
 const subsets=[],closures=[];
 for(let mask=0;mask<=all;mask++){let current=new Set(facts);const added_rounds=[];
  for(;;){const added=new Set();for(const i of ids(mask)){const r=rules[i];if(r.if.every(a=>current.has(a))&&!current.has(r.then))added.add(r.then)}added_rounds.push(names(added));if(!added.size)break;for(const a of added)current.add(a)}
  closures.push(current);subsets.push({mask,retained:ids(mask),closure:names(current),added_rounds});}
 const minimal=family=>family.filter(s=>!family.some(t=>s!==t&&(s&t)===t));
 const hitting=family=>minimal(Array.from({length:all+1},(_,m)=>m).filter(m=>family.every(f=>(m&f)!==0)));
 const queries=atoms.map(atom=>{const supports=minimal(subsets.filter(s=>closures[s.mask].has(atom)).map(s=>s.mask)),cuts=minimal(subsets.filter(s=>!closures[all^s.mask].has(atom)).map(s=>s.mask));
  return {atom,full_entailed:closures[all].has(atom),supports:supports.map(m=>({mask:m,rules:ids(m),deletions:ids(m).map(i=>({removed:i,remaining_mask:m^2**i,closure:names(closures[m^2**i])}))})),cuts:cuts.map(m=>({mask:m,removed:ids(m),retained_mask:all^m,closure:names(closures[all^m]),restorations:ids(m).map(i=>({restored:i,retained_mask:all^(m^2**i),closure:names(closures[all^(m^2**i)])}))})),minimal_hitting_supports:hitting(supports),minimal_hitting_cuts:hitting(cuts),intersections:supports.flatMap(s=>cuts.map(c=>({support:s,cut:c,rules:ids(s&c)})))};});
 return {schema:'hornlab-rules-v1',input:data,subsets,queries};
}
