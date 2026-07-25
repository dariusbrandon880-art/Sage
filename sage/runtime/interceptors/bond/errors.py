class BondError(Exception):
    """Base exception class for all SAGE Bond Layer errors."""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")

class AuthorityMismatchError(BondError):
    def __init__(self, message: str = "Authority credentials do not match active session signature"):
        super().__init__("CIV-ERR-AUTH-001", message)

class UnauthorizedIdentityMutationError(BondError):
    def __init__(self, message: str = "Attempt to mutate identity context during active session is unauthorized"):
        super().__init__("CIV-ERR-MUT-003", message)

class MalformedPayloadError(BondError):
    def __init__(self, message: str = "Payload formatting is malformed or invalid"):
        super().__init__("CIV-ERR-SCHM-002", message)

class MissingSchemaFieldsError(BondError):
    def __init__(self, message: str = "Required fields are missing from the schema"):
        super().__init__("CIV-ERR-SCHM-005", message)

class AmbiguousPayloadError(BondError):
    def __init__(self, message: str = "Payload is ambiguous due to conflicting keys or parameters"):
        super().__init__("CIV-ERR-EXT-004", message)
