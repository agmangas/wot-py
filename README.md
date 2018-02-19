# W3C WoT Python

## Introduction

This repository contains an experimental implementation of the [W3C WoT Scripting API](https://w3c.github.io/wot-scripting-api/).

Based on the exploratory implementations located in the [thingweb GitHub page](https://github.com/thingweb).

## Development

Install in development mode:

```
pip install -e .[tests]
```

To run the tests in both Python 2.7 and 3.6 environments:

```
tox
```

### Building the docs

Move to the `docs` folder and run:

```
make html
```