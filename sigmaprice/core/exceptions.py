"""Custom exceptions"""


class SigmaPriceError(Exception):
    """Base exception for all SigmaPrice errors"""
    pass


class ParseError(SigmaPriceError):
    """Error during price file parsing"""
    pass


class MatchError(SigmaPriceError):
    """Error during item matching"""
    pass


class CatalogError(SigmaPriceError):
    """Error in catalog operations"""
    pass


class SupplierError(SigmaPriceError):
    """Error in supplier operations"""
    pass


class DatabaseError(SigmaPriceError):
    """Database-related error"""
    pass


class AuthenticationError(SigmaPriceError):
    """Authentication/authorization error"""
    pass


class ValidationError(SigmaPriceError):
    """Data validation error"""
    pass


class ExportError(SigmaPriceError):
    """Export operation error"""
    pass