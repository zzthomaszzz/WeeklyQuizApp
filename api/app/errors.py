class EmailAlreadyRegistered(Exception):
    """A registration reused an email that already exists.

    Defined here rather than in the service so the repository can raise it
    without the service having to catch a storage-specific exception.
    """
