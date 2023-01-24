# Change or convert CSV column headers
expected = {'contact', 'genre', 'téléphone'}
incoming = {'Contact', 'genre'}

result = incoming.difference(expected)
converter = {'Contact': 'contact', 'genre': 'genre'}

clean = {converter.get(item, item).lower() for item in incoming}

diff = clean.symmetric_difference(expected)
clean.union(diff)
