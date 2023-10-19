# fyp-website-fingerprinting
This repository forms the software artefact for my "Application Layer Defences to Website Fingerprinting" final year project.

# Prerequisites
`go` must be installed, see [Go Install Documentation](https://go.dev/doc/install).

A copy of the `gen-bundle` executable can be found in src/. To install the latest version, see [go/bundle in the webpackage repo](https://github.com/WICG/webpackage/tree/main/go/bundle).

Create a virtual environment and install the requirements in `requirements.txt`.

# Running a website fingerprinting attack simulation end-to-end.
`src/main.py` perform requests for pages, and trains a website fingerprinting classifier on these traces, outputting results.

This file must be run with ambient capabilities using `assign_ambient_caps`. The command begins as:
`./assign_ambient_caps -c '13' ../venv/bin/python ./main.py ...`.

This allows the file to run without full root capabilities, and only the required `CAP_NET_RAW` root capability. This is safer than running the browser as root.

`main.py` must be run with command line arguments. Type this command for help.
`./assign_ambient_caps -c '13' ../venv/bin/python ./main.py -h`.
