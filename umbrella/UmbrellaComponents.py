# This file is part of the daspos-umbrella package.
#
# For copyright and licensing information about this package, see the
# NOTICE.txt and LICENSE.txt files in its top-level directory; they are
# available at https://github.com/crcresearch/daspos-umbrella
#
# Licensed under the MIT License (MIT);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import urllib2

from umbrella.UmbrellaError import MissingComponentError, ComponentTypeError, ProgrammingError
from umbrella.misc import get_md5_and_file_size

COMPONENT_NAME = "component_name"
TYPE = "type"
NEST = "nest"
END_NEST = "end_nest"

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


SPECIFICATION_ROOT_COMPONENT_NAMES = [
    SPECIFICATION_NAME, SPECIFICATION_DESCRIPTION, HARDWARE, KERNEL, OS, PACKAGE_MANAGER, SOFTWARE, DATA_FILES,
    ENVIRONMENT_VARIABLES, COMMANDS, OUTPUT,
]


class Component(object):
    _type = (str, unicode)
    _required_keys = {}
    is_required = False

    def __init__(self, umbrella_specification, component_name, component_json=None):
        self.umbrella_specification = umbrella_specification
        self.name = component_name
        self.component_json = component_json

    @property
    def required_keys(self):
        return self._required_keys

    def validate(self):
        is_valid = True

        if not isinstance(self.component_json, self._type):
            raise ComponentTypeError(
                "Component \"" + str(self.name) + "\" is of type \"" + str(type(self.component_json)) +
                "\" but must be of type \"" + str(self._type) + '"'
            )

        if isinstance(self.component_json, dict):  # Keys only apply to components that are dictionaries
            for key, info in self._required_keys.iteritems():
                if key not in self.component_json:  # Required key is missing
                    is_valid = False
                    self.umbrella_specification._error_log.append("\"%s\" key is required in %s component" % (key, self.name))  # noqa
                else:  # Required key is there, now check if it is set up right
                    if not self.validate_subcomponent(self.component_json[key], info, key):  # Call this recursive function and check all pieces
                        is_valid = False
        elif len(self._required_keys) > 0:
            raise ProgrammingError("Check component \"" + str(self.name) + "\" and its _required_keys")

        return is_valid

    def validate_subcomponent(self, subcomponent_json, info, key_name):
        is_valid = True

        if subcomponent_json is None:
            raise ProgrammingError("subcomponent_json should not be None")

        if info is None:
            raise ProgrammingError("info should not be None")

        if key_name is None:
            raise ProgrammingError("key_name should not be None")

        if info == END_NEST:  # This is used for things that do not need to look deeper (ie config for package_manager)
            return True

        if not isinstance(subcomponent_json, info[TYPE]):  # Check if it is the right type
            is_valid = False
            self.umbrella_specification._error_log.append(
                '"' + str(key_name) + "\" key or one of its children, in component \"" + str(self.name) +
                "\" is of type \"" + str(type(subcomponent_json)) + "\" but should be of type \"" +
                str(info[TYPE]) + '"')

        # Dictionaries will have key_names, but lists won't. If it is a list, we will just use last dictionary's key_name

        if isinstance(subcomponent_json, dict):
            for key in subcomponent_json:
                subkey_name = key

                if not self.validate_subcomponent(subcomponent_json[key], info[NEST], subkey_name):
                    is_valid = False

        if isinstance(subcomponent_json, list):
            for key in subcomponent_json:
                subkey_name = key_name

                if not self.validate_subcomponent(key, info[NEST], subkey_name):
                    is_valid = False

        return is_valid

    def set_type(self, new_type):
        if isinstance(new_type, type):
            self._type = new_type
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


class FileInfo(Component):
    _type = dict
    _required_keys = {
        ID: {
            TYPE: (str, unicode),
        },
        URL_SOURCES: {
            TYPE: list,
            NEST: {
                TYPE: (str, unicode),
            },
        },
        FILE_FORMAT: {
            TYPE: (str, unicode),
        },
        MD5: {
            TYPE: (str, unicode),
        },
        # FILE_SIZE should later be changed to int
        FILE_SIZE: {
            TYPE: (str, unicode),
        },
        MOUNT_POINT: {
            TYPE: (str, unicode),
        },
    }

    def __init__(self, file_name, umbrella_specification, component_name, component_json=None):
        super(FileInfo, self).__init__(umbrella_specification, component_name, component_json)

        self.file_name = file_name

    def validate(self):
        is_valid = super(FileInfo, self).validate()

        if is_valid:
            if not isinstance(self.component_json[URL_SOURCES], list):
                raise TypeError('"' + URL_SOURCES + '"' + " must be a list")

            file_info = self._get_file_info()

            for url in file_info[URL_SOURCES]:
                callback_function = self.umbrella_specification.callback_function
                args = self.umbrella_specification.args
                md5, file_size = self._get_md5_and_file_size(url, file_info, callback_function, *args)

                if file_size != int(file_info[FILE_SIZE]):
                    is_valid = False
                    self.umbrella_specification._error_log.append(
                        "The file named " + str(file_info[FILE_NAME]) + " on component " + str(file_info[COMPONENT_NAME]) +
                        " had a file size of " + str(file_size) + " but the specification says it should be " +
                        str(file_info[FILE_SIZE])
                    )

                if md5 and md5 != file_info[MD5]:
                    is_valid = False
                    self.umbrella_specification._error_log.append(
                        "The file named " + str(file_info[FILE_NAME]) + " on component " +
                        str(file_info[COMPONENT_NAME]) + " from the url source of " + str(url) +
                        " had a calculated md5 of " + str(md5) + " but the specification says it should be " +
                        str(file_info[MD5])
                    )

        return is_valid

    def _get_file_info(self):
        file_info = {}

        file_info[FILE_NAME] = self.file_name
        file_info[COMPONENT_NAME] = self.name
        file_info[URL_SOURCES] = self.component_json[URL_SOURCES]
        file_info[MD5] = self.component_json[MD5]
        file_info[FILE_SIZE] = self.component_json[FILE_SIZE]

        return file_info

    def _get_md5_and_file_size(self, the_file_or_url, file_info, callback_function=None, *args):
        if hasattr(the_file_or_url, "read"):
            return self._get_md5_and_file_size_via_file(the_file_or_url, file_info[FILE_SIZE], callback_function, *args)
        elif isinstance(the_file_or_url, (str, unicode)):
            return self._get_md5_and_file_size_via_url(the_file_or_url, file_info, callback_function, *args)
        else:
            raise ValueError("the_file_or_url must be a file or a string form of a url")

    def _get_md5_and_file_size_via_file(self, the_file, actual_file_size, callback_function=None, *args):
        if not hasattr(the_file, "read"):
            raise ValueError("the_file must be an open file ")

        return get_md5_and_file_size(the_file, actual_file_size, callback_function, *args)

    def _get_md5_and_file_size_via_url(self, url, file_info, callback_function=None, *args):
        if not isinstance(url, (str, unicode)):
            raise ValueError("Url must be in string form ")

        try:
            remote = urllib2.urlopen(url)
        except urllib2.HTTPError as error:
            self.umbrella_specification._error_log.append(
                "Http error for url " + str(url) + " associated with the file named " +
                str(file_info[FILE_NAME]) + " on component " + str(file_info[COMPONENT_NAME]) + " \"" + str(error) + '"'
            )

            return None, None
        except urllib2.URLError as error:
            self.umbrella_specification._error_log.append(
                "Url error for url " + str(url) + " associated with the file named " +
                str(file_info[FILE_NAME]) + " on component " + str(file_info[COMPONENT_NAME]) + " \"" + str(error) + '"'
            )

            return None, None

        # Get the file_size from the website. Some websites (old ones) may not give this information
        try:
            file_size_from_url = int(remote.headers["content-length"])

            if int(file_size_from_url) != int(file_info[FILE_SIZE]):
                self.umbrella_specification._error_log.append(
                    "Url " + str(url) + " associated with the file named \"" +
                    str(file_info[FILE_NAME]) + "\" on component \"" + str(file_info[COMPONENT_NAME]) +
                    "\" reported a file size of " + str(file_size_from_url) +
                    " but the specification says it should be " + str(file_info[FILE_SIZE])
                )
        except KeyError:
            file_size_from_url = None

        return get_md5_and_file_size(remote, file_size_from_url, callback_function, *args)


class OsFileInfo(FileInfo):
    _required_keys = {
        ID: {
            TYPE: (str, unicode),
        },
        URL_SOURCES: {
            TYPE: list,
            NEST: {
                TYPE: (str, unicode),
            },
        },
        FILE_FORMAT: {
            TYPE: (str, unicode),
        },
        MD5: {
            TYPE: (str, unicode),
        },
        # FILE_SIZE should later be changed to int
        FILE_SIZE: {
            TYPE: (str, unicode),
        },
    }


class NameComponent(Component):
    _type = (str, unicode)
    _required_keys = {}
    is_required = False

    def validate(self):
        is_valid = super(NameComponent, self).validate()

        return is_valid


class DescriptionComponent(Component):
    _type = (str, unicode)
    _required_keys = {}
    is_required = False

    def validate(self):
        is_valid = super(DescriptionComponent, self).validate()

        return is_valid


class HardwareComponent(Component):
    _type = dict
    _required_keys = {
        ARCHITECTURE: {
            TYPE: (str, unicode),
        },
        CORES: {  # CORES should be converted to int later.
            TYPE: (str, unicode),
        },
        MEMORY: {  # MEMORY should be converted to int later. In addition, this will require it to be converted from 2gb to 2097152 (kb) or whatever seems to be a sensible measurement
            TYPE: (str, unicode),
        },
        DISK_SPACE: {  # DISK_SPACE should be converted to int later. In addition, this will require it to be converted from 2gb to 2097152 (kb) or whatever seems to be a sensible measurement
            TYPE: (str, unicode),
        },
    }
    is_required = True


class KernelComponent(Component):
    _type = dict
    _required_keys = {
        NAME: {
            TYPE: (str, unicode),
        },
        VERSION: {
            TYPE: (str, unicode),
        },
    }
    is_required = True


class OsComponent(Component):
    _type = dict
    _required_keys = {
        NAME: {
            TYPE: (str, unicode),
        },
        VERSION: {
            TYPE: (str, unicode),
        },
    }
    is_required = True

    def validate(self):
        is_valid = super(OsComponent, self).validate()

        file_info = OsFileInfo(self.component_json[FILE_NAME], self.umbrella_specification, OS, self.component_json)

        if not file_info.validate():
            is_valid = False

        return is_valid


class PackageManagerComponent(Component):
    _type = dict
    _required_keys = {
        NAME: {
            TYPE: (str, unicode),
        },
        PACKAGES: {  # PACKAGES should be converted to list later
            TYPE: (str, unicode),
        },
        REPOSITORIES: {
            TYPE: dict,
            NEST: {
                TYPE: dict,
                NEST: END_NEST,  # END_NEST is used to stop nest checking at this point
            },
        },
    }
    is_required = False

    def validate(self):
        is_valid = super(PackageManagerComponent, self).validate()

        if REPOSITORIES in self.component_json and isinstance(self.component_json[REPOSITORIES], dict):
            for repository_name, repository_file_info in self.component_json[REPOSITORIES].iteritems():
                file_info = FileInfo(repository_name, self.umbrella_specification, self.name, repository_file_info)

                if not file_info.validate():
                    is_valid = False

        return is_valid


class SoftwareComponent(Component):
    _type = dict
    _required_keys = {}
    is_required = False

    def validate(self):
        is_valid = super(SoftwareComponent, self).validate()

        for software_name, software_file_info in self.component_json.iteritems():
            file_info = FileInfo(software_name, self.umbrella_specification, self.name, software_file_info)

            if not file_info.validate():
                is_valid = False

        return is_valid


class DataFileComponent(Component):
    _type = dict
    _required_keys = {}
    is_required = False

    def validate(self):
        is_valid = super(DataFileComponent, self).validate()

        for data_file_name, data_file_info in self.component_json.iteritems():
            file_info = FileInfo(data_file_name, self.umbrella_specification, self.name, data_file_info)

            if not file_info.validate():
                is_valid = False

        return is_valid


class EnvironmentVariableComponent(Component):
    _type = dict
    _required_keys = {}
    is_required = False

    def validate(self):
        is_valid = super(EnvironmentVariableComponent, self).validate()

        for environment_variable, value in self.component_json.iteritems():
            if not isinstance(value, (str, unicode)):
                is_valid = False
                self.umbrella_specification._error_log.append(
                    "Environment variable \"" + str(environment_variable) + "\" on component \"" + str(self.name) +
                    "\" is of type \"" + str(type(value)) + "\" but should be of type \"str\""
                )

        return is_valid


class CommandComponent(Component):
    _type = (str, unicode)
    _required_keys = {}
    is_required = False

    def validate(self):
        is_valid = super(CommandComponent, self).validate()

        return is_valid


class OutputComponent(Component):
    _type = dict
    _required_keys = {
        FILES: {
            TYPE: list,
            NEST: {
                TYPE: (str, unicode),
            },
        },
        DIRECTORIES: {
            TYPE: list,
            NEST: {
                TYPE: (str, unicode),
            },
        },
    }
    is_required = True

    def validate(self):
        is_valid = super(OutputComponent, self).validate()

        return is_valid