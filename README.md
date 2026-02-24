# ci-workflows

Reusable GitHub Actions workflows for [bloomreach-forge](https://github.com/bloomreach-forge) projects.

## Workflows

| Workflow | Description |
|---|---|
| `brxm-ci.yml` | Build and test a brXM Forge project (root + optional demo module) |
| `release.yml` | Set version, build, deploy to Forge Maven repository, tag, create GitHub Release, bump to next SNAPSHOT |
| `build-gh-pages.yml` | Build Maven site and publish to `gh-pages` branch |
| `configure-gh-pages.yml` | Configure repository Pages settings to serve from `gh-pages` branch |
| `forge-descriptor.yml` | Generate and commit `forge-addon.yaml` from `.forge/addon-config.yaml` |

Ready-to-use caller templates are in [`examples/`](examples/).

---

## Consumer setup

### 1. Repository secrets

All workflows require these two secrets set on the consuming repository
(Settings → Secrets and variables → Actions):

| Secret | Description |
|---|---|
| `BR_MAVEN_USERNAME` | Bloomreach Maven repository username |
| `BR_MAVEN_PASSWORD` | Bloomreach Maven repository password |

### 2. Actions token permissions

GitHub Actions automatically provides a `GITHUB_TOKEN` for every workflow run —
**you do not need to create or store a GitHub token as a secret.** It is generated
by GitHub per-run and scoped to the caller repository.

These workflows write back to the repository:

| Workflow | Permission | Write operation |
|---|---|---|
| `brxm-ci.yml` | `contents: write` | Removes committed `docs/` from source branch if present (one-time cleanup) |
| `release.yml` | `contents: write` | Commits version bumps, pushes tag, creates GitHub Release |
| `build-gh-pages.yml` | `contents: write` | Pushes built site to `gh-pages` branch |
| `configure-gh-pages.yml` | `pages: write` | Configures repository Pages source via GitHub API |
| `forge-descriptor.yml` | `contents: write` | Commits generated `forge-addon.yaml` |

Because these are cross-repository reusable workflows, the `permissions` declared
inside them are not sufficient on their own — the **caller job** must also grant
`contents: write`. The provided example callers already include this:

```yaml
jobs:
  release:
    permissions:
      contents: write
    uses: bloomreach-forge/ci-workflows/.github/workflows/release.yml@main
```

With explicit `permissions` on the caller job, the repository-wide Actions token
setting can remain at the default **Read repository contents and packages
permissions** (the more restrictive default). No token creation is required.

### 3. Caller workflows

Copy the applicable files from [`examples/`](examples/) into `.github/workflows/`
in the consuming repository. No modification is needed for projects that follow
the standard layout. Use inputs to override defaults for non-standard layouts.

#### `ci.yml` — inputs

All inputs are optional.

| Input | Default | Description |
|---|---|---|
| `run-demo-build` | `true` | Set to `false` for projects without a demo module |
| `demo-pom-path` | `demo/pom.xml` | Path to the demo module `pom.xml` |

Example — project without a demo module:
```yaml
jobs:
  build:
    if: >-
      github.event_name == 'push' ||
      github.event.pull_request.head.repo.full_name == github.repository
    permissions:
      contents: write
    uses: bloomreach-forge/ci-workflows/.github/workflows/brxm-ci.yml@main
    with:
      run-demo-build: false
    secrets:
      BR_MAVEN_USERNAME: ${{ secrets.BR_MAVEN_USERNAME }}
      BR_MAVEN_PASSWORD: ${{ secrets.BR_MAVEN_PASSWORD }}
```

#### `release.yml` — inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `version` | yes | — | Release version, e.g. `1.2.3` |
| `next-development-version` | yes | — | Next SNAPSHOT, e.g. `1.2.4-SNAPSHOT` |
| `branch` | no | `master` | Branch to release from and push back to |
| `dry-run` | no | `false` | Skip Nexus deploy and GitHub Release (for testing) |
| `run-demo-build` | no | `true` | Set to `false` for projects without a demo module |
| `demo-pom-path` | no | `demo/pom.xml` | Path to the demo module `pom.xml` |
| `forge-readme-path` | no | `README.md` | README path for `forge-addon.yaml` generation |

#### `build-gh-pages.yml` — inputs

| Input | Default | Description |
|---|---|---|
| `ref` | *(required)* | Commit SHA or ref to build docs from — passed by the caller |
| `java-version` | `17` | Java version |
| `docs-dir` | `docs` | Directory where `mvn site` writes output — must match `<outputDirectory>` in `pom.xml` |
| `site-profile` | `github.pages` | Maven profile used to build the site |

The consuming `pom.xml` must have a profile that sets `maven-site-plugin`'s
`<outputDirectory>` to match `docs-dir`:
```xml
<profile>
  <id>github.pages</id>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-site-plugin</artifactId>
        <configuration>
          <outputDirectory>docs</outputDirectory>
        </configuration>
      </plugin>
    </plugins>
  </build>
</profile>
```

#### `forge-descriptor.yml` — inputs

| Input | Default | Description |
|---|---|---|
| `config-path` | `.forge/addon-config.yaml` | Path to the addon config |
| `output-path` | `forge-addon.yaml` | Path where the generated descriptor is written |
| `readme-path` | `README.MD` | Path to the project README |

The consuming repository must have a `.forge/addon-config.yaml`. Use brut's
[`.forge/addon-config.yaml`](https://github.com/bloomreach-forge/brut/blob/master/.forge/addon-config.yaml)
as a reference.

Override `readme-path` if the project uses lowercase:
```yaml
jobs:
  generate:
    uses: bloomreach-forge/ci-workflows/.github/workflows/forge-descriptor.yml@main
    with:
      readme-path: README.md
```

### 4. GitHub Pages

For `build-gh-pages.yml` to publish successfully, GitHub Pages must be
configured to serve from the `gh-pages` branch:

> Settings → Pages → Source → **Deploy from a branch** → Branch: `gh-pages` / `/ (root)`

---

## Version pinning

The examples use `@main`. For production stability, pin to a specific tag or SHA:
```yaml
uses: bloomreach-forge/ci-workflows/.github/workflows/brxm-ci.yml@v1.0.0
```

---

## Testing the release workflow

### Dry-run smoke test (GitHub-hosted)

`examples/test-release.yml` exercises the full release flow without touching Nexus or creating a
GitHub Release. Copy it into `.github/workflows/` of the consuming repo, then:

1. Go to **Actions → Test Release (Dry Run) → Run workflow**
2. Accept the defaults (`0.0.0-test` / `0.0.1-SNAPSHOT`) or enter custom values
3. The workflow will:
   - Create a disposable branch `test/release-dry-run-{run_id}`
   - Run the full release sequence (version bump, build, commit, tag) against that branch
   - Skip Nexus deploy and GitHub Release creation
   - Delete the test branch and tag in a final cleanup job that always runs

This validates git operations, Maven version bumping, and the overall step sequence without any
external side-effects.

### Local execution with `act`

[`act`](https://github.com/nektos/act) runs GitHub Actions locally via Docker. It is well-suited
for testing standalone `workflow_dispatch` workflows. Note that reusable `workflow_call` workflows
have limited support in `act`; test the calling workflow (e.g. `test-release.yml`), not the
reusable workflow directly.

**Install**
```bash
# macOS
brew install act

# Linux
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

**Configure**

Create `.secrets` in the repo root (never commit this file):
```
BR_MAVEN_USERNAME=your-username
BR_MAVEN_PASSWORD=your-password
```

Create `.actrc` to set the runner image:
```
-P ubuntu-latest=catthehacker/ubuntu:act-latest
```

**Run**
```bash
# Dry-run smoke test (resolves reusable workflow from local path)
act workflow_dispatch \
  -W .github/workflows/test-release.yml \
  --secret-file .secrets \
  --input version=0.0.0-test \
  --input next-development-version=0.0.1-SNAPSHOT
```

`act` skips steps that require GitHub APIs (e.g. `gh release create`) by default when
`GITHUB_TOKEN` is not set. Pass `--env GITHUB_TOKEN=$(gh auth token)` to enable them.
