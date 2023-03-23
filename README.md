
Direct queries to [Jira](https://www.atlassian.com/software/jira) have two issues:

1. they are sloooooow
2. many queries are impossible with JQL

This project attempts to alleviate those problems by first caching all issues as JSON to an SQLite database, then extracting various pieces of information to 'view' tables.

### Example

The following example updates the cache with all issues changes then displays all requested issues, subtasks and blocking tasks, then filters out "Done" issues from the blockers:

```shell
cache-issues.py
list-issues.py --query 'summary ~ ios AND status in ("Code review", "In Progress", "To Do") AND  AND Sprint = 10' | grep -v <0001f7e9>
```

#### Output

```
🔶 GVO-7 Share a graph
🔴 GVO-8 Option to download SVG? enhancement
  🔴 GVO-9 Enable resizing of panels? enhancement
  🔴 GVO-11 Export as PDF
🔶 GVO-12 Import from Github gist enhancement
  🔶 GVO-15 Specify the engine via the url enhancement
    🔶 GVO-21 Feature request: zoom and pan enhancement
      🔴 GVO-23 Interactive display
```

## Cache issues

```
usage: cache-issues.py [-h] [--jira-url JIRA_URL] [--jira-user JIRA_USER]
                       [--jira-password JIRA_PASSWORD]
                       [--cache-path CACHE_PATH] [--json] [--clear]

Cache JIRA issues in a database and generate 'view' tables to allow easier
data access (e.g. parent child relationships).

optional arguments:
  -h, --help            show this help message and exit
  --jira-url JIRA_URL   JIRA base URL
  --jira-user JIRA_USER
                        username to access JIRA
  --jira-password JIRA_PASSWORD
                        password to access JIRA
  --cache-path CACHE_PATH
                        path of the cache
  --json                output progress JSON fragments
  --clear               clear the cache
```

## Dump issue

```
usage: dump-issue.py [-h] [--jira-url JIRA_URL] [--jira-user JIRA_USER]
                     [--jira-password JIRA_PASSWORD] [--fields FIELDS] --query
                     QUERY

Dump a JIRA issue to STDOUT

optional arguments:
  -h, --help            show this help message and exit
  --jira-url JIRA_URL   JIRA base URL
  --jira-user JIRA_USER
                        username to access JIRA
  --jira-password JIRA_PASSWORD
                        password to access JIRA
  --fields FIELDS       password to access JIRA
  --query QUERY         JQL to search for
```

## List issues

```
usage: list-issues.py [-h] [--jira-url JIRA_URL] [--jira-user JIRA_USER]
                      [--jira-password JIRA_PASSWORD]
                      [--cache-path CACHE_PATH] [--json] [--fields FIELDS]
                      [--format {summary,branch,markdown}]
                      (--query QUERY | --filter {done_issues,my_open_issues,open_issues,reported_by_me,resolved_recently,updated_recently,viewed_recently})

Use the issues cached by cache-issues.py to add subtasks to the query results.

optional arguments:
  -h, --help            show this help message and exit
  --jira-url JIRA_URL   JIRA base URL
  --jira-user JIRA_USER
                        username to access JIRA
  --jira-password JIRA_PASSWORD
                        password to access JIRA
  --cache-path CACHE_PATH
                        path of the cache
  --json                output progress JSON fragments
  --fields FIELDS       password to access JIRA
  --format {summary,branch,markdown}
                        display format
  --query QUERY         JQL to search for
  --filter {done_issues,my_open_issues,open_issues,reported_by_me,resolved_recently,updated_recently,viewed_recently}
                        Built in queries
```
