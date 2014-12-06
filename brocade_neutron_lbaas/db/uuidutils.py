'''
 Copyright 2013 by Brocade Communication Systems
 All rights reserved.

 This software is the confidential and proprietary information
 of Brocade Communication Systems, ("Confidential Information").
 You shall not disclose such Confidential Information and shall
 use it only in accordance with the terms of the license agreement
 you entered into with Brocade Communication Systems.
'''
"""
UUID related utilities and helper functions.
"""

import uuid
import random


def generate_uuid():
    return str(uuid.uuid4())


def is_uuid_like(val):
    """Returns validation of a value as a UUID.

    For our purposes, a UUID is a canonical form string:
    aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa

    """
    try:
        return str(uuid.UUID(val)) == val
    except (TypeError, ValueError, AttributeError):
        return False

def get_trans_id():
    r1 = random.SystemRandom()
    return r1.getrandbits(32)

def get_random():
    r1=random.SystemRandom()
    rand = r1.getrandbits(8)
    if(rand ==255):
        return rand-1
    if(rand==0):
        return 1
    return rand