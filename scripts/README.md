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