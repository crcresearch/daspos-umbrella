<a href="https://zenhub.com"><img src="https://raw.githubusercontent.com/ZenHubIO/support/master/zenhub-badge.png"></a>


# daspos-umbrella
Core library for Umbrella

# System requirements

Python 2.7 only. Requires setuptools. 

# Installation

Install the latest release using pip:

`pip install daspos-umbrella`

Development version can installed using `pip install git+https://github.com/crcresearch/daspos-umbrella.git`

Alternatively, you can download or clone this repo and call `pip install -e ..`

# Usage example

```python
    specification_file = open(file_name)
    umbrella_validator = UmbrellaSpecification(specification_file)
    umbrella_validator.validate()

    for error in umbrella_validator.error_log:
        print str(error)
```

# Useful links

Online JSON Schema validator - http://www.jsonschemavalidator.net/
