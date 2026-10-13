# unkode demo — runbook

Everything needed to run this shop and demonstrate unkode on it, in order.
LocalBooks is a deliberately ordinary bookshop: it has layers worth protecting,
exceptions worth noticing, and nothing that hints it exists for a demo.

- **Repo:** `D:\Workspaces\Python\unkode-test\book-store`
- **Reset helper:** `..\reset-book-store.py` (deliberately outside the repo)
- **Answer key:** `..\book-store-answer-key.md` — what the architecture actually is

---

## 0. Which state to start from

Two tags, and they exist for different demos.

| Tag | Contains | Use it to demo |
|-----|----------|----------------|
| `baseline-v1` | the shop, **no unkode at all** | `init` — a map appearing where there was none |
| `baseline-v2` | unkode installed: map, workflow, skill committed | drift — branch, change, PR comment |

`main` sits ahead of both with the current work. Pick a tag deliberately rather
than demoing from wherever `main` happens to be.

```powershell
cd D:\Workspaces\Python\unkode-test

python reset-book-store.py                    # -> baseline-v2 (the default)
python reset-book-store.py --to baseline-v1   # -> pristine, for the init demo
python reset-book-store.py --dry-run          # show the plan, change nothing
```

The reset deletes every branch except `main`, clears untracked files, drops
`.unkode/` when the chosen tag has none, and reseeds the database. It never
touches `.venv`.

---

## 1. Run the shop

```powershell
cd D:\Workspaces\Python\unkode-test\book-store
.\.venv\Scripts\activate
python -m tools.cli seed
uvicorn main:app --reload
```

Two dots at the start of the activate path — the folder is `.venv`, not `venv`.

- Storefront <http://localhost:8000>
- Staff console <http://localhost:8000/admin>
- Every demo account uses the password `demo`; the sign-in page lists them

First time on a fresh machine:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

If `pip` fails on a certificate behind a corporate proxy:

```powershell
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Resetting demo data between runs

`bookstore.db` is gitignored, so this costs nothing and touches no history:

```powershell
rm bookstore.db
python -m tools.cli seed
```

### Driving a full order by hand

1. Add something to the basket and check out — the order sits **pending**
2. Open it under `/admin/orders/...` and press **Confirm payment** (replays the
   webhook the payment provider would post)
3. Press **Run fulfilment now** — physical copies ship, ebooks get a download link
4. Everything the shop "sent" is at `/admin/outbox`, email and SMS alike

---

## 2. Where the unkode files go

Four separate things, and they land in different places.

### a. The skill — so the agent can run it

The real skill lives in `.agents/skills/unkode/` (also readable by Codex,
Cursor and other agents). Claude Code only looks in `.claude/skills/`, so an
eight-line pointer bridges the two.

To refresh the skill in this project from the unkode repo:

```powershell
$src = "D:\Workspaces\Python\unkode\skills\unkode"
Copy-Item -Force "$src\*.py" .\.agents\skills\unkode\
Copy-Item -Force "$src\SKILL.md" .\.agents\skills\unkode\
```

`.claude/skills/unkode/SKILL.md` is a stub that says "the instructions live at
`.agents/skills/unkode/SKILL.md`, and `<skill-dir>` means that folder." It never
needs updating unless the folder moves. **Restart Claude Code** after adding it.

### b. The GitHub Action — so pull requests get a comment

```powershell
$cfg = "D:\Workspaces\Python\unkode\config\github"
mkdir .github\actions\unkode -Force
mkdir .github\workflows -Force
Copy-Item "$cfg\action.yml" .\.github\actions\unkode\action.yml
Copy-Item "$cfg\unkode_arch_check.yml" .\.github\workflows\unkode_arch_check.yml
```

Both paths are forced — GitHub only reads workflows from `.github/workflows/`,
and the workflow's `uses: ./.github/actions/unkode` fixes the other.

The Action finds `yaml_diff.py` by looking in `.agents/skills/unkode/` and
`.claude/skills/unkode/` **inside this repo**, which is why the skill is
committed here. Update the skill (step a) and the Action picks it up.

### c. Config — per repo

`.agents/skills/unkode/config.yaml`: `base_branch`, `exclude_paths`,
`diagram_direction`. Defaults are fine for this demo.

### d. The map — generated, committed

`.unkode/arch.yaml` plus `arch_map.md` and `arch_map.html`. Never hand-write the
whole file; that is what `init --force` is for.

---

## 3. Demo A — the map appearing from nothing

Start pristine:

```powershell
cd D:\Workspaces\Python\unkode-test
python reset-book-store.py --to baseline-v1 --yes
```

Then in Claude Code, from the repo root:

```
/unkode init
```

It states a time estimate, reads the codebase, writes `.unkode/arch.yaml`,
validates it against the actual file tree, and renders both diagrams. Two to
five minutes.

What to show afterwards:

```powershell
python .agents\skills\unkode\validate.py
```

Expect something like *10 modules, 5 externals | 25 components, 25 with
dependencies*. That last number is the point — the map knows how work moves
through the system, not just what the folders are.

Then open `.unkode\arch_map.html` and switch between the **Modules** and
**Components** tabs. Modules is the view for someone who does not read code;
Components is the one that shows a request's path.

`arch_map.md` holds the same thing as Mermaid, which renders inline on GitHub —
useful when the repo is private.

Commit it as its own commit, so `git show` of that one SHA is a clean artifact:

```powershell
cd book-store
git add .unkode
git commit -m "Add the architecture baseline"
```

> Resetting `main` to `baseline-v1` leaves it behind `origin/main`, so do not
> push during this demo. Reset to `baseline-v2` afterwards.

---

## 4. Demo B — a change that moves nothing

The negative control. A tool that speaks on every pull request gets muted, so
showing the silence matters.

```powershell
cd D:\Workspaces\Python\unkode-test
python reset-book-store.py --yes
cd book-store
git checkout -b demo/sort-catalogue main
```

Hand the coding agent a product request, not an implementation:

> Add a sort control to the home page so shoppers can reorder the books. Offer
> title A–Z, author A–Z, price low to high, and price high to low. Show which
> option is active, and keep the choice applied when the page reloads.

Decline "Most popular" if it offers — that needs order data and would drift.

Click through the sorts, then:

```powershell
python .agents\skills\unkode\yaml_diff.py --base-branch main
```

Expect **"No architectural changes detected."** Leave `.unkode/arch.yaml`
untouched — nothing about the architecture moved, and that is the honest state.

```powershell
git add -A
git commit -m "Add sort options to the catalogue"
git push -u origin demo/sort-catalogue
```

Open the pull request against `main`. **No comment appears** — `action.yml`
checks for "No architectural changes detected" and deliberately stays quiet.
Open the **Actions** tab to show the run went green and chose silence.

Say that out loud, or the room reads it as a failure.

---

## 5. Demo C — a change that does move the architecture

```powershell
cd D:\Workspaces\Python\unkode-test\book-store
git checkout main
git checkout -b demo/shipping-sms main
```

The request, again at product level:

> When an order ships, text the customer their tracking number as well as
> emailing it. Let people add a mobile number to their account and show it on
> the account page. Follow the same pattern as the existing payment and email
> integrations — it should work without credentials, and the message should
> appear in the staff outbox.

This one cannot be implemented around. An SMS needs a provider, so a new
external appears whatever the developer does.

Check it works — set a mobile number on an account, ship an order, and look at
`/admin/outbox`: one email row and one `sms` row.

Then let unkode find it:

```
/unkode sync
```

Sync reads only what changed and patches the map. On this change it adds
`Twilio` as an external and one dependency, and leaves the other fourteen
entries byte-identical — which is why the diff shows the change rather than a
wall of reworded output.

```powershell
python .agents\skills\unkode\yaml_diff.py --base-branch main
```

```
**Added:**
  + Twilio (external)

**Modified:**
  ~ Third-Party Integrations
    + depends on Twilio

**Total:** 1 added, 0 removed, 1 modified
```

Ship it:

```powershell
git add -A
git commit -m "Text customers their tracking number when an order ships"
git push -u origin demo/shipping-sms
```

Open the pull request against `main`. The comment carries the summary, a
colour-coded Mermaid diagram behind a fold (green for added, amber for
modified, dashed arrows for new dependencies), and a link to the live dashboard.

The line to land: *a small request to text customers added a third-party vendor
to the system.* Nobody reading the code diff would have said that.

---

## 6. The one worth saving for last

A boundary violation. Same shape as Demo C, but the finding is a mistake rather
than an addition.

```powershell
git checkout main
git checkout -b demo/bestsellers main
```

> On the home page, add a "Bestsellers" strip above the catalogue — the five
> books that have sold the most copies, each with a badge showing the number
> sold. Keep it simple, we just want it on the page for now.

Nothing owns that query: it spans orders and books, and the catalogue service
has no route to order data. So the shortest path is for the web layer to reach
into the order repository directly.

Afterwards check which way it went:

```powershell
Select-String -Path apps\*\*.py -Pattern "^from data|^import data"
```

- **A match** — it took the shortcut. `/unkode sync`, and the diff shows
  `Customer Storefront` now depends on `Data Access Layer`. The web layer talks
  to the database. That is the demo.
- **No match** — it wired the feature through a service and the map will not
  move. Say *"do it without adding anything to the services layer"* and it will
  go straight to the data.

---

## 7. Resetting between demos

| Situation | Command |
|-----------|---------|
| Orders and edits piled up | `rm bookstore.db` then `python -m tools.cli seed` |
| Back to the drift baseline | `python reset-book-store.py --yes` |
| Back to pristine, no unkode | `python reset-book-store.py --to baseline-v1 --yes` |
| Also close the open pull requests | add `--remote` |

Leave the demo branches **open** as pull requests if you want them replayable —
each is one URL telling one story. Merging consumes them. `--remote` deletes the
remote branches and closes their pull requests, so reach for it only when you
want a clean slate.

---

## Known rough edges

Worth knowing before someone asks.

- **`sync` is manual.** Nothing updates the map automatically, so a developer
  who forgets leaves it stale and the Action compares two identical files and
  says nothing. Running `sync` in CI is the fix and it is not built yet.
- **The component view is dense.** Thirty-six nodes and sixty-six edges. The
  module tab is the default for that reason.
- **Cross-fork pull requests get no comment.** GitHub hands a read-only token to
  `pull_request` runs from a fork, so the Action cannot post. Demo from branches
  in this repo, not forks.
- **Table-level coupling is invisible.** `data/books.py` can query the order
  tables without importing the order repository, and no import means no edge.
- **Layout is not saved.** Every render re-runs the layout engine, so any
  arrangement you make by hand is lost on the next render.
