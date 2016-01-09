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
