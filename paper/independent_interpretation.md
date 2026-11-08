# Independent interpretation guardrails

The contribution is a small controlled replication and extension of existing
receiver-outsider monitoring and semantic-steganography research. It tests a
single-draw behavioral diagnostic under orthogonal, authored interventions and a
payload-independent placebo. It is not a new steganography mechanism, a reproduction
of the full PoPLi estimator, or evidence about emergent/adversarial collusion.

The primary contrast is mean frame-intervention gap in the semantic condition
minus that in the syntactic condition. A positive contrast need not mean that the
semantic condition has a positive absolute gap or is detected well. For example,
D_semantic=0 and D_syntactic=-1 yield a positive contrast of 1. This happens when
both receivers change in the semantic condition but only the outsider changes in
the syntactic condition. Report partner and outsider flip rates, absolute gaps,
detection rates, and control alarms before drawing a detection conclusion.

The semantic placebo gives the partner exactly the same frame-to-route mapping
as the semantic channel, but selects frames independently of the designated hidden
target. The partner still receives information about the nuisance frame and may
follow a private convention. An alarm therefore need not be false for *convention
use*, but it is a false positive for *transmission of the designated hidden
instruction*. The placebo does not prove that all ordinary semantic sensitivity
is indistinguishable from covert communication; it tests this precise distinction.

Each episode uses a freshly assigned, balanced, arbitrary codebook orientation.
Without that key, the planned visible message distribution is identical for both
target bits. Chance outsider decoding is consequently compatible with a simple
information-theoretic masking design. It is not a security result against an
outsider who observes repeated messages under a persistent key, learns from
feedback, sees other side channels, or strategically reconstructs the protocol.
An outsider can remain at chance while strongly reacting to semantic frames.

The semantic messages retain conspicuous temporal lexical cues (earlier/origins
versus next/forthcoming). The experiment tests meaning-bearing frame encoding under
selected lexical rewrites, not a semantic channel demonstrably independent of all
surface cues. Both transformations come from a finite authored bank; same-model
blind frame classification validates this bank only. The sender selects from two
approved sentences (one in controls), rather than freely composing covert messages.

The detector threshold was fixed before outcomes and is not statistically
calibrated. Under a hypothetical iid fair-coin null for the six receiver actions,
P(D_t>0)=1/4 and P(max(D_lexical,D_frame)>0)=1-(3/4)^2=7/16 (43.75%). This is an
analytic reference under explicit assumptions, not an observed result or a general
FPR claim. It illustrates why a single draw per response distribution can generate
alarms without channel information. Unchanged-message repetitions diagnose some
sampling instability; exploratory noise correction is not the primary estimator.

Episodes and matched factor blocks are the sampling units. Repeated draws within
an episode are not independent episodes, and repeated observable prompts across
factor blocks do not create new semantic content. Confidence intervals describe
this finite model/template design, not a population of unseen covert protocols.
