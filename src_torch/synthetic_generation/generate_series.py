"""
Module to generate synthetic series
"""

import numpy as np
import pandas as pd
from datetime import date
from pandas.tseries.frequencies import to_offset
from synthetic_generation.constants import *
from synthetic_generation.generate_series_components import make_series
from synthetic_generation.utils import sample_scale, get_transition_coefficients
from synthetic_generation.series_config import ComponentScale, SeriesConfig, ComponentNoise
from scipy.stats import beta

def __generate(
    n = 100,
    freq: str = None,
    start: pd.Timestamp = None,
    options: dict = {},
    random_walk: bool = False,
):
    """
    Function to construct synthetic series configs and generate
    synthetic series
    """
    if freq is None:
        freq = np.random.choice(freq_dict.keys())

    freq, timescale = freq_dict[freq]['freq'], freq_dict[freq]['time_scale']

    # annual, monthly, weekly, hourly and minutely components
    a, m, w, h, minute = 0.0, 0.0, 0.0, 0.0, 0.0
    if freq == "min":
        minute = np.random.uniform(0.0, 1.0)
        h = np.random.uniform(0.0, 0.2)
    elif freq == "H":
        minute = np.random.uniform(0.0, 0.1) #0.2)
        h = np.random.uniform(0.0, 1.0)
        w = np.random.uniform(0.0, 0.4) ## new
    elif freq == "D":
        w = np.random.uniform(0.0, 1.0)
        m = np.random.uniform(0.0, 0.4) #0.2)
        a = np.random.uniform(0.0, 0.2) ##new
    elif freq == "W":
        m = np.random.uniform(0.0, 0.3)
        a = np.random.uniform(0.0, 0.8)
    elif freq == "MS":
        w = np.random.uniform(0.0, 0.1)
        a = np.random.uniform(0.0, 1.0)
    elif freq == "Y":
        w = np.random.uniform(0.0, 0.2)
        a = np.random.uniform(0.0, 1)
    else:
        raise NotImplementedError

    if start is None:
        # start = pd.Timestamp(date.fromordinal(np.random.randint(BASE_START, BASE_END)))
        start = pd.Timestamp(date.fromordinal(int((BASE_START - BASE_END)*beta.rvs(5,1)+BASE_START)))

    scale_config = ComponentScale(
        base=1.0,
        linear=np.random.normal(0, 0.01),
        exp=min(1.01,np.random.normal(1, 0.005 / timescale)) if options["trend_exp"] else 1.0,
        a=a,
        m=m,
        w=w,
        minute=minute,
        h=h
    )

    offset_config = ComponentScale(
        base=0,
        linear=np.random.uniform(-0.1, 0.5),
        exp=np.random.uniform(-0.1, 0.5),
        a=np.random.uniform(0.0, 1.0),
        m=np.random.uniform(0.0, 1.0),
        w=np.random.uniform(0.0, 1.0),
    )

    noise_config = ComponentNoise(
        k=np.random.uniform(1, 5),
        median=1,
        scale=sample_scale(low_ratio=options["scale_noise"][0], moderate_ratio=options["scale_noise"][1])
    )

    cfg = SeriesConfig(scale_config, offset_config, noise_config)

    return cfg, make_series(cfg, to_offset(freq), n, start, options, random_walk)

def generate(
    n = 100,
    freq: str = None,
    start: pd.Timestamp = None,
    options: dict = {},
    transition: bool = True,
    random_walk: bool = False,
):
    """
    Function to generate a synthetic series for a given config
    """

    cfg1, series1 = __generate(n, freq, start, options, random_walk)
    cfg2, series2 = __generate(n, freq, start, options, random_walk)

    if transition:
        coeff = get_transition_coefficients(n)
        values = coeff * series1['values'] + (1 - coeff) * series2['values']
    else:
        values = series1['values']

    dataframe_data = {
        'series_values': values,
        'noise': series1['noise']
    }

    return cfg1, pd.DataFrame(data=dataframe_data, index=series1['dates'])#.clip(lower=0.0)

