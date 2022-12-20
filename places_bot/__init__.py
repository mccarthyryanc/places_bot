#
#
#
import asyncio
import os

import numpy as np
from shapely import Geometry
import pandas as pd
import geopandas as gpd

import rasterio
from rasterio import features
from planet import Session, DataClient, data_filter

from . import masto
from . import city

data_folder = Path(os.path.dirname(__file__)).absolute().parent() / "data"
viewed_cities_fn = data_folder / "viewed-places.csv"
not_viewed_cities_fn = data_folder / "not-viewed-places.csv"


def get_random_city() -> Tuple[str, str, Geometry]:
    """
    Pick a random city that isn't in the viewed
    cities list, and return it's boundary.
    """

    # get viewed/not-viewed cities
    viewed = pd.read_csv(viewed_cities_fn)
    not_viewed = pd.read_csv(not_viewed_cities_fn)

    # get random city
    city = not_viewed.sample(n=1)
    state = city.state.iloc[0]
    city_id = city.city_id.iloc[0]

    fn = list(data_folder.glob(f"{state}*.fgb"))[0]

    city_row = gpd.read_file(fn, rows=slice(city_id, city_id+1))

    city_name, city_geometry = city_row.iloc[0][["NAME", "geometry"]]
 
    # update viewed files
    viewed = pd.concat([viewed, city], ignore_index=True)
    not_viewed = not_viewed.drop(city.index)
    viewed.to_csv(viewed_cities_fn, ignore_index=True)
    not_viewed.to_csv(not_viewed_cities_fn, ignore_index=True)

    return (city_name, state, city_geometry)


def get_planet_scene(city: str, geometry: Geometry) -> str:
    """
    Find the most recent, least cloudy, Planet Scope scene,
    burn-in the city name and boundary, and save to PNG.
    """



