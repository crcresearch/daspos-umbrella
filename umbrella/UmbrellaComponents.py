import urllib2

from umbrella.UmbrellaError import MissingComponentError
from umbrella.misc import get_md5_and_file_size

COMPONENT_NAME = "component_name"

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
    __required_keys = []
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

        if not isinstance(self.component_json, dict):
            raise TypeError("Component %s must be dict" % self.name)

        for key in self.__required_keys:
            if key not in self.component_json:
                is_valid = False
                self.umbrella_specification.__error_log.append("\"%s\" key is required in %s component" % (key, self.name))  # noqa

        return is_valid

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
    __required_keys = [ID, URL_SOURCES, FILE_FORMAT, MD5, FILE_SIZE, MOUNT_POINT]

    def validate(self):
        is_valid = super(UmbrellaFileInfoSubComponent, self).validate()

        if URL_SOURCES in self.component_json:
            if not isinstance(self.component_json[URL_SOURCES], list):
                raise TypeError('"' + URL_SOURCES + '"' + " must be a list")

            for source in self.component_json[URL_SOURCES]:
                pass

            # MD5 and SIZE validation for all URL_SOURCES - passing callback function as self.umbrella_specification.callback_function
            # ...
        else:
            is_valid = False

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
    __required_keys = [ID, URL_SOURCES, FILE_FORMAT, MD5, FILE_SIZE]


class NameComponent(Component):
    __required_keys = []
    is_required = False

    def validate(self):
        is_valid = super(NameComponent, self).validate()

        return is_valid


class DescriptionComponent(Component):
    __required_keys = []
    is_required = False

    def validate(self):
        is_valid = super(DescriptionComponent, self).validate()

        return is_valid


class HardwareComponent(Component):
    __required_keys = [ARCHITECTURE, CORES, MEMORY, DISK_SPACE]
    is_required = True


class KernelComponent(Component):
    __required_keys = [NAME, VERSION]
    is_required = True


class OsComponent(Component):
    __required_keys = [NAME, VERSION]
    is_required = True

    def validate(self):
        is_valid = super(OsComponent, self).validate()

        os_file_info = OsUmbrellaFileInfoSubComponent({OS: self.component_json}, OS)

        if not os_file_info.validate():
            is_valid = False

        return is_valid


class PackageManagerComponent(Component):
    __required_keys = [NAME, PACKAGES, REPOSITORIES]
    is_required = False


class SoftwareComponent(Component):
    __required_keys = []
    is_required = False


class DataFileComponent(Component):
    __required_keys = []
    is_required = False


class EnvironmentVariableComponent(Component):
    __required_keys = []
    is_required = False


class CommandComponent(Component):
    __required_keys = []
    is_required = False


class OutputComponent(Component):
    __required_keys = [FILES, DIRECTORIES]
    is_required = True