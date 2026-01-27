# Extract Entities (URLs, Mentions, Hashtags)

## Description

The method extracts useful entities from social media posts such as URLs, hashtags, cashtags ($ and €), mentions (including Mastodon mentions), quoted texts, punctuations, punctuation emphasis (e.g., !!!), all caps words, negations, time expressions (e.g., today, next week), and emojis. It is a very simple method using only regular expressions to determine the mentioned entities. The method reads data from a CSV file with posts per row and writes output to a CSV file having the post text followed by the respective columns of the extracted entities.

## Use Cases

- To study the impact of users reaction and increase in their engagement with posts having URLs, hashtags, and mentioned compared to the posts without the mentioned entities on the same topic.
- Comparing the use of puntuation emphasis, all caps, and emojis between the social media posts on different topics indicating how formal or informal the general language is.
- To study the use of time expression in identifying collective activites and coordination patterns leading to real-time mobilization at the time of protests and political unrest.

## Input Data

The input data consists of social media posts (one per line) as a CSV file, i.e., `data/input_social_posts.csv`. The following are a few examples:

|Posts|
|---------|
|"@bob@infosec.exchange #Crypto €BMW ""Let’s go!"" https://t.co/xyz123 😀"|
|#Startups 💡 $GOOG https://t.co/xyz123 @dave@mastodon.social 'Not sure about this'|
|@bob@mastodon.social $AAPL 'This is amazing' 😀 #Crypto https://news.site/article|
|"@dave@infosec.exchange ""Exciting times ahead!"" https://t.co/xyz123 €BMW #AI 😀"|
|#AI @bob@mastodon.social €ETH 🚀 'Not sure about this' https://news.site/article|
|...|

## Output Data

The method writes output to a CSV file, i.e., `data/output_posts_with_entities.csv`. It has the first column as the original post's text, followed by columns representing entities extracted from the text. Each column value is a list of one or more entities extracted from a post.

| Posts | Mentions | Hashtags | Cashtags | URLs | Quoted_text | Punctuations | Punctuation_emphasis | All_caps | Negations | Time_expressions | Emojis |
|:-----:|:--------:|:--------:|:--------:|:----:|:-----------:|:------------:|:--------------------:|:--------:|:---------:|:----------------:|:------:|
|"@bob@infosec.exchange #Crypto €BMW ""Let’s go!"" https://t.co/xyz123 😀"|	['@bob@infosec.exchange']|	['#Crypto']	|['€BMW']	|['https://t.co/xyz123']	|"['""Let’s go!""']"|	[@, @, ., #, €, ", ’, !, ", :, /, /, ., /, 😀] | []	|['BMW']|	[]|	[]|	['😀']|
|"#Startups 💡 \$GOOG https://t.co/xyz123 @dave@mastodon.social 'Not sure about this'"|['@dave@mastodon.social']	|['#Startups']	|['\$GOOG']	|['https://t.co/xyz123']	|"[""'Not sure about this'""]"	| [#, 💡, \$, :, /, /, ., /, @, @, ., ', '] | []	|['GOOG']|	['not']	|[]	|['💡']|
|@bob@mastodon.social \$AAPL 'This is amazing' 😀 #Crypto https://news.site/article|	['@bob@mastodon.social']|	['#Crypto']|	['\$AAPL']|	['https://news.site/article']|	"[""'This is amazing'""]"| [@, @, ., $, ', ', 😀, #, :, /, /, ., /] |	[]|	['AAPL']|	[]|	[]|	['😀']|
|"@dave@infosec.exchange ""Exciting times ahead!"" https://t.co/xyz123 €BMW #AI 😀"	|['@dave@infosec.exchange']|	['#AI']|	['€BMW']|	['https://t.co/xyz123']|	"['""Exciting times ahead!""']"|	[@, @, ., ", !, ", :, /, /, ., /, €, #, 😀]	 | []|	['BMW', 'AI']|	[]|	['times']|	['😀']|
|#AI @bob@mastodon.social €ETH 🚀 'Not sure about this' https://news.site/article |	['@bob@mastodon.social']|	['#AI']|	['€ETH']|	['https://news.site/article']|	"[""'Not sure about this'""]"|	[#, @, @, ., €, 🚀, ', ', :, /, /, ., /]	| []|	['AI', 'ETH']|	['not']|	[]|	['🚀']|

## Hardware Requirements

The method runs on a small virtual machine provided by a cloud computing company (2 x86 CPU cores, 4 GB RAM, 40 GB HDD).
  
## Environment Setup

The method is tested with Python 3.10 and should work with other Python versions as well. Use the following command to setup the virtual working environment by installing all dependencies;

  ```pip install -r requirements.txt```

## How to Use

- Open `index.ipynb` and execute the cells to use the method. It imports and uses the entity extraction function defined in `entity_extractor.py`.
- Populate the input file `data/input_social_posts.csv` with social media posts on the topic of interest, keeping one per row (Optional: the file already has sample posts). 

## Technical Details

This method extracts a mix of entities including the common text entities e.g., punctuations, time expressions etc., the digital text entities e.g., Unique resource link (URL), pay-level domains (PLDs) and emojis, and social media entities e.g., mentions and hashtags. It is very common with digital content to provide relevant resources as URLs and its PLD e.g., the URL *https://example.com/category/topic-of-the-post* has *example.com* as PLD where *.com* is first level and *example* is the second level domain). The PLDs are useful in aggregating the use of the URLs from a specific body e.g., which news agency has the highest rate of tweet deletions with the URLs citing their source [1]. 

The social media related entities are more known to the social media users. The mentions are used to refer/respond to a person, give credit or simply to draw other users' attention to a post of common interest. They come with a slight variation across platforms e.g., X (formerly Twitter) uses mentions as *@alice*, while the same for Mastodon users is *@alice@instance.social*. The hashtags are used to associate the post with a specific topic category, school of thought or campaign. They are often popularized by early adopters where the general public jump in to share their opinions. There are also instances of campaigning through hashtags to promote or demoting social movements. For example 20% of the accounts contributing *Brexit* were later found inactive [2]. It is not unusual that the movements initiated with hashtags become a trending topic, questioning the decisions of the governments, institutions and individuals. 

This method limits to basic resources using only regular expressions to detect the mentioned entities. The regular expressions can be found in the file `entity_extractor.py` and be extended with newer entities and newer forms of existing entities. It may also be useful to consider using the `emoji` or spaCy packages for more robust entity extraction.

## References

[1] Khan, M. T., Dimitrov, D., & Dietze, S. (2025, September). Characterization of Tweet Deletion Patterns in the Context of COVID-19 Discourse and Polarization. In Proceedings of the 36th ACM Conference on Hypertext and Social Media (pp. 43-47).

[2] Bastos, M. (2021). This account doesn’t exist: Tweet decay and the politics of deletion in the brexit debate. American Behavioral Scientist, 65(5), 757-773.

## Contact

For queries, please contact, <taimoor.khan@gesis.org>
