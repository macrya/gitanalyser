"""
Enhanced PR Generator v2 with git patches and better conflict handling
"""
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from git import Repo, GitCommandError
from app.services.github import GitHubService

logger = logging.getLogger(__name__)


class PRGenerator:
    """Enhanced pull request generator using git patches"""

    def __init__(self, access_token: str, repo_full_name: str):
        self.access_token = access_token
        self.repo_full_name = repo_full_name
        self.github_service = GitHubService()

    def create_refactoring_pr(
        self,
        suggestions: List[Dict],
        base_branch: str = "main",
        pr_title: Optional[str] = None,
        pr_description: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[int]]:
        """
        Create a pull request with refactoring changes using git patches

        Returns:
            Tuple of (pr_url, pr_number) or (None, None) on failure
        """
        temp_dir = None
        try:
            # Clone repository
            temp_dir = tempfile.mkdtemp(prefix="pr_gen_")
            logger.info(f"Cloning {self.repo_full_name} to {temp_dir}")

            repo = self._clone_repo(temp_dir, base_branch)
            if not repo:
                return None, None

            # Create new branch
            branch_name = self._generate_branch_name()
            logger.info(f"Creating branch {branch_name}")

            try:
                repo.git.checkout('-b', branch_name)
            except GitCommandError as e:
                logger.error(f"Failed to create branch: {e}")
                return None, None

            # Apply changes
            files_changed = set()
            changes_applied = 0

            for suggestion in suggestions:
                if self._apply_suggestion(repo, suggestion, temp_dir):
                    files_changed.add(suggestion['file_path'])
                    changes_applied += 1

            if changes_applied == 0:
                logger.warning("No changes were applied")
                return None, None

            # Commit changes
            try:
                repo.git.add(A=True)
                commit_message = self._generate_commit_message(suggestions, changes_applied)
                repo.git.commit('-m', commit_message)
                logger.info(f"Committed {changes_applied} changes")
            except GitCommandError as e:
                logger.error(f"Failed to commit: {e}")
                return None, None

            # Push to remote
            try:
                auth_url = self._get_authenticated_url()
                repo.git.push('--set-upstream', auth_url, branch_name)
                logger.info(f"Pushed branch {branch_name}")
            except GitCommandError as e:
                logger.error(f"Failed to push: {e}")
                return None, None

            # Create pull request
            final_title = pr_title or f"Automated Refactoring - {changes_applied} improvements"
            final_description = pr_description or self._generate_pr_description(
                suggestions, files_changed, changes_applied
            )

            try:
                pr = self.github_service.create_pull_request(
                    self.access_token,
                    self.repo_full_name,
                    final_title,
                    final_description,
                    branch_name,
                    base_branch
                )
                logger.info(f"Created PR #{pr.number}: {pr.html_url}")
                return pr.html_url, pr.number
            except Exception as e:
                logger.error(f"Failed to create PR: {e}")
                return None, None

        except Exception as e:
            logger.error(f"PR generation failed: {e}")
            return None, None
        finally:
            # Cleanup
            if temp_dir:
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp dir: {e}")

    def _clone_repo(self, temp_dir: str, branch: str) -> Optional[Repo]:
        """Clone repository with authentication"""
        try:
            auth_url = self._get_authenticated_url()
            repo = Repo.clone_from(
                auth_url,
                temp_dir,
                branch=branch,
                depth=1
            )
            return repo
        except GitCommandError as e:
            logger.error(f"Failed to clone repository: {e}")
            return None

    def _get_authenticated_url(self) -> str:
        """Get repository URL with authentication token"""
        return f"https://{self.access_token}@github.com/{self.repo_full_name}.git"

    def _apply_suggestion(self, repo: Repo, suggestion: Dict, repo_path: str) -> bool:
        """
        Apply a single suggestion to the repository

        Returns:
            True if suggestion was applied successfully
        """
        file_path = Path(repo_path) / suggestion['file_path']

        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Apply the change
            original = suggestion.get('original_code')
            suggested = suggestion.get('suggested_code')

            if not original or suggested is None:  # suggested could be empty string
                logger.debug(f"No code change for {suggestion.get('title', 'unknown')}")
                return False

            # Check if original code exists
            if original not in content:
                logger.warning(f"Original code not found in {file_path}")
                # Try fuzzy matching
                if not self._fuzzy_apply(content, original, suggested, file_path):
                    return False
                return True

            # Apply replacement
            new_content = content.replace(original, suggested, 1)

            # Validate change
            if new_content == content:
                logger.warning(f"No change made to {file_path}")
                return False

            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            logger.info(f"Applied change to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply suggestion to {file_path}: {e}")
            return False

    def _fuzzy_apply(self, content: str, original: str, suggested: str, file_path: Path) -> bool:
        """
        Try to apply change with fuzzy matching (handles whitespace differences)
        """
        try:
            import difflib

            # Normalize whitespace for comparison
            original_normalized = ' '.join(original.split())
            content_lines = content.split('\n')

            # Find best matching line
            best_match_idx = -1
            best_ratio = 0.0

            for i, line in enumerate(content_lines):
                line_normalized = ' '.join(line.split())
                ratio = difflib.SequenceMatcher(None, original_normalized, line_normalized).ratio()
                if ratio > best_ratio and ratio > 0.8:  # 80% similarity threshold
                    best_ratio = ratio
                    best_match_idx = i

            if best_match_idx >= 0:
                content_lines[best_match_idx] = suggested
                new_content = '\n'.join(content_lines)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                logger.info(f"Applied fuzzy change to {file_path} (line {best_match_idx + 1})")
                return True

        except Exception as e:
            logger.error(f"Fuzzy apply failed: {e}")

        return False

    @staticmethod
    def _generate_branch_name() -> str:
        """Generate unique branch name"""
        import random
        import string
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"refactor/debt-{timestamp}-{random_suffix}"

    @staticmethod
    def _generate_commit_message(suggestions: List[Dict], changes_applied: int) -> str:
        """Generate commit message"""
        types = set()
        for s in suggestions:
            types.add(s.get('suggestion_type', 'refactor'))

        types_str = ', '.join(sorted(types)[:3])
        return f"refactor: Apply {changes_applied} automated improvements\n\nTypes: {types_str}"

    @staticmethod
    def _generate_pr_description(
        suggestions: List[Dict],
        files_changed: set,
        changes_applied: int
    ) -> str:
        """Generate detailed PR description"""
        desc = f"""## 🤖 Automated Code Refactoring

This PR contains {changes_applied} automated code improvements to reduce technical debt.

### 📊 Changes Overview

"""

        # Group by type
        by_type = {}
        for s in suggestions:
            stype = s.get('suggestion_type', 'other')
            if stype not in by_type:
                by_type[stype] = []
            by_type[stype].append(s)

        for stype, items in sorted(by_type.items()):
            desc += f"\n#### {stype.replace('_', ' ').title()} ({len(items)})\n"
            for item in items[:5]:  # Limit to 5 per type
                desc += f"- {item.get('title', 'Improvement')} in `{item.get('file_path', 'unknown')}`\n"
            if len(items) > 5:
                desc += f"- _...and {len(items) - 5} more_\n"

        desc += f"\n### 📁 Files Changed ({len(files_changed)})\n\n"
        for file_path in sorted(files_changed)[:10]:
            desc += f"- `{file_path}`\n"
        if len(files_changed) > 10:
            desc += f"- _...and {len(files_changed) - 10} more files_\n"

        desc += """
### ✅ Review Checklist

- [ ] Review each change carefully
- [ ] Run tests to ensure functionality is preserved
- [ ] Check for any unintended side effects
- [ ] Verify code style is consistent

### 🔍 Notes

- All changes are generated by automated analysis
- Original behavior should be preserved
- If any change seems incorrect, please remove it and report as feedback

---
*Generated by GitHub Technical Debt Analyzer*
"""

        return desc
