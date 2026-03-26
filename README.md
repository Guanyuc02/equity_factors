# Factor-Zoo-Replication

Replication and extension work around *Taming the Factor Zoo: A Test of New Factors*.

## What Is In This Repo

- [`replication-package/`](replication-package): original-style MATLAB replication package, including the reference `DS.m` implementation.
- [`model-replication/`](model-replication): Python port of the double-selection estimation pipeline.
- [`fzr/`](fzr): WRDS ETL and factor-construction toolkit used to rebuild factor inputs.
- [`data-replication/`](data-replication): data alignment and public-source factor preparation scripts.

## Local Setup


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


