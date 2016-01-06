import urllib2

from umbrella.UmbrellaError import MissingComponentError
from umbrella.UmbrellaSpecification import FILE_SIZE, COMPONENT_NAME, FILE_NAME
from umbrella.misc import get_md5_and_file_size


class Component(object):
    __required_keys = []
    is_required = False

    def __init__(self, umbrella_specification, component_name, component_json=None):
        self.umbrella_specification = umbrella_specification
        self.name = component_name
        self.component_json = component_json

    @property
    def required_keys(self):
        return self.__required_keys

    def validate(self):
        is_valid = True

        if not isinstance(self.component_json, dict):
            raise TypeError("Component %s must be dict" % self.name)

        for key in self.__required_keys:
            if key not in self.component_json:
                is_valid = False
                self.umbrella_specification.__error_log.append("\"%s\" key is required in %s component" % (key, self.name))  # noqa

        return is_valid

    @staticmethod
    def get_specific_component(umbrella_specification, component_name, component_json):
        if not isinstance(component_name, (str, unicode)):
            raise TypeError("component_name must be a string.")

        if component_name == "comment":
            return CommentComponent(umbrella_specification, component_name, component_json)
        elif component_name == "note":
            return NoteComponent(umbrella_specification, component_name, component_json)
        elif component_name == "hardware":
            return HardwareComponent(umbrella_specification, component_name, component_json)
        elif component_name == "kernel":
            return KernelComponent(umbrella_specification, component_name, component_json)
        elif component_name == "os":
            return OsComponent(umbrella_specification, component_name, component_json)
        elif component_name == "package_manager":
            return PackageManagerComponent(umbrella_specification, component_name, component_json)
        elif component_name == "software":
            return SoftwareComponent(umbrella_specification, component_name, component_json)
        elif component_name == "data":
            return DataComponent(umbrella_specification, component_name, component_json)
        elif component_name == "environ":
            return EnvironComponent(umbrella_specification, component_name, component_json)
        elif component_name == "cmd":
            return CmdComponent(umbrella_specification, component_name, component_json)
        elif component_name == "output":
            return OutputComponent(umbrella_specification, component_name, component_json)
        else:
            raise ValueError("There is no component called " + str(component_name))


class MissingComponent(Component):
    def validate(self):
        raise MissingComponentError("Component " + str(self.name) + " doesn't exist")


class UmbrellaFileInfoSubComponent(Component):
    __required_keys = ["id", "source", "format", "checksum", "size", "mountpoint"]
    __error_log = []
    __warning_log = []

    def validate(self):
        is_valid = True
        self.__error_log = []
        self.__warning_log = []

        if "source" in self.file_json:
            if not isinstance(self.file_json["source"], list):
                raise TypeError("\"source\" must be a list")

            # MD5 and SIZE validation for all sources - passing callback function as self.umbrella_specification_callback_function
            # ...
        else:
            is_valid = False

        return is_valid

    def __get_md5_and_file_size(self, the_file_or_url, file_info, callback_function=None, *args):
        if hasattr(the_file_or_url, "read"):
            return self.__get_md5_and_file_size_via_file(the_file_or_url, file_info[FILE_SIZE], callback_function, *args)
        elif isinstance(the_file_or_url, (str, unicode)):
            return self.__get_md5_and_file_size_via_url(the_file_or_url, file_info, callback_function, *args)
        else:
            raise ValueError("the_file_or_url must be a file or a string form of a url")

    def __get_md5_and_file_size_via_file(self, the_file, actual_file_size, callback_function=None, *args):
        if not hasattr(the_file, "read"):
            raise ValueError("the_file must be an open file ")

        return get_md5_and_file_size(the_file, actual_file_size, callback_function, *args)

    def __get_md5_and_file_size_via_url(self, url, file_info, callback_function=None, *args):
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

        return get_md5_and_file_size(remote, file_size_from_url, callback_function, *args)


class OsUmbrellaFileInfoSubComponent(UmbrellaFileInfoSubComponent):
    __required_keys = ["id", "source", "format", "checksum", "size"]


class CommentComponent(Component):
    __required_keys = []
    is_required = False

    def validate(self):
        is_valid = super(CommentComponent, self).validate()

        return is_valid


class NoteComponent(Component):
    __required_keys = []
    is_required = False

    def validate(self):
        is_valid = super(NoteComponent, self).validate()

        return is_valid


class HardwareComponent(Component):
    __required_keys = ["arch", "cores", "memory", "disk"]
    is_required = True


class KernelComponent(Component):
    __required_keys = ["name", "version"]
    is_required = True


class OsComponent(Component):
    __required_keys = ["name", "version"]
    is_required = True

    def validate(self):
        is_valid = super(OsComponent, self).validate()

        if "source" in self.component_json:
            os_file = OsUmbrellaFileInfoSubComponent(self.component_json["source"])
            os_file_info = OsUmbrellaFileInfoSubComponent({"os": self.component_json})
        else:
            os_file = OsUmbrellaFileInfoSubComponent(None)

        if not os_file.validate():
            is_valid = False

        return is_valid


class PackageManagerComponent(Component):
    __required_keys = ["NEED_TO_DO"]
    is_required = False


class SoftwareComponent(Component):
    __required_keys = ["NEED_TO_DO"]
    is_required = False


class DataComponent(Component):
    __required_keys = ["NEED_TO_DO"]
    is_required = False


class EnvironComponent(Component):
    __required_keys = ["NEED_TO_DO"]
    is_required = False


class CmdComponent(Component):
    __required_keys = ["NEED_TO_DO"]
    is_required = False


class OutputComponent(Component):
    __required_keys = ["NEED_TO_DO"]
    is_required = True