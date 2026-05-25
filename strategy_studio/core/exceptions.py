"""Strategy Studio exceptions."""


class StrategyStudioError(Exception):
    """Base exception for Strategy Studio."""


class LakeOSQueryError(StrategyStudioError):
    """Raised when a LakeOS query fails."""


class RecallAPIError(StrategyStudioError):
    """Raised when a Recall API call fails."""


class FalsificationFailed(StrategyStudioError):
    """Raised when a falsification test fails."""


class InsufficientEvidenceError(StrategyStudioError):
    """Raised when evidence is insufficient."""


class ConfigurationError(StrategyStudioError):
    """Raised when configuration is invalid."""
