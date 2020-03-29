import pandas as pd

def query_words(rendered, uploaded):
    words = get_words()
    filtered_words = words.query(f'rendered == {rendered} and uploaded == {uploaded}')
    return filtered_words['word'].tolist()

def set_rendered(rendered_words, status):
    words = get_words()
    words.loc[words['word'].isin(rendered_words), 'rendered'] = status
    save_words(words)
    print(f'Successfully updated words:', ', '.join(rendered_words))

def set_uploaded(uploaded_words, status):
    words = get_words()
    words.loc[words['word'].isin(uploaded_words), 'uploaded'] = status
    save_words(words)
    print(f'Successfully updated words:', ', '.join(uploaded_words))

def add_words(new_words, rendered=False, uploaded=False):
    words = get_words()
    new_words = pd.DataFrame(data={'word': new_words, 'rendered': [rendered] * len(new_words), 'uploaded': [uploaded] * len(new_words)})
    combined_words = pd.concat([words,new_words]).drop_duplicates('word')
    save_words(combined_words)
    print(f'Successfully added to schedule:', ', '.join(new_words))

def get_words():
    return pd.read_csv('words.csv', names=['word','rendered','uploaded'], dtype={'rendered': bool, 'uploaded': bool}, header=0)

def save_words(words):
    words.to_csv('words.csv', index=False)