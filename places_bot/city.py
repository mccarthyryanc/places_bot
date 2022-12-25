#
# City Module
#
import asyncio
import os
from typing import Tuple, Optional
import tempfile
from pathlib import Path
import datetime

from shapely import Geometry, intersection, area
from shapely.geometry import mapping, shape
import pandas as pd
import geopandas as gpd
from PIL import Image

import rasterio
from rasterio import features
from planet import Session, DataClient, data_filter

data_folder = Path(os.path.dirname(__file__)).absolute().parent / "data"
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

    city_row = gpd.read_file(fn, rows=slice(city_id, city_id+1)).to_crs("EPSG:4326")

    city_name, city_geometry = city_row.iloc[0][["NAME", "geometry"]]
 
    # update viewed files
    viewed = pd.concat([viewed, city], ignore_index=True)
    not_viewed = not_viewed.drop(city.index)
    viewed.to_csv(viewed_cities_fn, index=False)
    not_viewed.to_csv(not_viewed_cities_fn, index=False)

    return (city_name, state, city_geometry)


async def select_least_cloudy(
    items: dict, city_geometry: Geometry, overlap_min: float
) -> Optional[dict]:
    """Select the least cloudy image with a minimum overlap with a geometry."""

    # filter for cloud cover and overlap
    least_cloudy = None
    city_area = area(city_geometry)
    for item in items:
        asset_geo = shape(item["geometry"])
        overlap_pct = area(intersection(asset_geo, city_geometry)) / city_area

        if least_cloudy is None or (item["properties"]["cloud_cover"] < least_cloudy["properties"]["cloud_cover"] and overlap_pct > overlap_min):
            least_cloudy = item

    return least_cloudy


async def get_planet_scene(geometry: Geometry) -> str:
    """
    Find the most recent, least cloudy, Planet Scope scene,
    burn-in the city name and boundary, and save to PNG.
    """

    raster_tif_fn = tempfile.mktemp(suffix=".tif", prefix="placesbot")

    async with Session() as sess:
        cl = DataClient(sess)

        latest_cloud_filter = data_filter.and_filter([
            data_filter.geometry_filter(mapping(geometry)),
            data_filter.asset_filter(["ortho_visual"]),
            data_filter.range_filter('cloud_cover', lt=10),
            data_filter.date_range_filter('acquired', gt=datetime.datetime.now() - datetime.timedelta(days=30))
        ])
    
        items = [i async for i in cl.search(["PSScene"], latest_cloud_filter)]
        
        least_cloudy = None
        overlapy_min = 0.95
        while least_cloudy is None:
            least_cloudy = await select_least_cloudy(items, geometry, overlapy_min)
            overlapy_min -= 0.05

        asset = await cl.get_asset("PSScene", least_cloudy["id"], "ortho_visual")

        # activate asset
        await cl.activate_asset(asset)

        # wait for asset to become active
        asset = await cl.wait_asset(asset, callback=print)

        # download asset
        path = await cl.download_asset(asset, filename=raster_tif_fn)

        # validate download file
        cl.validate_checksum(asset, path)

    return raster_tif_fn


def edit_image(city: str, state:str, city_geometry: Geometry, filename: str) -> str:
    """For a downloaded planet scene, clip the city, add text to the image and save as PNG."""
    pass




#    image_stream = client.download(least_cloudy_image["id"])
#    with open(raster_tif_fn, "wb") as f:
#        f.write(image_stream.read())

#    # Open the TIFF image
#    with Image.open(raster_tif_fn) as im:
#        # Convert the image to RGB mode
#        im = im.convert('RGB')

#        # Save the image as a PNG file
#        im.save(raster_png_fn, 'PNG')

#    os.remove(raster_tif_fn)

#    return raster_fn



