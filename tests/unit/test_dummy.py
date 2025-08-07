"""
Dummy unit tests to validate test setup
"""

import pytest


@pytest.mark.unit
def test_dummy_unit_passing():
    """Basic unit test that should always pass"""
    assert True


@pytest.mark.unit
def test_dummy_unit_math():
    """Test basic math operations"""
    assert 1 + 1 == 2
    assert 2 * 3 == 6
    assert 10 / 2 == 5.0


@pytest.mark.unit
def test_dummy_unit_strings():
    """Test basic string operations"""
    assert "hello" + " " + "world" == "hello world"
    assert "test".upper() == "TEST"
    assert len("pytest") == 6


@pytest.mark.unit
def test_dummy_unit_lists():
    """Test basic list operations"""
    test_list = [1, 2, 3]
    test_list.append(4)
    assert len(test_list) == 4
    assert test_list[-1] == 4


@pytest.mark.unit
@pytest.mark.mock
def test_dummy_unit_with_fixture(mock_analyzer):
    """Test using a mocked fixture"""
    # Test that our mock analyzer fixture works
    assert mock_analyzer is not None
    assert hasattr(mock_analyzer, 'analyze_track')
    assert hasattr(mock_analyzer, 'get_supported_formats')
    
    # Test mock behavior
    formats = mock_analyzer.get_supported_formats()
    assert isinstance(formats, list)
    assert ".mp3" in formats