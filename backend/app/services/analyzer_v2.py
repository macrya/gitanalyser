"""
Enhanced Code Analyzer v2 with AST-based analysis and better insights
"""
import os
import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from radon.complexity import cc_visit, ComplexityVisitor
from radon.metrics import mi_visit, h_visit
from radon.raw import analyze
import subprocess
import logging
from collections import defaultdict
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Structured analysis result"""
    total_lines: int = 0
    total_files: int = 0
    average_complexity: float = 0.0
    maintainability_index: float = 0.0
    technical_debt_ratio: float = 0.0
    total_debt_items: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    debt_items: List[Dict[str, Any]] = None
    suggestions: List[Dict[str, Any]] = None
    metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.debt_items is None:
            self.debt_items = []
        if self.suggestions is None:
            self.suggestions = []
        if self.metrics is None:
            self.metrics = {}


class EnhancedCodeAnalyzer:
    """Enhanced code analyzer with better analysis capabilities"""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.result = AnalysisResult()
        self.complexity_by_file = {}
        self.max_file_size = 1024 * 1024  # 1MB

    def analyze_repository(self) -> Dict[str, Any]:
        """Analyze entire repository with enhanced capabilities"""
        try:
            logger.info(f"Starting analysis of {self.repo_path}")

            # Discover files
            python_files = list(self.repo_path.rglob("*.py"))
            js_files = list(self.repo_path.rglob("*.js")) + list(self.repo_path.rglob("*.jsx"))
            ts_files = list(self.repo_path.rglob("*.ts")) + list(self.repo_path.rglob("*.tsx"))

            all_files = python_files + js_files + ts_files
            self.result.total_files = len([f for f in all_files if not self._should_skip_file(f)])

            logger.info(f"Found {self.result.total_files} files to analyze")

            # Analyze Python files
            for file_path in python_files:
                if self._should_skip_file(file_path):
                    continue
                self._analyze_python_file_enhanced(file_path)

            # Analyze JavaScript/TypeScript files
            for file_path in js_files + ts_files:
                if self._should_skip_file(file_path):
                    continue
                self._analyze_js_file_enhanced(file_path)

            # Run security analysis
            self._run_security_analysis()

            # Detect code duplication
            self._detect_duplication()

            # Calculate aggregate metrics
            self._calculate_aggregate_metrics()

            logger.info(f"Analysis complete: {self.result.total_debt_items} issues found")

            return asdict(self.result)

        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_dirs = {
            "node_modules", ".git", "__pycache__", "venv", "env",
            "dist", "build", ".next", "coverage", ".pytest_cache",
            "migrations", "alembic"
        }
        skip_files = {"__init__.py"}

        # Skip if in excluded directory
        if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
            return True

        # Skip if excluded filename
        if file_path.name in skip_files:
            return True

        # Skip if file is too large
        try:
            if file_path.stat().st_size > self.max_file_size:
                logger.warning(f"Skipping large file: {file_path}")
                return True
        except Exception:
            return True

        return False

    def _analyze_python_file_enhanced(self, file_path: Path):
        """Enhanced Python file analysis using AST"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            relative_path = str(file_path.relative_to(self.repo_path))

            # Raw metrics
            raw_metrics = analyze(content)
            self.result.total_lines += raw_metrics.loc

            # Parse AST
            try:
                tree = ast.parse(content, filename=str(file_path))
                self._analyze_ast(tree, relative_path, content)
            except SyntaxError as e:
                logger.warning(f"Syntax error in {relative_path}: {e}")
                self.result.debt_items.append({
                    "file_path": relative_path,
                    "line_number": e.lineno if hasattr(e, 'lineno') else 1,
                    "debt_type": "syntax_error",
                    "severity": "high",
                    "title": "Syntax Error",
                    "description": str(e),
                    "estimated_effort_hours": 0.5
                })

            # Cyclomatic complexity
            try:
                complexity_results = cc_visit(content)
                for result in complexity_results:
                    complexity_score = float(result.complexity)

                    if complexity_score > 10:
                        severity = self._get_complexity_severity(complexity_score)

                        self.result.debt_items.append({
                            "file_path": relative_path,
                            "line_number": result.lineno,
                            "debt_type": "complexity",
                            "severity": severity,
                            "title": f"High complexity in {result.name}",
                            "description": f"Cyclomatic complexity of {complexity_score} exceeds threshold",
                            "complexity_score": complexity_score,
                            "estimated_effort_hours": complexity_score * 0.5
                        })

                        # Generate refactoring suggestion
                        self.result.suggestions.append({
                            "file_path": relative_path,
                            "line_start": result.lineno,
                            "suggestion_type": "refactor_complexity",
                            "title": f"Refactor {result.name} to reduce complexity",
                            "description": self._generate_complexity_suggestion(complexity_score),
                            "priority": 3 if complexity_score > 20 else 2,
                            "confidence": 0.85,
                            "impact": "high" if complexity_score > 20 else "medium"
                        })

                    # Track complexity by file
                    if relative_path not in self.complexity_by_file:
                        self.complexity_by_file[relative_path] = []
                    self.complexity_by_file[relative_path].append(complexity_score)

            except Exception as e:
                logger.error(f"Complexity analysis failed for {relative_path}: {e}")

            # Maintainability index
            try:
                mi_score = mi_visit(content, True)
                if mi_score < 20:
                    self.result.debt_items.append({
                        "file_path": relative_path,
                        "line_number": 1,
                        "debt_type": "maintainability",
                        "severity": "high",
                        "title": "Low maintainability index",
                        "description": f"Maintainability index of {mi_score:.2f} is below threshold",
                        "estimated_effort_hours": 2.0
                    })
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")

    def _analyze_ast(self, tree: ast.AST, file_path: str, content: str):
        """Analyze Python AST for patterns"""
        lines = content.split('\n')

        for node in ast.walk(tree):
            # Check for long functions/methods
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_lines = (node.end_lineno - node.lineno) if hasattr(node, 'end_lineno') else 0

                if func_lines > 50:
                    self.result.debt_items.append({
                        "file_path": file_path,
                        "line_number": node.lineno,
                        "debt_type": "code_smell",
                        "severity": "medium",
                        "title": f"Long function: {node.name}",
                        "description": f"Function has {func_lines} lines (threshold: 50)",
                        "estimated_effort_hours": 1.5
                    })

                    self.result.suggestions.append({
                        "file_path": file_path,
                        "line_start": node.lineno,
                        "suggestion_type": "extract_method",
                        "title": f"Extract methods from {node.name}",
                        "description": "Break down into smaller, focused functions",
                        "priority": 2,
                        "confidence": 0.8,
                        "impact": "medium"
                    })

                # Check for too many parameters
                param_count = len(node.args.args)
                if param_count > 5:
                    self.result.debt_items.append({
                        "file_path": file_path,
                        "line_number": node.lineno,
                        "debt_type": "code_smell",
                        "severity": "low",
                        "title": f"Too many parameters: {node.name}",
                        "description": f"Function has {param_count} parameters (threshold: 5)",
                        "estimated_effort_hours": 0.5
                    })

                    self.result.suggestions.append({
                        "file_path": file_path,
                        "line_start": node.lineno,
                        "suggestion_type": "introduce_parameter_object",
                        "title": f"Use parameter object for {node.name}",
                        "description": "Consider using a configuration object or dataclass",
                        "priority": 1,
                        "confidence": 0.75,
                        "impact": "low"
                    })

            # Check for deeply nested code
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With)):
                depth = self._get_nesting_depth(node)
                if depth > 4:
                    self.result.debt_items.append({
                        "file_path": file_path,
                        "line_number": node.lineno,
                        "debt_type": "complexity",
                        "severity": "medium",
                        "title": "Deeply nested code",
                        "description": f"Nesting depth of {depth} exceeds threshold of 4",
                        "estimated_effort_hours": 1.0
                    })

            # Check for missing docstrings
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    self.result.debt_items.append({
                        "file_path": file_path,
                        "line_number": node.lineno,
                        "debt_type": "maintainability",
                        "severity": "low",
                        "title": f"Missing docstring: {node.name}",
                        "description": "Add documentation for better maintainability",
                        "estimated_effort_hours": 0.25
                    })

        # Check for TODO/FIXME comments
        for i, line in enumerate(lines, 1):
            if re.search(r'\b(TODO|FIXME|HACK|XXX)\b', line, re.IGNORECASE):
                self.result.debt_items.append({
                    "file_path": file_path,
                    "line_number": i,
                    "debt_type": "code_smell",
                    "severity": "low",
                    "title": "TODO/FIXME comment",
                    "description": line.strip(),
                    "code_snippet": line.strip(),
                    "estimated_effort_hours": 0.25
                })

    def _analyze_js_file_enhanced(self, file_path: Path):
        """Enhanced JavaScript/TypeScript file analysis"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            relative_path = str(file_path.relative_to(self.repo_path))
            lines = content.split('\n')
            self.result.total_lines += len(lines)

            # Detect console statements
            for i, line in enumerate(lines, 1):
                if re.search(r'console\.(log|warn|error|debug|info)', line) and not line.strip().startswith('//'):
                    self.result.debt_items.append({
                        "file_path": relative_path,
                        "line_number": i,
                        "debt_type": "code_smell",
                        "severity": "low",
                        "title": "Console statement",
                        "description": "Remove console statements before production",
                        "code_snippet": line.strip(),
                        "estimated_effort_hours": 0.1
                    })

                    self.result.suggestions.append({
                        "file_path": relative_path,
                        "line_start": i,
                        "suggestion_type": "remove_console",
                        "title": "Remove console statement",
                        "description": "Use proper logging or remove debug statements",
                        "original_code": line.strip(),
                        "suggested_code": "",
                        "priority": 1,
                        "confidence": 0.95,
                        "impact": "low"
                    })

            # Detect debugger statements
            for i, line in enumerate(lines, 1):
                if 'debugger' in line and not line.strip().startswith('//'):
                    self.result.debt_items.append({
                        "file_path": relative_path,
                        "line_number": i,
                        "debt_type": "code_smell",
                        "severity": "medium",
                        "title": "Debugger statement",
                        "description": "Remove debugger statements",
                        "code_snippet": line.strip(),
                        "estimated_effort_hours": 0.1
                    })

            # Check for large files
            if len(lines) > 500:
                self.result.debt_items.append({
                    "file_path": relative_path,
                    "line_number": 1,
                    "debt_type": "maintainability",
                    "severity": "medium",
                    "title": "Large file",
                    "description": f"File has {len(lines)} lines (threshold: 500)",
                    "estimated_effort_hours": 2.0
                })

            # Detect TODO/FIXME
            for i, line in enumerate(lines, 1):
                if re.search(r'\b(TODO|FIXME|HACK|XXX)\b', line, re.IGNORECASE):
                    self.result.debt_items.append({
                        "file_path": relative_path,
                        "line_number": i,
                        "debt_type": "code_smell",
                        "severity": "low",
                        "title": "TODO/FIXME comment",
                        "description": line.strip(),
                        "code_snippet": line.strip(),
                        "estimated_effort_hours": 0.25
                    })

        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")

    def _run_security_analysis(self):
        """Run security analysis with Bandit"""
        try:
            result = subprocess.run(
                ["bandit", "-r", str(self.repo_path), "-f", "json", "-q"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode in [0, 1]:  # 0 = no issues, 1 = issues found
                import json
                data = json.loads(result.stdout)

                for issue in data.get("results", []):
                    severity_map = {
                        "HIGH": "high",
                        "MEDIUM": "medium",
                        "LOW": "low"
                    }

                    self.result.debt_items.append({
                        "file_path": issue["filename"].replace(str(self.repo_path) + "/", ""),
                        "line_number": issue["line_number"],
                        "debt_type": "security",
                        "severity": severity_map.get(issue["issue_severity"], "medium"),
                        "title": issue["issue_text"],
                        "description": f"{issue['issue_text']} - {issue.get('more_info', '')}",
                        "code_snippet": issue.get("code", ""),
                        "estimated_effort_hours": 1.0 if issue["issue_severity"] == "HIGH" else 0.5
                    })
        except subprocess.TimeoutExpired:
            logger.warning("Security analysis timed out")
        except Exception as e:
            logger.warning(f"Security analysis failed: {e}")

    def _detect_duplication(self):
        """Detect code duplication patterns"""
        # Simple duplication detection based on line similarity
        # In production, use tools like CPD or jscpd
        pass

    def _calculate_aggregate_metrics(self):
        """Calculate aggregate metrics"""
        if self.result.debt_items:
            # Count by severity
            for item in self.result.debt_items:
                severity = item.get("severity", "low")
                if severity == "critical":
                    self.result.critical_issues += 1
                elif severity == "high":
                    self.result.high_issues += 1
                elif severity == "medium":
                    self.result.medium_issues += 1
                else:
                    self.result.low_issues += 1

            # Calculate average complexity
            all_complexities = []
            for complexities in self.complexity_by_file.values():
                all_complexities.extend(complexities)

            if all_complexities:
                self.result.average_complexity = sum(all_complexities) / len(all_complexities)

            # Technical debt ratio
            if self.result.total_lines > 0:
                self.result.technical_debt_ratio = (
                    len(self.result.debt_items) / self.result.total_lines
                ) * 1000

            self.result.total_debt_items = len(self.result.debt_items)

            # Additional metrics
            self.result.metrics = {
                "files_by_language": self._count_files_by_language(),
                "debt_by_type": self._count_debt_by_type(),
                "average_file_lines": self.result.total_lines / self.result.total_files if self.result.total_files > 0 else 0
            }

    def _count_files_by_language(self) -> Dict[str, int]:
        """Count files by language"""
        counts = defaultdict(int)
        for file_path in self.repo_path.rglob("*"):
            if file_path.is_file() and not self._should_skip_file(file_path):
                ext = file_path.suffix
                if ext in ['.py']:
                    counts['Python'] += 1
                elif ext in ['.js', '.jsx']:
                    counts['JavaScript'] += 1
                elif ext in ['.ts', '.tsx']:
                    counts['TypeScript'] += 1
        return dict(counts)

    def _count_debt_by_type(self) -> Dict[str, int]:
        """Count debt items by type"""
        counts = defaultdict(int)
        for item in self.result.debt_items:
            counts[item.get("debt_type", "unknown")] += 1
        return dict(counts)

    @staticmethod
    def _get_complexity_severity(complexity: float) -> str:
        """Get severity level based on complexity score"""
        if complexity > 50:
            return "critical"
        elif complexity > 20:
            return "high"
        elif complexity > 10:
            return "medium"
        return "low"

    @staticmethod
    def _generate_complexity_suggestion(complexity: float) -> str:
        """Generate specific suggestion based on complexity"""
        if complexity > 30:
            return "This function is extremely complex. Consider breaking it into multiple smaller functions, extracting helper methods, and simplifying control flow."
        elif complexity > 20:
            return "Consider extracting methods, reducing nesting levels, and simplifying conditional logic."
        else:
            return "Consider refactoring to reduce complexity. Look for opportunities to extract methods or simplify logic."

    @staticmethod
    def _get_nesting_depth(node: ast.AST, depth: int = 0) -> int:
        """Calculate nesting depth of AST node"""
        max_depth = depth
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With)):
                child_depth = depth + 1
                if child_depth > max_depth:
                    max_depth = child_depth
        return max_depth
