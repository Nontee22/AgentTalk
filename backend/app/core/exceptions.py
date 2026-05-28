class LLMError(Exception):
    def __init__(self, message: str, model: str = "", status_code: int | None = None):
        self.message = message
        self.model = model
        self.status_code = status_code
        super().__init__(message)


class LLMStreamError(LLMError):
    pass
