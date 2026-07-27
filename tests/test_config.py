from cdqai.core.config import load_config


def test_config_loads():
    config = load_config()
    assert config.short_name == "CDQAI"
    assert config.version == "2.0.2"
