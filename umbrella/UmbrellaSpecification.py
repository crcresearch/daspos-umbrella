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

from umbrella.UmbrellaComponents import MissingComponent, Component, MissingComponentError, \
    SPECIFICATION_ROOT_COMPONENT_NAMES


class UmbrellaSpecification:
    """
    Note this class is NOT thread safe. Do not use it in multithreaded environment.
    """
    def __init__(self, specification_file=None):
        self._error_log = []
        self._warning_log = []
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
        return self._error_log

    @property
    def warning_log(self):
        return self._warning_log

    def validate(self, callback_function=None, *args):
        is_valid = True

        self._error_log = []
        self._warning_log = []

        self.callback_function = callback_function
        self.args = args

        # Go through each of the known components and check their validity
        for component_name in SPECIFICATION_ROOT_COMPONENT_NAMES:
            component = self.get_component(component_name)

            try:
                is_component_valid = component.validate(self._error_log)
            except MissingComponentError:
                if component.is_required:
                    self._error_log.append("Component \"" + str(component_name) + "\" is required")
                    is_component_valid = False
                else:
                    is_component_valid = True

            if not is_component_valid:
                is_valid = False

        return is_valid

    def get_component(self, component_name):
        if component_name in self.specification_json:
            return Component.get_specific_component(component_name, self.specification_json[component_name])
        else:
            missing_component = MissingComponent(component_name)
            missing_component.is_required = Component.get_specific_component(component_name, None).is_required

            return missing_component