# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack Foundation
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

import routes
import webob.dec
from reddwarf.openstack.common import log as logging

from reddwarf.openstack.common import extensions
from reddwarf.openstack.common.gettextutils import _
from reddwarf.common import cfg
from reddwarf.common import wsgi

LOG = logging.getLogger(__name__)

ExtensionsDescriptor = extensions.ExtensionDescriptor
ResourceExtension = extensions.ResourceExtension

CONF = cfg.CONF


class ReddwarfExtensionMiddleware(extensions.ExtensionMiddleware):

    def __init__(self, application, ext_mgr=None):
        ext_mgr = (ext_mgr or
                   ExtensionManager(CONF.api_extensions_path))
        mapper = routes.Mapper()

        # extended resources
        for resource_ext in ext_mgr.get_resources():
            LOG.debug(_('Extended resource: %s'), resource_ext.collection)
            # The only difference here is that we are using our common
            # wsgi.Resource instead of the openstack common wsgi.Resource
            exception_map = None
            if hasattr(resource_ext.controller, 'exception_map'):
                exception_map = resource_ext.controller.exception_map
            controller_resource = wsgi.Resource(resource_ext.controller,
                                                resource_ext.deserializer,
                                                resource_ext.serializer,
                                                exception_map)

            self._map_custom_collection_actions(resource_ext, mapper,
                                                controller_resource)
            kargs = dict(controller=controller_resource,
                         collection=resource_ext.collection_actions,
                         member=resource_ext.member_actions)
            if resource_ext.parent:
                kargs['parent_resource'] = resource_ext.parent
            mapper.resource(resource_ext.collection,
                            resource_ext.collection, **kargs)

        # extended actions
        action_resources = self._action_ext_resources(application, ext_mgr,
                                                      mapper)
        for action in ext_mgr.get_actions():
            LOG.debug(_('Extended action: %s'), action.action_name)
            resource = action_resources[action.collection]
            resource.add_action(action.action_name, action.handler)

        # extended requests
        req_controllers = self._request_ext_resources(application, ext_mgr,
                                                      mapper)
        for request_ext in ext_mgr.get_request_extensions():
            LOG.debug(_('Extended request: %s'), request_ext.key)
            controller = req_controllers[request_ext.key]
            controller.add_handler(request_ext.handler)

        self._router = routes.middleware.RoutesMiddleware(self._dispatch,
                                                          mapper)

        super(extensions.ExtensionMiddleware, self).__init__(application)


def factory(global_config, **local_config):
    """Paste factory."""
    def _factory(app):
        extensions.DEFAULT_XMLNS = "http://docs.openstack.org/reddwarf"
        ext_mgr = extensions.ExtensionManager(CONF.api_extensions_path)
        return ReddwarfExtensionMiddleware(app, ext_mgr)
    return _factory
