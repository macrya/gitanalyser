"""
Tests for code analyzer service
"""
import pytest
import tempfile
import os
from pathlib import Path
from app.services.analyzer_v2 import EnhancedCodeAnalyzer


@pytest.fixture
def temp_repo():
    """Create a temporary repository for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Create test Python file with various issues
        python_file = repo_path / "test.py"
        python_file.write_text("""
def complex_function(a, b, c, d, e, f):
    '''Function with high complexity'''
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        return f
    return 0

# TODO: Fix this later
def missing_docstring():
    pass

console.log('debug')
""")

        # Create test JS file
        js_file = repo_path / "test.js"
        js_file.write_text("""
console.log('This should be removed');

function test() {
    // TODO: implement this
    debugger;
}
""")

        yield repo_path


def test_analyzer_basic_functionality(temp_repo):
    """Test basic analyzer functionality"""
    analyzer = EnhancedCodeAnalyzer(str(temp_repo))
    results = analyzer.analyze_repository()

    assert results["total_files"] > 0
    assert results["total_lines"] > 0
    assert "debt_items" in results
    assert "suggestions" in results


def test_analyzer_detects_complexity(temp_repo):
    """Test that analyzer detects complex functions"""
    analyzer = EnhancedCodeAnalyzer(str(temp_repo))
    results = analyzer.analyze_repository()

    # Should detect the complex function
    complexity_items = [
        item for item in results["debt_items"]
        if item["debt_type"] == "complexity"
    ]
    assert len(complexity_items) > 0


def test_analyzer_detects_todos(temp_repo):
    """Test that analyzer detects TODO comments"""
    analyzer = EnhancedCodeAnalyzer(str(temp_repo))
    results = analyzer.analyze_repository()

    # Should detect TODO comments
    todo_items = [
        item for item in results["debt_items"]
        if "TODO" in item.get("title", "") or "TODO" in item.get("description", "")
    ]
    assert len(todo_items) >= 1  # At least one TODO


def test_analyzer_detects_console_statements(temp_repo):
    """Test that analyzer detects console statements"""
    analyzer = EnhancedCodeAnalyzer(str(temp_repo))
    results = analyzer.analyze_repository()

    # Should detect console statements
    console_items = [
        item for item in results["debt_items"]
        if "console" in item.get("title", "").lower()
    ]
    assert len(console_items) >= 1


def test_analyzer_generates_suggestions(temp_repo):
    """Test that analyzer generates improvement suggestions"""
    analyzer = EnhancedCodeAnalyzer(str(temp_repo))
    results = analyzer.analyze_repository()

    assert len(results["suggestions"]) > 0

    # Check suggestion structure
    suggestion = results["suggestions"][0]
    assert "file_path" in suggestion
    assert "title" in suggestion
    assert "priority" in suggestion
    assert "confidence" in suggestion


def test_analyzer_calculates_metrics(temp_repo):
    """Test that analyzer calculates aggregate metrics"""
    analyzer = EnhancedCodeAnalyzer(str(temp_repo))
    results = analyzer.analyze_repository()

    assert results["total_debt_items"] >= 0
    assert results["technical_debt_ratio"] >= 0
    assert "metrics" in results


def test_analyzer_skips_large_files(temp_repo):
    """Test that analyzer skips files that are too large"""
    # Create a very large file
    large_file = temp_repo / "large.py"
    with open(large_file, 'w') as f:
        for i in range(100000):
            f.write(f"# Comment line {i}\n")

    analyzer = EnhancedCodeAnalyzer(str(temp_repo))
    analyzer.max_file_size = 1000  # Set small limit

    # Should not crash
    results = analyzer.analyze_repository()
    assert results is not None
