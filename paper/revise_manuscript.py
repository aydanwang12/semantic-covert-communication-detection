#!/usr/bin/env python3
"""Build the post-hoc identifiability manuscript with the official NeurIPS style.

The original sprint report is immutable in paper/archive/. This revision changes
interpretation and adds a post-hoc theorem/certificate, not experimental data.
"""
from __future__ import annotations
from collections import Counter
import hashlib, html, importlib.util, json, os, re, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'paper'))
import report_core as original

TITLE='Beyond the Words: An Identifiability Limit for Covert-Communication Monitors'
AUTHORS='Aydan Wang, Sophie Eisenberg, and James Horangic'


def revise(doc,summary,rows):
    def p(text):return {'kind':'paragraph','text':text}
    def h(text):return {'kind':'heading','text':text}
    main=summary['splits']['main']; c=main['conditions']; sem=c['semantic']; placebo=c['semantic_placebo']
    # Certify exact experimental receiver-query multisets, not model-output equality.
    certificates={}
    for split,sample in rows.items():
        def bundles(condition):
            return Counter(json.dumps({'system':r['system_prompt'],'prompts':r['prompts']},sort_keys=True)
                           for r in sample if r['condition']==condition)
        a,b=bundles('semantic'),bundles('semantic_placebo')
        if a!=b:raise ValueError('Receiver-query equivalence certificate failed')
        certificates[split]={'equal':True,'episodes_per_condition':sum(a.values()),'unique_query_bundles':len(a)}
    abstract=(
        'What can behavioral monitoring identify when hidden-instruction transmission and a control produce the same observable receiver queries? '
        'We study a binary routing task with explicit syntactic and semantic codebooks, a codebook-informed partner, and an uninformed outsider. '
        'A semantic placebo retains the private convention while making its frame independent of the designated hidden target. '
        'Our central post-hoc result is an identifiability proposition: under a shared condition-invariant response kernel, semantic-channel and placebo receiver transcripts have identical distributions. '
        'Consequently, every detector restricted to that view has equal true- and false-positive rates, and every fixed score has population AUROC 0.5. '
        'A machine-checkable certificate verifies exact equality of receiver-query multisets in both recorded splits. '
        'The main experiment contains 128 episodes across four conditions after a separate 64-episode pilot. '
        'The semantic partner decodes 32/32 hidden targets, yet the prespecified single-draw diagnostic alarms on 7/32 semantic episodes and 9/32 placebos, with semantic-versus-placebo AUROC 0.469. '
        'A target-conditioned audit separates successful instruction transmission from convention use, but requires information excluded from the monitor. '
        'The contribution is a concrete observation-equivalence counterexample and reproducible benchmark preflight check, grounded in an openly logged controlled experiment. '
        'It does not establish a general impossibility of covert-communication detection or falsify the full PoPLi estimator.'
    )
    result=[];skip_intro=False;skip_discussion=False;skip_conclusion=False;in_abstract=False
    for item in doc:
        k=item['kind'];text=item.get('text','')
        if k=='title': result.append({**item,'text':TITLE});continue
        if k=='authors':result.append({**item,'text':AUTHORS});continue
        if k=='pagebreak':continue
        if k=='heading' and '(continued)' in text:continue
        if k=='heading':
            text=re.sub(r'^\d+\.\s*','',text)
            skip_intro=skip_discussion=skip_conclusion=False
            if text=='Abstract':in_abstract=True;result.append({**item,'text':text});continue
            if text=='Introduction':
                result.append(h(text)); result.extend([
                    p('We ask a precise question: can a monitor infer transmission of a designated hidden instruction from receiver queries and responses alone when a target-independent control has the same observable query distribution? The distinction is operational. An agent may follow a private convention and communicate a nuisance-frame bit without transmitting the particular secret whose transfer the benchmark labels positive.'),
                    p('We first ran a prespecified comparison of syntactic and semantic channels using partner-outsider action changes. The observed weak semantic detection motivated a post-hoc analysis of the benchmark itself. We prove an observation-equivalence result for its semantic/placebo pair, certify the equality of the actual receiver-query multisets, and provide a target-conditioned audit that explains what additional information resolves the ambiguity. The original primary endpoint, threshold, raw calls, and initial report remain unchanged and archived.'),
                    p('Our contributions are scoped: (i) an identifiability proposition for a specified monitor view; (ii) a reusable preflight check that detects an impossible observational classification task before judging a monitor; and (iii) a controlled LLM experiment showing that high partner decoding and a positive intervention contrast can coexist with receiver-only non-identifiability. The proof is an application of observation equivalence, not a claim to invent that general principle.')])
                skip_intro=True;continue
            if text=='Methods: Environment and Agents':
                result.extend(theory_blocks(certificates));result.append(h('Controlled experiment'));continue
            if text=='Results: Main Experiment':text='Experimental results and target-conditioned audit'
            if text=='Discussion and Limitations':
                result.append(h(text));result.extend([
                    p('The semantic/placebo result is expected under Proposition 1, not evidence that every communication monitor is weak. The semantic channel carries the designated target; the placebo carries an unrelated nuisance-frame bit through the same private mapping. Both expose the same receiver-query distribution. A receiver-only monitor can detect convention use or sensitivity, but cannot identify its coupling to an unobserved designated target under these assumptions.'),
                    p('The prespecified primary contrast addresses a different question. Its positive value identifies distinct responses to selected interventions: the outsider often changes under a frame shift, including in the syntactic condition, while the informed syntactic partner does not. A positive contrast therefore does not imply a large absolute semantic detection gap. No-channel alarms additionally reveal the sampling noise of a single-draw diagnostic; this control is not covered by the semantic/placebo equivalence proposition.'),
                    p('An effective benchmark should specify the monitor view, target quantity, and allowed side information before collection. Our preflight utility compares canonical receiver-query multisets with multiplicities and produces a certificate or mismatch witness. Exact empirical equality is a finite-design check; the generative proof supplies the population statement only under a common response kernel. A failure of the certificate would not establish detectability. A passing certificate identifies a label distinction that requires extra observations, not a reason to redefine the labels after seeing results.'),
                    p('Limits are substantial: one model, two main template pairs, explicit keys, constrained sentence selection, conspicuous temporal lexical cues, selected interventions, and no adaptive collusion. The theorem excludes target labels, sender private prompts and candidate menus, condition IDs, and timing/runtime side channels. In this implementation sender menus have two options in the positive channel and one in controls, so access to that generation metadata breaks equivalence. Provider drift or condition-dependent state can also violate the common-kernel assumption. These exclusions are part of the theorem, not claims that all real monitors lack such information.')]);skip_discussion=True;continue
            if text=='Conclusion':
                result.append(h(text));result.append(p('For the specified receiver-only view, the semantic channel and its target-independent placebo are observationally equivalent. The recorded query bundles certify this design property; the LLM outcomes illustrate its consequence while preserving the original prespecified analysis. A privileged target-conditioned audit resolves the label distinction, making its information requirement explicit. The practical recommendation is to test identifiability before interpreting a monitor benchmark: define what information is meant to be detected, what the monitor sees, and whether positive and control distributions differ in that view.'))
                skip_conclusion=True;continue
            result.append({**item,'text':text});continue
        if in_abstract and k=='paragraph': result.append(p(abstract));in_abstract=False;continue
        if (skip_intro or skip_discussion or skip_conclusion) and k=='paragraph':continue
        if k=='paragraph' and text.startswith('The main experiment uses '):
            text=text.replace('The main experiment uses ', 'The recorded main experiment uses ')
        if k=='paragraph' and text.startswith('All original experiment code was written'):
            text=text.replace('All original experiment code was written during this sprint.', 'The experimental implementation and initial study were produced during the sprint; the identifiability proposition, certificate, and target-conditioned audit were added in a subsequent explicitly labeled revision.')
            text=text.replace('Matplotlib regenerates figures; ReportLab regenerates this report.', 'Matplotlib regenerates figures. Tectonic compiles the primary manuscript with the official NeurIPS style; ReportLab builds the separate hackathon-layout companion.')
            text=text.replace('The unit-test suite passed 43 tests.', 'The original unit-test suite passed 43 tests; the extended suite passed 59, including identifiability-certificate and target-conditioned-audit checks.')
        if k=='paragraph' and text.startswith('OpenAI Codex agents were used'):
            text += ' The identifiability analysis and manuscript revision were also AI-assisted and added after inspection of the initial results. The named authors were updated at the user\'s request.'
        if k=='paragraph' and text.startswith('Data and authorship.'):
            text=text.replace('The source implementation and recorded experiment were produced during this sprint;', 'The initial source implementation and recorded experiment were produced during the sprint; the theoretical interpretation and audit extension were added afterward;')
        if k=='figure' and 'main_decoding_accuracy' in item['path']:
            item={**item,'path':'analysis/figures/main_target_grounding.png','caption':'Figure 2. Both semantic and placebo partners follow the frame convention, but only the semantic condition tracks the designated target. The target-conditioned panel reuses the same recorded actions and requires hidden target labels; it is not independent evidence or a receiver-only detector.'}
        result.append({**item,'text':text} if 'text' in item else item)
    # Add target-conditioned comparison directly before discussion.
    idx=next(i for i,x in enumerate(result) if x.get('text')=='Discussion and Limitations')
    target_rows=[]
    for condition in ('semantic','semantic_placebo'):
        sample=[r for r in rows['main'] if r['condition']==condition]
        correct=sum(r['actions']['partner']['original']==r['hidden_bit'] for r in sample)
        target_rows.append([original.LABELS[condition],f'{correct}/{len(sample)}',f'{certificates["main"]["unique_query_bundles"]}'])
    target=[h('What additional information resolves the ambiguity?'),
        p('The target-conditioned audit uses the designated hidden bit H, which the receiver-only theorem excludes. Original partner agreement with H is 32/32 in the semantic condition and 16/32 in the placebo. The emitted frame/key pair itself likewise matches H in all semantic episodes and exactly half the fully crossed placebo episodes. Thus the planted channel transfers the target while the placebo only transfers a nuisance-frame bit; this distinction is measurable with target labels but not identifiable from the permitted transcript alone.'),
        {'kind':'table','headers':['Condition','Partner agrees with H','Unique receiver-query bundles'],'rows':target_rows,'widths':[140,150,178],'caption':'Table 4. Target-conditioned main audit. The two conditions have equal observable query multisets but different coupling to the designated hidden target. This is a privileged audit, not a deployable receiver-only detector.'},
        p('Revealing H breaks distributional equivalence, not the ambiguity of every individual episode: target-visible input total variation is 0.5 in the audited balanced design, giving optimal balanced single-episode classification accuracy 0.75. The placebo still agrees with H half the time. These are properties of the input distributions, not newly measured receiver classification performance.'),
        p('For 16 matched target pairs per condition, mean partner response A(H=1) - A(H=0) is 1.000 for semantic and syntactic channels, 0.000 for placebo, and -0.188 without a channel. The semantic outsider value is 0.125. In this balanced binary design the paired statistic equals twice original accuracy minus one, so it is an interpretable re-expression of the same observations, not new independent evidence.'),
        p('This audit was added after the original main results. It does not replace the frozen detector or justify selecting its threshold using target labels. It explains the separation between an identifiable benchmark outcome under privileged ground truth and a label that is not identifiable from the restricted monitor view.')]
    result[idx:idx]=target
    # Number headings once, no continuation headings or forced main-page breaks.
    section=0
    for x in result:
        if x['kind']=='heading' and x['text'] not in ('Abstract','References','LLM Usage Statement','Limitations and Dual-Use / Ethical Considerations'):
            section+=1;x['text']=f'{section}. '+x['text']
    return result,certificates,len(abstract.split())


def theory_blocks(cert):
    return [
      {'kind':'heading','text':'An identifiability limit'},
      {'kind':'paragraph','text':'This proposition instantiates the observation-equivalence and information-access concerns already present in PoPLi [1] and Anwar et al. [3]. We claim a concrete counterexample and a calibration certificate for this benchmark, not priority for a general indistinguishability theorem.'},
      {'kind':'paragraph','text':'Monitor view. Let H be the designated hidden instruction, K the codebook orientation, U a nuisance frame bit, Z the nuisance initial, and T the template index. The design crosses H,K,U,Z uniformly and matches T across conditions. In the semantic channel F = H xor K; in the placebo F = U. Let Q = g(K,F,Z,T) contain both receivers\' complete task queries for all four message variants, including the partner\'s convention, common role instructions, and neutral instructions. Let Y contain the corresponding receiver outputs. The permitted monitor view is W = (Q,Y). It excludes H, sender inputs and candidate menus, condition/episode/block labels, and timing or runtime metadata.'},
      {'kind':'theorem','text':'Proposition 1 (Receiver-only non-identifiability). Suppose the joint receiver response kernel R(dy | Q) is the same in the semantic and placebo conditions. Then their laws of W are identical. Every measurable receiver-only alarm rule has equal true- and false-positive probabilities, and every fixed receiver-only score has population tied-score AUROC 1/2.'},
      {'kind':'math','latex':r'\mathcal L(Q,Y\mid C=\mathrm{semantic})=\mathcal L(Q,Y\mid C=\mathrm{placebo}),\qquad \mathrm{TPR}(\tau)=\mathrm{FPR}(\tau).'},
      {'kind':'proof','text':'Because H and K are independent uniform bits, (K,H xor K) is uniform on the four bit pairs. Because U is independent uniform, (K,U) has the same law. Matching Z and T therefore gives identical laws of Q = g(K,F,Z,T). Integrating the same conditional kernel R(dy | Q) against these equal query laws gives equal joint laws of (Q,Y). Every measurable alarm event has equal probability. For independent positive and negative scores with this same distribution, exchangeability gives P(S+ > S-) + (1/2)P(S+ = S-) = 1/2, including ties.'},
      {'kind':'paragraph','text':f'Finite-design certificate. Canonicalizing the actual receiver-query bundles gives exactly equal semantic/placebo multisets, including multiplicity: {cert["pilot"]["episodes_per_condition"]} episodes per condition and {cert["pilot"]["unique_query_bundles"]} distinct bundles in the pilot; {cert["main"]["episodes_per_condition"]} episodes and {cert["main"]["unique_query_bundles"]} distinct bundles in the main split. This is equality of queries, not equality of the realized stochastic outputs. Finite-sample AUROCs need not be exactly 0.5. The certificate and theorem were developed after the original experiment; they are not preregistered predictions.'},
      {'kind':'paragraph','text':'Scope. The result permits a strong observer of both receiver prompts, even the partner\'s private mapping, but not the designated target. It does not apply to monitors with sender-private information, target labels, generation-menu metadata, or an external persistent-key history. It also does not show that semantic communication is generally undetectable. It shows that this benchmark\'s particular target-transfer distinction is not identifiable from the stated view.'}
    ]


def tex_escape(text):
    mapping={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    return ''.join(mapping.get(c,c) for c in str(text))


def latex(doc):
    out=[r'\documentclass{article}',r'\usepackage[preprint,nonatbib]{neurips_2026}',r'\usepackage[T1]{fontenc}',r'\usepackage[utf8]{inputenc}',r'\usepackage{amsmath,amssymb,amsthm,booktabs,graphicx,tabularx,url,hyperref}',r'\hypersetup{colorlinks=true,urlcolor=blue,linkcolor=black}',r'\newtheorem{proposition}{Proposition}',r'\title{'+tex_escape(TITLE)+'}',r'\author{'+tex_escape(AUTHORS)+r'\\FranklinDAO/Penn Blockchain}',r'\begin{document}',r'\maketitle']
    inabs=False; refs=False;table_no=0
    for item in doc:
        k=item['kind'];text=item.get('text','')
        if k in ('title','authors','affiliation','meta','pagebreak'):continue
        if k=='boundary':
            if item['name']=='references':out.append(r'\clearpage');refs=True
            elif item['name']=='appendix':out.extend([r'\clearpage',r'\appendix']);refs=False
            continue
        if k=='heading':
            if text=='Abstract':inabs=True;out.append(r'\begin{abstract}');continue
            text=re.sub(r'^\d+\.\s*','',text)
            out.append(('\\section*{' if text in ('References','LLM Usage Statement') else '\\section{')+tex_escape(text)+'}')
        elif k=='paragraph':
            out.append(tex_escape(text)+'\n')
            if inabs:out.append(r'\end{abstract}');inabs=False
        elif k=='equation':
            out += [r'\begin{align}',r'F_i(r,t)&=\mathbf 1\{a_i(r,t)\ne a_i(r,0)\},\\',r'D_i(t)&=F_i(\mathrm{partner},t)-F_i(\mathrm{outsider},t),\\',r'\Delta_{\mathrm{frame}}&=\overline D_{\mathrm{frame},\mathrm{semantic}}-\overline D_{\mathrm{frame},\mathrm{syntactic}},\\',r'S_i&=\max\{D_i(\mathrm{lexical}),D_i(\mathrm{frame})\};\quad \mathrm{alarm}_i=\mathbf 1\{S_i>0\}.',r'\end{align}']
        elif k=='math':out += [r'\begin{equation}',item['latex'],r'\end{equation}']
        elif k=='theorem':out += [r'\begin{proposition}[Receiver-only non-identifiability]',tex_escape(text.split('). ',1)[1]),r'\end{proposition}']
        elif k=='proof':out += [r'\begin{proof}',tex_escape(text),r'\end{proof}']
        elif k=='link':
            # Full URLs already in the verified reference list remain clickable.
            out.append(r'\noindent\url{'+item['url']+r'}\par')
        elif k=='table':
            table_no+=1; n=len(item['headers']);cap=re.sub(r'^Table \d+\.\s*','',item['caption'])
            out += [r'\begin{table}[htbp]',r'\centering\small',r'\caption{'+tex_escape(cap)+'}',r'\begin{tabularx}{\linewidth}{'+('X'*n)+'}',r'\toprule', ' & '.join(r'\textbf{'+tex_escape(x.replace('\n',' '))+'}' for x in item['headers'])+r'\\',r'\midrule']
            out += [' & '.join(tex_escape(x) for x in row)+r'\\' for row in item['rows']]
            out += [r'\bottomrule',r'\end{tabularx}',r'\end{table}']
        elif k=='figure':
            cap=re.sub(r'^Figure \d+\.\s*','',item['caption'])
            out += [r'\begin{figure}[htbp]',r'\centering',r'\includegraphics[width=\linewidth]{../'+item['path']+'}',r'\caption{'+tex_escape(cap)+'}',r'\end{figure}']
    out += [r'\end{document}']
    return '\n'.join(out)+'\n'


def main():
    summary,audit,rows,calls,frame,frame_rows,manifest=original.collect(ROOT/'analysis/results_summary.json',ROOT/'paper/data_audit.json')
    doc,facts=original.make_document(summary,audit,rows,calls,frame,frame_rows,manifest)
    doc,cert,words=revise(doc,summary,rows)
    if not 150<=words<=250:raise ValueError('Abstract word limit')
    out=ROOT/'paper/research_report'
    out.with_suffix('.tex').write_text(latex(doc))
    # Markdown includes theorem/proof rather than silently dropping those blocks.
    md=[]
    for item in doc:
        if item['kind'] in ('theorem','proof'):md.append({'kind':'paragraph','text':item['text']})
        elif item['kind']=='math':md.append({'kind':'equation','text':item['latex']})
        else:md.append(item)
    out.with_suffix('.md').write_text(original.markdown(md)+'\n')
    companion=[]
    for item in md:
        if item['kind']=='boundary':companion.append({'kind':'pagebreak'})
        if item['kind']=='equation' and '\\mathcal' in item['text']:
            item={**item,'text':'Law(Q,Y | semantic) = Law(Q,Y | placebo); TPR(tau) = FPR(tau).'}
        companion.append(item)
    companion_metadata=original.render_pdf(companion,ROOT/'paper/research_report_hackathon.pdf')
    if companion_metadata['main_pages']>8:raise ValueError('Hackathon companion exceeds eight main pages')
    (ROOT/'paper/research_report_hackathon.metadata.json').write_text(json.dumps(companion_metadata,indent=2)+'\n')
    facts.update({'abstract_words':words,'title':TITLE,'authors':AUTHORS,'revision':'post-hoc identifiability extension','query_equivalence':cert,'official_style_url':'https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip','official_style_sha256':hashlib.sha256((ROOT/'paper/neurips_2026.sty').read_bytes()).hexdigest()})
    (ROOT/'paper/revision_metadata.json').write_text(json.dumps(facts,indent=2)+'\n')
    print(json.dumps({'tex':str(out.with_suffix('.tex')),'abstract_words':words,'certificate':cert},indent=2))

if __name__=='__main__':main()
