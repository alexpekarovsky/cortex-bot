class PAPIClientError(Exception):
    """Base exception for PAPI client errors"""
    pass


class PAPIConnectionError(PAPIClientError):
    """Raised when there's a connection issue with the PAPI server"""
    pass


class PAPIAuthenticationError(PAPIClientError):
    """Raised when there's an authentication issue with the PAPI server"""
    pass


class PAPIServerError(PAPIClientError):
    """Raised when the PAPI server returns a server error (5xx)"""
    pass


class PAPIClientRequestError(PAPIClientError):
    """Raised when there's a client request error (4xx)"""
    pass


class PAPIResponseError(PAPIClientError):
    """Raised when the response from PAPI server is invalid or empty"""
    pass

