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

import unittest
from umbrella.misc import get_callback_function


def callback_validation_filename(filename, percentage, validation_job):
    return filename


def callback_validation_percentage(filename, percentage, validation_job):
    return percentage


def callback_validation_job(filename, percentage, validation_job):
    return validation_job


class TestGetCallbackFunction(unittest.TestCase):
    def setUp(self):
        pass

    def test_get_callback_function(self):
        self.assertEqual(get_callback_function(callback_validation_job, "123")("file", 0.0), "123")
        self.assertEqual(get_callback_function(callback_validation_job, validation_job="1234")("file", 0.0), "1234")
        self.assertEqual(get_callback_function(callback_validation_filename, "123")("file", 0.0), "file")
        self.assertEqual(get_callback_function(callback_validation_percentage, "123")("file", 0.0), 0.0)

if __name__ == "__main__":
    unittest.main()
