"""
Basic unit tests to validate test framework setup - no external dependencies
"""

import pytest
import sys
import os
from pathlib import Path


@pytest.mark.unit
def test_python_version():
    """Test that we're running on a supported Python version"""
    assert sys.version_info >= (3, 8), f"Python 3.8+ required, got {sys.version_info}"


@pytest.mark.unit
def test_pytest_markers():
    """Test that pytest markers are working"""
    # This test should have the 'unit' marker
    pass


@pytest.mark.unit
def test_project_structure():
    """Test that basic project structure exists"""
    project_root = Path(__file__).parent.parent.parent
    
    # Check essential directories
    assert (project_root / "backend").exists(), "backend directory should exist"
    assert (project_root / "tests").exists(), "tests directory should exist"
    assert (project_root / "tests" / "unit").exists(), "tests/unit directory should exist"
    assert (project_root / "tests" / "integration").exists(), "tests/integration directory should exist"
    assert (project_root / "tests" / "api").exists(), "tests/api directory should exist"


@pytest.mark.unit
def test_required_packages():
    """Test that required testing packages are available"""
    try:
        import pytest
        assert pytest is not None
    except ImportError:
        pytest.fail("pytest is not available")
    
    try:
        import numpy
        assert numpy is not None
    except ImportError:
        pytest.fail("numpy is not available")
    
    try:
        import sqlite3
        assert sqlite3 is not None
    except ImportError:
        pytest.fail("sqlite3 is not available")


@pytest.mark.unit
def test_basic_math():
    """Test basic mathematical operations"""
    assert 2 + 2 == 4
    assert 5 * 6 == 30
    assert 10 / 2 == 5.0
    assert 2 ** 3 == 8


@pytest.mark.unit
def test_string_operations():
    """Test string operations"""
    test_str = "Hello, World!"
    assert len(test_str) == 13
    assert test_str.lower() == "hello, world!"
    assert test_str.upper() == "HELLO, WORLD!"
    assert test_str.replace("World", "pytest") == "Hello, pytest!"


@pytest.mark.unit
def test_list_operations():
    """Test list operations"""
    test_list = [1, 2, 3]
    test_list.append(4)
    assert len(test_list) == 4
    assert test_list[0] == 1
    assert test_list[-1] == 4
    
    test_list.extend([5, 6])
    assert len(test_list) == 6
    assert sum(test_list) == 21


@pytest.mark.unit
def test_dict_operations():
    """Test dictionary operations"""
    test_dict = {"a": 1, "b": 2, "c": 3}
    assert len(test_dict) == 3
    assert test_dict["a"] == 1
    
    test_dict["d"] = 4
    assert len(test_dict) == 4
    assert "d" in test_dict
    assert test_dict.get("e", 0) == 0


@pytest.mark.unit
def test_file_path_operations():
    """Test path operations"""
    test_path = Path("/test/path/file.txt")
    assert test_path.name == "file.txt"
    assert test_path.suffix == ".txt"
    assert test_path.stem == "file"
    assert str(test_path.parent) == "/test/path" or str(test_path.parent) == "\\test\\path"


@pytest.mark.unit
def test_exception_handling():
    """Test exception handling"""
    with pytest.raises(ZeroDivisionError):
        result = 1 / 0
    
    with pytest.raises(KeyError):
        test_dict = {"a": 1}
        value = test_dict["b"]
    
    with pytest.raises(IndexError):
        test_list = [1, 2, 3]
        value = test_list[10]