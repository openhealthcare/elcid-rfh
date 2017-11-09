import re

def check_alpha_numeric(some_var):
    valid = re.match('^[\w- ]+$', str)
    if valid is not None:
        raise ValueError('unable to process {}'.format(some_var))
