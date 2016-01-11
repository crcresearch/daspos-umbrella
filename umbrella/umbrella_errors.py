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

REQUIRED_SECTION_MISSING_ERROR_CODE = "REQ_SECT_MISS"
WRONG_SECTION_TYPE_ERROR_CODE = "WRONG_SECT_TYPE"
REQUIRED_ATTRIBUTE_MISSING_ERROR_CODE = "REQ_ATTR_MISS"
WRONG_ATTRIBUTE_TYPE_ERROR_CODE = "WRONG_ATTR_TYPE"
WRONG_FILE_SIZE_ERROR_CODE = "WRONG_FILE_SIZE"
WRONG_MD5_ERROR_CODE = "WRONG_MD5"
BAD_URL_ERROR_CODE = "BAD_URL"


class UmbrellaError(object):
    # Fields are error_code, description, component_name, file_name, url, may_be_temporary

    def __init__(self, error_code, description, may_be_temporary=False, component_name=None, file_name=None, url=None):
        self.error_code = error_code
        self.description = description
        self.may_be_temporary = may_be_temporary
        self.component_name = component_name
        self.file_name = file_name
        self.url = url

    @property
    def json(self):
        the_json = {}
        the_json["error_code"] = self.error_code
        the_json["description"] = self.description
        the_json["may_be_temporary"] = self.may_be_temporary
        the_json["component_name"] = self.component_name
        the_json["file_name"] = self.file_name
        the_json["url"] = self.url

        return the_json

    def __str__(self):
        return json.dumps(self.json)


class MissingComponentError(Exception):
    pass


class ComponentTypeError(Exception):
    def __init__(self, *args, **kwargs):
        if "component_name" not in kwargs:
            raise ProgrammingError("component_name is required for ComponentTypeError")

        if "attempted_type" not in kwargs:
            raise ProgrammingError("attempted_type is required for ComponentTypeError")

        if "correct_type" not in kwargs:
            raise ProgrammingError("correct_type is required for ComponentTypeError")

        self.component_name = kwargs["component_name"]
        self.attempted_type = kwargs["attempted_type"]
        self.correct_type = kwargs["correct_type"]


class ProgrammingError(Exception):
    pass