# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2014 Brocade, Inc.  All rights reserved.
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
#
#

from neutron.common import exceptions as qexception


class UnsupportedFeature(qexception.NeutronException):
    message = _("Unsupported Feature: %(msg)s")


class UnsupportedOption(qexception.NeutronException):
    message = _("Unsupported Value %(value)s specified for attribute %(name)s")


class ConfigError(qexception.NeutronException):
    message = _("Configuration Error on the device: %(msg)s")

class NoValidDevice(qexception.NotFound):
    message = _("No valid device found")


class NoValidDeviceFile(qexception.NotFound):
    message = _("Device Inventory File %(name)s either not found or invalid")

class StartupError(qexception.NotFound):
    message = _("ADX device Driver configuration Error: %(msg)s")
