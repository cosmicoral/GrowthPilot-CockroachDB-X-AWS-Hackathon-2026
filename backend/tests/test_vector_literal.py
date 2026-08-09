from backend.database.database import to_vector_literal
import pytest


def test_to_vector_literal_formats_embedding():
    embedding = [0.1] * 1024

    result = to_vector_literal(embedding)

    assert result.startswith("[0.1,0.1")
    assert result.endswith("]")


def test_to_vector_literal_rejects_wrong_dimension():
    with pytest.raises(ValueError):
        to_vector_literal([0.1] * 10)