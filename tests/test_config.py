# CDQAI file version: 2.2.5
from cdqai.core.config import load_config
from cdqai.core.build_info import VERSION


def test_config_loads():
    config = load_config()
    assert config.short_name == "CDQAI"
    assert config.version == VERSION
