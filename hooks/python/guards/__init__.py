"""Guard implementations for Claude Code hook system.

REMINDER: Update HOOKS.md when adding/removing guards from __all__!
"""

from .awareness_guards import DirectoryAwarenessGuard, PipInstallGuard, TestSuiteEnforcementGuard
from .conversation_log_guard import ConversationLogGuard
from .docker_env_guard import DockerEnvGuard
from .docker_guards import ContainerStateGuard, DockerRestartGuard, DockerWithoutComposeGuard
from .env_bypass_guard import EnvBypassGuard
from .file_guards import HookInstallationGuard, MockCodeGuard
from .git_guards import GitCheckoutSafetyGuard, GitForcePushGuard, GitNoVerifyGuard, PreCommitConfigGuard
from .git_hook_protection_guard import GitHookProtectionGuard
from .lint_guards import LintGuard
from .meta_cognitive_guard import MetaCognitiveGuard
from .path_guards import AbsolutePathCdGuard, CurlHeadRequestGuard
from .python_venv_guard import PythonVenvGuard
from .reminder_guards import ContainerRebuildReminder, DatabaseSchemaReminder, TempFileLocationGuard

__all__ = [
    "GitCheckoutSafetyGuard",
    "GitNoVerifyGuard",
    "GitForcePushGuard",
    "GitHookProtectionGuard",
    "DockerRestartGuard",
    "DockerWithoutComposeGuard",
    "DockerEnvGuard",
    "ContainerStateGuard",
    "MockCodeGuard",
    "PreCommitConfigGuard",
    "HookInstallationGuard",
    "DirectoryAwarenessGuard",
    "PipInstallGuard",
    "PythonVenvGuard",
    "TestSuiteEnforcementGuard",
    "ContainerRebuildReminder",
    "DatabaseSchemaReminder",
    "TempFileLocationGuard",
    "LintGuard",
    "EnvBypassGuard",
    "AbsolutePathCdGuard",
    "CurlHeadRequestGuard",
    "MetaCognitiveGuard",
    "ConversationLogGuard",
]
