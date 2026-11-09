# HornLab rule subsets: fixed seeds, alternative routes

[Live rule inspector](https://midya8.github.io/hornlab/rules.html) · [Original inference inspector](https://midya8.github.io/hornlab/) · [Source](https://github.com/midya8/hornlab)

An original bounded implementation of established monotone explanation/deletion and minimal hitting-set duality. This is not a new algorithm, ontology reasoner, general SAT/MUS tool, scalable diagnosis engine or causal analysis. No copied examples, code or figures. Generic style and Chrome startup helpers retain the existing house tooling.

## Fixed facts, indexed rules

The exact input domain is unchanged from [METHOD.md](METHOD.md): at most six unique lowercase atoms, eight indexed positive propositional definite-Horn rules and 65,536 input bytes. Initial facts are held fixed. All 2^m rule masks are enumerated, in ascending numeric order; bit i retains original indexed rule i. Duplicate whole rules remain independent indexed choices. Each subset retains its full least closure and synchronous added-atom rounds, including the final stable empty round. There are at most 256 subsets. Initial facts remain even at mask zero.

For each declared atom q:

- A minimal rule support S derives q from the fixed facts using only S. No proper subset of S derives q. It is inclusion-minimal, not necessarily minimum cardinality. Every one-rule removal records the remaining mask and closure.
- A minimal deletion set C leaves q non-entailed when precisely C is removed from the full rule set. Restoring any one removed rule makes q entailed. Every restoration records the retained mask and closure.
- The minimal hitting sets of all supports are exactly all deletion sets. The minimal hitting sets of all deletion sets recover all supports. Both families are enumerated independently and every support/deletion pair retains its nonempty rule intersection.

The generator uses bitmask closure and immediate deletion/restoration checks, sufficient by monotonicity. The independent native checker never calls it: explicit sets replay each synchronous closure, enumerate all classical assignments for each retained subset and confirm closure equals their intersection, check all proper candidate subsets for minimality, and enumerate both minimal hitting families by set inclusion. Shared schema validation remains. Canonical complete-report equality rejects missing, extra or reordered records, forged boundaries and booleans substituted for integer metadata. This is bounded exhaustive validation, not a formal proof, signed certificate or arbitrary-proof checker. JavaScript uses an independently written set engine; browser export has no independent verifier.

## Edge conventions

- An initial fact has the sole empty rule support and no deletion set. Deleting rules cannot remove a fixed fact.
- A currently non-entailed atom has no support and one empty deletion set. It is already absent; zero changes suffice.
- The empty family has one minimal hitting set, the empty set. A family containing the empty set has none. These conventions make both dualities hold at the boundaries.
- Non-entailment is not classical falsity. Cyclic supported models still do not yield a derivation; the base inspector exposes that distinction.
- Rule supports are sets of usable rules, not ordered proof trees, proof multiplicities, seed supports or causal mechanisms. Rules can be shared among routes. Duplicate indexed alternatives are not deduplicated.

## Original controls

Eleven controls: a new two-route goal with supports {0} and {1,2}, deletion sets {0,1} and {0,2}, plus an irrelevant self-cycle; the ten retained base controls cover unsupported mutual cycles, tied first achievers, synchronous chains, empty-body rules, duplicate indexed rules, seeded cycles, unconstrained atoms, empty universes, six fixed facts and the eight-rule bound. All together: 305 retained subsets, 35 queries, 36 minimal supports, 27 deletion sets and 36 support/deletion intersections.

The new default's supports have different sizes. Its deletion sets both have size two. A support is a retained set; a deletion mask has the opposite role. Tables label these roles explicitly.

## Reproduce

```sh
python -m unittest discover -s tests -v
npm test
bash tools/wheel_smoke.sh
python -m hornlab --rules examples/cycle.json -o rules.json
python -m hornlab --rules --verify rules.json
hornlab --rules --verify rules.json
```

The original API/CLI/ten controls/inspector stay intact; `--rules` selects the new schema `hornlab-rules-v1`. Native report verification still allows at most 8 MiB and atomic output replacement. The package is version 0.2.0. Python API: `hornlab.rule_audit.audit_rules` and `hornlab.rule_verify.verify_rules`.

Eighteen native tests retain all ten base tests and add all 1,024 two-atom rule/fact combinations, 150 seeded lattices, full-report forgery controls, generator-disabled verification, rule-permutation equivariance, strict/atomic CLI and boundary cases. Five Node/actual-Chrome tests retain all three base tests. Independent Python/JavaScript match 131 rule audits (5,304 subsets, 422 queries, 305 supports, 236 deletion sets). Chrome checks every retained subset/round, query, support/removal, deletion/restoration and intersection at 320/390/1280, plus full JSON/export/invalid clearing and overflow at each visited record. Installed wheel reproduction runs ten base and eleven rule reports through both CLI entry points outside checkout.

## Inspected source coverage

The six inspected semantics/official/community sources in [METHOD.md](METHOD.md) remain applicable to closure and fragment limits. Added primary research readings below support terminology and duality, not a claim to implement their algorithms, reproduce their performance or accept their ontology languages.

1. Birte Glimm and Yevgeny Kazakov, **SAT-Based Axiom Pinpointing Revisited**, DL 2022. Inspected introduction, justification/repair definitions, non-entailment empty-repair convention and inference-derived monotone subset discussion. This tool brute-force enumerates finite rule subsets, not MARCO or the paper's SAT encodings. https://ceur-ws.org/Vol-3263/paper-10.pdf
2. Alexey Ignatiev, Alessandro Previti, Mark Liffiton and Joao Marques-Silva, **Smallest MUS Extraction with Minimal Hitting Set Dualization**, preprint. Inspected preliminaries: inclusion-minimal versus smallest, hitting sets and duality. HornLab applies the finite-set principle directly to monotone entailment, not inconsistent definite-Horn inputs; no SMUS implementation or complexity benchmark claim. https://alexeyignatiev.github.io/assets/pdf/iplms-cp15-preprint.pdf
3. Alexey Ignatiev, Joao Marques-Silva, Carlos Mencia and Rafael Penaloza, **Debugging EL+ Ontologies through Horn MUS Enumeration**. Inspected introduction and Definitions 1, 3, 4, plus MinA/deletion hitting-set relation and Horn encoding context. HornLab does not translate EL+ or group axioms; its units are indexed propositional rules with fixed seed background. https://ceur-ws.org/Vol-1879/paper54.pdf
