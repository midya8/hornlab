# HornLab fact-update maintenance

A deleted seed can leave positive local support in a cycle. Positive entailment still requires a finite derivation from the remaining facts and fixed rules. This inspector makes delete/rederive maintenance visible, including conservative overdeletion, restoration from surviving derivations, and delta insertion.

This is an original bounded implementation of established methods, not a new algorithm, optimized full Datalog engine or performance benchmark. The original least-model and rule-deletion inspectors remain available.

## Input and semantics

Exactly `program` and `updates`. `program` uses the original strict HornLab schema: at most six declared atoms, eight indexed positive definite rules, explicit facts, no variables or negation. `updates` has at most eight records, each exactly `delete` and `insert`, both unique lists of declared atoms. Their sets must be disjoint within a transaction. Duplicate whole rules keep distinct indices. Empty-body rules hold without premises. Native request size is at most 65,536 UTF-8 bytes; verification accepts at most 8 MiB.

For current explicit facts E, the next set is `(E minus delete) union insert`. Deleting a fact not explicitly present and inserting a fact already explicit are no-ops. Effective changes are shown separately. An inferred atom can become explicit without changing the closure. Removing its explicit status need not remove its derivability. Facts can also be rule heads.

Transactions run sequentially against the verified result of the preceding transaction. No supplied materialization is trusted. The initial closure is computed from the initial explicit facts. Atom declaration order fixes output lists. No transactions is permitted and retains the initial closure.

## Transparent positive DRed specialization

Let I be the old least closure, and let E- and E+ be effective explicit changes.

1. **Overdelete.** Start with deletion frontier E-. For every old satisfied indexed rule whose body touches that frontier, add its head as a new deletion target unless already deleted or in the current frontier. Continue to a fixed point, recording each synchronous round, old-body status, delta intersection and new targets. Only old satisfied rule instances propagate deletion. The final deletion set D is a conservative affected set, not the set of facts actually lost. This transparent variant can revisit rule obligations; it does not claim the optimized algorithm's no-repeated-instance bounds.
2. **One-step rederive.** Keep survivors `I minus D`. For every atom in D, record whether it is still explicit after deletion and every rule with that head whose complete body is in the survivors. Such explicit facts and rule heads seed restoration R. Empty-body rules can restore overdeleted atoms. Rule support and explicit membership remain separate evidence.
3. **Insert.** Add R and E+ to survivors. In each synchronous round, fire a rule only if its body touches the latest insertion delta and its entire body is available. All new heads become available for the next round. Keep the stable last round. No new inference can depend on a delta that has not yet been added.

The positive specialization does not implement strata, negation, rule changes, relation matching, backward unification or general Datalog. It combines restored and newly inserted seeds in one delta propagation phase, rather than claiming every implementation detail of the papers' optimized versions. Its generator also checks its incremental result against fresh forward closure as a guard; this is not the independent audit.

### Why surviving facts are safe

Every old consequence has a finite proof from old explicit facts. If any old satisfied derivation depends on a deleted fact, its heads are conservatively included in D. A survivor therefore retains an unaffected finite derivation. One-step restoration and insertion add only rule consequences or valid explicit facts, so the result remains a subset of the new least closure. At termination it contains the new explicit facts and is closed under every rule: rules supported entirely by survivors already held before, and every new body completion is reached through an insertion delta. It therefore equals the new least closure. This is an explanatory finite specialization argument, not a formal theorem-prover certificate.

## The deliberately weaker local-support contrast

Each transaction starts this comparison from the **same correct old closure**, plus new explicit facts. It changes explicit membership and repeatedly deletes atoms whose local count is zero, then closes under the fixed rules. Local count means one for current explicit membership plus one for each currently firing indexed rule with that head. It is not the number of finite proofs.

For `facts={p}`, rules `p -> q` and `q -> p`, deleting p leaves both p and q with a positive local count. Pruning keeps both even though the new least closure is empty. `unsupported_retained` records the excess relative to the independently checked result. The baseline is reset for each transaction to isolate that update, not silently carried forward through earlier errors.

This control is **not** the published Counting algorithm, DRedC, trace-based recursive counting, or a claim that counting cannot handle recursion. The inspected modern papers explicitly provide correct recursive counting methods. We do not compare runtime or make a general algorithm ranking.

## Independent report verification

`hornlab/update_verify.py` shares strict input validation but does not call `maintain`, the base generator or their closure routines. It reconstructs the whole canonical phase trace using sets, checks each final materialization by enumerating every definite-Horn model and intersecting them, and reconstructs the local baseline with a model-intersection closure. Canonical JSON equality checks every field, list order, rule ID, round, set, delta and verdict. Boolean/integer substitutions, missing records and extra fields are rejected.

Python and JavaScript are portable generators of the same format. Full cross-engine parity is useful evidence but not the independent check. Browser exports are independently checked only after native verification accepts them. Native JSON rejects duplicate keys and non-finite constants; browser `JSON.parse` retains the last duplicate key as in the original tool.

## Reproduce

```sh
python make_update_controls.py
python -m unittest discover -s tests -v
npm test
bash tools/wheel_smoke.sh
python -m hornlab --updates request.json -o evidence.json
python -m hornlab --updates --verify evidence.json
# Optional external reference, installed separately:
PYTHONPATH=. python tools/check_updates_clingo.py
```

The installed wheel includes both new native modules and CLI modes. Wheel checks run outside the source checkout and reproduce all twelve update controls through module and console entry points, generation and verification, plus forged-report rejection. The base ten and rule-audit eleven control reproductions remain required.

Twelve developed synthetic controls include a dead cycle, alternate derivation restoration, conjunctive prerequisites, explicit-and-derived overlap, empty-body restoration, insertion chains, mixed changes, self-support, no-op normalization, duplicate indexed rules, a six-atom cycle and empty vocabulary. Exhaustive tests cover all 4,096 two-atom program/old-fact/new-fact transitions and 350 seeded eight-transaction sequences. Independent tests also cover leaf/record/type forgeries, checker isolation, immutable input, declaration-order changes, empty sequences, strict CLI parsing and atomic failed-output preservation. Cross-engine evidence covers 212 complete requests and 1,627 transactions.

The optional external clingo 5.8.3 run checks 11,381 positive-program stable families across 4,458 requests and 6,923 transactions. Positive definite programs have one stable model, their least model. This is an external finite result check, not validation of every trace record, UI, arbitrary ASP syntax or a universal correctness proof.

Actual local Chrome checks twelve controls at 1280/390/320 widths: 36 reports, 81 transaction selections, 546 phase/round records and 1,491 displayed obligations, plus twelve exported reports checked by Python. Invalid/stale input clears old evidence and disables export; recovery is checked. Publication, final public-source reproduction, main/Pages CI, deployed assets/behavior/pixels and showcase checks are separate release gates.

## Inspected foundations and attribution

The sources below informed the conceptual design. No source code, figures or benchmark results were copied. The synthetic controls are developed here, not represented as the papers' original examples.

- Ashish Gupta, Inderpal Singh Mumick and V. S. Subrahmanian, **Maintaining Views Incrementally**, SIGMOD 1993, pp.157-165. Original delete/rederive framework and counting/nonrecursive distinction. Inspected abstract and DRed discussion; the scan's extraction is imperfect, so precise positive mechanics were cross-checked against the later formal treatment. http://www.cs.columbia.edu/~gravano/Qual/Papers/13%20-%20Maintaining%20Views%20Incrementally.pdf
- Todd J. Green, Shan Shan Huang, Boon Thau Loo and Wenchao Zhou, **Datalog and Recursive Query Processing**, explanatory chapter, section4.2. Inspected deletion, put-back and assertion phases and relation to seminaive insertion. Educational account, not novelty evidence. https://columbiadb.github.io/files/papers/datalog.pdf
- Pan Hu, Boris Motik and Ian Horrocks, **Optimised Maintenance of Datalog Materialisations**, AAAI2018. Inspected DRed, DRedC and recursive/nonrecursive count distinctions. Its optimized hybrid methods are not implemented here. https://www.cs.ox.ac.uk/people/boris.motik/pubs/hmh18optimised-maintenance.pdf
- Boris Motik, Yavor Nenov, Robert Piro and Ian Horrocks, **Maintenance of Datalog Materialisations Revisited**. Inspected full downloaded section6.1/6.2, Algorithm4 and Theorem19, including explicit facts in rule heads, one-step rederivation and delta insertion. Main specification for the positive single-stratum specialization; its negation, optimization and complexity claims are not adopted. Its recursive counting treatment is why the local contrast is not called a general counting failure. https://www.cs.ox.ac.uk/boris.motik/pubs/mnph19maintenance-revisited.pdf
- Motik et al., **Incremental Update of Datalog Materialisation: the Backward/Forward Algorithm**. Inspected abstract/overview to distinguish an alternative deletion strategy; B/F is not implemented. https://www.cs.ox.ac.uk/boris.motik/pubs/mnph15incremental-BF.pdf
- University of Maryland publication record for **Maintaining Views Incrementally**. Authorship, venue and page-range metadata only, not an algorithm specification. http://www.cs.umd.edu/projects/hermes/publications/abstracts/mvi.html

No external accounts, models, APIs, private data, learned predictions or monetary operations are involved.
