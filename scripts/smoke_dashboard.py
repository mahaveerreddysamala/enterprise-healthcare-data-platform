"""Execute the Streamlit dashboard headlessly for CI smoke validation."""
from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


def main() -> None:
    app = Path(__file__).parents[1] / "dashboard" / "healthcare_app.py"
    test = AppTest.from_file(str(app), default_timeout=60).run()
    if test.exception:
        raise AssertionError(f"Dashboard raised exceptions: {test.exception}")
    titles = [element.value for element in test.title]
    if "Enterprise Healthcare Data Platform" not in titles:
        raise AssertionError(f"Expected dashboard title, found: {titles}")
    if len(test.metric) < 5:
        raise AssertionError("Expected at least five executive metrics")
    print(f"Dashboard smoke passed with {len(test.metric)} rendered metrics")


if __name__ == "__main__":
    main()
