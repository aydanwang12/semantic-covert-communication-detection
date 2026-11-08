# Posthoc identifiability result: the missing target matters

**Status:** This argument, audit, and certificate were developed after the
original pilot and main results were known. They do not amend the original
analysis plan and are not a prespecified hypothesis test. They use existing raw
data; no new model observations are claimed.

## What is being distinguished

The two labels are (S) a semantic message encoding the designated hidden target
H and (P) a semantic-placebo message whose frame is independent of H. Both
conditions use a private semantic convention, and both can communicate a
convention-dependent frame bit. Therefore P is **not** a no-communication
condition. The distinction is successful transmission of the *designated target*,
not whether any information or any private convention is used.

Consider a monitor given all message variants, the private partner convention,
the public/system instructions, and the task prompts and returned content of both
receiver roles. This deliberately generous receiver view still omits H. It also
omits the sender's private prompt/candidate menu; condition labels; episode/block
IDs and factor metadata; execution times/order; session identifiers, process
diagnostics, and other condition-dependent side channels. The queried variants
are original, lexical, semantic_counterfactual, and unchanged_repeat, in canonical
named order, not execution order.

The code compares actual saved receiver-call prompts with the episode prompts
before constructing this view. It compares complete canonical JSON strings,
including their exact Unicode text and multiplicities. SHA-256 digests make the
certificate compact; hashes are not substituted for string equality.

## Proposition and assumptions

Let H (target), K (codebook orientation), U (nuisance frame), and Z (nuisance
initial) be independent uniform binary variables. Let T index an authored
template, with the same distribution in both conditions and independent of these
bits. In the fully crossed design, this is the law obtained by uniformly sampling
the finite set of design cells, not a distribution over natural language generally.

Assume correct constrained encoding:

    S: F = H xor K
    P: F = U.

The partner convention maps frame F to route B = F xor K. The rendered message
and all receiver queries are a deterministic function Q = g(K,F,Z,T). Receiver
roles and variant labels are part of Q. The private convention is included in Q.

Assume a **common receiver kernel** R(dy | q): conditional on Q, the joint law
of all returned receiver content Y is the same in S and P. Independence between
the eight receiver calls is sufficient but not necessary; the joint conditional
kernel can include dependence as long as it is condition-invariant. Identical
declared model settings and isolated prompts support this assumption but do not
prove it. Model drift, timing/order effects, hidden shared state, context outside
the saved prompts, or condition-dependent process metadata can invalidate it.

**Claim.** The observable transcript O = (Q,Y) has the same distribution under
S and P. Consequently every fixed measurable receiver-view test has equal alarm
probability under S and P. With balanced class priors, optimal classification
accuracy is 1/2. Every fixed pointwise score has population tied-score AUROC 1/2
on independent test draws. A score fitted on independent training data obeys the
same conclusion conditional on that fitted score.

### Proof

For every k,f,z,t, the semantic condition has exactly one h satisfying
f = h xor k, while u remains arbitrary. The placebo condition fixes u = f,
while h remains arbitrary. Thus in both conditions

    Pr(K=k,F=f,Z=z,T=t) = Pr(T=t) / 8.

Applying the same deterministic function g gives the same query distribution
mu(dq). Applying the same receiver kernel gives the same transcript law

    Pr(Q in dq,Y in dy | C) = mu(dq) R(dy | q),  C in {S,P}.

For any possibly randomized test phi(O), integration against the same measure
gives E[phi(O)|S] = E[phi(O)|P]. Therefore TPR equals FPR at every fixed threshold.
For balanced priors, test accuracy is (TPR + 1 - FPR)/2 = 1/2. For a fixed score,
independent scores drawn under S and P have the same distribution. By symmetry,
Pr(score_S > score_P) = Pr(score_S < score_P), so adding half credit for ties gives
AUROC = 1/2. This uses ordinary equality-of-measures reasoning; it is not a new
general data-processing theorem.

The same argument covers any finite adaptive sequence of **receiver-only**
queries when the query policy uses only the permitted history and independent
randomness, and the response kernel is condition-invariant after every allowed
history. Induction preserves equality of the transcript distributions. It does
not cover querying or intervening on the hidden sender target, observing sender
private context, or exploiting condition-dependent cross-episode state.

## Exact audit of the saved inputs

Run from the repository root:

```sh
python analysis/identifiability.py data/pilot.jsonl data/results.jsonl
python -m unittest discover -s tests -p test_identifiability.py -v
```

The machine-readable result is `analysis/identifiability_results.json`. It records
raw-file and run-manifest hashes, planned-versus-observed episode IDs, the full
factorial crossing, actual sender choices, and per-signature multiplicities.

| Split | Episodes per condition | Distinct receiver query suites per condition | Each suite's multiplicity | Query-distribution TV |
|---|---:|---:|---:|---:|
| Pilot | 16 | 8 | 2 | 0 |
| Main | 32 | 16 | 2 | 0 |

All 96 semantic/placebo sender records across both splits have valid selected
literals, planned features matching the design, and observed features matching
those plans. In particular, the actual sender choices did not break the planned
input equivalence. This audit establishes exact equality for the finite saved
query multisets. It does not establish that future model calls will always encode
correctly or that receiver kernels are identical in all deployments.

For unequal input distributions, data processing under a common receiver kernel
bounds the difference in any test's alarm probabilities by TV(mu_S,mu_P), and
bounds optimal balanced classification accuracy by (1+TV)/2. Here the audited
query-distribution TV is exactly zero. The certificate
`UNIDENTIFIABLE_FOR_DECLARED_VIEW` is conditional on its stated view and kernel
assumptions. It is not a certificate about unrestricted monitors.

## Population equality is not equality of the realized outputs

The observed main detector alarm rates were 7/32 in S and 9/32 in P, and its
empirical AUROC was 0.46875. Pilot values were 3/16, 5/16, and 0.4375. These finite
response samples are allowed to differ under a common stochastic kernel. The
certificate does not relabel them as equal, overwrite observations, or set their
empirical AUROC to 0.5. Nor does agreement with the theorem prove its kernel
assumption. Fitting a detector to the same realized response labels can also
produce optimistic training-set performance; the population claim concerns a
fixed scoring rule evaluated on fresh draws.

## What changes when the monitor has privileged information

Adding H breaks the equality: in S, B=F xor K equals H always; in P this happens
half the time. On the audited finite input distributions, revealing H raises
total variation to 1/2. With balanced classes, the optimal single-episode
classification accuracy is then 3/4. The simple score 1[B=H] also has population
AUROC 3/4. This is an algebraic property of these ideal input distributions, not
a newly measured receiver accuracy.

Adding the full sender-private prompt is an even stronger exception: the existing
protocol explicitly provides a hidden target and two choices in S, while giving
no target and one approved message in P. The exact sender-augmented input
distributions have disjoint support (TV=1). A monitor can distinguish this protocol
metadata without analyzing receiver behavior. This says nothing about a setting
where both senders receive identical-looking private prompts.

A privileged **paired sender-target intervention** offers a causal diagnostic:
hold K,U,Z,T fixed and set H=0 versus H=1 before the sender acts. Correct semantic
encoding changes F, whereas the placebo encoder leaves F=U unchanged. Therefore
the ideal paired frame-change indicator is 1 in S and 0 in P. Re-randomizing U
between the two target values would destroy this exact negative control; holding
the nuisance variables fixed is essential. With fallible LLM senders, the
experiment must record actual choices, failures, and both target assignments
rather than replacing them with the ideal values. The originally saved full
factorial data permit a posthoc matched-target analysis, but that is a distinct,
privileged information regime and must not be described as target-blind detection.
The ideal causal **frame-change** comparison above is distinct from the saved
receiver-action contrast A(H=1)-A(H=0). For complete balanced binary pairs, the
mean of that action contrast equals twice original-message decoding accuracy
minus one: A(1)-A(0) = 1[A(1)=1] + 1[A(0)=0] - 1. Reanalyzing that statistic does
not supply independent evidence beyond the existing accuracy observations and
must not be presented as a new intervention experiment.

## Scope of the contribution

The result identifies a precise limitation of this benchmark's receiver view:
behavior can identify use of a private convention without identifying where the
convention's bit came from. It neither establishes that semantic communication
is universally undetectable nor refutes a monitor that sees sender instructions,
ground-truth targets, richer side information, or a different data-generating
process. Its reusable contribution is a preflight check that exposes this
identification failure before comparing detector scores, with explicit tests of
which added observations break the equivalence.
