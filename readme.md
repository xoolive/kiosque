# kiosque

## Command-line interface

```bash
# prints to file (named after the url)
kiosque https://url.com/article
# prints to file (named output)
kiosque https://url.com/article output.md
# prints to stdout
kiosque https://url.com/article -
# read in a pager
kiosque https://url.com/article - | bat - -l md
# download current PDF
kiosque [alias]
```

## Python interface

```python
from kiosque import Website

md_text = Website.instance(url).full_text(url)
```

## Credentials

Edit the configuration file with entries as follows

```conf
[https://www.lemonde.fr/]  # or any base_url
username =
password =
```

The configuration file location appears in the following variable:

```python
from kiosque import configuration_file
```

## Installation

```bash
pip install kiosque
```

Development version:

```bash
poetry install
```

## License

MIT
