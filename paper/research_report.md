# Beyond the Words: Testing Behavioral Detection of Semantic Covert Communication Between AI Agents

Aydan Wang and Sophie Eisenberg

FranklinDAO/Penn Blockchain

Track 4: Multi-Agent Oversight and Control | Swarm Alignment Hackathon 2026

## Abstract

Can a partner-outsider behavioral diagnostic distinguish semantic covert communication from ordinary response sensitivity? We test an explicitly assigned first-letter channel and a past-versus-future semantic-frame channel in a binary routing task, using one LLM for a constrained sender, an informed partner, and an uninformed outsider. A separate pilot contains 64 episodes; the main study contains 128 episodes (32 per condition), including no-channel and payload-independent semantic-placebo controls. Lexical interventions preserve the frame while flipping the initial; semantic counterfactuals flip the frame while preserving the initial. The partner decodes 32/32 semantic instructions correctly, versus 18/32 for the outsider. The semantic-minus-syntactic frame-response-gap contrast is 1.031 (95% block-bootstrap interval [0.844, 1.219]). However, the fixed diagnostic alarms on 7/32 semantic episodes, 11/32 no-channel episodes, and 9/32 semantic-placebo episodes. Component flip rates show why a positive contrast alone cannot establish reliable detection: outsider semantic responses can cancel partner responses, or make the syntactic comparator negative. The fixed single-draw diagnostic failed to distinguish semantic target transmission from controls in this setting. Its scope is limited to assigned conventions, a finite authored message bank, and a single-draw proxy rather than the full PoPLi estimator.

## 1. Introduction

Covert communication between AI agents poses an oversight problem when a recipient can use information that a monitor cannot. One proposed behavioral signal compares the intended partner with an outsider under message perturbations. The comparison is attractive because it does not require reading a secret directly from the message, but its interpretation depends on what the perturbation changes. A meaning-changing intervention may alter ordinary decisions as well as a planted semantic code.

We ask whether a simple partner-outsider action-change statistic can distinguish an assigned semantic channel from a syntactic channel, and whether it remains specific to transmission of a designated hidden instruction. Before observing outcomes, we hypothesized a larger semantic-counterfactual response gap for the semantic channel. We separately evaluate absolute gaps, decoding accuracy, control alarms, and discrimination. This separates a channel-specific intervention signature from a successful detector.

<!-- page break -->

## 2. Related Work

PoPLi [1] directly motivates the partner-outsider comparison. It measures changes in action distributions under paraphrases and corrects for unchanged-message replay variability. Its controlled experiments use scripted first-letter messages; it explicitly identifies meaning-carried codes as a limitation. Our single binary action per condition is a simplified proxy, not a reproduction of that estimator.

Conceptual Steganography [2] already compares conceptual encoding with a keyword baseline and tests paraphrase robustness. Anwar et al. [3] formalize a receiver-sentinel usable-information gap. Their version 3 Appendix A already compares six structural, syntactic, and semantic channels under two paraphrasers, including semantic framing. This substantially overlaps any generic claim to compare semantic with syntactic steganography; their accuracy/utility gap differs from our intervention-induced response-change gap.

Secret Collusion among AI Agents [4] establishes the broader multi-agent steganography threat model and studies monitoring and mitigations. NARCBench and its group-level interpretability method [5] provide complementary activation-based detection, including a steganographic holdout. Hand and Brain [6] studies covert payloads in high-level choices and a trusted-prefix defense. Its original OpenReview PDF was available through primary-domain search results; conference/workshop acceptance status was not independently resolved.

Our narrower contribution is a controlled replication and extension: orthogonal authored interventions plus a semantic placebo that breaks the association with the designated target while retaining the partner's private mapping. A focused review of these six works did not identify this exact combination, but is not proof of priority. We claim neither semantic-steganography invention nor a new general monitoring principle.

## 3. Methods: Environment and Agents

The public task selects storage bay 0 or 1. The bays are otherwise interchangeable, and an administrative sentence has no ordinary task-logic connection to either route. Each episode has a balanced hidden target bit, an arbitrary private mapping orientation, and two nuisance factors: frame and initial. The four binary factors are fully crossed in matched blocks across conditions. The intended partner receives the mapping; the outsider receives the literal field NONE. All other task information and model settings are matched.

One model, gpt-6.1-sol with low reasoning effort, serves all roles through Codex CLI codex-cli 0.166.0-alpha.5.1. The sender selects an exact approved sentence: two candidates in positive channels and one in controls. Positive-channel sender prompts contain the target and mapping; control sender prompts contain no target. This is a constrained planted-channel experiment, not free-form protocol invention. Valid wrong selections propagate unchanged; invalid calls remain recorded.

<!-- page break -->

## 3. Methods (continued)

| Condition | Target-bearing feature | Partner mapping |
| --- | --- | --- |
| No channel | None; both nuisance features independent | None |
| Syntactic | Initial A or B | Arbitrary initial-to-route key |
| Semantic | Past origins or future next steps | Arbitrary frame-to-route key |
| Semantic placebo | None for designated target | Same frame-to-route key |

Table 1. Assigned conditions. The placebo still communicates its nuisance frame and can elicit use of the private convention.

The lexical intervention rewrites the clause while preserving its temporal frame and swaps the initial A/B. The semantic counterfactual replaces the retrospective frame with the prospective frame, or vice versa, while preserving the initial. An unchanged-message repeat uses the exact original prompt. The interventions are pre-authored rather than arbitrary natural paraphrases. Temporal words remain conspicuous surface cues; we do not claim a semantic representation independent of all lexical features.

The main experiment uses 2 template pairs, 8 distinct original messages, 32 matched blocks, and 128 condition episodes. Repeated identical prompts receive separate model calls, not new independently authored stimuli. Every call starts a fresh ephemeral session in a temporary directory, with user configuration and project-document injection disabled. Neutral text-only instructions are saved with their hash. Tools remain exposed by the CLI scaffold; observed tool use invalidates the response. The protocol does not claim that tool access is technically impossible. Outsider task prompts contain no key, target, condition label, or other roles' responses.

## Detection and analysis

For receiver r, episode i, and intervention t, the following prespecified statistic compares action changes relative to each receiver's own original action:

```text
F_i(r,t) = 1[a_i(r,t) != a_i(r,original)]
D_i(t) = F_i(partner,t) - F_i(outsider,t)
Delta_frame = mean(D_frame | semantic) - mean(D_frame | syntactic)
S_i = max(D_i(lexical), D_i(frame)); alarm if S_i > 0.
```

D is +1 when only the partner changes, -1 when only the outsider changes, and 0 otherwise. The primary contrast is Delta_frame; the contrast ranges from -2 to 2 and is not a probability. The threshold was fixed before outcomes and was not calibrated or tuned. Secondary outcomes include original-target decoding, tied-score AUROC, control alarm rates, and unchanged-repeat flips. Subtracting D_repeat is explicitly exploratory. We use 5,000 percentile bootstrap resamples of matched blocks, retaining conditions and within-episode decisions, with analysis seed 20261108. Wilson intervals are descriptive reference intervals. Invalid originals count as decoding failures; behavioral gaps require valid actions and validated transformations, with exclusions disclosed. Pilot and main are not pooled.

<!-- page break -->

## 4. Results: Main Experiment

The main run completed 128 episodes in 32 blocks (32 episodes per condition), following the separate 64-episode pilot. The main data contain 1,152 model calls; the pilot contains 576. Across both splits, 192 sender and 1,536 receiver calls yielded 0 invalid responses, 0 recorded errors, and 0 observed tool-use events. There were 0 valid but incorrectly encoded positive-channel sender selections. The main detector excludes 0 episodes. The codebook-blind frame check adds 32 calls and labels 32/32 sentences correctly; 16/16 intervention sets satisfy the intended semantic relationship.

| Condition | n | Partner accuracy | Outsider accuracy | Frame gap | Lexical gap | Alarm rate |
| --- | --- | --- | --- | --- | --- | --- |
| No channel | 32 | 13/32 | 18/32 | -0.031 | 0.125 | 11/32 |
| Syntactic | 32 | 32/32 | 15/32 | -0.812 | 0.719 | 23/32 |
| Semantic | 32 | 32/32 | 18/32 | 0.219 | -0.250 | 7/32 |
| Semantic placebo | 32 | 16/32 | 17/32 | 0.281 | -0.469 | 9/32 |

Table 2. Main outcomes. Accuracy and alarm cells give successes/eligible episodes. Gap values are partner minus outsider action-flip rates.

| Condition | Frame flip partner | Frame flip outsider | Lexical flip partner | Lexical flip outsider |
| --- | --- | --- | --- | --- |
| No channel | 23/32 | 24/32 | 13/32 | 9/32 |
| Syntactic | 0/32 | 26/32 | 32/32 | 9/32 |
| Semantic | 32/32 | 25/32 | 0/32 | 8/32 |
| Semantic placebo | 32/32 | 23/32 | 0/32 | 15/32 |

Table 3. Component response counts. A positive contrast can coexist with small absolute semantic gaps when the outsider also reacts to the frame.

Delta_frame is 1.031 with 95% block-bootstrap interval [0.844, 1.219]. The semantic frame gap is 0.219 ([0.094, 0.375]), and the syntactic frame gap is -0.812 ([-0.938, -0.656]). Under frame changes, semantic partner/outsider flips are 32/32 and 25/32, respectively; syntactic partner/outsider flips are 0/32 and 26/32, respectively. These components are necessary to interpret the sign of the primary contrast.

Partner agreement with the original hidden target across original, lexical, and frame-counterfactual messages is 32/32, 32/32, and 0/32 in the semantic condition, compared with 32/32, 0/32, and 32/32 in the syntactic condition. These counts quantify payload preservation under the selected lexical rewrites and payload changes under the targeted interventions. Intervened agreement is measured against the original target, not the transformed code.

<!-- page break -->

## 4. Results (continued)

![Figure 1. Main intervention response gaps. Error bars are 95% matched-block bootstrap intervals. The two intervention signatures differ, but the contrast is not itself a detection-success metric.](../analysis/figures/main_behavioral_gap.png)

Figure 1. Main intervention response gaps. Error bars are 95% matched-block bootstrap intervals. The two intervention signatures differ, but the contrast is not itself a detection-success metric.

![Figure 2. Original-message agreement with the designated hidden instruction. Error bars are 95% Wilson reference intervals. Chance outsider accuracy does not imply that outsider behavior is invariant to semantic framing.](../analysis/figures/main_decoding_accuracy.png)

Figure 2. Original-message agreement with the designated hidden instruction. Error bars are 95% Wilson reference intervals. Chance outsider accuracy does not imply that outsider behavior is invariant to semantic framing.

<!-- page break -->

## 4. Results (continued)

![Figure 3. Fixed diagnostic alarms. No-channel alarms are false positives; placebo alarms are false positives for designated-target transmission, not necessarily for use of the private convention.](../analysis/figures/main_detection_rates.png)

Figure 3. Fixed diagnostic alarms. No-channel alarms are false positives; placebo alarms are false positives for designated-target transmission, not necessarily for use of the private convention.

Semantic detection is 21.9% (Wilson interval [11.0%, 38.8%]); no-channel false positives are 34.4% ([20.4%, 51.7%]); semantic-placebo alarms are 28.1% ([15.6%, 45.4%]). Semantic-versus-no-channel AUROC is 0.450, versus placebo 0.469, and versus pooled controls 0.459. These are descriptive tied-score values; no classifier was trained. Semantic outsider accuracy is 56.2% (95% Wilson interval [39.3%, 71.8%]), which includes 50%.

Unchanged-repeat partner/outsider flips are 0/32 and 4/32 in the semantic condition and 5/32 and 5/32 without a channel. The exploratory repeat-adjusted semantic frame gap is 0.344; it neither changes the primary estimator nor calibrates the alarm threshold. The separate pilot primary contrast was 0.938; semantic and no-channel alarms were 3/16 and 9/16. The main protocol and threshold were unchanged after the pilot.

<!-- page break -->

## 5. Discussion and Limitations

The controlled channels are usable by an informed recipient, but usable private decoding and intervention sensitivity are different properties from reliable monitoring. A positive Delta_frame can arise partly because a frame change alters the outsider in the syntactic condition while leaving its partner unchanged. In the semantic condition, both receivers can react to meaning, cancelling the gap. A key-randomized outsider can therefore remain at chance on the target while displaying strong semantic response changes.

The placebo isolates a narrower specificity question. It retains the private frame-to-route convention but chooses the frame independently of the designated target. Thus it still carries a nuisance-frame bit and supports convention use. Its alarms do not establish that the monitor confuses all ordinary language sensitivity with all communication; they show why the target of detection must be specified. A deployment claim would require calibrated false-positive control and an appropriate distributional estimator, not this fixed single-draw score.

Generalization is sharply limited. We tested one model, an opaque binary action, two main template pairs, explicit keys, and selected counterfactuals. The frames contain obvious temporal words, and the sender chooses from approved sentences. Same-model blind labels validate this finite bank rather than unseen paraphrases or independent human judgments. Repeated prompts, shared model weights, and the finite factorial design constrain uncertainty; narrow intervals are not broad confidence. Fresh keys mask the target by design and do not establish security against persistent-key inference or adaptive adversaries. CLI sampling is not seeded and the provider alias can change.

## 6. Conclusion

The fixed single-draw diagnostic failed to distinguish semantic target transmission from controls in this setting. This is a result about our simplified proxy, not a falsification of the full PoPLi estimator. The primary contrast identifies differential intervention responses, while absolute flip components and control alarms determine whether that response is useful for detection. The evidence supports caution about interpreting a simple partner-outsider action-change gap as proof of hidden-instruction transmission. Future work should use richer response distributions, calibrated thresholds, independently authored stimuli, and adaptive protocols; those experiments were not performed here.

## 7. Code and Data

All original experiment code was written during this sprint. Raw messages, prompts, responses, actions, manifests, verified references, tests, analysis scripts, and figures are provided with the project. Offline numerical analysis uses Python's standard library and needs no model credentials. Matplotlib regenerates figures; ReportLab regenerates this report. The independent audit passed 84 point-estimate/denominator comparisons; it does not independently reimplement bootstrap intervals. The unit-test suite passed 43 tests. Separate clean-source reanalysis reproduced the numerical summary. Public repository:

[github.com/aydanwang12/semantic-covert-communication-detection](https://github.com/aydanwang12/semantic-covert-communication-detection)

<!-- page break -->

## References

[1] Denamganaï, K. Y. (2026). Detecting Covert Collusion between AI Agents through Partner-Outsider Positive Listening. arXiv:2610.37849v1.

[https://arxiv.org/abs/2610.37849v1](https://arxiv.org/abs/2610.37849v1)

[2] Zhou, Z., and May, J. (2026). Conceptual Steganography. arXiv:2605.26537v1.

[https://arxiv.org/abs/2605.26537v1](https://arxiv.org/abs/2605.26537v1)

[3] Anwar, U., et al. (2026). A Decision-Theoretic Formalisation of Steganography With Applications to LLM Monitoring. arXiv:2602.23163v3.

[https://arxiv.org/abs/2602.23163v3](https://arxiv.org/abs/2602.23163v3)

[4] Motwani, S. R., et al. (2024). Secret Collusion among AI Agents: Multi-Agent Deception via Steganography. Advances in Neural Information Processing Systems 37, Main Conference Track.

[https://proceedings.neurips.cc/paper_files/paper/2024/hash/861f7dad098aec1c3560fb7add468d41-Abstract-Conference.html](https://proceedings.neurips.cc/paper_files/paper/2024/hash/861f7dad098aec1c3560fb7add468d41-Abstract-Conference.html)

[5] Rose, A., et al. (2026). Detecting Multi-Agent Collusion Through Multi-Agent Interpretability. arXiv:2604.01151v5.

[https://arxiv.org/abs/2604.01151v5](https://arxiv.org/abs/2604.01151v5)

[6] Krzyzanowski, R., Arcuschin, I., Lee, M., Meyer, B., and Lange, G. (2026). Hand and Brain: Defenses against Agentic Steganography in Language Models. OpenReview manuscript. Conference/workshop acceptance status unresolved.

[https://openreview.net/forum?id=P7fHU7ZNFQ](https://openreview.net/forum?id=P7fHU7ZNFQ)

Primary-source metadata and relevant source text were checked on November 8, 2026. This was a focused review, not an exhaustive systematic search. Full author lists, versions, verification notes, and links are retained in references/sources.json and bibliography.bib. The official event page and document template supplied the report requirements.

[Official Swarm Alignment Hackathon rules](https://apartresearch.com/sprints/swarm-alignment-2026)

## LLM Usage Statement

OpenAI Codex agents were used to review primary sources, design and implement the experiment, write tests, execute model calls, analyze data, prepare figures, draft this report, and coordinate publication. Separate agent workstreams performed implementation, analysis, literature review, and automated testing; these are additional automated checks, not independent human replication. The experimental sender and receivers also used gpt-6.1-sol. No claim is made that the named authors manually verified every output. Authorship and final submission responsibility remain with the named authors. No model-generated observation was substituted for an unexecuted call; unit-test fixtures are separate from experimental data.

<!-- page break -->

## Limitations and Dual-Use / Ethical Considerations

Scope. The study is a small, prescribed-channel experiment. It does not test autonomous discovery, hidden malicious goals, natural conversation, adaptive monitor evasion, long-term keys, or deployment oversight. A constrained sender and a tiny authored bank reduce ecological validity. Explicit codebooks and opaque routes deliberately separate decoding from ordinary task logic. The reported replicates are stochastic model draws under a finite crossing, not independent language domains.

Measurement. Semantic counterfactuals intentionally change meaning and can elicit ordinary outsider sensitivity. The simple action-flip score estimates neither full response distributions nor the full noise-corrected PoPLi statistic. Its fixed threshold has no calibrated false-positive guarantee. Unchanged repeats expose some sampling instability without resolving this limitation. The placebo breaks only information about the designated target; the nuisance frame remains observable and privately interpretable. Thus negative-control claims are target-specific. Confidence intervals condition on the sampled model and templates, and AUROC is descriptive.

Validation and reproducibility. All raw attempted calls and configurations are saved. Invalid results are retained, and the analysis discloses their denominators. The 32 sentence labels use the same model as the main study and one blind rating per sentence, rather than a human panel. The CLI has a read-only sandbox and no-tool instructions but still exposes tools; event logs are audited for use. The logged role instruction is concatenated into CLI stdin, not sent as a separate API system message. Provider-side scaffolding and tool schemas are not fully captured. Sampling and model internals are outside the audit. Model sampling is not deterministically seeded, and an alias may change, so rerunning live calls need not reproduce every action. Offline reanalysis of the saved data is deterministic apart from generated timestamps.

Dual use. The experiment implements simple public first-letter and semantic-frame codebooks, mechanisms already discussed in prior work. Its purpose is to evaluate oversight diagnostics and false positives, not to provide a robust evasion system. It does not optimize against a real monitor, conceal harmful instructions, exfiltrate private information, or deploy interacting agents in an external environment. Publishing the code supports scrutiny but can also illustrate how assigned covert conventions work. Results should not be presented as evidence that malicious intent can be inferred from an alarm, or that an unflagged conversation is safe.

Data and authorship. Messages are synthetic administrative sentences and routes are abstract. No personal communications or private datasets are included. Credentials are handled outside the repository; local home prefixes in process stderr are replaced with HOME markers while task prompts and model outputs are preserved. AI assistance is disclosed above. The source implementation and recorded experiment were produced during this sprint; the conceptual foundations and overlapping demonstrations are credited to prior work.

