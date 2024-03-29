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

filters = {
    'my_open_issues' : 'assignee IN (currentUser()) AND statusCategory in ("To Do", "In Progress") ORDER BY created DESC',
    'reported_by_me' : 'reporter IN (currentUser()) ORDER BY created DESC',
    'open_issues' : 'statusCategory in ("To Do", "In Progress") ORDER BY updated DESC',
    'done_issues' : 'statusCategory = "Done" ORDER BY created DESC',
    'viewed_recently' : 'ORDER BY lastviewed DESC',
    'resolved_recently' : 'resolved >= -1w ORDER BY updated DESC',
    'updated_recently' : 'ORDER BY updated DESC',

}


def list_issues(jira, cache_path, query, fields, format):
    issues = jira.searchAll(query, fields=fields)
    conn = sqlite3.connect(cache_path)

    if len(issues) == 0: return

    requested_keys = list(map(lambda issue: issue['key'], issues))
    handled_keys = set()

    parent_keys = dict()

    for key in requested_keys:
        parent_keys[key] = None

    for key in requested_keys:
        for relation,destination in sql_get_rows(conn, 'SELECT relation,destination FROM IssueLinks where source=?', key):
            if relation in {'has parent', 'subtask of'}:
                parent_keys[key]=destination

    for key in requested_keys:
        if parent_keys[key] not in requested_keys:
            handle_issue(jira, conn, key, format)

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


def handle_issue(jira, conn, key, format, depth=0, prefix=""):
    # print(f"key {key}")
    content = None
    for content, in sql_get_rows(conn, 'SELECT content FROM IssueCache where key=? limit 1', key):
        # print(f"content {content}")
        pass

    if content is None or not len(content):
        print(f"❗ Missing issue, update the cache: {key}", file=sys.stderr)
        return

    # print(key, content)
    issue = json.loads(content)
    issuetype = value_in_dict(issue, 'fields', 'issuetype', 'name')
    summary = value_in_dict(issue, 'fields', 'summary')
    labels = value_in_dict(issue, 'fields', 'labels')
    statusCategory = value_in_dict(issue, 'fields', 'status', 'statusCategory', 'key')

    if format == 'summary':
        print(f"{'  '*depth}{statusCategoryAttributes[statusCategory]['symbol']} {key} {summary}")
    elif format == 'markdown':
        print(f"{'  '*depth}- {statusCategoryAttributes[statusCategory]['symbol']} [{key}]({jira.jira_url}/browse/{key}) {summary}")
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
            handle_issue(jira, conn, destination, format, depth=depth+1, prefix=relation+" ")

class ArgumentParser(argparse.ArgumentParser):
    def add_argument(self, *args, **kwargs):
        if 'default' in kwargs and kwargs['default'] and 'required' in kwargs:
            del kwargs['required']
        super().add_argument(*args, **kwargs)


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(os.path.expanduser('~/.jira-cache.config'))
    parser = ArgumentParser(description="Use the issues cached by cache-issues.py to add subtasks to the query results.",
                             fromfile_prefix_chars='@')

    parser.add_argument('--jira-url', required=True, help='JIRA base URL', default=value_in_dict(config, 'default', 'jira-url'))
    parser.add_argument('--jira-user', required=True, help='username to access JIRA', default=value_in_dict(config, 'default', 'jira-user'))
    parser.add_argument('--jira-password', required=True, help='password to access JIRA', default=value_in_dict(config, 'default', 'jira-password'))
    parser.add_argument('--cache-path', required=True, help='path of the cache', default=value_in_dict(config, 'default', 'cache-path'))
    parser.add_argument('--json', action='store_true', help='output progress JSON fragments')
    parser.add_argument('--fields', default='*all', help='password to access JIRA')
    parser.add_argument('--format', choices=['summary', 'branch', 'markdown'], default='summary', help='display format')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--query', help='JQL to search for')
    group.add_argument('--filter', choices=sorted(filters.keys()), help='Built in queries')
    args = parser.parse_args()

    jira = Jira(args.jira_url, args.jira_user, args.jira_password)
    cache_path = os.path.expanduser(args.cache_path)

    query = args.query
    if args.filter is not None:
        query = filters[args.filter]

    # exit(args)
    list_issues(jira, cache_path, query, args.fields, args.format)
