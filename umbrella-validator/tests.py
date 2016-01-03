from UmbrellaValidator import UmbrellaValidator

VALID_FILE = "E:/PycharmProjects/daspos-umbrella/umbrella-validator/openmalaria.umbrella"
PATH = "E:/PycharmProjects/daspos-umbrella/umbrella-validator/BrokenSpecs/"


def test_all_errors():
    validate_and_report("all-errors.umbrella")


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
    specification_file = open(PATH + file_name)

    umbrella_validator = UmbrellaValidator(specification_file)
    umbrella_validator.validate()

    print umbrella_validator.error_log
    print umbrella_validator.warning_log


def test_all():
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