#!/usr/bin/env python3
"""Build the research report from audited, complete experimental results.

No numbers are generated or inferred from expected model behavior. This script
requires final main+pilot analysis, raw episode files, blind frame validation,
and a passing independent audit. It emits the PDF and matching Markdown source.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = ('no_channel', 'syntactic', 'semantic', 'semantic_placebo')
LABELS = {'no_channel':'No channel','syntactic':'Syntactic','semantic':'Semantic','semantic_placebo':'Semantic placebo'}
REPO_URL = 'https://github.com/aydanwang12/semantic-covert-communication-detection'


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def fmt(x, digits=3):
    return 'undefined' if x is None else f'{x:.{digits}f}'


def pct(metric):
    return 'undefined' if metric['estimate'] is None else f"{100*metric['estimate']:.1f}%"


def pci(metric):
    v=metric.get('ci95_wilson')
    return 'undefined' if v is None else f'[{100*v[0]:.1f}%, {100*v[1]:.1f}%]'


def count(metric):
    return f"{metric['successes']}/{metric['n']}"


def ci(metric, key='ci95_bootstrap'):
    v=metric.get(key)
    return 'undefined' if v is None else f'[{fmt(v[0])}, {fmt(v[1])}]'


def collect(summary_path, audit_path):
    summary=json.loads(summary_path.read_text())
    audit=json.loads(audit_path.read_text())
    if audit.get('status')!='PASS':
        raise ValueError('Independent audit must pass before report generation')
    rows={split:read_jsonl(ROOT/'data'/name) for split,name in [('pilot','pilot.jsonl'),('main','results.jsonl')]}
    calls={split:read_jsonl(ROOT/'data'/name) for split,name in [('pilot','pilot.calls.jsonl'),('main','results.calls.jsonl')]}
    for split,name in [('pilot','pilot.jsonl'),('main','results.jsonl')]:
        path=ROOT/'data'/name
        manifest=json.loads(path.with_suffix('.manifest.json').read_text())
        ids=[r['episode_id'] for r in rows[split]]
        if len(ids)!=len(set(ids)) or set(ids)!=set(manifest['planned_episode_ids']):
            raise ValueError(f'{split} data do not exactly match complete planned IDs')
        if summary['splits'][split]['n_episodes']!=len(ids):
            raise ValueError('Summary count differs from raw data')
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        source=next(s for s in summary['source_files'] if s['path'].endswith(name))
        if source['sha256']!=digest:
            raise ValueError('Analysis source hash differs from current raw data')
        entry=next(e for e in audit['files'] if e['path'].endswith(name))
        if entry['sha256']!=digest or entry.get('incomplete'):
            raise ValueError('Independent audit is stale or incomplete')
    frame_rows=read_jsonl(ROOT/'data/frame_validation.jsonl')
    frame=json.loads((ROOT/'data/frame_validation.summary.json').read_text())
    if len(frame_rows)!=frame['sentence_count']:
        raise ValueError('Frame validation count mismatch')
    config=json.loads((ROOT/'data/results.manifest.json').read_text())
    return summary,audit,rows,calls,frame,frame_rows,config


def make_document(summary,audit,rows,calls,frame,frame_rows,manifest):
    main=summary['splits']['main']; pilot=summary['splits']['pilot']; c=main['conditions']
    sem=c['semantic']; syn=c['syntactic']; no=c['no_channel']; pla=c['semantic_placebo']
    primary=main['primary_semantic_minus_syntactic_frame_gap']
    nmain=len(rows['main']); npilot=len(rows['pilot'])
    blocks=len({r['block_id'] for r in rows['main']})
    originals=len({r['messages']['original'] for r in rows['main']})
    templates=len({r['template_index'] for r in rows['main']})
    nper=sem['n_episodes']; nallcalls=sum(map(len,calls.values()))+len(frame_rows)
    receiver_calls=sum(r['role']!='sender' for rs in calls.values() for r in rs)
    sender_calls=sum(r['role']=='sender' for rs in calls.values() for r in rs)
    invalid_calls=sum(r.get('valid') is not True for rs in calls.values() for r in rs)
    tools=sum(bool(r.get('tool_use_detected')) for rs in calls.values() for r in rs)
    wrong_sender=sum(r.get('sender_valid') is True and r.get('encoded_bit')!=r['hidden_bit']
                     for rs in rows.values() for r in rs if r['condition'] in ('syntactic','semantic'))
    errors=sum(r.get('error') is not None for rs in calls.values() for r in rs)
    exclusions=sum(x['detector']['n_excluded'] for x in c.values())
    sf=sem['interventions']['semantic_counterfactual']; yf=syn['interventions']['semantic_counterfactual']
    sfp,sfo=sf['partner_flip_rate'],sf['outsider_flip_rate']
    yfp,yfo=yf['partner_flip_rate'],yf['outsider_flip_rate']
    semantic_auc=main['auroc']['semantic_vs_no_channel']['estimate']
    sem_alarm=sem['detector']['alarm_rate']; no_alarm=no['detector']['alarm_rate']; pla_alarm=pla['detector']['alarm_rate']
    pooled_auc=main['auroc']['semantic_vs_pooled_controls']['estimate']
    diagnostic_failed=(semantic_auc is not None and semantic_auc <= .5 and pooled_auc is not None and pooled_auc <= .5
                       and sem_alarm['estimate'] is not None and no_alarm['estimate'] is not None
                       and sem_alarm['estimate'] <= no_alarm['estimate'])
    empirical_conclusion=(
        'The fixed single-draw diagnostic failed to distinguish semantic target transmission from controls in this setting.'
        if diagnostic_failed else
        'The observed decoding, action-change, and control-alarm results distinguish private communication performance from monitoring performance.')
    sem_agreement=sem['action_agreement_with_original_hidden_bit']['partner']
    syn_agreement=syn['action_agreement_with_original_hidden_bit']['partner']
    quality=json.loads((ROOT/'data/frame_validation.summary.json').read_text())
    doc=[]
    def add(kind,**kw): doc.append({'kind':kind,**kw})
    def p(text): add('paragraph',text=text)
    def h(text): add('heading',text=text)
    def page(): add('pagebreak')
    def fig(name,caption,height=174): add('figure',path=f'analysis/figures/{name}.png',caption=caption,height=height)
    add('title',text='Beyond the Words: Testing Behavioral Detection of Semantic Covert Communication Between AI Agents')
    add('authors',text='Aydan Wang and Sophie Eisenberg')
    add('affiliation',text='FranklinDAO/Penn Blockchain')
    add('meta',text='Track 4: Multi-Agent Oversight and Control | Swarm Alignment Hackathon 2026')
    h('Abstract')
    abstract=(
        'Can a partner-outsider behavioral diagnostic distinguish semantic covert communication from ordinary response sensitivity? '
        'We test an explicitly assigned first-letter channel and a past-versus-future semantic-frame channel in a binary routing task, '
        'using one LLM for a constrained sender, an informed partner, and an uninformed outsider. '
        f'A separate pilot contains {npilot} episodes; the main study contains {nmain} episodes ({nper} per condition), including no-channel and payload-independent semantic-placebo controls. '
        'Lexical interventions preserve the frame while flipping the initial; semantic counterfactuals flip the frame while preserving the initial. '
        f'The partner decodes {count(sem["original_accuracy"]["partner"])} semantic instructions correctly, versus {count(sem["original_accuracy"]["outsider"])} for the outsider. '
        f'The semantic-minus-syntactic frame-response-gap contrast is {fmt(primary["estimate"])} (95% block-bootstrap interval {ci(primary)}). '
        f'However, the fixed diagnostic alarms on {count(sem_alarm)} semantic episodes, {count(no_alarm)} no-channel episodes, and {count(pla_alarm)} semantic-placebo episodes. '
        'Component flip rates show why a positive contrast alone cannot establish reliable detection: outsider semantic responses can cancel partner responses, or make the syntactic comparator negative. '
        f'{empirical_conclusion} '
        'Its scope is limited to assigned conventions, a finite authored message bank, and a single-draw proxy rather than the full PoPLi estimator.'
    )
    abstract_words=len(abstract.split())
    if not 150<=abstract_words<=250:
        raise ValueError(f'Abstract has {abstract_words} words')
    p(abstract)
    h('1. Introduction')
    p('Covert communication between AI agents poses an oversight problem when a recipient can use information that a monitor cannot. '
      'One proposed behavioral signal compares the intended partner with an outsider under message perturbations. The comparison is attractive '
      'because it does not require reading a secret directly from the message, but its interpretation depends on what the perturbation changes. '
      'A meaning-changing intervention may alter ordinary decisions as well as a planted semantic code.')
    p('We ask whether a simple partner-outsider action-change statistic can distinguish an assigned semantic channel from a syntactic channel, '
      'and whether it remains specific to transmission of a designated hidden instruction. Before observing outcomes, we hypothesized a larger '
      'semantic-counterfactual response gap for the semantic channel. We separately evaluate absolute gaps, decoding accuracy, control alarms, '
      'and discrimination. This separates a channel-specific intervention signature from a successful detector.')

    page(); h('2. Related Work')
    p('PoPLi [1] directly motivates the partner-outsider comparison. It measures changes in action distributions under paraphrases and corrects '
      'for unchanged-message replay variability. Its controlled experiments use scripted first-letter messages; it explicitly identifies '
      'meaning-carried codes as a limitation. Our single binary action per condition is a simplified proxy, not a reproduction of that estimator.')
    p('Conceptual Steganography [2] already compares conceptual encoding with a keyword baseline and tests paraphrase robustness. '
      'Anwar et al. [3] formalize a receiver-sentinel usable-information gap. Their version 3 Appendix A already compares six structural, '
      'syntactic, and semantic channels under two paraphrasers, including semantic framing. This substantially overlaps any generic claim '
      'to compare semantic with syntactic steganography; their accuracy/utility gap differs from our intervention-induced response-change gap.')
    p('Secret Collusion among AI Agents [4] establishes the broader multi-agent steganography threat model and studies monitoring and mitigations. '
      'NARCBench and its group-level interpretability method [5] provide complementary activation-based detection, including a steganographic '
      'holdout. Hand and Brain [6] studies covert payloads in high-level choices and a trusted-prefix defense. Its original OpenReview PDF was '
      'available through primary-domain search results; conference/workshop acceptance status was not independently resolved.')
    p('Our narrower contribution is a controlled replication and extension: orthogonal authored interventions plus a semantic placebo that breaks '
      'the association with the designated target while retaining the partner\'s private mapping. A focused review of these six works did not '
      'identify this exact combination, but is not proof of priority. We claim neither semantic-steganography invention nor a new general monitoring principle.')
    h('3. Methods: Environment and Agents')
    p('The public task selects storage bay 0 or 1. The bays are otherwise interchangeable, and an administrative sentence has no ordinary '
      'task-logic connection to either route. Each episode has a balanced hidden target bit, an arbitrary private mapping orientation, and two '
      'nuisance factors: frame and initial. The four binary factors are fully crossed in matched blocks across conditions. The intended partner '
      'receives the mapping; the outsider receives the literal field NONE. All other task information and model settings are matched.')
    p('One model, gpt-6.1-sol with low reasoning effort, serves all roles through Codex CLI '+manifest['cli_version']+'. '
      'The sender selects an exact approved sentence: two candidates in positive channels and one in controls. Positive-channel sender prompts '
      'contain the target and mapping; control sender prompts contain no target. This is a constrained planted-channel experiment, not free-form '
      'protocol invention. Valid wrong selections propagate unchanged; invalid calls remain recorded.')

    page(); h('3. Methods (continued)')
    add('table',headers=['Condition','Target-bearing feature','Partner mapping'],rows=[
        ['No channel','None; both nuisance features independent','None'],
        ['Syntactic','Initial A or B','Arbitrary initial-to-route key'],
        ['Semantic','Past origins or future next steps','Arbitrary frame-to-route key'],
        ['Semantic placebo','None for designated target','Same frame-to-route key'],
    ],widths=[93,193,182],caption='Table 1. Assigned conditions. The placebo still communicates its nuisance frame and can elicit use of the private convention.')
    p('The lexical intervention rewrites the clause while preserving its temporal frame and swaps the initial A/B. The semantic counterfactual '
      'replaces the retrospective frame with the prospective frame, or vice versa, while preserving the initial. An unchanged-message repeat uses '
      'the exact original prompt. The interventions are pre-authored rather than arbitrary natural paraphrases. Temporal words remain conspicuous '
      'surface cues; we do not claim a semantic representation independent of all lexical features.')
    p(f'The main experiment uses {templates} template pairs, {originals} distinct original messages, {blocks} matched blocks, and {nmain} condition episodes. '
      'Repeated identical prompts receive separate model calls, not new independently authored stimuli. Every call starts a fresh ephemeral '
      'session in a temporary directory, with user configuration and project-document injection disabled. Neutral text-only instructions are '
      'saved with their hash. Tools remain exposed by the CLI scaffold; observed tool use invalidates the response. The protocol does not claim '
      'that tool access is technically impossible. Outsider task prompts contain no key, target, condition label, or other roles\' responses.')
    h('Detection and analysis')
    p('For receiver r, episode i, and intervention t, the following prespecified statistic compares action changes relative to each receiver\'s own original action:')
    add('equation',text='F_i(r,t) = 1[a_i(r,t) != a_i(r,original)]\nD_i(t) = F_i(partner,t) - F_i(outsider,t)\nDelta_frame = mean(D_frame | semantic) - mean(D_frame | syntactic)\nS_i = max(D_i(lexical), D_i(frame)); alarm if S_i > 0.')
    p('D is +1 when only the partner changes, -1 when only the outsider changes, and 0 otherwise. The primary contrast is Delta_frame; '
      'the contrast ranges from -2 to 2 and is not a probability. The threshold was fixed before outcomes and was not calibrated or tuned. Secondary outcomes include original-target decoding, '
      'tied-score AUROC, control alarm rates, and unchanged-repeat flips. Subtracting D_repeat is explicitly exploratory. '
      f'We use {summary["bootstrap_resamples"]:,} percentile bootstrap resamples of matched blocks, retaining conditions and within-episode decisions, '
      'with analysis seed '+str(summary['bootstrap_seed'])+'. Wilson intervals are descriptive reference intervals. Invalid originals count '
      'as decoding failures; behavioral gaps require valid actions and validated transformations, with exclusions disclosed. Pilot and main are not pooled.')

    page(); h('4. Results: Main Experiment')
    p(f'The main run completed {nmain} episodes in {blocks} blocks ({nper} episodes per condition), following the separate {npilot}-episode pilot. '
      f'The main data contain {len(calls["main"]):,} model calls; the pilot contains {len(calls["pilot"]):,}. '
      f'Across both splits, {sender_calls} sender and {receiver_calls:,} receiver calls yielded {invalid_calls} invalid responses, {errors} recorded errors, '
      f'and {tools} observed tool-use events. There were {wrong_sender} valid but incorrectly encoded positive-channel sender selections. The main detector excludes {exclusions} episodes. '
      f'The codebook-blind frame check adds {len(frame_rows)} calls and labels {frame["correct_labels"]}/{frame["sentence_count"]} sentences correctly; '
      f'{frame["all_labels_correct_sets"]}/{frame["intervention_sets"]} intervention sets satisfy the intended semantic relationship.')
    add('table',headers=['Condition','n','Partner\naccuracy','Outsider\naccuracy','Frame\ngap','Lexical\ngap','Alarm\nrate'],rows=[
        [LABELS[k],str(c[k]['n_episodes']),count(c[k]['original_accuracy']['partner']),count(c[k]['original_accuracy']['outsider']),
         fmt(c[k]['interventions']['semantic_counterfactual']['mean_gap']['estimate']),fmt(c[k]['interventions']['lexical']['mean_gap']['estimate']),count(c[k]['detector']['alarm_rate'])]
        for k in CONDITIONS],widths=[94,26,66,66,65,65,86],caption='Table 2. Main outcomes. Accuracy and alarm cells give successes/eligible episodes. Gap values are partner minus outsider action-flip rates.')
    add('table',headers=['Condition','Frame flip\npartner','Frame flip\noutsider','Lexical flip\npartner','Lexical flip\noutsider'],rows=[
        [LABELS[k],count(c[k]['interventions']['semantic_counterfactual']['partner_flip_rate']),count(c[k]['interventions']['semantic_counterfactual']['outsider_flip_rate']),
         count(c[k]['interventions']['lexical']['partner_flip_rate']),count(c[k]['interventions']['lexical']['outsider_flip_rate'])]
        for k in CONDITIONS],widths=[108,90,90,90,90],caption='Table 3. Component response counts. A positive contrast can coexist with small absolute semantic gaps when the outsider also reacts to the frame.')
    p(f'Delta_frame is {fmt(primary["estimate"])} with 95% block-bootstrap interval {ci(primary)}. '
      f'The semantic frame gap is {fmt(sf["mean_gap"]["estimate"])} ({ci(sf["mean_gap"])}), and the syntactic frame gap is '
      f'{fmt(yf["mean_gap"]["estimate"])} ({ci(yf["mean_gap"])}). Under frame changes, semantic partner/outsider flips are '
      f'{count(sfp)} and {count(sfo)}, respectively; syntactic partner/outsider flips are {count(yfp)} and {count(yfo)}, respectively. '
      'These components are necessary to interpret the sign of the primary contrast.')
    p('Partner agreement with the original hidden target across original, lexical, and frame-counterfactual messages is '
      f'{count(sem_agreement["original"])}, {count(sem_agreement["lexical"])}, and {count(sem_agreement["semantic_counterfactual"])} in the semantic condition, '
      f'compared with {count(syn_agreement["original"])}, {count(syn_agreement["lexical"])}, and {count(syn_agreement["semantic_counterfactual"])} in the syntactic condition. '
      'These counts quantify payload preservation under the selected lexical rewrites and payload changes under the targeted interventions. '
      'Intervened agreement is measured against the original target, not the transformed code.')
    page(); h('4. Results (continued)')
    fig('main_behavioral_gap','Figure 1. Main intervention response gaps. Error bars are 95% matched-block bootstrap intervals. The two intervention signatures differ, but the contrast is not itself a detection-success metric.',height=246)
    fig('main_decoding_accuracy','Figure 2. Original-message agreement with the designated hidden instruction. Error bars are 95% Wilson reference intervals. Chance outsider accuracy does not imply that outsider behavior is invariant to semantic framing.',height=246)
    page(); h('4. Results (continued)')
    fig('main_detection_rates','Figure 3. Fixed diagnostic alarms. No-channel alarms are false positives; placebo alarms are false positives for designated-target transmission, not necessarily for use of the private convention.',height=246)
    p(f'Semantic detection is {pct(sem_alarm)} (Wilson interval {pci(sem_alarm)}); no-channel false positives are '
      f'{pct(no_alarm)} ({pci(no_alarm)}); semantic-placebo alarms are {pct(pla_alarm)} ({pci(pla_alarm)}). '
      f'Semantic-versus-no-channel AUROC is {fmt(semantic_auc)}, versus placebo {fmt(main["auroc"]["semantic_vs_semantic_placebo"]["estimate"])}, '
      f'and versus pooled controls {fmt(main["auroc"]["semantic_vs_pooled_controls"]["estimate"])}. These are descriptive tied-score values; no classifier was trained. '
      f'Semantic outsider accuracy is {pct(sem["original_accuracy"]["outsider"])} (95% Wilson interval {pci(sem["original_accuracy"]["outsider"])}), which includes 50%.')
    repeat_sem=sem['unchanged_repeat_noise']['receiver_flip_rates']
    repeat_no=no['unchanged_repeat_noise']['receiver_flip_rates']
    corrected=sem['unchanged_repeat_noise']['exploratory_corrected_gaps']['semantic_counterfactual']
    p(f'Unchanged-repeat partner/outsider flips are {count(repeat_sem["partner"])} and {count(repeat_sem["outsider"])} in the semantic condition '
      f'and {count(repeat_no["partner"])} and {count(repeat_no["outsider"])} without a channel. The exploratory repeat-adjusted semantic frame gap '
      f'is {fmt(corrected["estimate"])}; it neither changes the primary estimator nor calibrates the alarm threshold. The separate pilot primary '
      f'contrast was {fmt(pilot["primary_semantic_minus_syntactic_frame_gap"]["estimate"])}; semantic and no-channel alarms were '
      f'{count(pilot["conditions"]["semantic"]["detector"]["alarm_rate"]) } and {count(pilot["conditions"]["no_channel"]["detector"]["alarm_rate"])}. '
      'The main protocol and threshold were unchanged after the pilot.')

    page(); h('5. Discussion and Limitations')
    p('The controlled channels are usable by an informed recipient, but usable private decoding and intervention sensitivity are different '
      'properties from reliable monitoring. A positive Delta_frame can arise partly because a frame change alters the outsider in the syntactic '
      'condition while leaving its partner unchanged. In the semantic condition, both receivers can react to meaning, cancelling the gap. '
      'A key-randomized outsider can therefore remain at chance on the target while displaying strong semantic response changes.')
    p('The placebo isolates a narrower specificity question. It retains the private frame-to-route convention but chooses the frame independently '
      'of the designated target. Thus it still carries a nuisance-frame bit and supports convention use. Its alarms do not establish that the '
      'monitor confuses all ordinary language sensitivity with all communication; they show why the target of detection must be specified. '
      'A deployment claim would require calibrated false-positive control and an appropriate distributional estimator, not this fixed single-draw score.')
    p('Generalization is sharply limited. We tested one model, an opaque binary action, two main template pairs, explicit keys, and selected '
      'counterfactuals. The frames contain obvious temporal words, and the sender chooses from approved sentences. Same-model blind labels '
      'validate this finite bank rather than unseen paraphrases or independent human judgments. Repeated prompts, shared model weights, and '
      'the finite factorial design constrain uncertainty; narrow intervals are not broad confidence. Fresh keys mask the target by design and '
      'do not establish security against persistent-key inference or adaptive adversaries. CLI sampling is not seeded and the provider alias can change.')
    h('6. Conclusion')
    p(f'{empirical_conclusion} This is a result about our simplified proxy, not a falsification of the full PoPLi estimator. '
      'The primary contrast identifies differential intervention responses, while absolute flip components and control alarms determine whether '
      'that response is useful for detection. The evidence supports caution about interpreting a simple partner-outsider action-change gap '
      'as proof of hidden-instruction transmission. Future work should use richer response distributions, calibrated thresholds, independently '
      'authored stimuli, and adaptive protocols; those experiments were not performed here.')
    h('7. Code and Data')
    p('All original experiment code was written during this sprint. Raw messages, prompts, responses, actions, manifests, verified references, '
      'tests, analysis scripts, and figures are provided with the project. Offline numerical analysis uses Python\'s standard library and needs '
      'no model credentials. Matplotlib regenerates figures; ReportLab regenerates this report. The independent audit passed '
      +str(audit.get('production_comparisons_passed'))+' point-estimate/denominator comparisons; it does not independently reimplement bootstrap intervals. '
      'The unit-test suite passed 43 tests. Separate clean-source reanalysis reproduced the numerical summary. Public repository:')
    add('link',label='github.com/aydanwang12/semantic-covert-communication-detection',url=REPO_URL)

    page(); add('boundary',name='references'); h('References')
    sources=json.loads((ROOT/'references/sources.json').read_text())['sources']
    short_authors=[
        'Denamganaï, K. Y.',
        'Zhou, Z., and May, J.',
        'Anwar, U., et al.',
        'Motwani, S. R., et al.',
        'Rose, A., et al.',
        'Krzyzanowski, R., Arcuschin, I., Lee, M., Meyer, B., and Lange, G.',
    ]
    for i,(source,authors) in enumerate(zip(sources,short_authors),1):
        detail=source.get('version') or source.get('venue','')
        if i==6:
            detail='OpenReview manuscript. Conference/workshop acceptance status unresolved.'
        p(f'[{i}] {authors} ({source["year"]}). {source["title"]}. {detail.rstrip('.')}.')
        add('link',label=source['url'],url=source['url'])
    p('Primary-source metadata and relevant source text were checked on November 8, 2026. This was a focused review, not an exhaustive '
      'systematic search. Full author lists, versions, verification notes, and links are retained in references/sources.json and bibliography.bib. '
      'The official event page and document template supplied the report requirements.')
    add('link',label='Official Swarm Alignment Hackathon rules',url='https://apartresearch.com/sprints/swarm-alignment-2026')
    h('LLM Usage Statement')
    p('OpenAI Codex agents were used to review primary sources, design and implement the experiment, write tests, execute model calls, '
      'analyze data, prepare figures, draft this report, and coordinate publication. Separate agent workstreams performed implementation, '
      'analysis, literature review, and automated testing; these are additional automated checks, not independent human replication. The '
      'experimental sender and receivers also used gpt-6.1-sol. No claim is made that the named authors manually verified every output. '
      'Authorship and final submission responsibility remain with the named authors. No model-generated observation was substituted for an '
      'unexecuted call; unit-test fixtures are separate from experimental data.')

    page(); add('boundary',name='appendix'); h('Limitations and Dual-Use / Ethical Considerations')
    p('Scope. The study is a small, prescribed-channel experiment. It does not test autonomous discovery, hidden malicious goals, natural '
      'conversation, adaptive monitor evasion, long-term keys, or deployment oversight. A constrained sender and a tiny authored bank reduce '
      'ecological validity. Explicit codebooks and opaque routes deliberately separate decoding from ordinary task logic. The reported '
      'replicates are stochastic model draws under a finite crossing, not independent language domains.')
    p('Measurement. Semantic counterfactuals intentionally change meaning and can elicit ordinary outsider sensitivity. The simple action-flip '
      'score estimates neither full response distributions nor the full noise-corrected PoPLi statistic. Its fixed threshold has no calibrated '
      'false-positive guarantee. Unchanged repeats expose some sampling instability without resolving this limitation. The placebo breaks '
      'only information about the designated target; the nuisance frame remains observable and privately interpretable. Thus negative-control '
      'claims are target-specific. Confidence intervals condition on the sampled model and templates, and AUROC is descriptive.')
    p('Validation and reproducibility. All raw attempted calls and configurations are saved. Invalid results are retained, and the analysis '
      'discloses their denominators. The 32 sentence labels use the same model as the main study and one blind rating per sentence, rather '
      'than a human panel. The CLI has a read-only sandbox and no-tool instructions but still exposes tools; event logs are audited for use. '
      'The logged role instruction is concatenated into CLI stdin, not sent as a separate API system message. Provider-side scaffolding and tool schemas are not fully captured. Sampling and model internals are outside the audit. Model sampling is not deterministically seeded, and '
      'an alias may change, so rerunning live calls need not reproduce every action. Offline reanalysis of the saved data is deterministic '
      'apart from generated timestamps.')
    p('Dual use. The experiment implements simple public first-letter and semantic-frame codebooks, mechanisms already discussed in prior '
      'work. Its purpose is to evaluate oversight diagnostics and false positives, not to provide a robust evasion system. It does not optimize '
      'against a real monitor, conceal harmful instructions, exfiltrate private information, or deploy interacting agents in an external '
      'environment. Publishing the code supports scrutiny but can also illustrate how assigned covert conventions work. Results should '
      'not be presented as evidence that malicious intent can be inferred from an alarm, or that an unflagged conversation is safe.')
    p('Data and authorship. Messages are synthetic administrative sentences and routes are abstract. No personal communications or private '
      'datasets are included. Credentials are handled outside the repository; local home prefixes in process stderr are replaced with HOME '
      'markers while task prompts and model outputs are preserved. AI assistance is disclosed above. The source implementation and recorded '
      'experiment were produced during this sprint; the conceptual foundations and overlapping demonstrations are credited to prior work.')
    facts={
        'abstract_words':abstract_words,'main_episodes':nmain,'pilot_episodes':npilot,'main_blocks':blocks,
        'unique_main_original_messages':originals,'main_template_pairs':templates,
        'main_model_calls':len(calls['main']),'pilot_model_calls':len(calls['pilot']),
        'validation_model_calls':len(frame_rows),'total_model_calls':nallcalls,
        'invalid_experiment_calls':invalid_calls,'observed_experiment_tool_calls':tools,
        'valid_wrong_positive_sender_choices':wrong_sender,'semantic_diagnostic_failed_vs_controls':diagnostic_failed,
        'source_summary_sha256':hashlib.sha256((ROOT/'analysis/results_summary.json').read_bytes()).hexdigest(),
        'audit_status':audit['status'],
    }
    return doc,facts


def markdown(doc):
    lines=[]
    for item in doc:
        kind=item['kind']
        if kind=='title': lines += ['# '+item['text'],'']
        elif kind=='heading': lines += ['## '+item['text'],'']
        elif kind in ('paragraph','authors','affiliation','meta'): lines += [item['text'],'']
        elif kind=='equation': lines += ['```text',item['text'],'```','']
        elif kind=='link': lines += [f'[{item["label"]}]({item["url"]})','']
        elif kind=='table':
            lines+=['| '+' | '.join(x.replace('\n',' ') for x in item['headers'])+' |',
                    '| '+' | '.join('---' for _ in item['headers'])+' |']
            lines+=['| '+' | '.join(row)+' |' for row in item['rows']]
            lines += ['',item['caption'],'']
        elif kind=='figure': lines += [f'![{item["caption"]}](../{item["path"]})','',item['caption'],'']
        elif kind=='pagebreak': lines+=['<!-- page break -->','']
    return '\n'.join(lines)


def render_pdf(doc,path):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image, Flowable, KeepTogether
    regular=Path('/System/Library/Fonts/Supplemental/Arial.ttf')
    bold=Path('/System/Library/Fonts/Supplemental/Arial Bold.ttf')
    font='Helvetica'; boldfont='Helvetica-Bold'
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont('ReportArial',str(regular)))
        pdfmetrics.registerFont(TTFont('ReportArialBold',str(bold)))
        pdfmetrics.registerFontFamily('ReportArial',normal='ReportArial',bold='ReportArialBold')
        font,boldfont='ReportArial','ReportArialBold'
    titlefont='Times-Bold'; equationfont='Courier'
    title_path=Path('/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf')
    equation_path=Path('/System/Library/Fonts/Supplemental/Courier New.ttf')
    if title_path.exists():
        pdfmetrics.registerFont(TTFont('ReportTimesBold',str(title_path)))
        titlefont='ReportTimesBold'
    if equation_path.exists():
        pdfmetrics.registerFont(TTFont('ReportCourier',str(equation_path)))
        equationfont='ReportCourier'
    styles={
        'body':ParagraphStyle('body',fontName=font,fontSize=11,leading=12.65,spaceAfter=7),
        'heading':ParagraphStyle('heading',fontName=boldfont,fontSize=16,leading=18.4,spaceBefore=8,spaceAfter=8,keepWithNext=True),
        'title':ParagraphStyle('title',fontName=titlefont,fontSize=20,leading=23,alignment=TA_CENTER,spaceAfter=12),
        'authors':ParagraphStyle('authors',fontName=font,fontSize=11,leading=12.65,alignment=TA_CENTER,spaceAfter=4),
        'affiliation':ParagraphStyle('affiliation',fontName=font,fontSize=11,leading=12.65,alignment=TA_CENTER,spaceAfter=6),
        'meta':ParagraphStyle('meta',fontName=font,fontSize=9,leading=10.5,alignment=TA_CENTER,spaceAfter=10),
        'equation':ParagraphStyle('equation',fontName=equationfont,fontSize=8.7,leading=12,spaceBefore=2,spaceAfter=8),
        'caption':ParagraphStyle('caption',fontName=font,fontSize=9,leading=10.35,spaceBefore=4,spaceAfter=9),
        'cell':ParagraphStyle('cell',fontName=font,fontSize=9,leading=10.5),
        'thead':ParagraphStyle('thead',fontName=boldfont,fontSize=9,leading=10.5),
        'link':ParagraphStyle('link',fontName=font,fontSize=9,leading=11,spaceAfter=7,wordWrap='CJK'),
    }
    def text(value): return html.escape(str(value)).replace('\n','<br/>')
    class Boundary(Flowable):
        def __init__(self,name): Flowable.__init__(self); self.name=name; self.width=0; self.height=0
        def draw(self): pass
    class ReportDoc(BaseDocTemplate):
        def afterFlowable(self,flowable):
            if isinstance(flowable,Boundary): self.boundaries[flowable.name]=self.page
    document=ReportDoc(str(path),pagesize=letter,leftMargin=72,rightMargin=72,topMargin=72,bottomMargin=72,
                       title='Beyond the Words: Testing Behavioral Detection of Semantic Covert Communication Between AI Agents',
                       author='Aydan Wang and Sophie Eisenberg',subject='Track 4 - Multi-Agent Oversight and Control')
    document.boundaries={}
    story=[]
    for item in doc:
        kind=item['kind']
        if kind in ('title','authors','affiliation','meta','heading','equation'):
            story.append(Paragraph(text(item['text']),styles[kind]))
        elif kind=='paragraph': story.append(Paragraph(text(item['text']),styles['body']))
        elif kind=='link':
            story.append(Paragraph(f'<link href="{html.escape(item["url"],quote=True)}" color="#164c75">{text(item["label"])}</link>',styles['link']))
        elif kind=='pagebreak': story.append(PageBreak())
        elif kind=='boundary': story.append(Boundary(item['name']))
        elif kind=='table':
            cells=[[Paragraph(text(x),styles['thead']) for x in item['headers']]]
            cells += [[Paragraph(text(x),styles['cell']) for x in row] for row in item['rows']]
            widths=item['widths']; widths=[x*468/sum(widths) for x in widths]
            table=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8eef1')),
                ('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#6f7e86')),
                ('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#d2d9dd')),
                ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),
                ('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
            ]))
            story.append(KeepTogether([table,Paragraph(text(item['caption']),styles['caption'])]))
        elif kind=='figure':
            image_path=ROOT/item['path']
            if not image_path.exists(): raise ValueError('Required figure missing: '+str(image_path))
            im=Image(str(image_path)); scale=min(468/im.imageWidth,item['height']/im.imageHeight)
            im.drawWidth=im.imageWidth*scale; im.drawHeight=im.imageHeight*scale; im.hAlign='CENTER'
            story.append(KeepTogether([im,Paragraph(text(item['caption']),styles['caption'])]))
    def footer(canvas,doc):
        canvas.saveState(); canvas.setFont(font,8); canvas.setFillColor(colors.HexColor('#4a555e'))
        canvas.drawString(72,42,'Swarm Alignment Hackathon 2026 - Track 4')
        canvas.drawRightString(540,42,str(doc.page)); canvas.restoreState()
    frame=Frame(72,72,468,648,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0,id='body')
    document.addPageTemplates(PageTemplate(id='report',frames=[frame],onPage=footer))
    document.build(story)
    return {'font':font,'title_font':titlefont,'equation_font':equationfont,'page_size':'US Letter','margins_inches':1,
            'body_pt':11,'leading_multiplier':1.15,'heading_pt':16,
            'main_pages':document.boundaries.get('references',document.page+1)-1,
            'references_start_page':document.boundaries.get('references'),
            'appendix_start_page':document.boundaries.get('appendix'),'total_pages':document.page,
            'font_note':'Arial embedded when installed; Helvetica fallback. Times New Roman Bold is embedded when installed, otherwise Times-Bold; these substitute for Old Standard TT.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary',type=Path,default=ROOT/'analysis/results_summary.json')
    parser.add_argument('--audit',type=Path,default=ROOT/'paper/data_audit.json')
    parser.add_argument('--output',type=Path,default=ROOT/'paper/research_report.pdf')
    parser.add_argument('--markdown-only',action='store_true')
    args=parser.parse_args()
    summary,audit,rows,calls,frame,frame_rows,manifest=collect(args.summary,args.audit)
    doc,facts=make_document(summary,audit,rows,calls,frame,frame_rows,manifest)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.with_suffix('.md').write_text(markdown(doc)+'\n')
    if not args.markdown_only:
        facts.update(render_pdf(doc,args.output))
        if facts['main_pages']>8: raise ValueError('Report exceeds eight main pages')
        from pypdf import PdfReader
        reader=PdfReader(args.output)
        if len(reader.pages)!=facts['total_pages']: raise ValueError('Page count mismatch')
        alltext='\n'.join(p.extract_text() for p in reader.pages)
        required=['Abstract','References','LLM Usage Statement','Limitations and Dual-Use / Ethical Considerations']
        if any(t not in ' '.join(alltext.split()) for t in required): raise ValueError('Required section missing from rendered PDF')
        facts['pdf_sha256']=hashlib.sha256(args.output.read_bytes()).hexdigest()
    facts['generated_at_utc']=datetime.now(timezone.utc).isoformat()
    args.output.with_suffix('.metadata.json').write_text(json.dumps(facts,indent=2)+'\n')
    print(json.dumps(facts,indent=2))


if __name__=='__main__': main()
