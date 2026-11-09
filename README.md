# HornLab

A circle is not a proof. A bounded positive propositional definite-Horn workbench with complete closure-round, model and minimal initial-fact support witnesses.

[Live inspector](https://midya8.github.io/hornlab/) · [Method and inspected sources](METHOD.md)

The default program has a nonleast supported model containing an unsupported cycle. Forward chaining derives only its initial seed. A satisfying model can contain atoms without any rule justification; a supported model can justify atoms circularly. Positive entailment is captured by the least model, not by either weaker check. Not entailed is not classically false: every definite-Horn program here has an all-true model.

## Inspect

- Every synchronous closure round, including the stable last round, and every indexed rule's missing premises, readiness and newly derivable head.
- All classical satisfying assignments, supported-model flags and the unique least model.
- Each atom's entailment, first derivation round, all tied first achiever rule IDs and an actual countermodel when it is not entailed.
- Every subset of the supplied initial facts, its closure and every inclusion-minimal sufficient seed set with single-deletion failures. Minimal does not mean smallest. Rules are fixed.
- A full JSON report, atomic native CLI and independent native report checker. The checker replays with sets and verifies model intersection and all proper seed subsets, without calling the generator.

## Run

```sh
python -m hornlab examples/cycle.json
python -m hornlab examples/cycle.json -o report.json
python -m hornlab --verify report.json
python -m unittest discover -s tests -v
npm test
bash tools/wheel_smoke.sh
```

Install the wheel for the `hornlab` console command. No runtime dependency, API, model, account or data download. Serve `docs/` over HTTP for the browser inspector.

```json
{"atoms":["seed","bridge","goal"],"facts":["seed"],"rules":[{"if":["seed"],"then":"bridge"},{"if":["bridge"],"then":"goal"}]}
```

Ten original synthetic controls retain 19 rounds, 13 models, 32 atomic queries and 89 initial-fact subsets. Native checks cover all 1,024 two-atom programs/initial-fact sets from the eight possible distinct positive rules, plus 400 seeded programs. Independently written Python bitset and JavaScript set engines agree on 210 full reports. Actual Chrome checks every retained record at 320/390/1280, export and invalid-input clearing. Installed-wheel checks reproduce all ten reports through both entry points, in analyze and verify modes, outside the checkout.

## Limits

At most six atoms, eight indexed rules and 65,536 input bytes. Positive propositional definite clauses only: no negation, denials, variables, functions, relation tuples, unification, SLD search or full Datalog/Prolog syntax. Counts are exact finite enumeration, not probabilities or scalability evidence. Supports are subsets of initial facts, not all proof trees, rule provenance or causal explanations. Native verification shares input validation with generation and validates the canonical report, not a formal proof or signed source. The browser has no independent report verifier. Established inference/model theory, not a new algorithm or a production rule engine.
