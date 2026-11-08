# Review of the strongest defensible extension

Reviewed 2026-11-08 against the current code, saved pilot/main data, and primary papers. Recommendation: lead with a **receiver-view identifiability counterexample**, supported by the placebo experiment and an exact prompt-multiset certificate. Treat the syntactic/semantic comparison as the instrument check that enables this finding. Do not claim a general new impossibility theorem or that the placebo carries no information whatsoever.

## Why this improves the submission

The [official judging rubric](https://apartresearch.com/sprints/swarm-alignment-2026) scores impact/innovation, execution, and clarity. It explicitly distinguishes new work from replication when awarding the highest innovation scores. Repeating the established paraphrase-robustness finding is therefore a weak central contribution. A precise account of what the monitor can identify, with a machine-checkable counterexample and a target-grounded comparison, is more useful than additional samples from the same template bank. This is a reasoned recommendation, not a prediction of a prize.

Suggested central claim: **A private-convention response gap can be equally strong with and without transmission of the designated secret. In this balanced construction, every receiver-side replay monitor that lacks the target reference faces identical observation distributions.**

Suggested title: **Convention Is Not Transmission: A Placebo Test for Behavioral Detection of Semantic Covert Communication.** The original title can remain as a subtitle or be retained if submission replacement requires it.

## Exact proposition and proof

Let condition C be either semantic or placebo. Let H, K, N, and I be mutually independent uniform bits: designated hidden target, private codebook orientation, nuisance frame, and nuisance initial. Let template T have the same distribution in both conditions and be independent of these factors. Define

```
Semantic: F = H xor K.
Placebo:  F = N.
Message:  M = render(F, I, T).
```

Both conditions give the partner the same K-indexed semantic codebook and the outsider NONE. Let V denote their complete experiment-owned prompt suite, including original, lexical, semantic-counterfactual, and unchanged-repeat prompts. All these prompts are fixed functions of (K,F,I,T). The target H, condition label, sender prompt, and target-bearing metadata are excluded from V.

**Proposition.** The marginal distribution of V is identical in the two conditions. If the complete receiver/replay response process is a common stochastic kernel Q(.|V), the joint distribution of (V, responses) is also identical. Every detector based only on that joint view has TPR equal to FPR. With balanced condition priors, its expected accuracy and population tie-aware AUROC are 1/2.

**Proof.** Conditional on every template, (K,F,I) is uniform over eight tuples in both conditions. Therefore V, a deterministic function of the tuple, has the same law. Applying the same stochastic kernel preserves equality. Any randomized detector is another common kernel, so its alarm probability is equal under both conditions. Any score has identical positive/negative distributions, yielding AUROC 1/2 with half credit for ties. This is an application of distributional indistinguishability and data processing, not a new general statistical principle.

The same argument covers arbitrary adaptive receiver-side queries if each next query is chosen from the accumulated target-blind view and the response kernels remain condition-independent. It does **not** cover interventions on the sender's hidden target, access to sender prompts, or an external reference revealing H. The supplied experiment uses fixed interventions, so adaptive-query scope is a mathematical corollary rather than an empirical claim.

For the ideal code-following partner A=F xor K, semantic has A=H, whereas placebo has A independent of H. Equivalently, I(H;F|K)=1 bit in semantic and 0 in placebo. Thus the property that differs is **transmission of H**, even though the receiver-visible behavior has the same marginal distribution.

## What the existing data establish

A direct read-only recalculation found:

| Split | Episodes per condition | Semantic/placebo unique prompt suites | Exact prompt-suite multisets equal? |
|---|---:|---:|---|
| Pilot | 16 | 8 each | Yes |
| Main | 32 | 16 each | Yes |

All semantic sender choices matched their planned frame. Both saved splits use full crossing, not the optional half-fraction. The comparison serialized the complete saved `prompts` dictionaries with sorted keys, including both receivers and every intervention. This confirms equality of supplied receiver task content; it does not assert that realized stochastic response multisets are identical or that the full provider requests were captured.

Main original-action partner accuracy is 32/32 in semantic and 16/32 in placebo. Because H is balanced, the equivalent target-conditioned contrast E[A|H=1]-E[A|H=0] is 1.0 and 0.0 respectively. These are alternative descriptions of the same observations, not additional independent evidence. Present an exact generator-level certificate separately from the measured finite-sample performance.

Recommended implementation addition: an audited script that projects each episode onto receiver-visible content, asserts semantic/placebo `Counter` equality per split/template, verifies the full factorial schedule, and emits hashes, multiplicities, and a compact equality table. Preserve that certificate in the repository. A two-panel figure can show (left) intervention response gap and (right) accuracy against H, making the specificity failure immediately visible.

## Assumptions and ways the claim can fail

- **Defined observation boundary:** raw episode/block IDs contain H. A detector given these, condition labels, hidden-bit fields, or sender prompts can distinguish conditions through unintended metadata. The theorem applies only to the declared receiver-side view.
- **Common response kernel:** identical experiment-owned prompts do not prove identical service-side context, routing, or time-dependent model behavior. Fresh sessions and randomized order support the assumption; uncaptured provider scaffolding remains a limitation.
- **Correct or controlled encoding:** arbitrary LLM sender errors can alter frame frequencies and break marginal equality. Here the saved semantic selections preserve the planned construction. The generator theorem applies exactly to its specified encoder.
- **Target-specific claim:** placebo messages still communicate their randomly selected frame. They can support a private convention and influence actions. Call them a negative control for *transmission of H*, not for all communication, code use, or covert intent.
- **Full crossing matters:** the optional eight-block half-fraction imposes I=H xor K xor N. In placebo this makes H=I xor K xor F, so the full message plus key leaks H despite F alone being independent. It was not used in the saved pilot/main runs. Do not use that fraction for future target-independence claims without redesign.
- **Finite data versus population:** unequal empirical scores can arise from independent noisy draws even when observation laws are equal. The proposition does not force every realized finite-sample AUROC to equal 0.5.
- **Scope:** nothing here proves that deployable monitoring of all covert channels is impossible, that any actual participant intended harm, or that private conventions are unauthorized.

## Primary-source connections and overlap

**PoPLi:** [Denamganai, 2026](https://arxiv.org/html/2610.37849v1), Definition 4, Proposition 5, Appendix B.1, and Section 5, already separates private-channel use from collusion and invokes indistinguishability for message-only monitors. Our construction applies that familiar equality-of-laws argument to the *receiver replay view*, because both positive and placebo have the same partner convention. It is a specificity calibration, not a refutation of PoPLi's own restricted claim.

**Decision-theoretic formalism:** [Anwar et al., v3](https://arxiv.org/html/2602.23163v3), Appendix A already compares semantic/syntactic channels; Appendix E.3 proves state-omission and finite-task-family incompleteness, and E.5 discusses capability-mismatch false positives. Their utility gap is explicitly target/task-relative. Our target-independent response statistic can alarm while their H-accuracy utility gap vanishes in placebo. Acknowledge this conceptual connection and avoid portraying the utility-gap framework as making our error.

**Semantic-channel prior work:** [Conceptual Steganography](https://arxiv.org/html/2605.26537v1) and [Hand and Brain](https://openreview.net/attachment?id=P7fHU7ZNFQ&name=pdf) establish preservation of high-level channels under ordinary paraphrase. Our intervention validation is a local instrument check, not a novel defense or first demonstration of that phenomenon.

Focused primary-paper review and targeted searches did not establish whether this exact placebo certificate has been published elsewhere. The mathematically honest claim is **a concrete, reproducible counterexample and calibration protocol**, with no priority assertion. NeurIPS-like formatting may improve clarity but does not confer conference acceptance or replace the hackathon's required content.
