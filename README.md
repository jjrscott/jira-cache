
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

Cache JIRA issues in a database and generate 'view' tables to allow easier data access (e.g. parent child relationships).

### Optional arguments
```
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

Dump a JIRA issue to STDOUT.

### Optional arguments
```
-h, --help            show this help message and exit
--jira-url JIRA_URL   JIRA base URL (default: None)
--jira-user JIRA_USER
                      username to access JIRA (default: None)
--jira-password JIRA_PASSWORD
                      password to access JIRA (default: None)
--fields FIELDS       password to access JIRA (default: *all)
--query QUERY         JQL to search for (default: None)
```

## List issues

Use the issues cached by `cache-issues.py` to add subtasks to the query results.

### Optional arguments
```
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
--format {summary,branch,markdown}
                      display format (default: summary)
--query QUERY         JQL to search for (default: None)
```
