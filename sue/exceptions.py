class SueError(Exception):
    """Base SUE error."""


class ModelNotFound(SueError):
    pass


class BinaryNotFound(SueError):
    pass


class ConfigError(SueError):
    pass


class LlamaError(SueError):
    pass
