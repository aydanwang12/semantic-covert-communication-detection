# Manuscript style and reproducible build

The primary revised manuscript uses the **unmodified official NeurIPS 2026
LaTeX style**, downloaded from the [author-kit link](https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip)
on the [official Call for Papers](https://neurips.cc/Conferences/2026/CallForPapers).
It is compiled with `[preprint,nonatbib]`, not the accepted-paper `final` option.
The manuscript is not represented as accepted by or submitted to NeurIPS.

```sh
# Requires Python dependencies from requirements.txt and Tectonic on PATH.
python paper/build_report.py --compiler tectonic
```

`TECTONIC_BIN` can instead identify an installed executable. The published build
script contains no machine-specific compiler path. Tectonic 0.17.0 from the
[official release](https://github.com/tectonic-typesetting/tectonic/releases/tag/tectonic%400.17.0)
was used for this revision. Its first build downloads standard TeX dependencies;
subsequent cached builds can run without those downloads. The official `.sty`
and generated `.tex` source are included. No modifications were made to `.sty`.

The same command also generates `research_report_hackathon.pdf`, preserving the
original event layout: US Letter, one-inch margins, Arial 11-point body, 1.15
leading, and 16-point headings. It contains the same prose and equivalent
mathematical statements. This companion meets the event's eight-main-page limit;
the requested primary version uses the NeurIPS layout. Both include the required
ethics appendix and AI-use disclosure. Neither uses continuation headings.

The original sprint artifact is immutable in `archive/research_report_sprint_v1.pdf`
with its source, Markdown, metadata, and QA record. The revision is explicitly
post-hoc and does not replace the saved experiment or prespecified primary metric.

`build_report.py` is the current entry point. `report_core.py` supplies shared
recorded-data checks and the companion renderer; `revise_manuscript.py` constructs
the revised contents and LaTeX source. Rendering warns only about underfull boxes,
which are checked visually; no overfull/clipped material was observed.
