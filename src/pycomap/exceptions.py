"""Exception hierarchy for pycomap."""

from __future__ import annotations


class ComApError(Exception):
    """Base class for all pycomap errors."""


class ComApConnectionError(ComApError):
    """Raised on TCP-level connection problems (refused, closed, timed out)."""


class ComApProtocolError(ComApError):
    """Raised when the wire protocol itself misbehaves (bad CRC, unexpected framing,
    unsupported cipher, unexpected message type, etc.) — never on a clean controller-side
    error response, see [ComApControllerError][pycomap.ComApControllerError] for that.
    """


class ComApAuthError(ComApError):
    """Raised when access-code verification fails or is rejected by the controller."""


class ComApControllerError(ComApError):
    """Raised when the controller answers with an explicit ``Error`` operation.

    Attributes:
        code: the raw ``uint32`` error code reported by the controller. See
            ``docs/protocol.md`` section 2.6 for known values.
    """

    def __init__(self, code: int, message: str | None = None) -> None:
        self.code = code
        super().__init__(message or f"controller error: {code} (0x{code:08x})")
