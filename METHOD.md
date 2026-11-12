# HornLab inference and seed-support method

[Live inspector](https://midya8.github.io/hornlab/) · [Source](https://github.com/midya8/hornlab)

An original bounded implementation of established positive propositional definite-Horn inference. Not a new algorithm, full Datalog interpreter, general SAT solver or production rule engine. All controls and code are original; the stylesheet and generic Chrome startup helper follow the portfolio's existing house style/tooling.

## Exact fragment

Input has exactly `atoms`, `facts` and `rules`. At most six unique declared atom names and eight indexed rules. Atom names match `[a-z][a-z0-9_]{0,23}`. Facts and each rule body are duplicate-free lists of declared atoms. A rule has exactly `if` (a conjunction, possibly empty) and `then` (one atom). Duplicate whole rules are allowed and retain separate IDs. Names have no built-in meaning. No negated atom, headless denial, variable, constructor, relation argument, probability or external side effect.

A classical assignment M is a subset of the declared universe. It must contain the initial facts and satisfy every body-to-head implication. An empty body is true. Thus the all-true assignment is always a model; programs in this fragment cannot be inconsistent. This does not solve general Horn satisfiability with denials.

Masks use bit i for declared atom i. Lists of sets follow atom declaration order; models and seed subsets use ascending masks. Facts/rules are retained verbatim in the input field. Input byte limit is 65,536 UTF-8 bytes. Native report verification accepts at most 8 MiB. Native JSON parsing rejects duplicate keys and nonfinite constants; browser JSON.parse keeps the last duplicate key.

## Synchronous inference

Start K0 = supplied facts. In each round set Knext = K union all rule heads whose complete body is in K. All rule decisions read the same K, not an in-place partially updated set. Record before, added, after and every indexed rule's missing atoms, readiness and whether its head is new. Keep the final no-change round. There are at most n strict-growth rounds plus one stable round for n declared atoms.

This is an inflationary closure operator with retained initial facts. It is not the bare immediate-consequence operator on arbitrary interpretations. It reaches the same least model of the program plus initial-fact clauses. A first-round number is zero for initial facts, the first adding round for derived atoms, and null if never derived. For a newly derived atom every rule ready in that first round with that head is a tied first achiever; initial atoms report no achiever rule. This is not enumeration of every proof tree.

## Models and supported models

Enumerate every one of at most 64 truth assignments. A satisfying assignment is supported exactly when it equals initial facts union heads whose bodies hold in that assignment. Supported models can be nonleast because of circular justification. The default original control has a seed plus a two-atom rule cycle; the all-true assignment supports that cycle, while the least model contains only the seed. An additional model contains an arbitrary goal without support.

The least model equals the intersection of all classical models. A positive atomic query is entailed iff its atom belongs to that intersection. An unentailed atom gets the lowest-mask actual countermodel excluding it. This is not classical negation or negation-as-failure: the all-true model still makes that atom true. Model counts are not probabilities. No stable-model/answer-set semantics is implemented.

## Minimal initial-fact supports

Rules stay fixed. Enumerate every subset S of the supplied initial facts, including empty, and its closure. A support for atom a has a in closure(S). It is inclusion-minimal iff deleting any member loses a, using monotonicity of positive inference. Native checking instead tests every proper seed subset, not only immediate deletions. All ties and different cardinalities are retained. The two-support control has both a singleton support and a distinct two-fact support. An empty-body rule can give an empty support.

Each support retains every single deletion's remaining seed set and full closure, visibly excluding the query. These are seed-subset witnesses, not minimal rule subsets, semiring provenance, all derivation trees, causal counterfactuals or minimal abductive explanations over arbitrary hypotheses.

## Independent implementations and checking

The Python generator uses bitsets and indexed masks. The independently written JavaScript generator uses sets, membership and ordered projection. The native verifier does not call the generator: it replays rounds with sets, enumerates all classical models, intersects them, recomputes supportedness and uses an asynchronous set-closure procedure plus all-proper-subset support tests. It checks the full canonical JSON report, including ordering, every rule decision, model, seed subset, countermodel, query and support/deletion record. Exact serialization rejects boolean-for-integer metadata and extra/missing fields. Shared input validation remains a shared dependency. This is an executable finite audit, not a machine-checked theorem or source signature. The browser itself has no independent verifier.

## Reproducible evidence

Ten original controls retain 19 rounds, 13 models, 32 atom queries and 89 seed subsets. They cover unsupported cycles, a seed breaking recursion, different-size minimal supports, synchronous chains, empty-body derivation, duplicate rule IDs, unconstrained atoms, the empty universe, all 64 seed subsets and the eight-rule bound.

Ten native tests pass on Python 3.10-3.13. Exhaustive tests cover all 1,024 combinations of the eight possible distinct rules on two atoms and four initial-fact choices. Another 400 seeded programs exercise larger universes. Tests include model-intersection entailment, actual countermodels, permutation equivalence, immutable input, checker isolation, forged/missing records, bool metadata, strict CLI JSON and atomic failed-output preservation.

Three Node/actual-Chrome tests include 210 full cross-engine reports, 691 model records, 294 rounds and 807 seed subsets from controls plus 200 differently seeded programs. Chrome checks every control, round/rule, model, query/support and ablation at 320/390/1280, including JSON export and invalid-input clearing. The bounded enumerations and tests are not a universal implementation proof or a speed benchmark. Installed wheel checks reproduce all ten full reports via module and console entry points, both analyze and verify modes, outside the checkout with four module origins in site-packages.

## Inspected sources and boundaries

Six groups were found by public search and fetched. Only the sections below informed this implementation. No source code, figures or examples were copied.

1. Stefan Brass, **Logic Programming and Deductive Databases, Chapter 10: The Minimal Model**, Summer 2023 course notes. Inspected definite-rule/fact definitions, minimal-model intersection and positive-ground entailment, monotone immediate consequence/least-fixed-point results and supported-model counterexample. This project's propositional universe is smaller; general Herbrand terms and the notes' operational discussion are not adopted. https://users.informatik.uni-halle.de/~brass/lp23/print/ca_minmo.pdf
2. Lee Naish, **Conventional definite clause semantics**. Inspected model-theoretic, fixed-point and operational-semantics overview: models as implication-satisfying atom sets, least-model intersection, monotonicity and positive success sets. Used for semantic cross-checks, not an SLD implementation or claims about failure/negation. https://lee-naish.github.io/papers/sem3neg/html/node4.html
3. Dan Suciu, **CS294-248 Special Topics in Database Theory, Unit 9: Datalog (Part 2)**, lecture PDF hosted by the course. Inspected positive-rule/least-fixed-point recap and recursion/negation examples. Semipositive, stratified and inflationary/partial-fixpoint language extensions are not implemented. The author page identifies University of Washington; hosting does not change authorship. https://berkeley-cs294-248.github.io/lectures/unit9b.pdf
4. **Datalog and Recursive Query Processing** reading notes on mwhittaker.github.io. Inspected model-, fixed-point- and proof-theoretic semantics, source-fact inclusion, monotonicity and naive versus semi-naive evaluation. A secondary explanatory summary, not primary novelty evidence; this tool does not implement semi-naive optimization or quote its complexity results as a benchmark. https://mwhittaker.github.io/papers/html/green2013datalog.html
5. Souffle official **Tutorial**. Inspected introduction, language motivation and recursive transitive-closure example to delimit actual Datalog from this tiny propositional fragment. No tuple relations, arithmetic functors, compiler, syntax compatibility or Souffle performance is claimed. https://www.souffle-lang.com/tutorial
6. Wikipedia community **Horn clause** overview. Inspected Horn versus definite versus goal-clause definitions, fact/empty-body interpretation and the least-model positive-query description. Terminology cross-check, not primary correctness authority. Denials and SLD resolution discussed there are out of scope. https://en.wikipedia.org/wiki/Horn_clause

## Scope of later inspectors

The original model/seed inspector above is unchanged. [RULES.md](RULES.md) documents rule-subset auditing. [UPDATES.md](UPDATES.md) separately documents the v0.3 fact-maintenance generator's positive delete/rederive specialization, delta insertion, independent checker and local-support contrast. Claims about the original inference path above do not imply that the later maintenance path lacks delta insertion.
