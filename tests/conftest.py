"""Shared pytest configuration for the BioStudio test suite."""


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "network: test makes a real network call (e.g. RCSB PDB fetch). "
        "Free, no API key, but requires internet access to pass.",
    )
