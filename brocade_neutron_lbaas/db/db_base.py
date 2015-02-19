# Copyright 2012 OpenStack Foundation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# Majority of the code has been copied from the OpenStack Foundation Source Code

from sqlalchemy import create_engine
import logging

from sqlalchemy.orm import sessionmaker, scoped_session
import sqlalchemy.exc

from brocade_neutron_lbaas.db.brocade_db_base import BASEV2


LOG = logging.getLogger(__name__)
_ENGINE = None
_MAKER = None


def get_session(autocommit=True, expire_on_commit=False):
    """Helper method to grab session"""
    global _MAKER, _ENGINE
    if not _MAKER:
        if _ENGINE is None:
            return None
        _MAKER = scoped_session(sessionmaker(bind=_ENGINE,
                                autocommit=autocommit,
                                expire_on_commit=expire_on_commit))
    return _MAKER()


def get_session_with_url(autocommit=True, expire_on_commit=False, db_url=None):
    """Helper method to grab session"""
    global _MAKER, _ENGINE
    if not _MAKER:
        if _ENGINE is None and db_url is not None:
            _ENGINE = create_engine(db_url, pool_recycle=3600)
            _MAKER = sessionmaker(bind=_ENGINE,
                                  autocommit=autocommit,
                                  expire_on_commit=expire_on_commit)
    return _MAKER()


def register_models(BASEV2):
    global _ENGINE
    assert _ENGINE
    try:
        BASEV2.metadata.create_all(_ENGINE)
    except sqlalchemy.exc.OperationalError as e:
        print e
        raise e
    except sqlalchemy.exc.OperationalError as e:
        print "Invalid url specified " + e
        raise e
    return True


def unregister_models(base=BASEV2):
    global _ENGINE
    assert _ENGINE
    base.metadata.drop_all(_ENGINE)


def configure_db(db_url):
    global _ENGINE
    if db_url == ' ':
        LOG.error("db url not configured ...db model creation failed")
        return

    if db_url is None:
        LOG.error("db url not configured ...db model creation failed")
        return

    if not _ENGINE:
        _ENGINE = create_engine(db_url, pool_recycle=3600)

    register_models(BASEV2)


def get_engine():
    global _ENGINE
    return _ENGINE


def __init__(self, db_url):
    configure_db(db_url)
