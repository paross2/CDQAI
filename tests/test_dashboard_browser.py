# CDQAI file version: 2.5.0
"""Opt-in Windows Edge check; all files live in pytest's disposable workspace."""
import os
from pathlib import Path
import runpy
import subprocess
import sys

import pytest


@pytest.mark.skipif(os.getenv("CDQAI_BROWSER_TEST") != "1" or sys.platform != "win32",
                    reason="Set CDQAI_BROWSER_TEST=1 for the synthetic Edge check")
def test_expansion_and_highlight_guidance_in_edge(tmp_path):
    fixture = runpy.run_path(str(Path(__file__).with_name("test_dashboard_highlight_pipeline.py")))
    fixture["test_full_rule_to_dashboard_highlights_late_trigger"](tmp_path)
    script = r"""<script>
(async()=>{
try {
 const assert=(ok,message)=>{if(!ok)throw Error(message);};
 const buttons=[...document.querySelectorAll('.expand-button')],tables=[...document.querySelectorAll('table.findings-table')];
 assert(document.querySelector('.pagination-controls .page-size'),'all findings pagination controls');
 assert(tables.find(t=>t.id==='all-findings-table').dataset.paginated==='true','only the current all-findings page is rendered');
 document.querySelector('[data-table="top-findings-table"] .expand-block[data-open="true"]').click();
 assert(buttons.length===2&&buttons[0].getAttribute('aria-expanded')==='true'&&buttons[1].getAttribute('aria-expanded')==='false','top block expansion scope');
 document.querySelector('[data-table="top-findings-table"] .expand-block[data-open="false"]').click();
 document.querySelector('[data-table="all-findings-table"] .expand-block[data-open="true"]').click();
 assert(buttons[0].getAttribute('aria-expanded')==='false'&&buttons[1].getAttribute('aria-expanded')==='true','all block expansion scope');
 document.querySelector('[data-table="top-findings-table"] .expand-block[data-open="true"]').click();
 assert(buttons.every(b=>b.getAttribute('aria-expanded')==='true'),'both blocks expanded independently');
 await new Promise(resolve=>setTimeout(resolve,200));
 for(const slot of document.querySelectorAll('.narrative-slot')) {
   assert([...slot.querySelectorAll('mark')].map(m=>m.textContent).join('|')==='AIRLIFTED|hospital','exact Unicode spans');
   assert(getComputedStyle(slot.querySelector('mark')).backgroundColor==='rgb(255, 235, 59)','yellow fill');
   assert(slot.querySelector('.evidence-label').textContent.includes('2 yellow highlights'),'count');
   assert(!slot.querySelector('unsafe'),'escaped narrative HTML');
   const panel=slot.querySelector('.narrative-evidence');panel.style.maxHeight='50px';focusNarrativeEvidence(slot);
   assert(panel.scrollTop>0,'first highlight brought into view');
 }
 document.querySelector('[data-table="all-findings-table"] .expand-block[data-open="false"]').click();
 assert(buttons[0].getAttribute('aria-expanded')==='true'&&buttons[1].getAttribute('aria-expanded')==='false','all block collapse scope');
 document.querySelector('[data-table="top-findings-table"] .expand-block[data-open="false"]').click();
 buttons[0].click();assert(buttons[0].getAttribute('aria-expanded')==='true','individual expansion');
 const records=window.CDQAIAllFindings.records,originalMfn=records[0][0],template=records[0];
 for(let i=0;i<110;i++){const record=template.slice();record[0]='PAGINATED-'+i;record[12]=record[0].toLowerCase();record[13]=records.length;records.push(record);}
 const search=document.querySelector('.filter-search'),pager=document.querySelector('.pagination-controls'),pageStatus=pager.querySelector('.page-status'),allTable=tables.find(t=>t.id==='all-findings-table');
 search.dispatchEvent(new Event('input'));await new Promise(resolve=>setTimeout(resolve,200));
 assert(pageStatus.textContent.includes('Page 1 of 2')&&allTable.querySelectorAll('.finding-summary').length===100,'page size and page count');
 pager.querySelector('.page-next').click();
 assert(pageStatus.textContent.includes('Page 2 of 2')&&allTable.querySelectorAll('.finding-summary').length===11,'next page renders only that page');
 allTable.querySelector('.flag-review').click();
 assert(document.getElementById('review-count').textContent==='1 crash flagged','flags persist across pages');
 pager.querySelector('.page-previous').click();
 search.value=originalMfn;search.dispatchEvent(new Event('input'));await new Promise(resolve=>setTimeout(resolve,200));
 assert(pageStatus.textContent.includes('1 finding')&&allTable.querySelectorAll('.finding-summary').length===1,'filters search every page');
 search.value='NO-MATCH';search.dispatchEvent(new Event('input'));await new Promise(resolve=>setTimeout(resolve,200));
 document.querySelector('[data-table="all-findings-table"] .expand-block[data-open="true"]').click();
 assert(!allTable.querySelector('.finding-summary'),'respect filters');
 search.value='';search.dispatchEvent(new Event('input'));
 const factorFilter=document.querySelector('[data-factor-type="human"]');
 for(const code of ['02','04'])factorFilter.querySelector(`.factor-option[value="${code}"]`).click();
 document.querySelector('[data-table="all-findings-table"] .expand-block[data-open="false"]').click();
 const currentSummary=()=>tables.find(t=>t.id==='all-findings-table').querySelector('.finding-summary');
 assert(currentSummary(),'multiple selected codes within category use OR');
 const environmental=document.querySelector('[data-factor-type="environmental"]');
 environmental.querySelector('.factor-option[value="11"]').click();
 assert(currentSummary(),'active factor categories use AND when all match');
 environmental.querySelector('.factor-clear').click();
 environmental.querySelector('.factor-option[value="03"]').click();
 assert(!currentSummary(),'active factor categories exclude records without every category');
 const probe=document.createElement('div');document.body.append(probe);
 window.CDQAINarratives.plain={narrativeFull:'A synthetic narrative.',evidenceSpans:[],evidenceMethod:'no_segment_evidence'};
 renderNarrative('plain',probe);
 assert(!probe.querySelector('mark')&&probe.textContent.includes('No supported text highlight'),'unhighlighted state');
 assert(!probe.querySelector('.review-instruction').textContent.includes('Compare the highlighted'),'honest guidance');
 window.CDQAINarratives.plain.evidenceSpans=[{start:0,end:1,text:'incorrect'}];renderNarrative('plain',probe);
 assert(!probe.querySelector('mark'),'reject invalid span');
 const saved=window.CDQAINarratives;delete window.CDQAINarratives;renderNarrative('plain',probe);
 assert(probe.textContent.includes('Narrative companion unavailable'),'companion error');window.CDQAINarratives=saved;
 renderNarrative('missing',probe);assert(probe.textContent.includes('Narrative unavailable'),'missing record');
 const result=document.createElement('p');result.id='browser-test-result';result.textContent='PASS';document.body.append(result);
} catch(e) {
 const result=document.createElement('p');result.id='browser-test-result';result.textContent='FAIL: '+e.message;document.body.append(result);
}
})();
</script>"""
    page = tmp_path / "dashboard.html"
    html = page.read_text(encoding="utf-8")
    # The PDF script also contains a closing body literal; insert only at the end.
    index = html.rindex("</body>")
    page.write_text(html[:index] + script + html[index:], encoding="utf-8")
    browser = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe"
    assert browser.is_file(), "Edge is required for this explicitly requested browser test"
    def quote(value):
        return "'" + str(value).replace("'", "''") + "'"
    args = ["--headless=new", "--disable-gpu", "--disable-background-networking", "--disable-sync",
            "--no-first-run", "--no-default-browser-check", "--allow-file-access-from-files",
            "--virtual-time-budget=1000",
            '--user-data-dir="' + str(tmp_path / "profile") + '"', "--dump-dom", page.as_uri()]
    powershell = f"""$ErrorActionPreference='Stop'
$p=Start-Process -FilePath {quote(browser)} -ArgumentList @({','.join(map(quote,args))}) -WindowStyle Hidden -PassThru -RedirectStandardOutput {quote(tmp_path / 'stdout.txt')} -RedirectStandardError {quote(tmp_path / 'stderr.txt')}
try {{ if(-not $p.WaitForExit(45000)) {{ throw 'Browser timeout' }} }}
finally {{ if(-not $p.HasExited) {{ Stop-Process -Id $p.Id -Force; $p.WaitForExit() }} }}
"""
    subprocess.run(["powershell.exe", "-NoProfile", "-Command", powershell], check=True, timeout=60,
                   capture_output=True, text=True)
    output = (tmp_path / "stdout.txt").read_text(encoding="utf-8")
    import re
    result = re.search(r'<p id="browser-test-result">([^<]+)</p>', output)
    assert result is not None, "Browser did not complete its assertions"
    assert result.group(1) == "PASS", result.group(1)
