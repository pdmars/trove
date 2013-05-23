import eventlet
import netaddr

from datetime import datetime
from novaclient import exceptions as nova_exceptions
from reddwarf.common import cfg
from reddwarf.common import exception
from reddwarf.common import utils
from reddwarf.common.remote import create_dns_client
from reddwarf.common.remote import create_guest_client
from reddwarf.common.remote import create_nova_client
from reddwarf.common.remote import create_nova_volume_client
from reddwarf.db import models as dbmodels
from reddwarf.instance.tasks import InstanceTask
from reddwarf.instance.tasks import InstanceTasks
from reddwarf.guestagent import models as agent_models
from reddwarf.taskmanager import api as task_api
from reddwarf.openstack.common import log as logging
from reddwarf.openstack.common.gettextutils import _

from eventlet import greenthread

LOG = logging.getLogger(__name__)


class Configurations(object):
    _data_fields = ['id', 'name', 'description']

    @staticmethod
    def load(context):
        if context is None:
            raise TypeError("Argument context not defined.")
        elif id is None:
            raise TypeError("Argument is not defined.")

        """ TODO(jrodom): Pagination support required! """
        db_info = DBConfiguration.find_all(tenant_id=context.tenant)

        if db_info is None:
            LOG.debug("No configuration found for tenant % s" % context.tenant)

        return db_info


class Configuration(object):

    @property
    def instances(self):
        return self.instances

    @staticmethod
    def create(name, description, tenant_id, values):
        configurationGroup = DBConfiguration.create(name=name,
                                                    description=description,
                                                    tenant_id=tenant_id,
                                                    items=values)
        return configurationGroup

    @staticmethod
    def delete(id):
        DBConfiguration.delete(id=id)

    @staticmethod
    def load(context, id):
        configuration_from_db = DBConfiguration.find_by(
            id=id, tenant_id=context.tenant)
        return configuration_from_db


def persisted_models():
    return {
        'configuration': DBConfiguration,
        'configuration_item': DBConfigurationItem
    }


class DBConfiguration(dbmodels.DatabaseModelBase):
    _data_fields = ['name', 'description', 'tenant_id']


class DBConfigurationItem(dbmodels.DatabaseModelBase):
    _data_fields = ['configuration_key', 'configuration_value']

    def __hash__(self):
        return self.configuration_key.__hash__()
