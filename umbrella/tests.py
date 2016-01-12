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

from umbrella import UmbrellaSpecification
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

VALID_FILE = os.path.join(base_dir, "openmalaria.umbrella")
PATH = os.path.join(base_dir, "BrokenSpecs")


def test_all_errors():
    validate_and_report("all-errors.umbrella")


def test_lots_of_errors():
    validate_and_report("lots-of-errors.umbrella")


def test_missing_hardware():
    validate_and_report("missing-hardware.umbrella")


def test_missing_kernel():
    validate_and_report("missing-kernel.umbrella")


def test_missing_os():
    validate_and_report("missing-os.umbrella")


def test_openmalaria_broken():
    validate_and_report("openmalaria-broken.umbrella")


def test_wrong_checksum():
    validate_and_report("wrong-checksum.umbrella")


def test_wrong_file_size():
    validate_and_report("wrong-file-size.umbrella")


def test_wrong_source():
    validate_and_report("wrong-source.umbrella")


def validate_and_report(file_name):
    specification_file = open(os.path.join(PATH,file_name))

    umbrella_validator = UmbrellaSpecification(specification_file)
    umbrella_validator.validate()

    for error in umbrella_validator.error_log:
        print str(error)

    # print str(umbrella_validator.error_log)
    # print umbrella_validator.warning_log


def test_all():
    print "Testing lots-of-errors.umbrella:"
    test_lots_of_errors()

    print "Testing all-errors.umbrella:"
    test_all_errors()

    print "Testing missing-hardware.umbrella:"
    test_missing_hardware()

    print "Testing missing-kernel.umbrella:"
    test_missing_kernel()

    print "Testing missing-os.umbrella:"
    test_missing_os()

    print "Testing openmalaria-broken.umbrella:"
    test_openmalaria_broken()

    print "Testing wrong-checksum.umbrella:"
    test_wrong_checksum()

    print "Testing wrong-file-size.umbrella:"
    test_wrong_file_size()

    print "Testing wrong-source.umbrella:"
    test_wrong_source()


if __name__ == "__main__":
    test_all()