#!/usr/bin/env python
#
#
from pathlib import Path

import numpy as np
import pandas as pd

viewed_fn = Path("data/viewed-places.csv")
not_viewed_fn = Path("data/not-viewed-places.csv")

dfs = []

for fn in Path("data/").glob("*.fgb"):
    state_name, fips, num_cities = fn.name.replace(".fgb", "").split("_")
    num_cities = int(num_cities)

    dfs.append(
        pd.DataFrame(
            {
                "city_id": list(range(0, num_cities)),
                "state": [state_name] * num_cities
            }
        )
    )

df = pd.concat(dfs, ignore_index=True)
df.to_csv(not_viewed_fn, index=False)

empty_df = pd.DataFrame({"city_id":[], "state":[]})
empty_df.to_csv(viewed_fn, index=False)

