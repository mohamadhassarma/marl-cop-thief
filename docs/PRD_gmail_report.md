# PRD — Gmail Automated Reporter

**Version:** 1.00
**Component:** `services/reporter.py`

---

## 1. Description

After all 6 sub-games complete, the Cop agent's server triggers an automated
email report to the course staff address. The email body must contain only
a valid JSON object — no subject line content beyond a fixed string,
no free text, no markdown. This enables automated parsing by the grader.

## 2. Input / Output

### Input
- Completed game results: sub-game outcomes, scores, agent info
- Group metadata: group name, student list, GitHub repo URL, MCP URLs
- Gmail OAuth token (pre-generated, stored in config/gmail_token.json)

### Output
- Email sent to: rmisegal+uoh26b@gmail.com
- Subject: fixed string (e.g. "EX06 Game Report — <group_name>")
- Body: JSON only (internal game report or inter-group bonus report)

## 3. JSON Report Schema

### Internal Game Report
```json
{
  "group_name": "string",
  "students": ["string"],
  "github_repo": "https://...",
  "cop_mcp_url": "https://...",
  "thief_mcp_url": "https://...",
  "timezone": "Asia/Jerusalem",
  "sub_games": [],
  "totals": {
    "cop": 0,
    "thief": 0
  }
}
```

### Inter-Group Bonus Report
```json
{
  "report_type": "bonus_game",
  "groups": {"group_1": "string", "group_2": "string"},
  "github_repo_group_1": "https://...",
  "github_repo_group_2": "https://...",
  "mcp_url_group_1_cop": "https://...",
  "mcp_url_group_1_thief": "https://...",
  "mcp_url_group_2_cop": "https://...",
  "mcp_url_group_2_thief": "https://...",
  "timezone": "Asia/Jerusalem",
  "students_group_1": [],
  "students_group_2": [],
  "sub_games": [],
  "totals_by_group": {},
  "bonus_claim": {},
  "mutual_agreement": true
}
```

## 4. Auth Mechanism

- Gmail API with OAuth 2.0 (google-auth + google-api-python-client)
- Token stored at path from env variable GMAIL_TOKEN_PATH
- Token is one-time-password style: revocable, time-limited
- Credentials JSON (from Google Cloud Console) stored at GMAIL_CREDENTIALS_PATH
- Neither file committed to git (.gitignore covers both)

## 5. Success Criteria

- [ ] Email sent automatically after game completes (no manual trigger)
- [ ] Body is valid JSON parseable by json.loads()
- [ ] No free text outside JSON in email body
- [ ] OAuth token auth works without password
- [ ] Sending fails gracefully with clear error log if token expired
- [ ] gmail_token.json and credentials.json excluded from git
