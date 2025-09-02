# Kindle Utils

Kindle as a productivity hub. Utilities to act as proxy to render on Kindle basic browser.

## Virtual env

If it does not exist, create one:

```bash
$ python3 -m venv .venv
```

To activate:

```bash
$ source .venv/bin/activate
```

To deactivate:

```bash
$ deactivate
```

### Useful commands

Generate `requirement.txt` file:

```bash
$ pip3 freeze > requirements.txt
```

To install from the dependency file:

```bash
$ pip3 install -r requirements.txt
```

## Run the project

### Development

```bash
$ python -m kindler.app
```

### Production (Gunicorn WSGI)

```bash
$ gunicorn kindler.wsgi:app
```

## Calibre

To support generating epub, mobi, azw3 of pages on the fly, need to install calibre, or more specific `ebook-convert` as it's invoked as a sub process to generate ebooks.

The usage of `aspose-words` library is remove as it not only left a notice that the library is not paid for but also wouldn't convert more than 20 pages. So it was too annoying to work with.


## Docker build

Run:

```bash
$ docker build -t kindler-app .
```

To test:

```bash
$ docker run -p 8181:8181 kindler-app
```

Test an image from Docker Hub:

```bash
$ docker run -p 8181:8181 kasramp/kindler:v0.0.2
```

## Formatting

Run:

```bash
$ black --check .
```

To fix:

```bash
$ black .
```