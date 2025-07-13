"""Linting guards that provide auto-fix capabilities and code quality feedback.

REMINDER: Update HOOKS.md when modifying guards!
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_guard import BaseGuard, GuardAction, GuardContext, GuardResult  # noqa: E402


class LintGuard(BaseGuard):
    """
    Master linting guard that provides real-time auto-fix capabilities.

    This guard never blocks operations - it only provides helpful feedback
    and auto-fixes issues when possible.

    Features:
    - Auto-fixes: trailing whitespace, missing newlines, Python formatting
    - Auto-fixes: import sorting, JSON formatting, YAML formatting
    - Auto-fixes: JS/TS formatting, CSS formatting
    - Provides: Helpful suggestions for unfixable issues
    - Never blocks: All feedback is informational only
    """

    def __init__(self):
        super().__init__(
            name="Code Linting and Auto-fix", description="Provides real-time linting with auto-fix capabilities"
        )
        self.excluded_dirs = ["archive/", "temp/", "test-screenshots/", ".git/"]

    def should_trigger(self, context: GuardContext) -> bool:
        """Trigger for Edit, Write, and MultiEdit operations on files."""
        if context.tool_name not in ["Edit", "Write", "MultiEdit"]:
            return False

        if not context.file_path:
            return False

        # Skip if file doesn't exist (can't lint non-existent files)
        if not os.path.isfile(context.file_path):
            return False

        # Skip excluded directories
        return all(not context.file_path.startswith(excluded) for excluded in self.excluded_dirs)

    def get_message(self, context: GuardContext) -> str:
        """Run linting and return feedback message."""
        file_path = context.file_path
        messages = []

        # Apply generic fixes first
        generic_fixes = self._apply_generic_fixes(file_path)
        if generic_fixes:
            messages.extend(generic_fixes)

        # Run file-type specific linting
        file_ext = Path(file_path).suffix.lower()

        if file_ext == ".py":
            messages.extend(self._run_python_linters(file_path))
        elif file_ext == ".json":
            messages.extend(self._run_json_linters(file_path))
        elif file_ext in [".yaml", ".yml"]:
            messages.extend(self._run_yaml_linters(file_path))
        elif file_ext in [".sh", ".bash"]:
            messages.extend(self._run_shell_linters(file_path))
        elif file_ext in [".js", ".jsx", ".ts", ".tsx", ".mjs"]:
            messages.extend(self._run_javascript_linters(file_path))
        elif file_ext in [".css", ".scss", ".less"]:
            messages.extend(self._run_css_linters(file_path))

        if messages:
            return "\n".join(messages)

        return f"✅ Code quality check completed for {file_path}"

    def get_default_action(self) -> GuardAction:
        """Always allow - linting never blocks operations."""
        return GuardAction.ALLOW

    def check(self, context: GuardContext, is_interactive: bool = False) -> GuardResult:
        """
        Override check method to never block operations.

        The lint guard provides feedback but never blocks, regardless of
        interactive mode or issues found.
        """
        if not self.should_trigger(context):
            return GuardResult(should_block=False)

        message = self.get_message(context)

        # Always allow - never block for linting issues
        return GuardResult(should_block=False, message=message)

    def _apply_generic_fixes(self, file_path: str) -> List[str]:
        """Apply generic fixes that work for all file types."""
        messages = []
        fixed_trailing = False
        fixed_newline = False

        try:
            # Read file content
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            if not lines:
                return messages

            original_lines = lines.copy()

            # Fix trailing whitespace
            for i, line in enumerate(lines):
                if line.rstrip() != line.rstrip("\n\r"):
                    lines[i] = line.rstrip() + "\n"
                    fixed_trailing = True

            # Fix missing final newline
            if lines and not lines[-1].endswith("\n"):
                lines[-1] += "\n"
                fixed_newline = True

            # Write back if changes were made
            if lines != original_lines:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)

                if fixed_trailing:
                    messages.append(f"✅ Fixed trailing whitespace in {file_path}")
                if fixed_newline:
                    messages.append(f"✅ Added missing final newline in {file_path}")

        except (OSError, UnicodeDecodeError) as e:
            messages.append(f"⚠️ Could not apply generic fixes to {file_path}: {str(e)}")

        return messages

    def _run_python_linters(self, file_path: str) -> List[str]:
        """Run Python-specific linters and auto-fixes."""
        messages = []
        fixed_issues = False
        issues_found = False

        # Auto-fix with ruff (fast and comprehensive)
        if self._command_exists("ruff"):
            try:
                # First try to auto-fix
                result = subprocess.run(
                    ["ruff", "check", "--fix", file_path, "--quiet"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    fixed_issues = True

                # Check if any issues remain
                result = subprocess.run(["ruff", "check", file_path, "--quiet"], capture_output=True, text=True)
                if result.returncode != 0:
                    issues_found = True
                    messages.append(f"⚠️ Python style issues remain in {file_path} after auto-fix")
                    messages.append(f"Run: ruff check '{file_path}' to see remaining issues")

            except subprocess.SubprocessError:
                pass

        # Auto-fix formatting with black
        if self._command_exists("black"):
            try:
                result = subprocess.run(
                    ["black", "--line-length=120", "--quiet", file_path], capture_output=True, text=True
                )
                if result.returncode == 0:
                    fixed_issues = True
            except subprocess.SubprocessError:
                pass

        # Auto-fix imports with isort
        if self._command_exists("isort"):
            try:
                result = subprocess.run(
                    ["isort", "--profile=black", "--line-length=120", "--quiet", file_path],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    fixed_issues = True
            except subprocess.SubprocessError:
                pass

        # Check with flake8 for additional issues
        if self._command_exists("flake8"):
            try:
                result = subprocess.run(["flake8", "--config=.flake8", file_path], capture_output=True, text=True)
                if result.returncode != 0:
                    issues_found = True
                    messages.append(f"⚠️ Code style issues found in {file_path}")
                    messages.append(f"Run: flake8 '{file_path}' for detailed analysis")
            except subprocess.SubprocessError:
                pass

        # Generate summary message
        if fixed_issues and issues_found:
            messages.insert(0, f"🔧 Auto-fixed Python issues, some manual fixes may still be needed in {file_path}")
        elif fixed_issues:
            messages.insert(0, f"✅ Auto-fixed Python code style in {file_path}")
        elif issues_found:
            messages.insert(0, f"ℹ️ Python linting suggestions available for {file_path}")

        return messages

    def _run_json_linters(self, file_path: str) -> List[str]:
        """Run JSON linting and auto-formatting."""
        messages = []

        try:
            # Check JSON syntax and auto-format
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # Auto-format JSON (pretty print)
            formatted_json = json.dumps(data, indent=2, ensure_ascii=False)

            with open(file_path, encoding="utf-8") as f:
                original_content = f.read()

            if formatted_json + "\n" != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(formatted_json + "\n")
                messages.append(f"✅ Auto-formatted JSON in {file_path}")

        except json.JSONDecodeError as e:
            messages.append(f"⚠️ JSON syntax error in {file_path}: {str(e)}")
            messages.append(f"Run: python3 -m json.tool '{file_path}' to see specific errors")
        except (OSError, UnicodeDecodeError) as e:
            messages.append(f"⚠️ Could not process JSON file {file_path}: {str(e)}")

        return messages

    def _run_yaml_linters(self, file_path: str) -> List[str]:
        """Run YAML linting and auto-formatting."""
        messages = []
        fixed_issues = False
        issues_found = False

        try:
            import yaml

            # Try to reformat YAML with consistent indentation
            with open(file_path, encoding="utf-8") as f:
                original_content = f.read()

            try:
                data = yaml.safe_load(original_content)

                # Auto-format YAML
                formatted_yaml = yaml.dump(data, default_flow_style=False, indent=2, width=120, sort_keys=False)

                if formatted_yaml != original_content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(formatted_yaml)
                    fixed_issues = True

            except yaml.YAMLError as e:
                issues_found = True
                messages.append(f"⚠️ YAML syntax error in {file_path}: {str(e)}")
                messages.append(f"Run: python3 -c \"import yaml; yaml.safe_load(open('{file_path}'))\" for details")

        except ImportError:
            messages.append(f"ℹ️ PyYAML not available for {file_path}")
            messages.append("Install with: pip install PyYAML")

        # Check with yamllint if available
        if self._command_exists("yamllint"):
            try:
                result = subprocess.run(["yamllint", "-c", ".yamllint.yaml", file_path], capture_output=True, text=True)
                if result.returncode != 0:
                    issues_found = True
                    messages.append(f"⚠️ YAML style issues found in {file_path}")
                    messages.append(f"Run: yamllint '{file_path}' for detailed analysis")
            except subprocess.SubprocessError:
                pass

        # Generate summary message
        if fixed_issues and issues_found:
            messages.insert(0, f"🔧 Auto-fixed YAML formatting, some manual fixes may still be needed in {file_path}")
        elif fixed_issues:
            messages.insert(0, f"✅ Auto-fixed YAML formatting in {file_path}")
        elif issues_found:
            messages.insert(0, f"ℹ️ YAML linting suggestions available for {file_path}")

        return messages

    def _run_shell_linters(self, file_path: str) -> List[str]:
        """Run shell script linting."""
        messages = []

        if self._command_exists("shellcheck"):
            try:
                result = subprocess.run(["shellcheck", "--severity=warning", file_path], capture_output=True, text=True)
                if result.returncode != 0:
                    messages.append(f"⚠️ Shell script issues found in {file_path}")
                    messages.append(f"Run: shellcheck '{file_path}' for detailed analysis")
                    messages.append("")
                    messages.append("Common fixes:")
                    messages.append('  - Quote variables: "$var" instead of $var')
                    messages.append("  - Use [[ ]] instead of [ ] for conditionals")
                    messages.append("  - Check for unused variables")
            except subprocess.SubprocessError:
                pass
        else:
            messages.append(f"ℹ️ shellcheck not available for {file_path}")
            messages.append("Install with: apt install shellcheck (or equivalent)")

        return messages

    def _run_javascript_linters(self, file_path: str) -> List[str]:
        """Run JavaScript/TypeScript linting and auto-formatting."""
        messages = []
        fixed_issues = False
        issues_found = False

        # Auto-fix formatting with Prettier
        if self._command_exists("prettier"):
            try:
                result = subprocess.run(
                    ["prettier", "--write", "--print-width=120", "--single-quote", "--trailing-comma=es5", file_path],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    fixed_issues = True
            except subprocess.SubprocessError:
                pass

        # Auto-fix code issues with ESLint
        if self._command_exists("eslint"):
            try:
                # Try to auto-fix with ESLint
                result = subprocess.run(["eslint", "--fix", file_path], capture_output=True, text=True)
                if result.returncode == 0:
                    fixed_issues = True

                # Check if any issues remain after auto-fix
                result = subprocess.run(["eslint", file_path], capture_output=True, text=True)
                if result.returncode != 0:
                    issues_found = True
                    messages.append(f"⚠️ JavaScript/TypeScript style issues remain in {file_path} after auto-fix")
                    messages.append(f"Run: eslint '{file_path}' to see remaining issues")
            except subprocess.SubprocessError:
                pass

        # Generate summary message
        if fixed_issues and issues_found:
            messages.insert(0, f"🔧 Auto-fixed JS/TS formatting, some manual fixes may still be needed in {file_path}")
        elif fixed_issues:
            messages.insert(0, f"✅ Auto-fixed JavaScript/TypeScript formatting in {file_path}")
        elif issues_found:
            messages.insert(0, f"ℹ️ JavaScript/TypeScript linting suggestions available for {file_path}")

        return messages

    def _run_css_linters(self, file_path: str) -> List[str]:
        """Run CSS/SCSS/LESS linting and auto-formatting."""
        messages = []
        fixed_issues = False
        issues_found = False

        # Auto-fix formatting with Prettier
        if self._command_exists("prettier"):
            try:
                result = subprocess.run(
                    ["prettier", "--write", "--print-width=120", file_path], capture_output=True, text=True
                )
                if result.returncode == 0:
                    fixed_issues = True
            except subprocess.SubprocessError:
                pass

        # Auto-fix CSS issues with Stylelint
        if self._command_exists("stylelint"):
            try:
                # Try to auto-fix with Stylelint
                result = subprocess.run(["stylelint", "--fix", file_path], capture_output=True, text=True)
                if result.returncode == 0:
                    fixed_issues = True

                # Check if any issues remain after auto-fix
                result = subprocess.run(["stylelint", file_path], capture_output=True, text=True)
                if result.returncode != 0:
                    issues_found = True
                    messages.append(f"⚠️ CSS style issues remain in {file_path} after auto-fix")
                    messages.append(f"Run: stylelint '{file_path}' to see remaining issues")
            except subprocess.SubprocessError:
                pass

        # Generate summary message
        if fixed_issues and issues_found:
            messages.insert(0, f"🔧 Auto-fixed CSS formatting, some manual fixes may still be needed in {file_path}")
        elif fixed_issues:
            messages.insert(0, f"✅ Auto-fixed CSS formatting in {file_path}")
        elif issues_found:
            messages.insert(0, f"ℹ️ CSS linting suggestions available for {file_path}")

        return messages

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in the system PATH."""
        try:
            subprocess.run(["which", command], check=True, capture_output=True, text=True)
            return True
        except subprocess.SubprocessError:
            return False
