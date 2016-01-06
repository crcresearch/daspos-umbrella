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


class UmbrellaFile(object):
    __required_keys = ['id', 'source', 'format', 'checksum', 'size', 'mountpoint']
    __error_log = []
    __warning_log = []

    def __init__(self, file_json=None, component_name=None):
        self.file_json = file_json
        self.component_name = component_name

    def validate(self):
        is_valid = True
        self.__error_log = []
        self.__warning_log = []

        if not isinstance(self.file_json, dict):
            # self.__error_log.append("Component %s must be dict" % self.name)

            return False

        if "source" in self.file_json:
            if not isinstance(self.file_json["source"], list):
                self.__error_log.append("\"source\" must be a list in %s component" % self.component_name)

            # MD5 and SIZE validation for all sources - passing callback function as self.umbrella_specification_callback_function
            # ...
        else:
            is_valid = False

        return is_valid

    def get_md5_and_file_size(self, the_file_or_url, file_info, call_back_function=None, *args):
        if hasattr(the_file_or_url, "read"):
            return self.get_md5_and_file_size_via_file(the_file_or_url, file_info, call_back_function, *args)
        elif isinstance(the_file_or_url, (str, unicode)):
            return self.get_md5_and_file_size_via_url(the_file_or_url, file_info, call_back_function, *args)
        else:
            raise ValueError("the_file_or_url must be a file or a string form of a url")

    def get_md5_and_file_size_via_url(self, url, file_info, call_back_function, *args):
        if not isinstance(url, (str, unicode)):
            raise ValueError("Url must be in string form ")

        try:
            remote = urllib2.urlopen(url)
        except urllib2.HTTPError as error:
            self.__error_log.append(
                "Http error for url " + str(url) + " associated with the file named " +
                str(file_info[FILE_NAME]) + " on component " + str(file_info[COMPONENT_NAME]) + " \"" + str(error) + '"'
            )

            return None, None
        except urllib2.URLError as error:
            self.__error_log.append(
                "Url error for url " + str(url) + " associated with the file named " +
                str(file_info[FILE_NAME]) + " on component " + str(file_info[COMPONENT_NAME]) + " \"" + str(error) + '"'
            )

            return None, None

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

    def get_md5_and_file_size_via_file(self, the_file, file_info, call_back_function, *args):
        if not hasattr(the_file, "read"):
            raise ValueError("the_file must be an open file ")

        return self.__calculate_md5(the_file, file_info[FILE_SIZE], file_info, call_back_function, *args)

    def __calculate_md5(self, data_source, actual_file_size, file_info, call_back_function, *args):
        bytes_processed = 0
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

            bytes_processed += len(data)

            if actual_file_size:
                percent_processed = float(bytes_processed / actual_file_size * 100)

                if percent_processed > 10:
                    if call_back_function:
                        call_back_function(percent_processed, *args)

            md5.update(data)

        if call_back_function:
            call_back_function(100.0, *args)

        return md5.hexdigest(), bytes_processed


class UmbrellaFileInOSComponent(UmbrellaFile):
    __required_keys = ['id', 'source', 'format', 'checksum', 'size']


class Component(object):
    __required_keys = []

    def __init__(self, umbrella_specification, component_name, component_json=None):
        self.umbrella_specification = umbrella_specification
        self.name = component_name
        self.component_json = component_json

    def validate(self):
        is_valid = True

        if not isinstance(self.component_json, dict):
            self.umbrella_specification.__error_log.append("Component %s must be dict" % self.name)

            return False

        for key in self.__required_keys:
            if key not in self.component_json:
                is_valid = False
                self.umbrella_specification.__error_log.append("\"%s\" key is required in %s component" % (key, self.name))  # noqa

        return is_valid


class MissingComponent(Component):
    def validate(self):
        self.umbrella_specification.__error_log.append("Component %s doesn't exist" % self.name)
        return False


class OsComponent(Component):
    __required_keys = ['version', 'name']

    def validate(self, *args):
        is_valid = super(OsComponent, self).validate()

        if "source" in self.component_json:
            os_file = UmbrellaFileInOSComponent(self.component_json["source"])
        else:
            os_file = UmbrellaFileInOSComponent(None)

        if not os_file.validate():
            is_valid = False

        return is_valid


class UmbrellaSpecification:
    """
    Note this class is NOT thread safe. Do not use it in multithreaded environment.
    """
    def __init__(self, specification_file):
        self.__error_log = []
        self.__warning_log = []
        self.callback_function = lambda *args, **kwargs: True
        self.args = []

        if specification_file is None:
            raise ValueError("Specification file is required.")

        if not isinstance(specification_file, (file, str, unicode, dict)):
            raise TypeError("Specification file must be an open file, json in string form, or a python dictionary")

        # Open Specification
        if hasattr(specification_file, "read"):
            self.specification_json = json.load(specification_file)
        elif isinstance(specification_file, (str, unicode)):
            self.specification_json = json.loads(specification_file)
        elif isinstance(specification_file, dict):
            self.specification_json = specification_file
        else:
            raise ValueError("Specification file must be an open file, json in string form, or a python dictionary")

        if "os" in self.specification_json:
            self.os = OsComponent(self, "os", self.specification_json["os"])
        else:
            self.os = MissingComponent(self, "os")

    def validate2(self, call_back_function=None, *args):
        is_valid = True
        self.callback_function = call_back_function
        self.args = args
        if not self.os.validate():
            is_valid = False

        return is_valid

    def validate(self, call_back_function=None, *args):
        self.__error_log = []
        self.__warning_log = []

        # Initialize lists
        file_infos = []
        valid_specification_components = []

        # Cycle through all of the specification components in the file
        for component_name, component in self.specification_json.iteritems():
            if component_name in SPECIFICATION_COMPONENTS:  # Is this component in the whitelist, if so, check it
                component = SPECIFICATION_COMPONENTS[component_name]
                valid_specification_components.append(component_name)

                if component["has_files"]:
                    if component_name == "package_manager":  # Package Manager has config and goes one extra level  (3 levels)  # noqa
                        component_file_info = self.specification_json[component_name][CONFIG]
                    elif component_name == "os":  # OS is on the base level, so one less level                      (1 level)   # noqa
                        component_file_info = {"os": self.specification_json[component_name]}
                    else:  # Everything else has two levels                                                         (2 levels)  # noqa
                        component_file_info = self.specification_json[component_name]

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
                md5, file_size = self.get_md5_and_file_size(url, file_info, call_back_function, *args)

                if file_size != int(file_info[FILE_SIZE]):
                    self.__error_log.append(
                        "The file named " + str(file_info[FILE_NAME]) + " on component " + str(file_info[COMPONENT_NAME]) +
                        " had a file size of " + str(file_size) + " but the specification says it should be " +
                        str(file_info[FILE_SIZE])
                    )

                if md5 and md5 != file_info[MD5]:
                    self.__error_log.append(
                        "The file named " + str(file_info[FILE_NAME]) + " on component " +
                        str(file_info[COMPONENT_NAME]) + " from the url source of " + str(url) +
                        " had a calculated md5 of " + str(md5) + " but the specification says it should be " +
                        str(file_info[MD5])
                    )

    @property
    def error_log(self):
        return self.__error_log

    @property
    def warning_log(self):
        return self.__warning_log


if __name__ == "__main__":
    pass