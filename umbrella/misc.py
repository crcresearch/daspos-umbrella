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
import hashlib


DOWNLOAD_CHUNK_SIZE = 10240


def get_md5_and_file_size(data_source, supposed_file_size=None, callback_function=None, *args):
        bytes_processed = 0
        md5 = hashlib.md5()

        if supposed_file_size is None:
            percent_processed = -1

            if callback_function:
                callback_function(percent_processed, *args)

        while True:
            data = data_source.read(DOWNLOAD_CHUNK_SIZE)

            # There was no more data to read
            if not data:
                break

            bytes_processed += len(data)

            if supposed_file_size:
                percent_processed = float(bytes_processed / supposed_file_size * 100)

                if percent_processed > 10:
                    if callback_function:
                        callback_function(percent_processed, *args)

            md5.update(data)

        if callback_function:
            callback_function(100.0, *args)

        return md5.hexdigest(), bytes_processed


def get_callback_function(callback_function, *args, **kwargs):
    """
    Note that callback function must interpret first parameter as filename, and second as percentage

    Example.
    We have a function that take Django model ValidationJob as a parameter
    def update_validation_job_status(filename, percentage, validation_job):
        validation_job.progress = percentage
        validation.job.save()

    It can be passed to validate() function as follows
    job_object = ValidationJob.object.get(id=my_id)
    umbrella_spec.validate(error_log, get_callback_function(update_validation_job_status, validation_job=job_object)

    :param callback_function:
    :param args: user-defined positional arguments for this callback function
    :param kwargs: user-defined kwargs for this callback function
    :return: bound function that can be passed as a parameter to Component.validate()
    """
    return lambda filename, percentage: callback_function(filename, percentage, *args, **kwargs)


