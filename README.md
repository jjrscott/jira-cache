
Direct queries to Jira have two issues:

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
🟩 GVO-1 cluster is not displayed bug
  🟩 GVO-2 syntax error on valid file bug
  🟩 GVO-3 Option to set rendering engine?
    🟩 GVO-5 Please add a license file to this repo
🔶 GVO-7 Share a graph
🔴 GVO-8 Option to download SVG? enhancement
  🔴 GVO-9 Enable resizing of panels? enhancement
  🔴 GVO-11 Export as PDF
🔶 GVO-12 Import from Github gist enhancement
  🔶 GVO-15 Specify the engine via the url enhancement
    🔶 GVO-21 Feature request: zoom and pan enhancement
      🔴 GVO-23 Interactive display
      🟩 GVO-24 Open in new tab on chrome
      🟩 GVO-25 neato different output
```

## Cache issues

Cache JIRA issues in a database and generate 'view' tables to allow easier data access (e.g. parent child relationships).

```
usage: cache-issues.py [-h] --jira-url JIRA_URL --jira-user JIRA_USER --jira-password JIRA_PASSWORD --cache-path CACHE_PATH [--json]

Cache data from JIRA

optional arguments:
  -h, --help            show this help message and exit
  --jira-url JIRA_URL   JIRA base URL (default: None)
  --jira-user JIRA_USER
                        username to access JIRA (default: None)
  --jira-password JIRA_PASSWORD
                        password to access JIRA (default: None)
  --cache-path CACHE_PATH
                        path of the cache (default: None)
  --json                output progress JSON fragments (default: False)
```

## Dump issue

```
usage: dump-issue.py [-h] --jira-url JIRA_URL --jira-user JIRA_USER --jira-password JIRA_PASSWORD [--fields FIELDS] --query QUERY

Dump a JIRA issue to STDOUT

optional arguments:
  -h, --help            show this help message and exit
  --jira-url JIRA_URL   JIRA base URL (default: http://jira.example.com)
  --jira-user JIRA_USER
                        username to access JIRA (default: None)
  --jira-password JIRA_PASSWORD
                        password to access JIRA (default: None)
  --fields FIELDS       password to access JIRA (default: *all)
  --query QUERY         JQL to search for (default: None)
```

## List issues

Use the issues cached by `cache-issues.py` to add subtasks to the query results.

```
usage: list-issues.py [-h] --jira-url JIRA_URL --jira-user JIRA_USER
                      --jira-password JIRA_PASSWORD --cache-path CACHE_PATH
                      [--json] [--fields FIELDS] --query QUERY

List issues using the JIRA cache

optional arguments:
  -h, --help            show this help message and exit
  --jira-url JIRA_URL   JIRA base URL (default: None)
  --jira-user JIRA_USER
                        username to access JIRA (default: None)
  --jira-password JIRA_PASSWORD
                        password to access JIRA (default: None)
  --cache-path CACHE_PATH
                        path of the cache (default: None)
  --json                output progress JSON fragments (default: False)
  --fields FIELDS       password to access JIRA (default: *all)
  --query QUERY         JQL to search for (default: None)
```
