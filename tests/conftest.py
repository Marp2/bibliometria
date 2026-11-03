import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "scripts"))

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def corpus():
    from src.corpus import obtener_corpus
    return obtener_corpus()


@pytest.fixture(scope="session")
def cliente():
    from src.api import app
    app.config["TESTING"] = True
    return app.test_client()
