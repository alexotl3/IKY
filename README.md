# IKY Scholarships Blog → Discord

Checks https://www.iky.gr/ypotrofies/ once a day and posts any new
announcements to a Discord channel via webhook.

## Setup (5 minutes)

1. **Create a Discord webhook** (if you haven't already):
   Discord → your server → the target channel → Edit Channel →
   Integrations → Webhooks → New Webhook → copy the Webhook URL.

2. **Create a new GitHub repository** and upload these files
   (`check_blog.py`, `seen_posts.json`, `.github/workflows/check-blog.yml`,
   `README.md`), keeping the folder structure intact.
   - Easiest way: create an empty repo on github.com, then on your
     computer run `git init`, `git add .`, `git commit -m "init"`,
     add the remote, and `git push`. Or use GitHub's "Upload files"
     button in the web UI (it preserves folder paths if you drag the
     whole folder in).

3. **Add your webhook URL as a secret**:
   In the repo → Settings → Secrets and variables → Actions →
   New repository secret →
   - Name: `DISCORD_WEBHOOK_URL`
   - Value: (paste the Discord webhook URL)

4. **Run it once manually** to test:
   Repo → Actions tab → "Check IKY Scholarships Blog" → Run workflow.
   - The first run won't post anything to Discord — it just records
     all current announcements as "already seen" so you don't get
     flooded with the whole history. From the next run onward, only
     genuinely new posts get sent.

That's it — it will now run automatically every day at 07:00 UTC
(edit the `cron` line in the workflow file to change the time).

## Files

- `check_blog.py` — scrapes the page, diffs against `seen_posts.json`,
  posts new items to Discord.
- `seen_posts.json` — list of post URLs already seen (the workflow
  commits updates to this automatically).
- `.github/workflows/check-blog.yml` — the daily schedule (GitHub
  Actions, free for public repos and generous free tier on private ones).

## Notes

- No server or always-on computer needed — GitHub Actions runs this
  in the cloud on schedule.
- If IKY redesigns the page layout, the scraper's heuristics (looking
  for the "Ανακοινώσεις Υποτροφίες+" heading and the links under it)
  may need small tweaks in `check_blog.py`.
- You can trigger a check anytime via Actions → Run workflow, instead
  of waiting for the daily schedule.
