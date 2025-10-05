import logging
import os
import pandas as pd
from rapidfuzz import process, fuzz
import re


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

        self.df["title_norm"] = self.df["title"].map(self.normalize_text)
        self.df["author_norm"] = self.df["author"].map(self.normalize_text)
        self.df["combined_norm"] = (
            self.df["title_norm"] + " " + self.df["author_norm"]
        ).str.strip()
        self.df = self.df[self.df["combined_norm"] != ""].copy()

    @staticmethod
    def normalize_text(text):
        text = str(text).lower().strip()
        text = re.sub(r"\s+", " ", text)  # collapse multiple spaces
        text = re.sub(r"[^\w\s]", "", text)  # remove punctuation
        return text

    def search(
        self,
        query: str,
        limit: int = 50,
        score_cutoff: int = 80,
        scorer=fuzz.token_set_ratio,
    ):
        if not query:
            return []

        query_norm = self.normalize_text(query)
        results = []
        title_matches = process.extract(
            query_norm,
            self.df["title_norm"].tolist(),
            scorer=scorer,
            score_cutoff=score_cutoff,
            limit=limit * 5,
        )
        for match, score, idx in title_matches:
            weighted_score = (
                score + 5
                if self.df["title_norm"].iloc[idx].startswith(query_norm)
                else score
            )
            results.append((idx, weighted_score))

        author_matches = process.extract(
            query_norm,
            self.df["author_norm"].tolist(),
            scorer=scorer,
            score_cutoff=score_cutoff,
            limit=limit * 5,
        )
        for match, score, idx in author_matches:
            weighted_score = (
                score + 3
                if self.df["author_norm"].iloc[idx].startswith(query_norm)
                else score
            )
            results.append((idx, weighted_score))

        combined_matches = process.extract(
            query_norm,
            self.df["combined_norm"].tolist(),
            scorer=scorer,
            score_cutoff=score_cutoff,
            limit=limit * 5,
        )
        for match, score, idx in combined_matches:
            results.append((idx, score))

        if not results:
            return []

        scores_by_idx = {}
        for idx, score in results:
            if idx not in scores_by_idx or score > scores_by_idx[idx]:
                scores_by_idx[idx] = score

        df_results = self.df.iloc[list(scores_by_idx.keys())].copy()
        df_results["score"] = df_results.index.map(scores_by_idx)
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
