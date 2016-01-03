# Copyright (C) 2016, University of Notre Dame
# All rights reserved
import hashlib
import json
import urllib2

CONFIG = "config"
FILE_NAME = "name"
COMPONENT_NAME = "component_name"
URL_SOURCES = "source"
MD5 = "checksum"
FILE_SIZE = "size"
UNCOMPRESSED_FILE_SIZE = "uncompressed_size"
FILE_FORMAT = "format"
DOWNLOAD_CHUNK_SIZE = 10240

SPECIFICATION_COMPONENTS = {
    "hardware": {
        "required": True,
        "has_files": False,
    },
    "kernel": {
        "required": True,
        "has_files": False,
    },
    "os": {
        "required": True,
        "has_files": True,
    },
    "package_manager": {
        "required": False,
        "has_files": True,
    },
    "software": {
        "required": False,
        "has_files": True,
    },
    "data": {
        "required": False,
        "has_files": True,
    },
}


class UmbrellaValidator:
    def __init__(self, specification_file):
        self.__error_log = []
        self.__warning_log = []

        if specification_file is None:
            raise ValueError("Specification file is required.")

        if not isinstance(specification_file, (file, str, unicode, dict)):
            raise TypeError("Specification file must be an open file, json in string form, or a python dictionary")

        self.specification_file = specification_file

    def validate(self, call_back_function=None, *args):
        self.__error_log = []
        self.__warning_log = []

        # Open Specification
        if isinstance(self.specification_file, file):
            specification_json = json.load(self.specification_file)
        elif isinstance(self.specification_file, (str, unicode)):
            specification_json = json.loads(self.specification_file)
        elif isinstance(self.specification_file, dict):
            specification_json = self.specification_file
        else:
            raise ValueError("Specification file must be an open file, json in string form, or a python dictionary")

        # Initialize lists
        file_infos = []
        valid_specification_components = []

        # Cycle through all of the specification components in the file
        for component_name, component in specification_json.iteritems():
            if component_name in SPECIFICATION_COMPONENTS:  # Is this component in the whitelist, if so, check it
                component = SPECIFICATION_COMPONENTS[component_name]
                valid_specification_components.append(component_name)

                if component["has_files"]:
                    if component_name == "package_manager":  # Package Manager has config and goes one extra level  (3 levels)  # noqa
                        component_file_info = specification_json[component_name][CONFIG]
                    elif component_name == "os":  # OS is on the base level, so one less level                      (1 level)   # noqa
                        component_file_info = {"os": specification_json[component_name]}
                    else:  # Everything else has two levels                                                         (2 levels)  # noqa
                        component_file_info = specification_json[component_name]

                    # Loop through each file's info
                    for name, file_info in component_file_info.iteritems():
                        # OS has its name inside its general info section
                        if component_name == "os":
                            file_name = file_info[FILE_NAME]
                        else:
                            file_name = name

                        file_infos.append({
                            FILE_NAME: file_name,
                            COMPONENT_NAME: component_name,
                            URL_SOURCES: file_info[URL_SOURCES],
                            MD5: file_info[MD5],
                            FILE_SIZE: file_info[FILE_SIZE]
                        })
            else:  # Is this component not in the list of possible components, if so, it is unknown
                self.__warning_log.append(
                    'Specification component "' + str(component_name) +
                    '" is an unknown component. Please check the spelling'
                )

        # Check for missing required components
        for component_name, component in SPECIFICATION_COMPONENTS.iteritems():
            # If the specification component is required and we didn"t find it
            if component["required"] and component_name not in valid_specification_components:
                self.__error_log.append(
                    'Specification component "' + str(component_name) +
                    '" was missing from the supplied specification file'
                )

        for file_info in file_infos:
            for url in file_info[URL_SOURCES]:
                md5 = self.get_md5(url, file_info, call_back_function, *args)

                if md5 and md5 != file_info[MD5]:
                    self.__error_log.append(
                        "The file named " + str(file_info[FILE_NAME]) + " on component " +
                        str(file_info[COMPONENT_NAME]) + " from the url source of " + str(url) +
                        " had a calculated md5 of " + str(md5) + " but the specification says it should be " +
                        str(file_info[MD5])
                    )

    def get_md5(self, the_file_or_url, file_info, call_back_function=None, *args):
        if isinstance(the_file_or_url, file):
            return self.__calculate_md5_via_file(the_file_or_url, file_info, call_back_function, *args)
        elif isinstance(the_file_or_url, (str, unicode)):
            return self.__calculate_md5_via_url(the_file_or_url, file_info, call_back_function, *args)
        else:
            raise ValueError("the_file_or_url must be a file or a string form of a url")

    @property
    def error_log(self):
        return self.__error_log

    @property
    def warning_log(self):
        return self.__warning_log

    def __calculate_md5_via_url(self, url, file_info, call_back_function, *args):
        if not isinstance(url, (str, unicode)):
            raise ValueError("Url must be in string form ")

        try:
            remote = urllib2.urlopen(url)
        except urllib2.HTTPError as error:
            self.__error_log.append(
                "Http error for url " + str(url) + " associated with the file named " +
                str(file_info[FILE_NAME]) + " on component " + str(file_info[COMPONENT_NAME]) + " \"" + str(error) + '"'
            )

            return -1
        except urllib2.URLError as error:
            self.__error_log.append(
                "Url error for url " + str(url) + " associated with the file named " +
                str(file_info[FILE_NAME]) + " on component " + str(file_info[COMPONENT_NAME]) + " \"" + str(error) + '"'
            )

            return -1

        # Get the file_size from the website. Some websites (old ones) may not give this information
        try:
            file_size_from_url = int(remote.headers["content-length"])

            if int(file_size_from_url) != int(file_info[FILE_SIZE]):
                self.__error_log.append(
                    "Url " + str(url) + " associated with the file named " +
                    str(file_info[FILE_NAME]) + " on component " + str(file_info[COMPONENT_NAME]) +
                    " reported a file size of " + str(file_size_from_url) +
                    " but the specification says it should be " + str(file_info[FILE_SIZE])
                )
        except KeyError:
            file_size_from_url = None

        return self.__calculate_md5(remote, file_size_from_url, file_info, call_back_function, *args)

    def __calculate_md5_via_file(self, the_file, file_info, call_back_function, *args):
        if not isinstance(the_file, file):
            raise ValueError("the_file must be an open file ")

        return self.__calculate_md5(the_file, file_info[FILE_SIZE], file_info, call_back_function, *args)

    def __calculate_md5(self, data_source, actual_file_size, file_info, call_back_function, *args):
        bytes_prcoessed = 0
        md5 = hashlib.md5()

        if actual_file_size is None:
            percent_processed = -1

            if call_back_function:
                call_back_function(percent_processed, *args)

        while True:
            data = data_source.read(DOWNLOAD_CHUNK_SIZE)

            # There was no more data to read
            if not data:
                break

            bytes_prcoessed += len(data)

            if actual_file_size:
                percent_processed = float(bytes_prcoessed / actual_file_size * 100)

                if percent_processed > 10:
                    if call_back_function:
                        call_back_function(percent_processed, *args)

            md5.update(data)

        if bytes_prcoessed != int(file_info[FILE_SIZE]):
            self.__error_log.append(
                "The file named " + str(file_info[FILE_NAME]) + " on component " + str(file_info[COMPONENT_NAME]) +
                " had a file size of " + str(bytes_prcoessed) + " but the specification says it should be " +
                str(file_info[FILE_SIZE])
            )

        return md5.hexdigest()


if __name__ == "__main__":
    pass