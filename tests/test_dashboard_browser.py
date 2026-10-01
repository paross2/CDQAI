# CDQAI file version: 2.3.6
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
try {
 const assert=(ok,message)=>{if(!ok)throw Error(message);};
 document.getElementById('expand-all-findings').click();
 const buttons=[...document.querySelectorAll('.expand-button')];
 assert(buttons.length===2&&buttons.every(b=>b.getAttribute('aria-expanded')==='true'),'expand all');
 for(const slot of document.querySelectorAll('.narrative-slot')) {
   assert([...slot.querySelectorAll('mark')].map(m=>m.textContent).join('|')==='AIRLIFTED|hospital','exact Unicode spans');
   assert(getComputedStyle(slot.querySelector('mark')).backgroundColor==='rgb(255, 235, 59)','yellow fill');
   assert(slot.querySelector('.evidence-label').textContent.includes('2 yellow highlights'),'count');
   assert(!slot.querySelector('unsafe'),'escaped narrative HTML');
   const panel=slot.querySelector('.narrative-evidence');panel.style.maxHeight='50px';focusNarrativeEvidence(slot);
   assert(panel.scrollTop>0,'first highlight brought into view');
 }
 document.getElementById('collapse-all-findings').click();
 assert(buttons.every(b=>b.getAttribute('aria-expanded')==='false'),'collapse all');
 buttons[0].click();assert(buttons[0].getAttribute('aria-expanded')==='true','individual expansion');
 const search=document.querySelector('.filter-search');search.value='NO-MATCH';search.dispatchEvent(new Event('input'));
 document.getElementById('expand-all-findings').click();
 assert(buttons[1].closest('.finding-summary').hidden&&buttons[1].getAttribute('aria-expanded')==='false','respect filters');
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
