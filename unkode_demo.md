# unkode demo — cheat sheet

Copy-paste, top to bottom. PowerShell, from the repo root unless noted.

```powershell
cd D:\Workspaces\Python\unkode-test\book-store
```

---

## 1. Run the shop

```powershell
.\.venv\Scripts\activate
python -m tools.cli seed
uvicorn main:app --reload
```

<http://localhost:8000> · admin at `/admin` · every account's password is `demo`

Reset the data any time (`bookstore.db` is gitignored):

```powershell
rm bookstore.db
python -m tools.cli seed
```

---

## 2. Copy unkode in

```powershell
$src = "D:\Workspaces\Python\unkode\skills\unkode"
Copy-Item -Force "$src\*.py" .\.agents\skills\unkode\
Copy-Item -Force "$src\SKILL.md" .\.agents\skills\unkode\

$cfg = "D:\Workspaces\Python\unkode\config\github"
Copy-Item -Force "$cfg\action.yml" .\.github\actions\unkode\action.yml
Copy-Item -Force "$cfg\unkode_arch_check.yml" .\.github\workflows\unkode_arch_check.yml
```

**Restart Claude Code** after changing the skill.

---

## 3. Build the map

```
/unkode init --force
```

`--force` because a map already exists. Then check it:

```powershell
python .agents\skills\unkode\validate.py
```

Want `34 components, 32 with dependencies` and no split warnings.

```powershell
git add .unkode ; git commit -m "Rebuild the architecture map" ; git push origin main
```

---

## 4. Look at it

Hosted — switch between the **Modules** and **Components** tabs:

<https://unkode.dev/dashboard/?repo=deepcodersinc/book-store>

Offline fallback:

```powershell
start .unkode\arch_map.html
```

`arch_map.md` is the same thing as Mermaid, renders inline on GitHub.

---

## 5. Branch

```powershell
git checkout main
git checkout -b demo/shipping-sms main
```

---

## 6. The change

Give the coding agent this, verbatim:

> When an order ships, text the customer their tracking number as well as
> emailing it. Let people add a mobile number to their account and show it on
> the account page. Follow the same pattern as the existing payment and email
> integrations — it should work without credentials, and the message should
> appear in the staff outbox.

Check it works: set a mobile number on an account, confirm payment on an order,
run fulfilment, then look at `/admin/outbox` — one email row, one `sms` row.

---

## 7. Let unkode find it

```
/unkode sync
```

```powershell
python .agents\skills\unkode\yaml_diff.py --base-branch main
```

Expect:

```
**Added:**
  + Twilio (external)

**Modified:**
  ~ Third-Party Integrations
    + depends on Twilio
```

---

## 8. Commit and open the PR

```powershell
git add -A
git commit -m "Text customers their tracking number when an order ships"
git push -u origin demo/shipping-sms
```

Open the pull request against `main`. The Action posts the summary, a
colour-coded Mermaid diff, and a dashboard link.

---

## The negative control

Worth showing — unkode stays silent when nothing moves.

```powershell
git checkout main
git checkout -b demo/sort-catalogue main
```

> Add a sort control to the home page so shoppers can reorder the books. Offer
> title A–Z, author A–Z, price low to high, and price high to low. Show which
> option is active, and keep the choice applied when the page reloads.

Decline "Most popular" if offered — that needs order data and would drift.

Leave `.unkode/` untouched, commit, push, open the PR. **No comment appears** —
say so out loud, or the room reads it as a failure. The Actions tab shows the
run went green and chose silence.

---

## Reset between demos

```powershell
cd D:\Workspaces\Python\unkode-test
python reset-book-store.py --yes                  # -> baseline-v2
python reset-book-store.py --to baseline-v1 --yes # -> no unkode at all
python reset-book-store.py --remote --yes         # also close the open PRs
```

Leave demo branches **open** as PRs if you want them replayable.

---

## If asked

- **"Does it work on my repo?"** — `/unkode init` on a repo they name. 2–5 min.
- **"How does the map stay current?"** — `sync` on a branch today; running it in
  CI is next.
- **Fork PRs get no comment** — GitHub gives fork runs a read-only token.
