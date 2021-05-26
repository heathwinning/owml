from typing import List
import pandas as pd

def query_words(rendered: bool, uploaded: bool) -> List[str]:
    words = get_words()
    filtered_words = words.loc[
        (words['rendered'] == rendered) &
        (words['uploaded'] == uploaded)
    ]
    return filtered_words['word'].tolist()

def set_rendered(rendered_words: List[str], status: bool) -> None:
    words = get_words()
    words.loc[words['word'].isin(rendered_words), 'rendered'] = status
    save_words(words)
    print(f'Successfully updated words:', ', '.join(rendered_words))

def set_uploaded(uploaded_words: List[str], status: bool) -> None:
    words = get_words()
    words.loc[words['word'].isin(uploaded_words), 'uploaded'] = status
    save_words(words)
    print(f'Successfully updated words:', ', '.join(uploaded_words))

def add_words(new_words: List[str], rendered: bool=False, uploaded: bool=False) -> None:
    words = get_words()
    new_words_df = pd.DataFrame(data={'word': new_words, 'rendered': rendered, 'uploaded': uploaded})
    combined_words = pd.concat([words,new_words_df]).drop_duplicates('word')
    unique_combined_words = combined_words.groupby("word").any()
    unique_combined_words = unique_combined_words.groupby(["rendered","uploaded"]).apply(lambda w: w.sample(frac=1)).droplevel(["rendered","uploaded"]).reset_index()
    save_words(unique_combined_words)
    print(f'Successfully added to schedule:', ', '.join(new_words))

def get_words() -> pd.DataFrame:
    return pd.read_csv('words.csv', names=['word','rendered','uploaded'], dtype={'rendered': bool, 'uploaded': bool}, header=0)

def save_words(words: pd.DataFrame) -> None:
    words.to_csv('words.csv', index=False)