# search.py
import pandas as pd
from rapidfuzz import process, fuzz


class FuzzySearcher:
    def __init__(self):
        self.df = pd.read_csv("../scripts/gutindex_aus_clean.csv")
        self.df["combined"] = (
            self.df["title"].astype(str)
            + " "
            + self.df["author"].astype(str)
            + " "
            + self.df["full_title"].astype(str)
            + " "
            + self.df["full_author"].astype(str)
        )

    def search(self, query, limit=50, score_cutoff=70):
        matches = process.extract(
            query,
            self.df["combined"].tolist(),
            scorer=fuzz.WRatio,
            limit=None,  # Get all matches to sort properly
            score_cutoff=score_cutoff,
        )

        if not matches:
            return []
        df_results = pd.DataFrame(
            [{**self.df.iloc[i].to_dict(), "score": score} for _, score, i in matches]
        )
        df_results["title"] = df_results["full_title"].combine_first(
            df_results["title"]
        )
        df_results["author"] = df_results["full_author"].combine_first(
            df_results["author"]
        )
        df_results = df_results.sort_values(by="score", ascending=False)
        df_results = df_results.head(limit)
        return df_results.to_dict(orient="records")
