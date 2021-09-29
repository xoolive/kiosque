# kiosque

```bash
# Runs the textual interface
kiosque
# equivalent to:
kiosque tui
# Display the link in a pager
kiosque preview https://...
# link = download to file, alias = get the PDF
kiosque download link_or_alias
kiosque download link_or_alias output.md
# get the PDF
kiosque latest_issue link_or_alias
```

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

## Authentication

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

## Supported websites

A comprehensive list is available here in the [`websites.md`](websites.md) file. Support for authentication is offered for some content, but help of subscribing readers is obviously wanted to provide access to more contents. More websites are integrated as soon as an opportunity to test them arises. Pull requests are of course welcome.

## License

MIT
