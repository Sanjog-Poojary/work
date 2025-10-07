import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder, MinMaxScaler
print("Starting Preprcessing...")
print("Loading CSV  data...")
movies = pd.read_csv('C:/Users/Sanjog/Downloads/Short film/movies_metadata.csv', low_memory=False)
print(f"Loaded {len(movies)} movies")
def extract_genre_names(genres_list):
    if isinstance(genres_list, str):
        import ast
        genres_list = ast.literal_eval(genres_list)
    if isinstance(genres_list, list):
        return [g['name'] for g in genres_list]
    return []

movies['genres_list'] = movies['genres'].apply(extract_genre_names)
movies['budget'] = pd.to_numeric(movies['budget'], errors='coerce').fillna(0)
movies['adult'] = movies['adult'].fillna(False)
movies['original_language'] = movies['original_language'].fillna('unknown')
movies['overview'] = movies['overview'].fillna('')
mlb = MultiLabelBinarizer()
genre_features = mlb.fit_transform(movies['genres_list'])
genre_df = pd.DataFrame(genre_features, columns=mlb.classes_)
movies = movies.reset_index(drop=True)
genre_df = genre_df.reset_index(drop=True)
ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
language_features = ohe.fit_transform(movies[['original_language']])
# Convert column names to strings to avoid mixed type issues
language_columns = [str(col) for col in ohe.categories_[0]]
language_df = pd.DataFrame(language_features, columns=language_columns)
language_df = language_df.reset_index(drop=True)
scaler = MinMaxScaler()
movies['budget_norm'] = scaler.fit_transform(movies[['budget']])
processed_df = pd.concat([
    movies[['id', 'original_title', 'overview', 'budget_norm', 'adult']],
    genre_df,
    language_df
], axis=1)
print("Saving preprocessed data..")
processed_df.to_csv('movies_preprocessed.csv', index=False)
print("Preprocessing complete! Data saved to movies_preprocessed.csv")
print("Creating visualizations...")

try:
    # Genre distribution bar plot
    genre_counts = processed_df[mlb.classes_].sum().sort_values(ascending=False)
    genre_counts.plot(kind='bar', figsize=(12,6), color='skyblue')
    plt.title('Movie Genre Distribution')
    plt.xlabel('Genre')
    plt.ylabel('Number of Movies')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    print("Visualizations created successfully!")

except Exception as e:
    print(f"Note: Visualizations could not be displayed (this is normal in some environments): {e}")
    print("Data processing completed successfully - visualizations can be generated separately if needed.")