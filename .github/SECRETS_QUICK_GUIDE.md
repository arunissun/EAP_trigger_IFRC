# Quick Reference: Adding GitHub Secrets

## Visual Guide

```
GitHub Repository Page
    ↓
Settings (tab at top)
    ↓
Left Sidebar → Secrets and variables (click to expand)
    ↓
Actions (under Secrets and variables)
    ↓
New repository secret (green button)
    ↓
Fill the form:
    Name: CDSAPI_URL
    Secret: https://cds.climate.copernicus.eu/api/v2
    ↓
Click "Add secret"
    ↓
Repeat for second secret:
    Name: CDSAPI_KEY
    Secret: [Your API key from Copernicus]
    ↓
Done! ✓
```

## Where to Find Your Copernicus API Key

### URL to Visit

<https://cds.climate.copernicus.eu>

### Navigation Path

```
Home Page
    ↓
Login (top right corner)
    ↓
After login → Click your username (top right)
    ↓
Select "Your profile"
    ↓
Scroll down to "API key" section
    ↓
Copy the entire key (format: UID:API-KEY-STRING)
```

### What Your API Key Looks Like

```
Example format:
12345:abcdef12-3456-7890-abcd-ef1234567890
  ↑               ↑
 UID         API Key String
```

**Important:** Copy the ENTIRE string including the colon `:` in the middle!

## Full Path in GitHub UI

```
Repository Home
└── Settings (top tab bar)
    └── Secrets and variables (left sidebar)
        └── Actions
            └── New repository secret (button)
                └── Form appears with:
                    • Name: [Enter secret name]
                    • Secret: [Enter secret value]
                    • [Add secret] button
```

## After Adding Secrets

You should see this list in **Settings → Secrets and variables → Actions**:

```
Repository secrets
• CDSAPI_KEY     [Updated: timestamp]  [Update] [Remove]
• CDSAPI_URL     [Updated: timestamp]  [Update] [Remove]
```

The actual secret values are HIDDEN by GitHub for security.

---

## Common Mistakes to Avoid

❌ **Wrong:** Using lowercase `cdsapi_url` or `cdsapi_key`
✅ **Correct:** Use exactly `CDSAPI_URL` and `CDSAPI_KEY` (all caps)

❌ **Wrong:** Only copying part of the API key
✅ **Correct:** Copy the entire key including the UID and colon

❌ **Wrong:** Adding spaces before/after the secret value
✅ **Correct:** Paste the value exactly as-is

❌ **Wrong:** Trying to add secrets in workflow file
✅ **Correct:** Add secrets in GitHub Settings UI only
