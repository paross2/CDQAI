<!-- CDQAI file version: 2.3.7 -->
# CDQAI 2.3.7 - Automated Main-Branch Releases

- Publishes a formal GitHub Release for each successful push to `main`.
- Verifies that every maintained public file carries the current release version
  and that every tracked path has an explicit public or excluded-file policy.
- Preserves historical documents, external workbooks, local SQL configuration,
  and generated runtime data without rewriting or publishing them.

The GitHub Actions workflow runs source-only release verification before creating
the release tag and publication. Feature-branch pushes do not publish releases.
