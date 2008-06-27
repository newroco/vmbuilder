import logging

FORMAT='%(asctime)s %(levelname)-8s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

def set_verbosity(option, opt_str, value, parser):
    if opt_str == '--debug':
        logging.getLogger().setLevel(logging.DEBUG)
    elif opt_str == '--verbose':
        logging.getLogger().setLevel(logging.INFO)
    elif opt_str == '--quiet':
        logging.getLogger().setLevel(logging.CRITICAL)
