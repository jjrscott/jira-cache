import requests
import json
import sys

class Jira:
    def __init__(self, jira_url, jira_user, jira_password):
        self.jira_url = jira_url
        self.jira_user = jira_user
        self.jira_password = jira_password

    def search(self, query, startAt=None, fields=None):
        params = dict()
        params['jql'] = query
        if fields: params['fields'] = fields
        if startAt: params['startAt'] = startAt
        result = requests.get(self.jira_url+'/rest/api/3/search',
                                auth=(self.jira_user, self.jira_password),
                                headers={'Content-type': 'application/json'},
                                params=params)
        return result.json()

    def searchAll(self, query, fields=None):
        issues = list()
        while True:
            # print("search", file=sys.stderr)
            result = self.search(query, startAt=len(issues), fields=fields)
            if 'issues' in result and len(result['issues']) > 0:
                issues += result['issues']
                if 'total' in result and len(issues) >= result['total']:
                    break
            else:
                break

        return issues

def sql_get_rows(conn, query, *values):
    return conn.execute(query, values)

def sql_set_row(conn, table, **row):
    keys = sorted(row)
    sql = f"""REPLACE INTO {table} ({','.join(map(lambda key: f"`{key}`", keys))}) VALUES ({','.join('?'*len(keys))})"""
    try:
        conn.execute(sql, list(map(lambda key: row[key], keys)))
    except Exception as e:
        print('sql', sql)
        print('keys', keys)
        print('row', row)
        raise

def value_in_dict(object, *keys):
    for key in keys:
        if key in object and object[key]:
            object = object[key]
        else:
            return None
    return object
