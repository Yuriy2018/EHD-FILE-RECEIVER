import json

from logging import config, Logger, getLogger


def get_config() -> dict:
    with open('config.json') as file:
        configuration_file = dict(json.load(file))
        return configuration_file


def get_logger() -> Logger:
    logger_config = {
        "logger_name": "mzrk-s-8579",
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {
                "format": "%(asctime)s — [ %(levelname)s ] — %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "console"
            }
        },
        "loggers": {
            "": {
                "handlers": [
                    "console"
                ],
                "level": "INFO",
                "propagate": True
            }
        }
    }
    config.dictConfig(logger_config)
    return getLogger(logger_config['logger_name'])


config_file = get_config()


class Configurations:
    port: str = config_file['service']['port']
    test: bool = config_file['test']
    shep_xml_signer: str = config_file['shep_xml_signer']
    test_url: str = config_file['smart_bridge']['test_url']
    production_url: str = config_file['smart_bridge']['production_url']
    login: str = config_file['service']['login']
    password: str = config_file['service']['password']


configurations = Configurations()
