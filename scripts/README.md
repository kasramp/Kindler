## Library Gutenberg Australia index converter

Library Gutenberg Australia is not adding new books to the collection as of December 2024.
Hence, it's safe to get the full `.txt` index and convert to CSV file that's easy to look up
and search.

The full index: [https://gutenberg.net.au/gutindex_aus.txt](https://gutenberg.net.au/gutindex_aus.txt).

Note that script doesn't handle the conversion perfectly. Some manual steps need to be taken to ensure
the data in the produced CSV file is perfect. So far the following cases are identified:

- Additional text at the beginning of the index file
- `, Vol` : ends up appending it to author name
- `htm;, httl, ...`: typo in `.html` url that ends up on `other_url` column. In reality the `other_url` column should never be populated.

For the above cases, it's better to manually directly change the source file (`gutindex_aus.txt`)
and run the script again.

The cleaned version of the original index is available to diff purpose. In case the library
decides again to add new titles, we can simply get the diff the updated version (after some minor cleaning of course).

Otherwise, the `gutindex_aus_clean.csv` will be used without any new revision.

## Local index

It's possible to build a better and more comprehensive index by scanning through all the ebooks (stored locally)
and parse each html to build a more accurate index. Of course still many records have wrong values
since the template used by Project Gutenberg Australia is not consistent and evolved throughout the years.

First make sure to set up a venv and install all dependencies. Refer to the parent's README file
on setting up a venv.

To build a local index, run:

```python
$ python3 build_index_from_local_storage.py
```

If needed, adjust the row file path.

This index also relies on building the `.epub`, `.mobi` and `.azw3` regardless of their existence
in Project Gutenberg Australia.

## Summary Generator

The `summary_generator.py` generates a summary for each index stored in `index.csv` file.

That means first a local index must be generated using `build_index_from_local_storage.py` and
then generate the summaries.

To generate a summary, the script relies on Ollama. Therefore, a strong machine or server is needed.
To get the full advantage of the machine capabilities, better to natively install it on the machine and avoid
Docker images.

On mac:

```bash
$ sudo brew install ollama
```

And then run:

```bash
$ ollama serve
```

Building the summary takes a very long time. However, the script has the capability to
resume from where it's left.

**Keep in mind that** the script expects a running Ollama and doesn't check whether it's running or not.
Hence, if it cannot reach Ollama, simply sets the entry as null.