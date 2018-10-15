# twitter-scraping
A simple implementation of web scraping on Twitter with requests and BeautifulSoup

Two functions are provided:

- `get_account_tweets()`: Gets the username of an account and downloads all the history of its tweets, re-tweets, etc as a pandas dataframe.

- `get_following()`: Gets the username of an account and downloads all the accounts it follows as a dataframe.

An interesting application of `get_following()` is on **verified**, a twitter maintained account that follows all verified users. Hence, you can use this to get a list of all of them.

**Note**: Twitter API is much faster, but comes with a lot of restrictions. Nevertheless, you may want to try this instead.
