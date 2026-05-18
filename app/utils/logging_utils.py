import logging

main_logger = None


def log_main(level, message, domain='general'):
    if main_logger is not None:
        getattr(main_logger, level.lower())(f"{domain} - {message}")


def set_main_logger(logger):
    global main_logger
    main_logger = logger
