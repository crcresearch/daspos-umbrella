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

import json

from umbrella.UmbrellaComponents import MissingComponent, Component, MissingComponentError, SPECIFICATION_COMPONENT_NAMES


class UmbrellaSpecification:
    """
    Note this class is NOT thread safe. Do not use it in multithreaded environment.
    """
    def __init__(self, specification_file=None):
        self.__error_log = []
        self.__warning_log = []
        self.callback_function = lambda *args, **kwargs: True
        self.args = []

        if specification_file is None:
            self.specification_json = {}
        else:
            if not hasattr(specification_file, "read") and not isinstance(specification_file, (str, unicode, dict)):
                raise TypeError("Specification file must be a file-like object, json in string form, or a python dictionary")

            # Open Specification
            if hasattr(specification_file, "read"):
                self.specification_json = json.load(specification_file)
            elif isinstance(specification_file, (str, unicode)):
                self.specification_json = json.loads(specification_file)
            elif isinstance(specification_file, dict):
                self.specification_json = specification_file
            else:
                raise ValueError("Specification file must be an open file, json in string form, or a python dictionary")

    @property
    def error_log(self):
        return self.__error_log

    @property
    def warning_log(self):
        return self.__warning_log

    def validate(self, callback_function=None, *args):
        is_valid = True

        self.__error_log = []
        self.__warning_log = []

        self.callback_function = callback_function
        self.args = args

        # Go through each of the known components and check their validity
        for component_name in SPECIFICATION_COMPONENT_NAMES:
            component = self.get_component(component_name)

            try:
                is_component_valid = component.validate()
            except MissingComponentError:
                if component.is_required:
                    self.__error_log.append("Component " + str(component_name) + " is required")
                    is_component_valid = False
                else:
                    is_component_valid = True

            if not is_component_valid:
                is_valid = False

        return is_valid

    # def validate(self, callback_function=None, *args):
    #     self.__error_log = []
    #     self.__warning_log = []
    #
    #     # Initialize lists
    #     file_infos = []
    #     valid_specification_components = []
    #
    #     # Cycle through all of the specification components in the file
    #     for component_name, component in self.specification_json.iteritems():
    #         if component_name in SPECIFICATION_COMPONENTS:  # Is this component in the whitelist, if so, check it
    #             component = SPECIFICATION_COMPONENTS[component_name]
    #             valid_specification_components.append(component_name)
    #
    #             if component["has_files"]:
    #                 if component_name == "package_manager":  # Package Manager has config and goes one extra level  (3 levels)  # noqa
    #                     component_file_info = self.specification_json[component_name][CONFIG]
    #                 elif component_name == "os":  # OS is on the base level, so one less level                      (1 level)   # noqa
    #                     component_file_info = {"os": self.specification_json[component_name]}
    #                 else:  # Everything else has two levels                                                         (2 levels)  # noqa
    #                     component_file_info = self.specification_json[component_name]
    #
    #                 # Loop through each file's info
    #                 for name, file_info in component_file_info.iteritems():
    #                     # OS has its name inside its general info section
    #                     if component_name == "os":
    #                         file_name = file_info[FILE_NAME]
    #                     else:
    #                         file_name = name
    #
    #                     file_infos.append({
    #                         FILE_NAME: file_name,
    #                         COMPONENT_NAME: component_name,
    #                         URL_SOURCES: file_info[URL_SOURCES],
    #                         MD5: file_info[MD5],
    #                         FILE_SIZE: file_info[FILE_SIZE]
    #                     })
    #         else:  # Is this component not in the list of possible components, if so, it is unknown
    #             self.__warning_log.append(
    #                 'Specification component "' + str(component_name) +
    #                 '" is an unknown component. Please check the spelling'
    #             )
    #
    #     # Check for missing required components
    #     for component_name, component in SPECIFICATION_COMPONENTS.iteritems():
    #         # If the specification component is required and we didn't find it
    #         if component["required"] and component_name not in valid_specification_components:
    #             self.__error_log.append(
    #                 'Specification component "' + str(component_name) +
    #                 '" was missing from the supplied specification file'
    #             )
    #
    #     for file_info in file_infos:
    #         for url in file_info[URL_SOURCES]:
    #             md5, file_size = self.__get_md5_and_file_size(url, file_info, callback_function, *args)
    #
    #             if file_size != int(file_info[FILE_SIZE]):
    #                 self.__error_log.append(
    #                     "The file named " + str(file_info[FILE_NAME]) + " on component " + str(file_info[COMPONENT_NAME]) +
    #                     " had a file size of " + str(file_size) + " but the specification says it should be " +
    #                     str(file_info[FILE_SIZE])
    #                 )
    #
    #             if md5 and md5 != file_info[MD5]:
    #                 self.__error_log.append(
    #                     "The file named " + str(file_info[FILE_NAME]) + " on component " +
    #                     str(file_info[COMPONENT_NAME]) + " from the url source of " + str(url) +
    #                     " had a calculated md5 of " + str(md5) + " but the specification says it should be " +
    #                     str(file_info[MD5])
    #                 )

    def get_component(self, component_name):
        if component_name in self.specification_json:
            return Component.get_specific_component(self, component_name, self.specification_json[component_name])
        else:
            return MissingComponent(self, component_name)


if __name__ == "__main__":
    pass