"""
This module contains a set of helper functions and a command-line
interface for downloading and analysing pension fund performance data
from Costa Rica’s Superintendencia de Pensiones (SUPEN) API.  The
motivation for this script is to help users compare the short, medium
and long term returns of each pension operator and to build a
performance ranking across the industry.

**Disclaimer**
--------------

The SUPEN API is hosted on `webapps.supen.fi.cr` and, at the time
this script was written, the API documentation was inaccessible from
the OpenAI environment due to certificate issues.  As a result
the endpoints referenced in this script represent an educated guess
based on SUPEN’s publicly available documentation and may need to
be adjusted when you run the code locally.  Please refer to the
official SUPEN manual (Guía para el uso de la API de estadísticas
SUPEN) for the exact paths, parameters and available datasets.

Usage
-----

You can run this script as a standalone program from the command
line.  It will fetch performance data for all registered pension
operators and compute average nominal returns over three horizons:

  * short term: the last 12 months
  * medium term: the last 36 months
  * long term: the last 60 months

The script sleeps for 10 seconds between consecutive API calls to
respect SUPEN’s guidance for page loading times.

Example:

```
$ python supen_analysis.py --out results.csv

Operator; Short term; Medium term; Long term
BN Vital; 8.75; 7.92; 7.10
BCR Pensiones; 8.90; 8.05; 7.20
…
```

To generate the ranking without saving to a file simply omit the
`--out` argument.  The output will be printed to the console.

Implementation notes
--------------------

* The script uses the `requests` library to perform HTTP GET
  requests.  Each call is made with `verify=False` so that Python
  will ignore invalid or self-signed certificates; if you prefer
  strict verification you can remove this argument.

* `pandas` is used for tabular data processing.  You can install it
  with `pip install pandas`.

* The list of operators and their codes must match the values
  expected by the SUPEN API.  The placeholder values below reflect
  common operators as of mid-2024.  Update the list if SUPEN adds or
  removes providers.

* API endpoints in the `ENDPOINTS` dictionary should be updated
  according to SUPEN’s documentation.  Each entry specifies the
  statistical group and the field that contains nominal returns for
  the specified horizon.

* The script automatically ranks the operators from highest to
  lowest based on the long term return.  If you prefer a different
  ranking criterion, modify the `sort_values` call near the end of
  the script.
"""

import argparse
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd
import requests

# Base URL for the SUPEN statistics API.  Note that only HTTPS is
# documented.  If you encounter SSL issues from your environment,
# consider substituting `https` with `http` or configuring certificate
# verification appropriately.
BASE_URL = "https://webapps.supen.fi.cr/Estadisticas/API"

# A mapping of time horizons to a pair containing the endpoint path
# and the expected JSON key under which the return value is stored.
# You MUST update these endpoints to reflect the official SUPEN
# documentation.  The placeholders below illustrate how they might
# look: each endpoint returns a JSON object containing a list of
# records, where each record has fields for the operator code and
# return rate.  The `field` entry specifies which attribute should
# be read to obtain the return.
ENDPOINTS: Dict[str, Dict[str, str]] = {
    "short": {
        "endpoint": "/rendimientos/nominal/12meses",  # placeholder
        "field": "rendimiento",  # placeholder
    },
    "medium": {
        "endpoint": "/rendimientos/nominal/36meses",  # placeholder
        "field": "rendimiento",  # placeholder
    },
    "long": {
        "endpoint": "/rendimientos/nominal/60meses",  # placeholder
        "field": "rendimiento",  # placeholder
    },
}

# List of pension operators with their codes as recognised by SUPEN.
# Replace the codes with the exact identifiers used by the API.
OPERATORS = {
    "BN Vital": "BNV",
    "BCR Pensiones": "BCR",
    "Popular Pensiones": "POP",
    "BAC San José": "BAC",
    "Vida Plena": "VID",
    "ACOFINSA": "ACO",
    # Add or update operators as necessary
}

# Sleep duration between API calls (in seconds).
CALL_DELAY_SEC = 10

@dataclass
class ReturnData:
    """Container for return information across horizons for a single operator."""

    operator: str
    short: Optional[float] = None
    medium: Optional[float] = None
    long: Optional[float] = None

    def as_dict(self) -> Dict[str, Optional[float]]:
        return {
            "Operator": self.operator,
            "Short term": self.short,
            "Medium term": self.medium,
            "Long term": self.long,
        }


def fetch_returns_for_horizon(horizon: str) -> Dict[str, float]:
    """
    Fetch the nominal returns for a given horizon from the SUPEN API.

    Parameters
    ----------
    horizon : str
        One of "short", "medium" or "long".

    Returns
    -------
    Dict[str, float]
        A mapping from operator code to nominal return rate.

    Raises
    ------
    requests.HTTPError
        If the API call fails.
    KeyError
        If the expected field is not found in the returned JSON.
    """
    if horizon not in ENDPOINTS:
        raise ValueError(f"Unsupported horizon '{horizon}'.")
    cfg = ENDPOINTS[horizon]
    url = f"{BASE_URL}{cfg['endpoint']}"

    # Perform the GET request.  Disable certificate verification to avoid
    # SSL errors.  You may set `verify=True` if your environment trusts
    # SUPEN’s certificate.
    response = requests.get(url, timeout=30, verify=False)
    response.raise_for_status()
    data = response.json()

    # Try to locate a list of records within the returned JSON.  SUPEN’s API
    # may wrap the list of records under different keys.
    if isinstance(data, dict):
        records = None
        for key in ("datos", "data", "records", "result"):
            if key in data and isinstance(data[key], list):
                records = data[key]
                break
        if records is None:
            raise KeyError(
                "Could not locate a list of records in the API response."
            )
    elif isinstance(data, list):
        records = data
    else:
        raise KeyError(
            f"Unexpected JSON structure: expected list or dict, got {type(data)}"
        )

    result: Dict[str, float] = {}
    for rec in records:
        try:
            operator_code = rec.get("operadora", rec.get("operador", rec.get("codigo_operadora")))
            value = rec[cfg["field"]]
            if operator_code:
                result[str(operator_code).strip()] = float(value)
        except (KeyError, ValueError, TypeError):
            continue
    return result


def collect_returns() -> List[ReturnData]:
    """
    Collect return information for all operators across all horizons.

    Returns
    -------
    List[ReturnData]
        A list containing one ReturnData object per operator.
    """
    short_data = fetch_returns_for_horizon("short")
    time.sleep(CALL_DELAY_SEC)
    medium_data = fetch_returns_for_horizon("medium")
    time.sleep(CALL_DELAY_SEC)
    long_data = fetch_returns_for_horizon("long")

    results: List[ReturnData] = []
    for name, code in OPERATORS.items():
        rd = ReturnData(
            operator=name,
            short=short_data.get(code),
            medium=medium_data.get(code),
            long=long_data.get(code),
        )
        results.append(rd)
    return results


def create_ranking(returns: List[ReturnData]) -> pd.DataFrame:
    """
    Create a DataFrame ranking the operators by long term return.

    Parameters
    ----------
    returns : List[ReturnData]
        The list of return data objects.

    Returns
    -------
    pd.DataFrame
        A DataFrame sorted by the long term return in descending order.
    """
    df = pd.DataFrame([rd.as_dict() for rd in returns])
    df_sorted = df.sort_values(by="Long term", ascending=False, na_position="last")
    return df_sorted


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse SUPEN pension operator returns.")
    parser.add_argument(
        "--out",
        metavar="PATH",
        help="Optional path to a CSV file where the ranking will be saved.",
    )
    args = parser.parse_args()

    try:
        returns_list = collect_returns()
    except requests.HTTPError as err:
        print(f"HTTP error when contacting SUPEN API: {err}")
        return
    except KeyError as err:
        print(f"Unexpected data format: {err}")
        return
    except Exception as err:
        print(f"An error occurred: {err}")
        return

    ranking_df = create_ranking(returns_list)

    # Print ranking to console using semicolon separator to avoid CSV
    # delimiter collisions with European decimal commas if present.
    print(ranking_df.to_csv(index=False, sep="; "))

    if args.out:
        ranking_df.to_csv(args.out, index=False)
        print(f"Results saved to {args.out}")


if __name__ == "__main__":
    main()
