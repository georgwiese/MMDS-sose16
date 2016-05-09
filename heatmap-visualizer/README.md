# Heatmap Visualizer

In order to get started, you'll need a `GOOGLE_API_KEY` file in the `heatmap-visualizer` directory.
This file should contain nothing but your Google API key.

To start the server run:

```bash
python server.py
```

You can select maps stored under `maps` from the UI.

Here's a sample map JSON file:

```json
{
  "title": "Example",
  "pointRadius": 10,
  "data": [
    {
      "lat": 40.818241,
      "lon": -73.947435,
      "weight": 1
    },
    ...
  ]
}
```

## Map Series (not yet implemented)

If you place a folder in the `map` directory, the files in that folder (assumed to be map JSONs as explained above) will all be loaded and displayed in alphabetical order in 1s steps.
