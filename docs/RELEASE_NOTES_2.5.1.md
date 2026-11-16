<!-- CDQAI file version: 2.5.1 -->
# CDQAI 2.5.1 — Public Configuration Privacy

## What changed

- Replaces provider-specific record labels and source mappings in public code and documentation with generic crash, vehicle, and person concepts.
- Uses generic placeholders in the public configuration example and preserves local source mappings in ignored configuration.
- Updates the optional-feature setup so it does not replace source mappings or cache names.
- Retains the 2.5.0 dashboard, pagination, factor-review, and analysis behavior.

## Configuration

Copy `config/config.example.yaml` to the ignored `config/config.yaml` and
configure the source identifiers, connection settings, and field names for your
environment. Never publish local configuration, data, or connection details.

## Validation

Automated tests use fabricated records and mocked source reads. No private
configuration or live data source is required for validation.
