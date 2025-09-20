import logging
import os
import pandas as pd
from rapidfuzz import process, fuzz


class FuzzySearcher:
    possible_paths = [
        "scripts/index.csv",
        "../scripts/index.csv",
        "/app/scripts/index.csv",
    ]

    def __init__(self):
        for path in self.possible_paths:
            if os.path.exists(path):
                self.df = pd.read_csv(path, encoding="utf-8").fillna("")
                logging.info(f"Loaded CSV from: {path}")
                break
        else:
            raise FileNotFoundError(
                f"CSV not found in any of the paths: {self.possible_paths}"
            )

        self.df["search_text"] = (
            self.df["title"].astype(str).str.lower()
            + " "
            + self.df["author"].astype(str).str.lower()
        ).str.strip()
        self.df = self.df[self.df["search_text"] != ""].copy()

    def search(
        self,
        query: str,
        limit: int = 50,
        score_cutoff: int = 50,
        scorer=fuzz.token_set_ratio,
    ):
        if not query:
            return []

        matches = process.extract(
            query.lower(),
            self.df["search_text"].tolist(),
            scorer=scorer,
            score_cutoff=score_cutoff,
            limit=limit * 5,
        )

        if not matches:
            return []

        indices = [i for _, score, i in matches]
        scores = [score for _, score, _ in matches]

        df_results = self.df.iloc[indices].copy()
        df_results["score"] = scores

        df_results = df_results.sort_values(
            by=["score", "author", "title"],
            ascending=[False, True, True],
        )

        return df_results.head(limit).to_dict(orient="records")

    def lookup_by_remote_url(self, url: str):
        if not url:
            return None
        mask = self.df["remote_url"].str.lower() == url.lower()
        df_result = self.df[mask]

        if df_result.empty:
            return None

        result = df_result.iloc[0].to_dict()
        result["score"] = 100

        return result
