"""
Custom exceptions for dataset validation and scanning.

These exceptions help maintain clean separation between
filesystem errors and logical dataset structure errors.
"""


class DatasetValidationError(Exception):
    """
    Raised when a dataset does not meet required structural
    constraints for image classification tasks.
    """
    pass


class UnsupportedDatasetStructureError(Exception):
    """
    Raised when a dataset structure is detected but not supported
    by the current framework configuration.
    """
    pass
