import re
import emoji
import sys
import pandas as pd

def extract_entities(ls_posts):
     
    # Patterns to extract
    patterns = {
        "Mentions": r'(?<!\w)@[\w.\-]+(?:@[\w\.\-]+\.\w+)?',                                           # including both normal and mastodon mentions
        "Hashtags": r'#\w+',                                                                           # hashtags
        "Cashtags":r'[\$\€][A-Za-z]{1,10}',                                                            # cash tags (only $ and €)
        "URLs": r'https?://\S+|www\.\S+',                                                              # urls
        "Quoted_text" : r'"[^"]*"|\'[^\']*\'',                                                         # quotations  
        "Punctuations": r'[^\w\s]',                                                                   # punctuations
        "Punctuation_emphasis": r'!{2,}|\?{2,}|\.{2,}',                                                # emphasis on ? and ! punctuations
        "All_caps": r'\b(?:[A-Z]{2,})\b',                                                              # All caps words
        "Negations": r'\b(not|no|never|none|n\'t)\b',                                                  # use of negations (no, not never, none)
        "Time_expressions": r'\b(?:tomorrow|yesterday|today|times|tonight|now|week|days|day|days|month|year)',     # time expressions (day, days, tomorrow, yesterday, tonight, next week, now) 
        "Emojis": r'[\U00010000-\U0010ffff]',                                                          # Basic Unicode emoji range
    }

    # extract entities from each post
    dict_entities = {'Posts':[], 'Mentions':[], 'Hashtags':[], 'Cashtags':[], 'URLs':[], 'Quoted_text':[], 'Punctuations':[], 
    'Punctuation_emphasis':[], 'All_caps':[], 'Negations': [], 'Time_expressions':[], 'Emojis':[]}
    
    dict_entities['Posts'] = ls_posts

    for post in ls_posts:
        for name, pattern in patterns.items():
            if name in ['Negations', 'Time_expressions']:
                found = re.findall(pattern, post.lower())
            elif name == 'Quoted_text':
                # Special handling for quoted text to flatten tuples
                matches = re.findall(pattern, post)
                found = [match[0] if match[0] else match[1] for match in matches]
            else:
                found = re.findall(pattern, post)
            dict_entities[name].append(found)
    
    df_output = pd.DataFrame(dict_entities)
    return df_output


