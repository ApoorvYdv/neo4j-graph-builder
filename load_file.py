import json
from tqdm import tqdm
import pandas as pd


def get_df():
    file = "./arxiv-metadata.json"

    metadata = []

    with open(file, "r") as f:
        for line in tqdm(f):
            metadata.append(json.loads(line))

    df = pd.DataFrame(metadata)
    return df