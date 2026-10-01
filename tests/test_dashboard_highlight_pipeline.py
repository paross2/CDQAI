# CDQAI file version: 2.3.6
from copy import deepcopy
from datetime import datetime
import json
import logging

import pandas as pd

from cdqai.core.config import CDQAIConfig, DEFAULT_CONFIG
from cdqai.data.dataset import CrashDataset, DatasetMetadata
from cdqai.evidence.engine import EvidenceCollection
from cdqai.findings.engine import FindingEngine
from cdqai.reports.dashboard_report import write_dashboard, _narrative_payload
from cdqai.rules.injury import NarrativeInjuryConflictRule


def test_full_rule_to_dashboard_highlights_late_trigger(tmp_path):
    raw = deepcopy(DEFAULT_CONFIG)
    raw['fields'] = {'normalized_mfn_field': 'MFN', 'narrative_text_field': 'NarrativeTxt'}
    raw['paths']['outputs_dir'] = str(tmp_path)
    raw['rules']['injury_conflict'] = {'injury_field_candidates': ['Injury'], 'no_injury_values': ['0']}
    config = CDQAIConfig(raw, tmp_path)
    mfn = raw['fields']['normalized_mfn_field']
    field = raw['fields']['narrative_text_field']
    narrative = '\U0001f697 ' + 'The vehicles stopped at the intersection. ' * 20 + 'Driver AIRLIFTED to hospital. <unsafe>'
    frame = pd.DataFrame({mfn: [123.0], field: [narrative], 'Injury': ['0']})
    evidence = EvidenceCollection(NarrativeInjuryConflictRule().evaluate(frame, config).evidence)
    assert evidence.items
    assert 'AIRLIFTED' not in evidence.items[0].supporting_values[field]
    dataset = CrashDataset(frame, frame, frame, DatasetMetadata(datetime.now(), 1, 1, 1, 1, 1, 0, 1, 0, len(narrative)))
    write_dashboard(dataset, evidence, FindingEngine().run(evidence), config, logging.getLogger(__name__))
    companion = (tmp_path / 'dashboard_narratives.js').read_text(encoding='utf-8')
    payload = json.loads(companion.removeprefix('window.CDQAINarratives = ').strip().removesuffix(';'))['123']
    assert [s['text'] for s in payload['evidenceSpans']] == ['AIRLIFTED', 'hospital']
    for span in payload['evidenceSpans']:
        assert narrative[span['start']:span['end']] == span['text']
        assert span['start'] > 500
    dashboard = (tmp_path / 'dashboard.html').read_text(encoding='utf-8')
    assert 'background:#ffeb3b' in dashboard
    assert 'Array.from(String(item.narrativeFull))' in dashboard
    assert 'Version ' + config.version in dashboard
    assert 'data-mfn="123"' in dashboard
    assert 'data-mfn="123.0"' not in dashboard


def test_highlight_matches_whole_rule_words_only():
    payload = _narrative_payload('pain painting PAIN', 'pain')
    assert [s['start'] for s in payload['evidenceSpans']] == [0, 14]
