# Kindle Utils

Kindle as a productivity hub. Utilities to act as proxy to render on Kindle basic browser.

### Virtual env

If does not exist, create one:

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

## Calibre

To support generating epub, mobi, azw3 of pages on the fly, need to install calibre, or more specific `ebook-convert` as it's invoked as a sub process to generate ebooks.

The usage of `aspose-words` library is remove as it not only left a notice that the library is not paid for but also wouldn't convert more than 20 pages. So it was too annoying to work with.
