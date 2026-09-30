# CDQAI file version: 2.3.5
"""Session-only crash selection and a local print report; no browser storage."""

REVIEW_CONTROLS = '''<section class="review-controls"><h2>Flagged crash report</h2>
<p>Check <strong>Flag for review</strong> beside a crash, then print only the selected crashes.
In the print dialog, choose Save as PDF or Microsoft Print to PDF.</p>
<p><strong id="review-count" role="status" aria-live="polite">0 crashes flagged</strong></p>
<button id="print-flagged" type="button" disabled>Print flagged crashes / Save as PDF</button>
<button id="clear-flagged" type="button" disabled>Clear flags</button>
<p>Flags stay selected while sorting or filtering. They are cleared when you reload or close this dashboard.
The report includes full available narratives and highlights. No analyst notes are collected.</p></section>'''

REVIEW_SCRIPT = r'''
const flaggedCrashes = new Set();
const reviewBoxes = [...document.querySelectorAll('.flag-review')];
const printFlagged = document.getElementById('print-flagged');
const clearFlagged = document.getElementById('clear-flagged');
function syncReviewSelection() {
  for (const box of reviewBoxes) box.checked = flaggedCrashes.has(box.dataset.mfn);
  document.getElementById('review-count').textContent = flaggedCrashes.size + ' crash' + (flaggedCrashes.size===1?'':'es') + ' flagged';
  printFlagged.disabled = clearFlagged.disabled = flaggedCrashes.size === 0;
}
for (const box of reviewBoxes) {
  box.checked = false;
  box.addEventListener('change', () => {
    if (box.checked) flaggedCrashes.add(box.dataset.mfn); else flaggedCrashes.delete(box.dataset.mfn);
    syncReviewSelection();
  });
}
clearFlagged.addEventListener('click', () => {flaggedCrashes.clear(); syncReviewSelection();});
printFlagged.addEventListener('click', () => {
  if (!flaggedCrashes.size) return;
  if (!window.CDQAINarratives) {
    alert('Narrative companion file is missing. Keep dashboard_narratives.js beside this dashboard and reopen it before printing.');
    return;
  }
  // Build from All Findings, not only visible/filter-matching rows or the top queue.
  const table = document.getElementById('all-findings-table');
  const selected = new Map();
  for (const [summary, detail] of findingGroups(table)) {
    const box = summary.querySelector('.flag-review');
    if (box && flaggedCrashes.has(box.dataset.mfn) && !selected.has(box.dataset.mfn))
      selected.set(box.dataset.mfn, [summary, detail]);
  }
  const report = window.open('', '_blank');
  if (!report) {alert('Allow pop-ups for this local dashboard, then click Print flagged crashes again.'); return;}
  const doc = report.document;
  doc.open();
  doc.write('<!doctype html><html><head><meta charset="utf-8"><title>CDQAI flagged crash report</title><style>body{font:12pt Arial,sans-serif;margin:24px;color:#111}h1{font-size:20pt}h2{font-size:16pt}h4{margin-bottom:4px}p{margin-top:4px}table{border-collapse:collapse;width:100%;font-size:10pt}td,th{padding:6px;border:1px solid #aaa;text-align:left;overflow-wrap:anywhere}.crash{break-before:page}.crash:first-of-type{break-before:auto}.narrative-evidence{white-space:pre-wrap;overflow-wrap:anywhere;max-height:none;overflow:visible}mark{background:#ffe58f;color:#111;border-bottom:1px solid #8a6900;print-color-adjust:exact;-webkit-print-color-adjust:exact}h2,h4{break-after:avoid}.attribution-note{font-size:10pt}.missing-narrative{border:1px solid #aaa;padding:10px}@page{margin:15mm}@media print{.print-toolbar{display:none}body{margin:0}}</style></head><body><div class="print-toolbar"><button id="report-print">Print / Save as PDF</button><p>Choose Save as PDF or Microsoft Print to PDF. Enable background graphics to retain yellow fills.</p></div><h1>Flagged crash review report</h1><p id="report-meta"></p><p>Selected for analyst review; findings are not proof of an error. Contains protected local crash information.</p><main id="selected-crashes"></main></body></html>');
  doc.close();
  doc.getElementById('report-meta').textContent = document.title + ' | ' + selected.size + ' selected crashes | ' + new Date().toLocaleString();
  const container = doc.getElementById('selected-crashes');
  for (const [mfn, [summary, detail]] of selected) {
    const article = doc.createElement('article'); article.className = 'crash';
    const heading = doc.createElement('h2'); heading.textContent = 'Crash ' + mfn; article.appendChild(heading);
    const summaryTable = doc.createElement('table');
    const head = table.tHead.cloneNode(true); head.rows[0].deleteCell(0);
    const row = summary.cloneNode(true); row.hidden = false; row.deleteCell(0);
    summaryTable.appendChild(head); summaryTable.createTBody().appendChild(row); article.appendChild(summaryTable);
    const details = detail.querySelector('.detail-grid').cloneNode(true);
    const slot = details.querySelector('.narrative-slot');
    // Always materialize the complete narrative, even if the dashboard row was never expanded.
    renderNarrative(summary.querySelector('.expand-button').dataset.mfn, slot);
    article.appendChild(details); container.appendChild(article);
  }
  doc.getElementById('report-print').addEventListener('click', () => {report.focus(); report.print();});
  report.focus(); report.print();
});
syncReviewSelection();
'''
