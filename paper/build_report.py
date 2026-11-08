#!/usr/bin/env python3
"""Build revised NeurIPS preprint plus the hackathon-layout companion.

Install Tectonic, then run: python paper/build_report.py --compiler tectonic
The original sprint report is preserved in paper/archive/.
"""
import argparse,json,os,shutil,subprocess,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'paper'))
import revise_manuscript

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',default=os.environ.get('TECTONIC_BIN') or shutil.which('tectonic'))
    parser.add_argument('--sources-only',action='store_true')
    args=parser.parse_args()
    revise_manuscript.main()
    if args.sources_only:return
    if not args.compiler:raise SystemExit('Tectonic is required: install it or set --compiler to its executable path. The .tex source and hackathon-layout companion were generated.')
    subprocess.run([args.compiler,'--untrusted','--keep-logs',str(ROOT/'paper/research_report.tex')],cwd=ROOT,check=True)
    from pypdf import PdfReader
    pdf=ROOT/'paper/Beyond_the_Words_NeurIPS_Manuscript.pdf'
    (ROOT/'paper/research_report.pdf').replace(pdf)
    reader=PdfReader(pdf)
    texts=[p.extract_text() for p in reader.pages]
    ref=next(i+1 for i,t in enumerate(texts) if t.lstrip().startswith('References'))
    if ref-1>8:raise ValueError('Revised manuscript exceeds eight main pages')
    if any('(continued)' in t for t in texts):raise ValueError('Continuation heading remains')
    for author in ['Aydan Wang','Sophie Eisenberg','James Horangic']:
        if author not in texts[0]:raise ValueError('Missing author '+author)
    meta=json.loads((ROOT/'paper/revision_metadata.json').read_text())
    meta.update({'renderer':'Tectonic, official unmodified neurips_2026.sty [preprint,nonatbib]','main_pages':ref-1,'total_pages':len(reader.pages),'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest()})
    (ROOT/'paper/research_report.metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({'main_pages':ref-1,'total_pages':len(reader.pages),'pdf_sha256':meta['pdf_sha256']},indent=2))
if __name__=='__main__':main()
