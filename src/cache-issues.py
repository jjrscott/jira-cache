#!/usr/bin/env python3

import sqlite3
import argparse
import configparser
import os
import requests
import json
import re
import progress
import sys
from common import value_in_dict,sql_set_row, Jira

def cache_issues(jira, cache_path):
    should_setup_database = False
    if not os.path.exists(cache_path):
        should_setup_database = True

    conn = sqlite3.connect(cache_path)

    if should_setup_database:
        print(f'Setting up database')
        conn.execute('''CREATE TABLE IssueCache (key, updated, content, PRIMARY KEY (key))''')

    start_at = 0

    while True:
        start_date = conn.execute('SELECT MAX(updated) FROM IssueCache').fetchone()[0] or '1979-04-04'

        content = jira.search(f'updated >= "{start_date}" ORDER BY updated ASC', startAt=start_at, fields='*all')

        if 'issues' not in content: raise Exception('Expected keys not returned "issues"')
        if len(content['issues']) == 0: break

        for issue in content['issues']:
            key = issue['key']
            # Jira doesn't appear to accept its own timestamps 🤷🏻‍♂️
            end_date = issue['fields']['updated']
            end_date = re.sub(r'T(\d+):(\d+).*', ' \\1:\\2', end_date)
            conn.execute('REPLACE INTO IssueCache (key, updated, content) VALUES (?,?,?)', [key, end_date, json.dumps(issue)])

        conn.commit()

        progress.progress('total: {total} ({start_date} ... {end_date} ) {start_at}',
                     total=content['total'] - start_at,
                     start_date=start_date,
                     end_date=end_date,
                     start_at=start_at)

        if content['total'] < content['maxResults']:
            break

        if start_date == end_date:
            start_at += len(content['issues'])
        else:
            start_at = 0

def rebuild_data_tables(cache_path):
    conn = sqlite3.connect(cache_path)

    total = conn.execute('SELECT COUNT(*) FROM IssueCache').fetchone()[0]

    progress.progress('Rebuilding data tables {total}', total=total)

    conn.execute('DROP TABLE IF EXISTS Issues')
    conn.execute('CREATE TABLE Issues (id,key,summary,assignee,creator,updated,status,timeoriginalestimate,type,storypoints,priority,resolutiondate, PRIMARY KEY (id))')
    conn.execute('DROP TABLE IF EXISTS Users')
    conn.execute('CREATE TABLE Users (id, emailAddress, displayName, timeZone, active, type, PRIMARY KEY (id))')
    conn.execute('DROP TABLE IF EXISTS Worklog')
    conn.execute('CREATE TABLE Worklog (issueId, authorId, started, timeSpent, PRIMARY KEY (issueId, authorId, started, timeSpent))')
    conn.execute('DROP TABLE IF EXISTS IssueLinks')
    conn.execute('CREATE TABLE IssueLinks (id, source, relation, destination)')

    all_fields = dict()
    handled_fields = set()

    count = 0
    percentage = 0

    for key,content in conn.execute('SELECT key,content FROM IssueCache'):
        content = json.loads(content)
        update_issue_from_content(conn, content, all_fields, handled_fields)
        count+=1

        current_percentage = int(10*count/total)
        if current_percentage != percentage:
            percentage = current_percentage
            progress.progress('Progress {percentage}%', percentage=10*percentage)

    conn.commit()

    # print(json.dumps(all_fields, sort_keys=True, indent=2))

def update_issue_from_content(conn, content, all_fields, handled_fields):
    if not content: return None
    for key,value in content['fields'].items():
        if value := value:
            all_fields[key] = value
    issue = {}
    issue['assignee'] = update_user_with_content(conn, value_in_dict(content, 'fields', 'assignee'))
    issue['creator'] = update_user_with_content(conn, value_in_dict(content, 'fields', 'creator'))
    issue['id'] = value_in_dict(content, 'id')
    issue['key'] = value_in_dict(content, 'key')
    issue['priority'] = value_in_dict(content, 'fields', 'priority', 'name')
    issue['resolutiondate'] = value_in_dict(content, 'fields', 'resolutiondate')
    issue['status'] = value_in_dict(content, 'fields', 'status', 'name')
    issue['storypoints'] = value_in_dict(content, 'fields', 'customfield_10600')
    issue['summary'] = value_in_dict(content, 'fields', 'summary')
    issue['timeoriginalestimate'] = value_in_dict(content, 'fields', 'timeoriginalestimate')
    issue['type'] = value_in_dict(content, 'fields', 'issuetype', 'name')
    issue['updated'] = value_in_dict(content, 'fields', 'updated')

    update_worklogs_with_content(conn, value_in_dict(content, 'fields', 'worklog', 'worklogs'))

    sql_set_row(conn, 'Issues', **issue)

    if parent_key := value_in_dict(content, 'fields', 'parent', 'key'):
        sql_set_row(conn, 'IssueLinks', source=issue['key'], relation='has parent', destination=parent_key)
        sql_set_row(conn, 'IssueLinks', source=parent_key, relation='parent of', destination=issue['key'])

    for subtask in value_in_dict(content, 'fields', 'subtasks') or []:
        sql_set_row(conn, 'IssueLinks', source=issue['key'], relation='has subtask', destination=subtask['key'])
        sql_set_row(conn, 'IssueLinks', source=subtask['key'], relation='subtask of', destination=issue['key'])


    for issuelink in value_in_dict(content, 'fields', 'issuelinks') or []:
        if 'outwardIssue' in issuelink:
            sql_set_row(conn, 'IssueLinks', id=issuelink['id'], source=issue['key'], relation=value_in_dict(issuelink, 'type', 'outward'), destination=value_in_dict(issuelink, 'outwardIssue', 'key'))
        if 'inwardIssue' in issuelink:
            sql_set_row(conn, 'IssueLinks', id=issuelink['id'], source=issue['key'], relation=value_in_dict(issuelink, 'type', 'inward'), destination=value_in_dict(issuelink, 'inwardIssue', 'key'))

    return issue['id']

def update_user_with_content(conn, content):
    if not content: return None
    user = {}
    user['id'] = value_in_dict(content, 'accountId')
    user['type'] = value_in_dict(content, 'accountType')
    user['active'] = value_in_dict(content, 'active')
    user['displayName'] = value_in_dict(content, 'displayName')
    user['emailAddress'] = value_in_dict(content, 'emailAddress')
    user['timeZone'] = value_in_dict(content, 'timeZone')
    sql_set_row(conn, 'Users', **user)
    return user['id']

def update_worklogs_with_content(conn, content):
    if not isinstance(content, list): return None

    for worklog_json in content:
        worklog = {}
        worklog['issueId'] = value_in_dict(worklog_json, 'issueId')
        worklog['authorId'] = value_in_dict(worklog_json, 'author', 'accountId')
        worklog['started'] = value_in_dict(worklog_json, 'started')
        worklog['timeSpent'] = value_in_dict(worklog_json, 'timeSpentSeconds')
        sql_set_row(conn, 'Worklog', **worklog)

class ArgumentParser(argparse.ArgumentParser):
    def add_argument(self, *args, **kwargs):
        if 'default' in kwargs and kwargs['default'] and 'required' in kwargs:
            del kwargs['required']
        super().add_argument(*args, **kwargs)

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(os.path.expanduser('~/.jira-cache.config'))
    parser = ArgumentParser(description="Cache data from JIRA",
                             formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                             fromfile_prefix_chars='@')

    parser.add_argument('--jira-url', required=True, help='JIRA base URL', default=value_in_dict(config, 'default', 'jira-url'))
    parser.add_argument('--jira-user', required=True, help='username to access JIRA', default=value_in_dict(config, 'default', 'jira-user'))
    parser.add_argument('--jira-password', required=True, help='password to access JIRA', default=value_in_dict(config, 'default', 'jira-password'))
    parser.add_argument('--cache-path', required=True, help='path of the cache', default=value_in_dict(config, 'default', 'cache-path'))
    parser.add_argument('--json', action='store_true', help='output progress JSON fragments')
    args = parser.parse_args()

    progress.output_json = args.json

    jira = Jira(args.jira_url, args.jira_user, args.jira_password)

    cache_path = os.path.expanduser(args.cache_path)

    # exit(args)
    cache_issues(jira, cache_path)
    rebuild_data_tables(cache_path)
