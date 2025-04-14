import hashlib  # Provides access to secure hash functions like SHA-256
import time     # Used to retrieve the current system time


def sha256(text):
    """
    Returns the SHA-256 hash of a given input string.

    Args:
        text (str): The input text to hash.

    Returns:
        str: A 64-character hexadecimal hash string.
    """
    # Encode the string into bytes (required by hashlib),
    # then compute SHA-256, and return the hex digest
    return hashlib.sha256(text.encode()).hexdigest()


def current_timestamp():
    """
    Returns the current time as a UNIX timestamp.

    Returns:
        float: Current time in seconds since the epoch (January 1, 1970).
    """
    return time.time()
