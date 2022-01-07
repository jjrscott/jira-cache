#!/usr/bin/env python3

import common
from common import value_in_dict
import argparse
import json
from getpass import getpass
import os
import sys
import configparser

def dump_issue(jira, query, fields):
    response = jira.search(query, fields=fields)
    print(json.dumps(response, sort_keys=True, indent=2))

class ArgumentParser(argparse.ArgumentParser):
    def add_argument(self, *args, **kwargs):
        if 'default' in kwargs and kwargs['default'] and 'required' in kwargs:
            del kwargs['required']
        super().add_argument(*args, **kwargs)

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(os.path.expanduser('~/.jira-cache.config'))
    parser = ArgumentParser(description="Dump a JIRA issue to STDOUT",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--jira-url', required=True, help='JIRA base URL', default=value_in_dict(config, 'default', 'jira-url'))
    parser.add_argument('--jira-user', required=True, help='username to access JIRA', default=value_in_dict(config, 'default', 'jira-user'))
    parser.add_argument('--jira-password', required=True, help='password to access JIRA', default=value_in_dict(config, 'default', 'jira-password'))
    parser.add_argument('--fields', default='*all', help='password to access JIRA')
    parser.add_argument('--query', required=True, help='JQL to search for')

    args = parser.parse_args()

    jira = common.Jira(args.jira_url, args.jira_user, args.jira_password)

    # exit(args)
    dump_issue(jira, args.query, args.fields)
