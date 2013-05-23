# Copyright 2013 Rackspace
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
import webob.exc
import json

from reddwarf.common import cfg
from reddwarf.common import exception
from reddwarf.common import pagination
from reddwarf.common import utils
from reddwarf.common import wsgi
from reddwarf.configuration.models import DBConfigurationItem

from reddwarf.openstack.common import log as logging
from reddwarf.openstack.common.gettextutils import _


from reddwarf.configuration import models
from reddwarf.configuration import views

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class ConfigurationsController(wsgi.Controller):
    def index(self, req, tenant_id):

        context = req.environ[wsgi.CONTEXT_KEY]
        configurations = models.Configurations.load(context)

        return wsgi.Result(views.ConfigurationsView(configurations).data(),
                           200)

    def show(self, req, tenant_id, id):
        context = req.environ[wsgi.CONTEXT_KEY]
        configuration = models.Configuration.load(context, id)

        return wsgi.Result(views.DetailedConfigurationView(
            configuration).data(), 200)

    def create(self, req, body, tenant_id):
        context = req.environ[wsgi.CONTEXT_KEY]

        LOG.info(_("req : '%s'\n\n") % req)
        LOG.info(_("body : '%s'\n\n") % req)

        name = body['configuration']['name']
        description = body['configuration']['description']
        values = body['configuration']['values']

        configItems = []
        if values:
            # validate that the values passed in are permitted by the operator.
            ConfigurationsController._validate_configuration(
                body['configuration']['values'])

            for k, v in values.iteritems():
                configItems.append(DBConfigurationItem(configuration_key=k,
                                                       configuration_value=v))

        cfg_group = models.Configuration.create(name, description, tenant_id,
                                                configItems)

        LOG.info (cfg_group.id)
        # LOG.info(_("Created configuration group {0} with ID {0}" %
        #            cfg_group.name, str(cfg_group.id)))

        return wsgi.Result(views.DetailedConfigurationView(cfg_group).data(),
                           200)

    def delete(self, req, tenant_id, id):
        context = req.environ[wsgi.CONTEXT_KEY]
        group = models.Configuration.load(context, id)
        group.delete()

        return wsgi.Result(None, 202)

    def update(self, req, body, tenant_id, id):
        context = req.environ[wsgi.CONTEXT_KEY]
        group = models.Configuration.load(context, id)

        # if name/description are provided in the request body, update the
        # model with these values as well.
        if 'name' in body['configuration']:
            group.name = body['configuration']['name']

        if 'description' in body['configuration']:
            group.description = body['configuration']['description']

        items = []
        if 'values' in body['configuration']:
            # validate that the values passed in are permitted by the operator.
            ConfigurationsController._validate_configuration(
                body['configuration']['values'])
            for k, v in body['configuration']['values'].iteritems():
                items.append(DBConfigurationItem(configuration_id=group.id,
                                                 configuration_key=k,
                                                 configuration_value=v))

            group.items = items

        group.save()

        return wsgi.Result(None, 202)

    @staticmethod
    def _validate_configuration(values):
        validation_config = open(CONF.validation_rules)

        rules = json.load(validation_config)

        LOG.info(_("Validating configuration values"))
        for k, v in values.iteritems():
            # get the validation rule dictionary, which will ensure there is a
            # rule for the given key name. An exception will be thrown if no
            # valid rule is located.
            rule = ConfigurationsController._get_item(
                k, rules['configuration-parameters'])

            # type checking
            valueType = rule['type']

            if not isinstance(v, ConfigurationsController._find_type(
                    valueType)):
                raise exception.UnprocessableEntity(
                    message=_("Incorrect data type supplied as a value for key"
                              " %s. Expected type of %s." % (k, valueType)))

            ## TODO(jrodom): integer min/max checking

        validation_config.close()

    @staticmethod
    def _find_type(valueType):
        if valueType == "boolean":
            return bool
        elif valueType == "string":
            return str
        elif valueType == "integer":
            return int
        else:
            raise exception.ReddwarfError(_(
                "Invalid or unsupported type defined in the "
                "configuration-parameters configuration file."))

    @staticmethod
    def _get_item(key, dictList):
        for item in dictList:
            if key in item:
                return item[key]

        raise exception.UnprocessableEntity(
            message=_("%s is not a supported configuration key. Please refer "
                      "to /configuration-parameters for a list of supported "
                      "keys." % key))
