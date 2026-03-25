#!/usr/bin/env python3
import os

import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

import pandas as pd
import openassetpricing as oap

def main():
    openap = oap.OpenAP()

    df = openap.dl_port("op", "pandas")

    out_path = "openap_monthly_ports.csv"
    df.to_csv(out_path, index=False)
    print(f"saved {out_path} with {df.shape[1]} columns and {df.shape[0]} rows")

if __name__ == "__main__":
    main()