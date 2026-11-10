// Positive propositional DRed-style maintenance. Portable generator, not an
// independent verifier. The Python model-intersection checker is independent.
export function validateUpdates(data) {
 if(!data||typeof data!=='object'||Array.isArray(data)||Object.keys(data).sort().join(',')!=='program,updates')throw Error('Expected exactly program and updates');
 const p=data.program;
 if(!p||typeof p!=='object'||Array.isArray(p)||Object.keys(p).sort().join(',')!=='atoms,facts,rules')throw Error('Program has exactly atoms, facts and rules');
 if(!Array.isArray(p.atoms)||p.atoms.length>6||p.atoms.some(a=>typeof a!=='string'||!/^[a-z][a-z0-9_]{0,23}$/.test(a))||new Set(p.atoms).size!==p.atoms.length)throw Error('Use at most six unique lowercase atom names');
 const subset=xs=>Array.isArray(xs)&&xs.every(a=>typeof a==='string'&&p.atoms.includes(a))&&new Set(xs).size===xs.length;
 if(!subset(p.facts)||!Array.isArray(p.rules)||p.rules.length>8)throw Error('Unique declared facts and at most eight indexed rules');
 for(const r of p.rules)if(!r||typeof r!=='object'||Array.isArray(r)||Object.keys(r).sort().join(',')!=='if,then'||!subset(r.if)||typeof r.then!=='string'||!p.atoms.includes(r.then))throw Error('Each rule has if and then over declared atoms');
 if(!Array.isArray(data.updates)||data.updates.length>8)throw Error('Use at most eight updates');
 for(const u of data.updates)if(!u||typeof u!=='object'||Array.isArray(u)||Object.keys(u).sort().join(',')!=='delete,insert'||!subset(u.delete)||!subset(u.insert)||u.delete.some(a=>u.insert.includes(a)))throw Error('Each update has disjoint unique delete and insert lists');
 return JSON.parse(JSON.stringify(data));
}
export function maintain(data) {
 data=validateUpdates(data);const p=data.program,atoms=p.atoms,rules=p.rules,bit=a=>1<<atoms.indexOf(a),mask=xs=>xs.reduce((m,a)=>m|bit(a),0),names=m=>atoms.filter(a=>m&bit(a)),compiled=rules.map(r=>[mask(r.if),bit(r.then)]);
 function closure(seed){let current=seed;for(;;){let next=current;for(const[b,h]of compiled)if((b&current)===b)next|=h;if(next===current)return current;current=next;}}
 function forward(survivors,seeds){let delta=seeds&~survivors,current=survivors|delta;const rounds=[];for(;;){let next=0;const decisions=compiled.map(([body,head],rule)=>{const touched_delta=Boolean(body&delta),missing=body&~current,fires=touched_delta&&!missing,new_head=fires&&!Boolean(head&current);if(new_head)next|=head;return{rule,touched_delta,missing:names(missing),fires,new_head};});rounds.push({round:rounds.length+1,before:names(current),delta:names(delta),rules:decisions,added:names(next),after:names(current|next)});if(!next)return[current,rounds];current|=next;delta=next;}}
 let facts=mask(p.facts),current=closure(facts);const initial=current,steps=[];
 for(const update of data.updates){const removed=facts&mask(update.delete),inserted=mask(update.insert)&~facts,newFacts=(facts&~removed)|inserted;let deleted=0,delta=removed;const over=[];
  for(;;){let next=0;const decisions=compiled.map(([body,head],rule)=>{const old_body_holds=(body&current)===body,touched_delta=Boolean(body&delta),fires=old_body_holds&&touched_delta,new_head=fires&&!Boolean(head&(deleted|delta));if(new_head)next|=head;return{rule,old_body_holds,touched_delta,fires,new_head};});over.push({round:over.length+1,deleted_before:names(deleted),delta:names(delta),rules:decisions,added:names(next),deleted_after:names(deleted|delta)});deleted|=delta;if(!next)break;delta=next;}
  const survivors=current&~deleted,reseed=[];let rederived=0;
  for(const atom of atoms){const h=bit(atom);if(!(deleted&h))continue;const ids=compiled.map(([body,head],i)=>head===h&&(body&survivors)===body?i:null).filter(i=>i!==null),explicit=Boolean(h&(facts&~removed)),recovered=explicit||ids.length>0;reseed.push({atom,surviving_explicit:explicit,surviving_rule_ids:ids,rederived:recovered});if(recovered)rederived|=h;}
  const[final,insertRounds]=forward(survivors,rederived|inserted);let naive=current|inserted;const prune=[];
  for(;;){let gone=0;const support=[];for(const atom of atoms){const b=bit(atom);if(!(naive&b))continue;const ids=compiled.map(([body,head],i)=>head===b&&(body&naive)===body?i:null).filter(i=>i!==null),explicit=Boolean(newFacts&b),count=Number(explicit)+ids.length;support.push({atom,explicit,rule_ids:ids,local_count:count});if(!count)gone|=b;}prune.push({round:prune.length+1,before:names(naive),support,removed:names(gone),after:names(naive&~gone)});if(!gone)break;naive&=~gone;}
  const naiveFinal=closure(naive);if(final!==closure(newFacts))throw Error('DRed disagrees with recomputation');
  steps.push({step:steps.length,update,facts_before:names(facts),closure_before:names(current),effective_delete:names(removed),effective_insert:names(inserted),facts_after:names(newFacts),overdelete_rounds:over,overdeleted:names(deleted),survivors:names(survivors),rederive:reseed,one_step_rederived:names(rederived),insertion_seed:names((rederived|inserted)&~survivors),insertion_rounds:insertRounds,closure_after:names(final),lost:names(current&~final),gained:names(final&~current),restored:names(deleted&final),local_prune_rounds:prune,local_prune_closure:names(naiveFinal),unsupported_retained:names(naiveFinal&~final),local_prune_agrees:naiveFinal===final});facts=newFacts;current=final;
 }
 return{schema:'hornlab-updates-v1',input:data,initial_closure:names(initial),steps,final_facts:names(facts),final_closure:names(current)};
}
