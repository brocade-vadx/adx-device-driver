'''
 Copyright 2013 by Brocade Communication Systems
 All rights reserved.

 This software is the confidential and proprietary information
 of Brocade Communication Systems, ("Confidential Information").
 You shall not disclose such Confidential Information and shall
 use it only in accordance with the terms of the license agreement
 you entered into with Brocade Communication Systems.
'''
from db_base import get_session

class Context:
    _session = None
    
    @property
    def session(self):
        #if self._session is None:
        self._session = get_session(True, False)
        return self._session