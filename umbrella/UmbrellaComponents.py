import urllib2

from umbrella.UmbrellaError import MissingComponentError, ComponentTypeError, ProgrammingError
from umbrella.misc import get_md5_and_file_size

COMPONENT_NAME = "component_name"
TYPE = "type"
NEST = "nest"

# Components
SPECIFICATION_NAME = "comment"
SPECIFICATION_DESCRIPTION = "note"
HARDWARE = "hardware"
KERNEL = "kernel"
OS = "os"
PACKAGE_MANAGER = "package_manager"
SOFTWARE = "software"
DATA_FILES = "data"
ENVIRONMENT_VARIABLES = "environ"
COMMANDS = "cmd"
OUTPUT = "output"

# Component keys
ARCHITECTURE = "arch"
CORES = "cores"
MEMORY = "memory"
DISK_SPACE = "disk"

NAME = "name"
VERSION = "version"

PACKAGES = "list"
REPOSITORIES = "config"

FILES = "files"
DIRECTORIES = "dirs"

ID = "id"
FILE_NAME = "name"
URL_SOURCES = "source"
MOUNT_POINT = "mountpoint"
MD5 = "checksum"
FILE_SIZE = "size"
FILE_FORMAT = "format"
UNCOMPRESSED_FILE_SIZE = "uncompressed_size"


SPECIFICATION_COMPONENT_NAMES = [
    SPECIFICATION_NAME, SPECIFICATION_DESCRIPTION, HARDWARE, KERNEL, OS, PACKAGE_MANAGER, SOFTWARE, DATA_FILES,
    ENVIRONMENT_VARIABLES, COMMANDS, OUTPUT,
]


class Component(object):
    __type = str
    __required_keys = {}
    is_required = False

    def __init__(self, umbrella_specification, component_name, component_json=None):
        self.umbrella_specification = umbrella_specification
        self.name = component_name
        self.component_json = component_json

    @property
    def required_keys(self):
        return self.__required_keys

    def validate(self):
        is_valid = True

        if not isinstance(self.component_json, self.__type):
            raise ComponentTypeError("Component \"" + str(self.name) + "\" must be of type \"" + str(self.__type) + '"')

        if isinstance(self.component_json, dict):  # Keys only apply to components that are dictionaries
            for key, info in self.__required_keys.iteritems():
                if key not in self.component_json:  # Required key is missing
                    is_valid = False
                    self.umbrella_specification.__error_log.append("\"%s\" key is required in %s component" % (key, self.name))  # noqa
                else:  # Required key is there, now check if it is set up right
                    if not self.validate_subcomponent(self.component_json[key], info, key):  # Call this recursive function and check all pieces
                        is_valid = False
        elif len(self.__required_keys) > 0:
            raise ProgrammingError("Check component \"" + str(self.name) + "\" and its __required_keys")

        return is_valid

    def validate_subcomponent(self, subcomponent_json, info, key_name):
        is_valid = True

        if subcomponent_json is None:
            raise ProgrammingError("subcomponent_json should not be None")

        if info is None:
            if key_name == REPOSITORIES:  # Special case piece for "config" on package_manager. We will check the config (the files) in a different place
                return True
            else:
                raise ProgrammingError("info should not be None")

        if key_name is None:
            raise ProgrammingError("key_name should not be None")

        while True:  # Loop until the object isn't comprehensive (list or dict)
            if not isinstance(subcomponent_json, info[TYPE]):  # Check if it is the right type
                is_valid = False
                self.umbrella_specification.__error_log.append(
                    '"' + str(key_name) + "\" key or one of its children, in component \"" + str(self.name) +
                    "\" is of type \"" + str(type(subcomponent_json)) + "\" but should be of type \"" +
                    str(info[TYPE]) + '"')

            if isinstance(subcomponent_json, (list, dict)):
                for key in subcomponent_json:
                    subkey_name = key_name

                    # Dictionaries will have key_names, but lists won't. If it is a list, we will just use last dictionary's key_name
                    if isinstance(subcomponent_json, dict):
                        subkey_name = key

                    if not self.validate_subcomponent(subcomponent_json[key], info[NEST], subkey_name):
                        is_valid = False
            else:
                break

        return is_valid

    def set_type(self, new_type):
        if isinstance(new_type, type):
            self.__type = new_type
        else:
            raise TypeError("New type must be of type \"type\". Confusing huh? :)")

    @staticmethod
    def get_specific_component(umbrella_specification, component_name, component_json):
        if not isinstance(component_name, (str, unicode)):
            raise TypeError("component_name must be a string.")

        if component_name == SPECIFICATION_NAME:
            return NameComponent(umbrella_specification, component_name, component_json)
        elif component_name == SPECIFICATION_DESCRIPTION:
            return DescriptionComponent(umbrella_specification, component_name, component_json)
        elif component_name == HARDWARE:
            return HardwareComponent(umbrella_specification, component_name, component_json)
        elif component_name == KERNEL:
            return KernelComponent(umbrella_specification, component_name, component_json)
        elif component_name == OS:
            return OsComponent(umbrella_specification, component_name, component_json)
        elif component_name == PACKAGE_MANAGER:
            return PackageManagerComponent(umbrella_specification, component_name, component_json)
        elif component_name == SOFTWARE:
            return SoftwareComponent(umbrella_specification, component_name, component_json)
        elif component_name == DATA_FILES:
            return DataFileComponent(umbrella_specification, component_name, component_json)
        elif component_name == ENVIRONMENT_VARIABLES:
            return EnvironmentVariableComponent(umbrella_specification, component_name, component_json)
        elif component_name == COMMANDS:
            return CommandComponent(umbrella_specification, component_name, component_json)
        elif component_name == OUTPUT:
            return OutputComponent(umbrella_specification, component_name, component_json)
        else:
            raise ValueError("There is no component called " + str(component_name))


class MissingComponent(Component):
    def validate(self):
        raise MissingComponentError("Component " + str(self.name) + " doesn't exist")


class UmbrellaFileInfoSubComponent(Component):
    __required_keys = {
        ID: {
            TYPE: str,
        },
        URL_SOURCES: {
            TYPE: list,
            NEST: {
                TYPE: str,
            },
        },
        FILE_FORMAT: {
            TYPE: str,
        },
        MD5: {
            TYPE: str,
        },
        # FILE_SIZE should later be changed to int
        FILE_SIZE: {
            TYPE: str,
        },
        MOUNT_POINT: {
            TYPE: str,
        },
    }

    def validate(self):
        is_valid = super(UmbrellaFileInfoSubComponent, self).validate()

        if is_valid:
            if not isinstance(self.component_json[URL_SOURCES], list):
                raise TypeError('"' + URL_SOURCES + '"' + " must be a list")

            file_info = {}

            file_info[FILE_NAME] = self.component_json[FILE_NAME]
            file_info[COMPONENT_NAME] = self.name
            file_info[URL_SOURCES] = self.component_json[URL_SOURCES]
            file_info[MD5] = self.component_json[MD5]
            file_info[FILE_SIZE] = self.component_json[FILE_SIZE]

            for url in file_info[URL_SOURCES]:
                callback_function = self.umbrella_specification.callback_function
                args = self.umbrella_specification.args
                md5, file_size = self.__get_md5_and_file_size(url, file_info, callback_function, *args)

                if file_size != int(file_info[FILE_SIZE]):
                    is_valid = False
                    self.umbrella_specification.__error_log.append(
                        "The file named " + str(file_info[FILE_NAME]) + " on component " + str(file_info[COMPONENT_NAME]) +
                        " had a file size of " + str(file_size) + " but the specification says it should be " +
                        str(file_info[FILE_SIZE])
                    )

                if md5 and md5 != file_info[MD5]:
                    is_valid = False
                    self.umbrella_specification.__error_log.append(
                        "The file named " + str(file_info[FILE_NAME]) + " on component " +
                        str(file_info[COMPONENT_NAME]) + " from the url source of " + str(url) +
                        " had a calculated md5 of " + str(md5) + " but the specification says it should be " +
                        str(file_info[MD5])
                    )

            # MD5 and SIZE validation for all URL_SOURCES - passing callback function as self.umbrella_specification.callback_function
            # ...

        return is_valid

    def __get_md5_and_file_size(self, the_file_or_url, file_info, callback_function=None, *args):
        if hasattr(the_file_or_url, "read"):
            return self.__get_md5_and_file_size_via_file(the_file_or_url, file_info[FILE_SIZE], callback_function, *args)
        elif isinstance(the_file_or_url, (str, unicode)):
            return self.__get_md5_and_file_size_via_url(the_file_or_url, file_info, callback_function, *args)
        else:
            raise ValueError("the_file_or_url must be a file or a string form of a url")

    def __get_md5_and_file_size_via_file(self, the_file, actual_file_size, callback_function=None, *args):
        if not hasattr(the_file, "read"):
            raise ValueError("the_file must be an open file ")

        return get_md5_and_file_size(the_file, actual_file_size, callback_function, *args)

    def __get_md5_and_file_size_via_url(self, url, file_info, callback_function=None, *args):
        if not isinstance(url, (str, unicode)):
            raise ValueError("Url must be in string form ")

        try:
            remote = urllib2.urlopen(url)
        except urllib2.HTTPError as error:
            self.umbrella_specification.__error_log.append(
                "Http error for url " + str(url) + " associated with the file named " +
                str(file_info[FILE_NAME]) + " on component " + str(file_info[COMPONENT_NAME]) + " \"" + str(error) + '"'
            )

            return None, None
        except urllib2.URLError as error:
            self.umbrella_specification.__error_log.append(
                "Url error for url " + str(url) + " associated with the file named " +
                str(file_info[FILE_NAME]) + " on component " + str(file_info[COMPONENT_NAME]) + " \"" + str(error) + '"'
            )

            return None, None

        # Get the file_size from the website. Some websites (old ones) may not give this information
        try:
            file_size_from_url = int(remote.headers["content-length"])

            if int(file_size_from_url) != int(file_info[FILE_SIZE]):
                self.umbrella_specification.__error_log.append(
                    "Url " + str(url) + " associated with the file named " +
                    str(file_info[FILE_NAME]) + " on component " + str(file_info[COMPONENT_NAME]) +
                    " reported a file size of " + str(file_size_from_url) +
                    " but the specification says it should be " + str(file_info[FILE_SIZE])
                )
        except KeyError:
            file_size_from_url = None

        return get_md5_and_file_size(remote, file_size_from_url, callback_function, *args)


class OsUmbrellaFileInfoSubComponent(UmbrellaFileInfoSubComponent):
    def __init__(self, umbrella_specification, component_name, component_json=None):
        super(OsUmbrellaFileInfoSubComponent, self).__init__(umbrella_specification, component_name, component_json)

        self.__required_keys[MOUNT_POINT] = None  # Remove this unrequired key


class NameComponent(Component):
    __type = str
    __required_keys = {}
    is_required = False

    def validate(self):
        is_valid = super(NameComponent, self).validate()

        return is_valid


class DescriptionComponent(Component):
    __type = str
    __required_keys = {}
    is_required = False

    def validate(self):
        is_valid = super(DescriptionComponent, self).validate()

        return is_valid


class HardwareComponent(Component):
    __type = dict
    __required_keys = {
        ARCHITECTURE: {
            TYPE: str,
        },
        CORES: {  # CORES should be converted to int later.
            TYPE: str,
        },
        MEMORY: {  # MEMORY should be converted to int later. In addition, this will require it to be converted from 2gb to 2097152 (kb) or whatever seems to be a sensible measurement
            TYPE: str,
        },
        DISK_SPACE: {  # DISK_SPACE should be converted to int later. In addition, this will require it to be converted from 2gb to 2097152 (kb) or whatever seems to be a sensible measurement
            TYPE: str,
        },
    }
    is_required = True


class KernelComponent(Component):
    __type = dict
    __required_keys = {
        NAME: {
            TYPE: str,
        },
        VERSION: {
            TYPE: str,
        },
    }
    is_required = True


class OsComponent(Component):
    __type = dict
    __required_keys = {
        NAME: {
            TYPE: str,
        },
        VERSION: {
            TYPE: str,
        },
    }
    is_required = True

    def validate(self):
        is_valid = super(OsComponent, self).validate()

        os_file_info = OsUmbrellaFileInfoSubComponent({FILE_NAME: OS, "json": self.component_json}, OS)

        if not os_file_info.validate():
            is_valid = False

        return is_valid


class PackageManagerComponent(Component):
    __type = dict
    __required_keys = {
        NAME: {
            TYPE: str,
        },
        PACKAGES: {  # PACKAGES should be converted to list later
            TYPE: str,
        },
        REPOSITORIES: {
            TYPE: dict,
            NEST: {
                TYPE: dict,
                NEST: None,
            },
        },
    }
    is_required = False


class SoftwareComponent(Component):
    __type = dict
    __required_keys = {}
    is_required = False


class DataFileComponent(Component):
    __type = dict
    __required_keys = {}
    is_required = False


class EnvironmentVariableComponent(Component):
    __type = dict
    __required_keys = {}
    is_required = False


class CommandComponent(Component):
    __type = str
    __required_keys = {}
    is_required = False


class OutputComponent(Component):
    __type = dict
    __required_keys = {FILES: list, DIRECTORIES: list}
    is_required = True