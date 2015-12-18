# Copyright (C) 2016, University of Notre Dame
# All rights reserved
import hashlib
import json
import urllib2

CONFIG = 'config'
FILE_NAME = 'name'
URL_SOURCES = 'source'
MD5 = 'checksum'
FILE_SIZE = 'size'
UNCOMPRESSED_FILE_SIZE = 'uncompressed_size'
FILE_FORMAT = 'format'
DOWNLOAD_CHUNK_SIZE = 10240

SPECIFICATION_COMPONENTS = {
    'hardware': {
        'required': True,
        'has_files': False,
    },
    'kernel': {
        'required': True,
        'has_files': False,
    },
    'os': {
        'required': True,
        'has_files': True,
    },
    'package_manager': {
        'required': False,
        'has_files': True,
    },
    'software': {
        'required': False,
        'has_files': True,
    },
    'data': {
        'required': False,
        'has_files': True,
    },
}


class UmbrellaValidator:
    def __init__(self, specification_file):
        if specification_file is None:
            raise ValueError('Specification file is required.')

        if not isinstance(specification_file, (file, str, unicode, dict)):
            raise TypeError('Specification file must be an open file, json in string form, or a python dictionary')

        self.specification_file = specification_file

    def validate(self, call_back_function=None, *args):
        # Open Specification
        if isinstance(self.specification_file, file):
            specification_json = json.load(self.specification_file)
        elif isinstance(self.specification_file, (str, unicode)):
            specification_json = json.loads(self.specification_file)
        elif isinstance(self.specification_file, dict):
            specification_json = self.specification_file
        else:
            raise ValueError('Specification file must be an open file, json in string form, or a python dictionary')

        # Initialize lists
        file_infos = []
        read_specifications = []
        duplicate_specifications = []
        missing_specifications = []
        unknown_specifications = []

        # Cycle through all of the known specification components
        for component_name, component in SPECIFICATION_COMPONENTS.iteritems():
            if component_name in read_specifications:  # Have this component already been read, if so, it is a duplicate
                duplicate_specifications.append(component_name)
            elif component_name in specification_json:  # Is this component in the file, if so, check it
                read_specifications.append(component_name)

                if component['has_files']:
                    # Package Manager is set up slightly differently
                    if component_name == 'package_manager':
                        component_file_info = specification_json[component_name][CONFIG]
                    else:
                        component_file_info = specification_json[component_name]

                    # Loop through each files info
                    for name, file_info in component_file_info.iteritems():
                        # OS has its name inside its general info section
                        if component_name == 'os':
                            file_name = file_info[FILE_NAME]
                        else:
                            file_name = name

                        file_infos.append({
                            FILE_NAME: file_name,
                            URL_SOURCES: file_info[URL_SOURCES],
                            MD5: file_info[MD5],
                            FILE_SIZE: file_info[FILE_SIZE]
                        })
            elif component['required']:  # Is this component required (and we didn't have it), if so, it is missing
                missing_specifications.append(component_name)
            else:  # Is this component not in the list of possible components, if so, it is unknown
                unknown_specifications.append(component_name)

        for file_info in file_infos:
            file_name = file_info[FILE_NAME]

            for url in file_info[URL_SOURCES]:
                md5 = self.get_md5(url, file_info[FILE_SIZE], call_back_function, *args)

                if md5 and md5 != file_info[MD5]:
                    pass

    def get_md5(self, the_file_or_url, file_size, call_back_function=None, *args):
        if isinstance(the_file_or_url, file):
            return self.__calculate_md5_via_file(the_file_or_url, file_size, call_back_function, *args)
        elif isinstance(the_file_or_url, (str, unicode)):
            return self.__calculate_md5_via_url(the_file_or_url, file_size, call_back_function, *args)
        else:
            raise ValueError('the_file_or_url must be a file or a string form of a url')

    def __calculate_md5_via_url(self, url, supposed_file_size, call_back_function, *args):
        if not isinstance(url, (str, unicode)):
            raise ValueError('Url must be in string form ')

        try:
            remote = urllib2.urlopen(url)
        except urllib2.HTTPError:
            raise ValueError('404? Need to put this in an error log.')

        # Get the file_size from the website. Some websites (old ones) may not give this information
        try:
            file_size = int(remote.headers['content-length'])
        except KeyError:
            file_size = None

        return self.__calculate_md5(remote, file_size, supposed_file_size, call_back_function, *args)

    def __calculate_md5_via_file(self, the_file, file_size, call_back_function, *args):
        if not isinstance(the_file, file):
            raise ValueError('the_file must be an open file ')

        return self.__calculate_md5(the_file, file_size, file_size, call_back_function, *args)

    def __calculate_md5(self, data_source, actual_file_size, supposed_file_size, call_back_function, *args):
        bytes_downloaded = 0
        md5 = hashlib.md5()

        if actual_file_size is None:
            percent_processed = -1
            call_back_function(percent_processed, *args)

        while True:
            data = data_source.read(DOWNLOAD_CHUNK_SIZE)

            # There was no more data to read
            if not data:
                break

            bytes_downloaded += len(data)

            if actual_file_size:
                percent_processed = float(bytes_downloaded / actual_file_size * 100)

                if percent_processed > 10:
                    call_back_function(percent_processed, *args)

            md5.update(data)

        if bytes_downloaded != supposed_file_size:
            raise ValueError('File size mismatch. Need to put this in a log.')

        return md5.hexdigest()


if __name__ == "__main__":
    pass