# Todo: Does this even work as a context manager?
"""Adapter module for MySQLdb to provide more pythonic interface"""
import functools

import MySQLdb as mysqldb
# We import * to use this module as a drop in replacement for MySQLdb.connections
from MySQLdb.connections import *


class ConnectionAdapter(mysqldb.connections.Connection):
    """Adapter class to provide context manager for MySQLdb connection"""

    def __enter__(self):
        pass

    def __exit__(self, *args):
        if args[0] is None:
            self.commit()
        else:
            self.rollback()
        self.close()

@functools.wraps(mysqldb.connections.Connection.__init__)
def connect(*args, **kwargs):
    return ConnectionAdapter(*args, **kwargs)
