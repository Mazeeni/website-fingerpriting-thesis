"""
- Get the HAR files from a given list of webpages using 'chrome-har-capturer'
- Save the webpages as Web Bundles in a given output directory using the HAR files

Requirements:
- 'chrome-har-capturer' library installed on the machine: https://github.com/cyrus-and/chrome-har-capturer
- a active headless chrome instance on thet machine, run with: google-chrome --remote-debugging-port=9222 --headless
- the 'gen-bundle' command line tool, installation instructions at: https://github.com/WICG/webpackage/tree/main/go/bundle#getting-started
"""

# TODO: change name of this file

import subprocess
import argparse
from pathlib import Path
from utils import extract_domain_name

parser = argparse.ArgumentParser()
parser.add_argument(
    "--website_list_path",
    help="path to .txt file containing urls of webpages to create Web Bundles for (one line per webpage)",
    required=True,
)
parser.add_argument(
    "--hars_output_path",
    help="path to .txt file containing urls of webpages to create Web Bundles for (one line per webpage)",
    required=True,
)
# parser.add_argument("--server_domain_name", help="IP address or domain name of server hosting Web Bundle (.wbn) files", required=True)
parser.add_argument(
    "--wbns_output_path",
    help="output directory for Web Bundle files (.wbn)",
    required=True,
)

options = parser.parse_args()

Path(options.hars_output_path).mkdir(parents=True, exist_ok=True)
Path(options.wbns_output_path).mkdir(parents=True, exist_ok=True)

file = open(options.website_list_path, "r")
webpage_list = [line.strip() for line in file.readlines()]

command_list = []
url_list = []
for webpage in webpage_list:
    domain_name = extract_domain_name(webpage)

    # get har file
    command_list.append(
        "npx chrome-har-capturer -o "
        + options.hars_output_path
        + domain_name
        + ".har -c "
        + webpage
    )
    # covert har file to wbn file
    command_list.append(
        "./gen-bundle -har "
        + options.hars_output_path
        + domain_name
        + ".har -o "
        + options.wbns_output_path
        + domain_name
        + ".wbn -primaryURL "
        + webpage
    )
    # add url to list
    url_list.append(domain_name + ".wbn")

subprocess.call(" ; ".join(command_list), shell=True)

file = open(options.wbns_output_path + "/url_list.txt", "w")
file.write("\n".join(url_list))
file.close()
