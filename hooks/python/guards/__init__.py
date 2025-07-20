"""Guard implementations for Claude Code hook system.

REMINDER: Update HOOKS.md when adding/removing guards from __all__!
"""

from .assumption_detection_guard import AssumptionDetectionGuard
from .awareness_guards import DirectoryAwarenessGuard, PipInstallGuard  # TestSuiteEnforcementGuard disabled
from .conversation_log_guard import ConversationLogGuard
from .docker_env_guard import DockerEnvGuard
from .docker_guards import ContainerStateGuard, DockerRestartGuard, DockerWithoutComposeGuard
from .env_bypass_guard import EnvBypassGuard
from .false_success_guard import FalseSuccessGuard
from .file_guards import HookInstallationGuard, MockCodeGuard
from .git_guards import GitCheckoutSafetyGuard, GitForcePushGuard, GitNoVerifyGuard, PreCommitConfigGuard
from .git_hook_protection_guard import GitHookProtectionGuard
from .install_script_prevention_guard import InstallScriptPreventionGuard
from .lint_guards import LintGuard
from .meta_cognitive_guard import MetaCognitiveGuard
from .path_guards import AbsolutePathCdGuard, CurlHeadRequestGuard
from .python_venv_guard import PythonVenvGuard
from .reminder_guards import ContainerRebuildReminder, DatabaseSchemaReminder, TempFileLocationGuard
from .rule_zero_guard import RuleZeroReminderGuard

__all__ = [
    "AssumptionDetectionGuard",
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
    "InstallScriptPreventionGuard",
    "DirectoryAwarenessGuard",
    "PipInstallGuard",
    "PythonVenvGuard",
    # "TestSuiteEnforcementGuard",  # Disabled per user request
    "ContainerRebuildReminder",
    "DatabaseSchemaReminder",
    "TempFileLocationGuard",
    "LintGuard",
    "EnvBypassGuard",
    "AbsolutePathCdGuard",
    "CurlHeadRequestGuard",
    "MetaCognitiveGuard",
    "ConversationLogGuard",
    "FalseSuccessGuard",
    "RuleZeroReminderGuard",
]
