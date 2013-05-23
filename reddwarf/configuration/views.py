class ConfigurationView(object):

    def __init__(self, configuration):
        self.configuration = configuration

    def data(self):
        configuration_dict = {
            "id": self.configuration.id,
            "name": self.configuration.name,
            "description": self.configuration.description
        }

        return {"configuration": configuration_dict}


class ConfigurationsView(object):

    def __init__(self, configurations):
        self.configurations = configurations

    def data(self):
        data = []

        for configuration in self.configurations:
            data.append(self.data_for_configuration(configuration))

        return {"configurations": data}

    def data_for_configuration(self, configuration):
        view = ConfigurationView(configuration)
        return view.data()['configuration']


class DetailedConfigurationView(object):

    def __init__(self, configuration):
        self.configuration = configuration

    def data(self):
        values = {}

        for configItem in self.configuration.items:
            key = configItem.configuration_key
            value = configItem.configuration_value
            values[key] = value

        instances_dict = []

        for instance in self.configuration.instances:
            instances_dict.append(
                {
                    "id": instance.id,
                    "name": instance.name
                }
            )

        configuration_dict = \
            {
                "id": self.configuration.id,
                "name": self.configuration.name,
                "description": self.configuration.description,
                "values": values,
                "instances": instances_dict
            }

        return {"configuration": configuration_dict}
