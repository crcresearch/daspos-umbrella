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

from umbrella.umbrella_components import MissingComponent, Component, MissingComponentError, \
    SPECIFICATION_ROOT_COMPONENT_NAMES
from umbrella.umbrella_errors import UmbrellaError, REQUIRED_SECTION_MISSING_ERROR_CODE, ComponentTypeError, \
    WRONG_SECTION_TYPE_ERROR_CODE, JsonError


class UmbrellaSpecification:
    """
    Note this class is NOT thread safe. Do not use it in multithreaded environment.
    """
    def __init__(self, specification=None):
        self._error_log = []
        self._warning_log = []
        self.callback_function = lambda *args, **kwargs: True
        self.args = []

        if specification is None:
            self.specification_json = {}
        else:
            if not hasattr(specification, "read") and not isinstance(specification, (str, unicode, dict)):
                raise TypeError("Specification must be a file-like object, json in string form, or a python dictionary")

            # Open Specification
            if hasattr(specification, "read"):
                try:
                    self.specification_json = json.load(specification)
                except:
                    raise JsonError("Specification was invalid json")
            elif isinstance(specification, (str, unicode)):
                try:
                    self.specification_json = json.loads(specification)
                except:
                    raise JsonError("Specification was invalid json")
            elif isinstance(specification, dict):
                self.specification_json = specification
            else:
                raise ValueError("Specification must be an open file, json in string form, or a python dictionary")

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
                    umbrella_error = UmbrellaError(
                        error_code=REQUIRED_SECTION_MISSING_ERROR_CODE, description="Missing section",
                        may_be_temporary=False, component_name=component_name
                    )
                    self._error_log.append(umbrella_error)
                    # self._error_log.append("Component \"" + str(component_name) + "\" is required")
                    is_component_valid = False
                else:
                    is_component_valid = True
            except ComponentTypeError as error:
                umbrella_error = UmbrellaError(
                    error_code=WRONG_SECTION_TYPE_ERROR_CODE,
                    description="Wrong section type of \"" + str(error.attempted_type) + "\". Should be type \"" +
                                str(error.correct_type) + '"',
                    may_be_temporary=False, component_name=component_name
                )
                self._error_log.append(umbrella_error)
                is_component_valid = False

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