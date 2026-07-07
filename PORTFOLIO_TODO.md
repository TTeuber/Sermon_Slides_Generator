# Portfolio Polish — Remaining Items

Things that still need a human (or a future session) to finish. Roughly in priority order.

## High impact

- [ ] **Add a GUI screenshot to the README.** Launch the app (`uv run python main.py`), take a screenshot of the main window (ideally with a few passages filled in), save it as `docs/gui_screenshot.png`, and add it near the top of the README above the example slide. A short screen-recording GIF of "type references → generate → PDF opens" would be even better.
- [ ] **Publish a GitHub Release.** Run `uv run python build.py`, zip `dist/Sermon Slides Generator.app`, and attach it to a `v1.0.0` release on GitHub. Then add a "Download the latest release" link/badge to the README. Few portfolio projects ship a runnable binary — this is a differentiator.
- [ ] **Add the CI badge to the README** once the CI workflow has run on GitHub:
  `![CI](https://github.com/TTeuber/Sermon_Slides_Generator/actions/workflows/ci.yml/badge.svg)`
- [ ] **Verify CI passes on GitHub.** The workflow at `.github/workflows/ci.yml` runs ruff + pytest on Ubuntu. `uv sync` there will also install pywebview; if that fails on Linux headless, change the install step to `uv sync --no-install-project` or split GUI deps into an extra.

## Medium

- [x] **Make the QR code configurable.** The GUI now has a checkbox to skip the title-slide QR and a file-picker to choose a custom QR/logo image (with a reset-to-default button). Transparent PNGs are composited correctly.
- [x] **Rename the local project directory** from `csbText` to match the GitHub repo (`Sermon_Slides_Generator`).
- [x] **Update the bundle identifier** in `sermon_slides.spec` (`com.csbtext.sermonslides` → `com.tylerteuber.sermonslides`).
- [x] **More tests with mocked HTML.** `tests/test_passage_fetching.py` feeds saved BibleGateway HTML fixtures (`tests/fixtures/`) to `fetch_passage_text` and `_remove_footnotes` with `requests.get` mocked — no network calls.

## Nice to have

- [ ] **Code signing / notarization** for the macOS app so it opens without the Gatekeeper warning (requires an Apple Developer ID).
- [ ] **Windows/Linux builds.** The spec file already excludes platform GUI frameworks; test `build.py` on Windows and document it in BUILD.md.
- [ ] **Passage validation UX.** The GUI's `validate_passage` does a full network fetch per passage; consider debouncing or validating format locally first.
- [ ] **Error surfacing.** Most exceptions are logged and swallowed (fine for a GUI, but a "details" expander in the error toast would help debugging).
- [ ] **Portfolio site blurb.** One paragraph: the problem (weekly manual slide prep), the solution, and one interesting technical detail (e.g. sentence-boundary text chunking to fit slides, or shipping a native app with PyWebView + PyInstaller).
