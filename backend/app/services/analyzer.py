import os
import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from radon.complexity import cc_visit
from radon.metrics import mi_visit, h_visit
from radon.raw import analyze
import subprocess

class CodeAnalyzer:
    """Analyze code for technical debt and quality metrics"""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.results = {
            "total_lines": 0,
            "total_files": 0,
            "average_complexity": 0.0,
            "maintainability_index": 0.0,
            "debt_items": [],
            "suggestions": [],
            "metrics": {}
        }

    def analyze_repository(self) -> Dict[str, Any]:
        """Analyze entire repository"""
        python_files = list(self.repo_path.rglob("*.py"))
        js_files = list(self.repo_path.rglob("*.js")) + list(self.repo_path.rglob("*.jsx"))
        ts_files = list(self.repo_path.rglob("*.ts")) + list(self.repo_path.rglob("*.tsx"))

        all_files = python_files + js_files + ts_files
        self.results["total_files"] = len(all_files)

        # Analyze Python files
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue
            self._analyze_python_file(file_path)

        # Analyze JavaScript/TypeScript files
        for file_path in js_files + ts_files:
            if self._should_skip_file(file_path):
                continue
            self._analyze_js_file(file_path)

        # Run security analysis
        self._run_security_analysis()

        # Calculate aggregate metrics
        self._calculate_aggregate_metrics()

        return self.results

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_dirs = {"node_modules", ".git", "__pycache__", "venv", "env", "dist", "build", ".next"}
        return any(skip_dir in file_path.parts for skip_dir in skip_dirs)

    def _analyze_python_file(self, file_path: Path):
        """Analyze Python file for complexity and issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Skip if file is too large
            if len(content) > 1024 * 1024:  # 1MB
                return

            relative_path = str(file_path.relative_to(self.repo_path))

            # Raw metrics
            raw_metrics = analyze(content)
            self.results["total_lines"] += raw_metrics.loc

            # Cyclomatic complexity
            try:
                complexity_results = cc_visit(content)
                for result in complexity_results:
                    if result.complexity > 10:
                        self.results["debt_items"].append({
                            "file_path": relative_path,
                            "line_number": result.lineno,
                            "debt_type": "complexity",
                            "severity": "high" if result.complexity > 20 else "medium",
                            "title": f"High complexity in {result.name}",
                            "description": f"Cyclomatic complexity of {result.complexity} exceeds recommended threshold of 10",
                            "complexity_score": float(result.complexity),
                            "estimated_effort_hours": result.complexity * 0.5
                        })

                        # Generate suggestion
                        self.results["suggestions"].append({
                            "file_path": relative_path,
                            "line_start": result.lineno,
                            "suggestion_type": "refactor_complexity",
                            "title": f"Reduce complexity in {result.name}",
                            "description": "Consider breaking this function into smaller, more manageable pieces",
                            "priority": 2 if result.complexity > 20 else 1,
                            "confidence": 0.8,
                            "impact": "high" if result.complexity > 20 else "medium"
                        })
            except Exception:
                pass

            # Maintainability index
            try:
                mi_results = mi_visit(content, True)
                if mi_results < 20:
                    self.results["debt_items"].append({
                        "file_path": relative_path,
                        "line_number": 1,
                        "debt_type": "maintainability",
                        "severity": "high",
                        "title": "Low maintainability index",
                        "description": f"Maintainability index of {mi_results:.2f} is below recommended threshold of 20",
                        "estimated_effort_hours": 2.0
                    })
            except Exception:
                pass

            # Check for code smells
            self._detect_python_code_smells(content, relative_path)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def _detect_python_code_smells(self, content: str, file_path: str):
        """Detect common Python code smells"""
        lines = content.split('\n')

        # Long functions
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                    if func_lines > 50:
                        self.results["debt_items"].append({
                            "file_path": file_path,
                            "line_number": node.lineno,
                            "debt_type": "code_smell",
                            "severity": "medium",
                            "title": f"Long function: {node.name}",
                            "description": f"Function has {func_lines} lines, consider breaking it down",
                            "estimated_effort_hours": 1.5
                        })

                # Too many parameters
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    param_count = len(node.args.args)
                    if param_count > 5:
                        self.results["debt_items"].append({
                            "file_path": file_path,
                            "line_number": node.lineno,
                            "debt_type": "code_smell",
                            "severity": "low",
                            "title": f"Too many parameters in {node.name}",
                            "description": f"Function has {param_count} parameters, consider using a config object",
                            "estimated_effort_hours": 0.5
                        })
        except Exception:
            pass

        # Detect TODO/FIXME comments
        for i, line in enumerate(lines, 1):
            if "TODO" in line or "FIXME" in line:
                self.results["debt_items"].append({
                    "file_path": file_path,
                    "line_number": i,
                    "debt_type": "code_smell",
                    "severity": "low",
                    "title": "TODO/FIXME comment found",
                    "description": line.strip(),
                    "code_snippet": line.strip(),
                    "estimated_effort_hours": 0.25
                })

    def _analyze_js_file(self, file_path: Path):
        """Analyze JavaScript/TypeScript file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if len(content) > 1024 * 1024:  # 1MB
                return

            relative_path = str(file_path.relative_to(self.repo_path))
            lines = content.split('\n')
            self.results["total_lines"] += len(lines)

            # Detect console.log statements
            for i, line in enumerate(lines, 1):
                if re.search(r'console\.(log|warn|error|debug)', line) and not line.strip().startswith('//'):
                    self.results["debt_items"].append({
                        "file_path": relative_path,
                        "line_number": i,
                        "debt_type": "code_smell",
                        "severity": "low",
                        "title": "Console statement found",
                        "description": "Remove console statements before production",
                        "code_snippet": line.strip(),
                        "estimated_effort_hours": 0.1
                    })

            # Detect TODO/FIXME
            for i, line in enumerate(lines, 1):
                if "TODO" in line or "FIXME" in line:
                    self.results["debt_items"].append({
                        "file_path": relative_path,
                        "line_number": i,
                        "debt_type": "code_smell",
                        "severity": "low",
                        "title": "TODO/FIXME comment found",
                        "description": line.strip(),
                        "code_snippet": line.strip(),
                        "estimated_effort_hours": 0.25
                    })

            # Check for large files
            if len(lines) > 500:
                self.results["debt_items"].append({
                    "file_path": relative_path,
                    "line_number": 1,
                    "debt_type": "maintainability",
                    "severity": "medium",
                    "title": "Large file",
                    "description": f"File has {len(lines)} lines, consider splitting into smaller modules",
                    "estimated_effort_hours": 2.0
                })

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def _run_security_analysis(self):
        """Run security analysis using Bandit"""
        try:
            result = subprocess.run(
                ["bandit", "-r", str(self.repo_path), "-f", "json", "-q"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0 or result.returncode == 1:
                import json
                data = json.loads(result.stdout)

                for issue in data.get("results", []):
                    self.results["debt_items"].append({
                        "file_path": issue["filename"].replace(str(self.repo_path) + "/", ""),
                        "line_number": issue["line_number"],
                        "debt_type": "security",
                        "severity": issue["issue_severity"].lower(),
                        "title": issue["issue_text"],
                        "description": f"{issue['issue_text']} - {issue.get('more_info', '')}",
                        "code_snippet": issue.get("code", ""),
                        "estimated_effort_hours": 1.0 if issue["issue_severity"] == "HIGH" else 0.5
                    })
        except Exception as e:
            print(f"Security analysis failed: {e}")

    def _calculate_aggregate_metrics(self):
        """Calculate aggregate metrics"""
        if self.results["debt_items"]:
            # Count by severity
            severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            total_complexity = 0
            complexity_count = 0

            for item in self.results["debt_items"]:
                severity = item.get("severity", "low")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

                if "complexity_score" in item:
                    total_complexity += item["complexity_score"]
                    complexity_count += 1

            self.results["critical_issues"] = severity_counts["critical"]
            self.results["high_issues"] = severity_counts["high"]
            self.results["medium_issues"] = severity_counts["medium"]
            self.results["low_issues"] = severity_counts["low"]

            if complexity_count > 0:
                self.results["average_complexity"] = total_complexity / complexity_count

            # Technical debt ratio (debt items per 1000 lines of code)
            if self.results["total_lines"] > 0:
                self.results["technical_debt_ratio"] = (
                    len(self.results["debt_items"]) / self.results["total_lines"]
                ) * 1000

        self.results["total_debt_items"] = len(self.results["debt_items"])
