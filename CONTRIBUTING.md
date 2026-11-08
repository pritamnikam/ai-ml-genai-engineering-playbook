# Contributing

Keep concepts independently teachable: add one guide under
`guides/concepts/` and one matching notebook under `notebooks/`. Update
`guides/ROADMAP.md` and the topic catalog in
`scripts/generate_learning_assets.py` when adding a concept.

Prefer small synthetic examples, reproducible outputs, and explicit statements
about assumptions and limitations. Keep credentials and personal data out of
the repository. Run `python -m pytest` and validate notebooks as JSON before
opening a pull request.
