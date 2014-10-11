# Fantasy Football Playground

Nothing but chaos at the moment

## Dependencies

    mkvirtualenv fantasy

### PsycoPG2

    PATH=$PATH:/Applications/Postgres.app/Contents/Versions/9.3/bin/ pip install psycopg2

### Everything else:

    pip install -r requirements.txt

### Basic usage:

    FFN_API_KEY=<your api key> pipeline.sh <Game ID> <Week>

### Bookmarklet Local

1. start server.py

```
$ python server.py
```

2. go to `https://localhost:5000` and accept the self signed certificate

3. setup the bookmarklet:

```javascript:(function(){document.body.appendChild(document.createElement('script')).src='https://localhost:5000/static/bookmarklet.js';})();
```

4. use the bookmarklet
