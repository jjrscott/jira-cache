#!/usr/bin/env python3

from common import value_in_dict,Jira,sql_get_rows
import argparse
import json
from getpass import getpass
import os
import sys
import sqlite3
import configparser
import re
# from colorama import Fore, Back, Style


def list_issues(jira, cache_path, query, fields, format):
    issues = jira.searchAll(query, fields=fields)
    conn = sqlite3.connect(cache_path)

    if len(issues) == 0: return

    requested_keys = set(map(lambda issue: issue['key'], issues))
    handled_keys = set()

    parent_keys = dict()

    for key in requested_keys:
        parent_keys[key] = None

    for key in requested_keys:
        for relation,destination in sql_get_rows(conn, 'SELECT relation,destination FROM IssueLinks where source=?', key):
            if relation in {'has parent', 'subtask of'}:
                parent_keys[key]=destination

    for key in sorted(requested_keys):
        if parent_keys[key] not in requested_keys:
            handle_issue(conn, key, format)

validRelations = {
    'blocked by',
    'has subtask',
    'parent of',
}

statusCategoryAttributes = {
    'new' :           {'color': '#44516B', 'fontcolor': '#44516B', 'fillcolor': '#DFE1E5', 'symbol': '🔴'},
    'indeterminate' : {'color': '#1F46A0', 'fontcolor': '#1F46A0', 'fillcolor': '#E0EBFD', 'symbol': '🔶'},
    'done' :          {'color': '#2A6447', 'fontcolor': '#2A6447', 'fillcolor': '#E8FBF0', 'symbol': '🟩', 'fontsize': 8},
}


def handle_issue(conn, key, format, depth=0, prefix=""):
    for _,content in sql_get_rows(conn, 'SELECT key,content FROM IssueCache where key=? limit 1', key):
        pass
    if not len(content):
        raise Exception(f"Failed to retrieve issue: {key}")
    # print(key, content)
    issue = json.loads(content)
    issuetype = value_in_dict(issue, 'fields', 'issuetype', 'name')
    summary = value_in_dict(issue, 'fields', 'summary')
    labels = value_in_dict(issue, 'fields', 'labels')
    statusCategory = value_in_dict(issue, 'fields', 'status', 'statusCategory', 'key')

    if format == 'summary':
        print(f"{'  '*depth}{statusCategoryAttributes[statusCategory]['symbol']} {key} {summary}")
    elif format == 'branch':
        emailAddress = value_in_dict(issue, 'fields', 'assignee', 'emailAddress')
        if emailAddress is None: return

        emailAddress = re.sub(r'[\.@].*', '', emailAddress)

        summary = summary.lower()

        branch = f"{key}-{summary}"


        branch = re.sub(r'\[[^\]]+\]', '', branch)
        branch = re.sub(r'[^a-zA-Z0-9]+', '-', branch)

        print(f"{'  '*depth}{statusCategoryAttributes[statusCategory]['symbol']} {emailAddress}/{branch}")

    links = dict()
    for relation,destination in sql_get_rows(conn, 'SELECT relation,destination FROM IssueLinks where source=?', key):
        links[destination] = relation

    for destination,relation in links.items():
        if relation in validRelations:
            handle_issue(conn, destination, format, depth=depth+1, prefix=relation+" ")

class ArgumentParser(argparse.ArgumentParser):
    def add_argument(self, *args, **kwargs):
        if 'default' in kwargs and kwargs['default'] and 'required' in kwargs:
            del kwargs['required']
        super().add_argument(*args, **kwargs)


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(os.path.expanduser('~/.jira-cache.config'))
    parser = ArgumentParser(description="List issues using the JIRA cache",
                             formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                             fromfile_prefix_chars='@')

    parser.add_argument('--jira-url', required=True, help='JIRA base URL', default=value_in_dict(config, 'default', 'jira-url'))
    parser.add_argument('--jira-user', required=True, help='username to access JIRA', default=value_in_dict(config, 'default', 'jira-user'))
    parser.add_argument('--jira-password', required=True, help='password to access JIRA', default=value_in_dict(config, 'default', 'jira-password'))
    parser.add_argument('--cache-path', required=True, help='path of the cache', default=value_in_dict(config, 'default', 'cache-path'))
    parser.add_argument('--json', action='store_true', help='output progress JSON fragments')
    parser.add_argument('--fields', default='*all', help='password to access JIRA')
    parser.add_argument('--format', choices=['summary', 'branch'], default='summary', help='display format')
    parser.add_argument('--query', required=True, help='JQL to search for')
    args = parser.parse_args()

    jira = Jira(args.jira_url, args.jira_user, args.jira_password)
    cache_path = os.path.expanduser(args.cache_path)

    # exit(args)
    list_issues(jira, cache_path, args.query, args.fields, args.format)
