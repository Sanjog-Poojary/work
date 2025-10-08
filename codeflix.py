import argparse
import ast
from pathlib import Path
from typing import List, Any, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder, MinMaxScaler


def extract_genre_names(genres_value: Any) -> List[str]:
    """
    Robustly parse a TMDB-like 'genres' field which may be:
      - a JSON-like string of list[dict{name:str, id:int}]
      - an actual list of dicts
      - NaN/None/other
    Returns a list of genre names.
    """
    if isinstance(genres_value, list):
        try:
            return [g.get("name", "") for g in genres_value if isinstance(g, dict) and "name" in g]
        except Exception:
            return []

    if isinstance(genres_value, str):
        try:
            parsed = ast.literal_eval(genres_value)
            if isinstance(parsed, list):
                return [g.get("name", "") for g in parsed if isinstance(g, dict) and "name" in g]
        except (ValueError, SyntaxError):
            # Fall through to empty
            pass

    return []


def coerce_adult(value: Any) -> bool:
    """
    Coerce TMDB 'adult' values into booleans:
      - true/false (case-insensitive) strings
      - actual booleans
      - numbers (non-zero -> True)
    Defaults to False if unknown.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        s = value.strip().lower()
        if s in {"true", "t", "1", "yes", "y"}:
            return True
        if s in {"false", "f", "0", "no", "n"}:
            return False
    return False


def build_one_hot_encoder():
    """
    Build a OneHotEncoder that works across sklearn versions.
    sklearn >= 1.2: use sparse_output
    sklearn < 1.2: fall back to sparse
    """
    try:
        return OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    except TypeError:
        return OneHotEncoder(sparse=False, handle_unknown="ignore")


def preprocess(
    input_csv: Path,
    output_path: Path,
    plot_path: Optional[Path] = None,
    save_parquet: bool = False,
) -> None:
    print("Starting Preprocessing...")
    print(f"Loading CSV data from: {input_csv}")

    # Read with low_memory=False for mixed dtypes; allow caller to pass any CSV
    movies = pd.read_csv(input_csv, low_memory=False)
    print(f"Loaded {len(movies)} movies")

    # Genres
    movies["genres_list"] = movies.get("genres", pd.Series([np.nan] * len(movies))).apply(extract_genre_names)

    # Budget: numeric + treat zeros as missing; apply log1p then min-max scale
    movies["budget"] = pd.to_numeric(movies.get("budget", pd.Series([np.nan] * len(movies))), errors="coerce")
    # Consider 0 as missing for TMDB budgets
    movies.loc[movies["budget"] == 0, "budget"] = np.nan
    budget_log = np.log1p(movies["budget"].fillna(0))
    scaler = MinMaxScaler()
    movies["budget_norm"] = scaler.fit_transform(budget_log.to_frame())

    # Adult flag -> bool
    movies["adult"] = movies.get("adult", pd.Series([False] * len(movies))).apply(coerce_adult)

    # Language -> one-hot
    movies["original_language"] = movies.get("original_language", pd.Series(["unknown"] * len(movies))).fillna("unknown")
    ohe = build_one_hot_encoder()
    lang_arr = ohe.fit_transform(movies[["original_language"]])
    lang_cols = [f"lang_{str(cat)}" for cat in ohe.categories_[0]]
    language_df = pd.DataFrame(lang_arr, columns=lang_cols).astype(np.uint8)

    # Genres -> MultiLabelBinarizer
    mlb = MultiLabelBinarizer()
    genre_arr = mlb.fit_transform(movies["genres_list"])
    genre_cols = [f"genre_{g}" for g in mlb.classes_]
    genre_df = pd.DataFrame(genre_arr, columns=genre_cols).astype(np.uint8)

    # Assemble final frame
    base_cols = []
    for col in ["id", "original_title", "overview", "budget_norm", "adult"]:
        if col in movies.columns:
            base_cols.append(col)

    processed_df = pd.concat(
        [
            movies[base_cols].reset_index(drop=True),
            genre_df.reset_index(drop=True),
            language_df.reset_index(drop=True),
        ],
        axis=1,
    )

    # Save output
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if save_parquet or output_path.suffix.lower() == ".parquet":
        try:
            processed_df.to_parquet(output_path, index=False)
            print(f"Preprocessing complete! Data saved to {output_path} (Parquet)")
        except Exception as e:
            # Fallback to CSV if parquet engine is missing
            csv_fallback = output_path.with_suffix(".csv")
            processed_df.to_csv(csv_fallback, index=False)
            print(f"Parquet not available ({e}). Saved CSV to {csv_fallback}")
    else:
        processed_df.to_csv(output_path, index=False)
        print(f"Preprocessing complete! Data saved to {output_path}")

    # Visualization (optional)
    if plot_path is not None and len(genre_cols) > 0:
        try:
            print("Creating visualizations...")
            genre_counts = processed_df[genre_cols].sum().sort_values(ascending=False)
            plt.figure(figsize=(12, 6))
            genre_counts.plot(kind="bar", color="skyblue")
            plt.title("Movie Genre Distribution")
            plt.xlabel("Genre")
            plt.ylabel("Number of Movies")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()

            plot_path = Path(plot_path)
            plot_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(plot_path, dpi=150)
            plt.close()
            print(f"Visualization saved to {plot_path}")
        except Exception as e:
            print(f"Note: Could not create/save visualization: {e}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preprocess TMDB-like movie metadata into ML-ready features.")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to movies_metadata.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("movies_preprocessed.csv"),
        help="Output file path (.csv or .parquet). Default: movies_preprocessed.csv",
    )
    parser.add_argument(
        "--plot",
        type=Path,
        default=None,
        help="Optional path to save the genre distribution plot (e.g., plots/genre_distribution.png)",
    )
    parser.add_argument(
        "--parquet",
        action="store_true",
        help="Save output as Parquet (overrides output extension if provided).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    preprocess(args.input, args.output, plot_path=args.plot, save_parquet=args.parquet)
