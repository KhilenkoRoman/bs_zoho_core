from ast import literal_eval
import logging
import dj_database_url
import os

from django.conf import global_settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

__all__ = (
    'fetch_settings_from_env',
    'apply_settings',
    'load_and_apply_settings_from_env',
)


def match_whitelist(name, white_list):
    if white_list is None:
        return True
    # TODO: whitelist can be ['PREFIX_*' (mask, regex), 'DEBUG' (explicit)])
    return name in white_list


def fetch_settings_from_env(prefix=None, white_list=None):
    logger.debug('Fetching settings from environment')
    env = dict(os.environ)
    if prefix is not None:
        env = {k[len(prefix):]:v for k,v in env.items() if k.lower().startswith(prefix.lower())}  # some evns tronsform names
    env = {k: v for k, v in env.items() if match_whitelist(k, white_list)}  # or k not in black_list }

    parsed_settings = {}

    for name, raw_value in env.items():
        # special cases:
        if name == 'DATABASE_URL':
            try:
                value = dj_database_url.parse(raw_value)
                if 'DATABASES' not in parsed_settings:
                    parsed_settings['DATABASES'] = {'default': {}}
                parsed_settings['DATABASES']['default'] = {
                    **value,
                    **parsed_settings["DATABASES"]["default"]
                }
            except Exception as e:
                logger.warning('Could not parse database configurations form url "%s", reason %r' % (raw_value, e))
                # fail cause DATABASE_URL is important config, and if specified it must be parsed correctly
                raise ImproperlyConfigured('Could not parse database configurations form url "%s", reason %r' % (raw_value, e))
            continue
        if name == "DB_CONN_MAX_AGE":
            try:
                value = literal_eval(raw_value)
                if 'DATABASES' not in parsed_settings:
                    parsed_settings['DATABASES'] = {'default': {}}
                parsed_settings['DATABASES']['default'].update({"CONN_MAX_AGE": value})
            except Exception as e:
                logger.warning('Could not parse database configurations form url "%s", reason %r' % (raw_value, e))
                # fail cause DATABASE_URL is important config, and if specified it must be parsed correctly
                raise ImproperlyConfigured('Could not parse database configurations form url "%s", reason %r' % (raw_value, e))
            continue
        try:
            value = literal_eval(raw_value)  # never use eval()
            parsed_type = type(value)
            basic_type = type(getattr(global_settings, name, None))
            if basic_type is not type(None) and parsed_type is not type(None):
                if parsed_type is not basic_type:
                    logger.warning('Mismatched type %s!=%s (name="%s" value="%s")' % (basic_type, parsed_type, name, raw_value))
        except (ValueError, SyntaxError) as e:
            if raw_value.lower() == 'true':
                value = True
            elif raw_value.lower() == 'false':
                value = False
            else:
                logger.debug('Could not parse "%s"="%s", reason "%r", keep as string' % (name, raw_value, e))
                value = raw_value  # keep as string

        subkeys = name.split('.')
        if len(subkeys) > 0:
            pointer = parsed_settings
            for key in subkeys[:-1]:
                if key not in pointer or not isinstance(pointer[key], dict):
                    pointer[key] = {}
                pointer = pointer[key]
            pointer[subkeys[-1]] = value
        else:
            parsed_settings[name] = value

    logger.debug('Fetched settings %s' % parsed_settings)
    return parsed_settings


def apply_settings(obj, settings):
    for setting in settings:
        setattr(obj, setting, settings[setting])


def load_and_apply_settings_from_env(obj, prefix=None, prefixes=None, white_list=None):
    """
    :param obj: settings object, or sys.modules[__name__]
    :param prefix: use only vars starting with prefix, and trim it (prefixVAR_NAME -> VAR_NAME)
    :param prefixes: array of prefix
    :param white_list:
    :return:
    """
    if prefixes is not None:
        for pr in prefixes:
            apply_settings(obj, fetch_settings_from_env(prefix=pr, white_list=white_list))
    else:
        apply_settings(obj, fetch_settings_from_env(prefix=prefix, white_list=white_list))
