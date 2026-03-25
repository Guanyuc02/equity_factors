# Factor-Zoo-Replication

Replication and extension work around *Taming the Factor Zoo: A Test of New Factors*.

## What Is In This Repo

- [`replication-package/`](replication-package): original-style MATLAB replication package, including the reference `DS.m` implementation.
- [`model-replication/`](model-replication): Python port of the double-selection estimation pipeline.
- [`fzr/`](fzr): WRDS ETL and factor-construction toolkit used to rebuild factor inputs.
- [`data-replication/`](data-replication): data alignment and public-source factor preparation scripts.

## Local Setup

The most reliable local setup for this repo is Python 3.11 in a virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Then you can run:

```bash
python -m pytest fzr/tests -q
cd model-replication/main
python main.py
```

Note: the Python replication path uses `python-glmnet`, which installs cleanly on modern Python 3.11/macOS setups more reliably than the older `glmnet==2.2.1` package.

## Suggested Repo Story

If you share this publicly, describe the project as:

1. original MATLAB replication code in `replication-package/`
2. Python reimplementation in `model-replication/`
3. factor-building and ETL support code in `fzr/`

## Notes On Data Sharing

Some files in this repository may be derived from WRDS or other third-party sources. Before publishing publicly, confirm that you are allowed to redistribute those datasets or derived outputs.

