"""
    This module contains the utility functions used internally in Iris.

    FUNCTIONS:
    is_valid_address(host, port)
"""

import ipaddress
import socket


def is_valid_address(host, port):
    """ Responsible for checking whether the given host port pair is valid.

        Host can be given either as an ip address string or hostname.
        Uses `socket.gethostbyname()` to check whether a hostname exists.
        Else tries to create the `ipaddress.ip_address` our of a string.

        Returns True or False """
    if not 0 < port < 65535:
        return False
    try:
        socket.gethostbyname(host)
    except socket.gaierror:
        pass
    else:
        return True
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return False
    else:
        return True
