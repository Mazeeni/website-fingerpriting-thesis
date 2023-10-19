""" utils related to pcap files and traces """
# TODO: types

from wf_tools.classifiers.kfingerprinting.rf_fextract import TOTAL_FEATURES
from ipaddress import IPv4Network
import wf_tools.trace as trv1
import wf_tools.fetch_websites as fw
import wf_tools.sniffer as sn
from pathlib import Path
import socket
import numpy as np
import pickle
import matplotlib.pyplot as plt
import pandas as pd


def website_file_to_list(website_list_path):
    f = open(website_list_path, "r")
    website_list = f.read().splitlines()
    f.close()
    return website_list


def appendToFile(filename, content):
    f = open(filename, "wb")  # wb required because writing bytes
    f.write(content)
    f.close()


def readFromFile(filename):
    f = open(filename, "rb")
    bytes = f.read()  # read whole file
    f.close()
    return bytes


# The file required by rf_fextract is one line per packet, where each line
# is of the form "time direction size", e.g. "1.242 -1 60"
def convert_trace_to_list(trace):
    data_list = []
    for packet in trace:
        data_list.append(
            str(packet.timestamp) + " " + str(packet.direction) + " " + str(packet.size)
        )
    return data_list


def convert_trace_to_df_input(trace):
    data_list = []
    for packet in trace:
        data_list.append(packet.size * packet.direction)
    return data_list


def pcap_file_to_trace(filename):
    packet_trace = trv1.pcap_to_trace(
        readFromFile(filename), IPv4Network(get_client_interface_ip_addr())
    )[0]
    return packet_trace


def trace_total_features(trace):
    return TOTAL_FEATURES(trace)


def fetch_webpage(
    url, protocol="tcp", test_web_bundle=False, browser="Chrome", browser_options=[]
):
    if browser == "Chrome":
        driverFactory = fw.ChromiumFactory(extra_options=browser_options)
        sessionFactory = fw.ChromiumSessionFactory(driverFactory)  # create factory
    else:  # Firefox
        driverFactory = fw.FirefoxFactory(extra_options=browser_options)
        sessionFactory = fw.FirefoxSessionFactory(driverFactory)
    session = sessionFactory.create(
        url, protocol
    )  # invoke factory to create actual session
    session.begin()  # must begin session before anything
    page = session.fetch_page(test_web_bundle=test_web_bundle)  # fetch page
    session.close()
    return page


# Will fetch a webpage, and sniff all TCP packets, outputting them to a pcap file.
def sniff_packets_to_pcap_file(
    url,
    filename,
    protocol="tcp",
    test_web_bundle=False,
    browser="Chrome",
    browser_options=[],
    save_to_file=True,
):
    proto = "tcp"
    if protocol == "quic":
        proto = "udp"
    tcp_sniffer = sn.ScapyPacketSniffer(capture_filter=proto)
    tcp_sniffer.start()
    page = fetch_webpage(url, protocol, test_web_bundle, browser, browser_options)
    tcp_sniffer.stop()
    pcap_bytes = (
        tcp_sniffer.pcap()
    )  # turn sniffed packets into a pcap format serialised in bytes
    if save_to_file:
        appendToFile(filename, pcap_bytes)  # TODO: make directory a constant
    return page, pcap_bytes


def extract_domain_name(site):
    return (
        site.replace("https://", "")
        .replace("http://", "")
        .replace("www.", "")
        .split("/")[0]
    )


# gets the IP address of the interface used to connect to the internet
def get_client_interface_ip_addr():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


def save_object(obj, filename):
    with open(filename, "wb") as outp:  # Overwrites any existing file.
        pickle.dump(obj, outp, pickle.HIGHEST_PROTOCOL)


def save_importances_graph(importances, std, labels, filename, num_importances):
    forest_importances = pd.Series(importances, index=labels)
    forest_importances.sort_values(ascending=False, inplace=True)
    forest_importances = forest_importances.head(num_importances)

    fig, ax = plt.subplots()
    forest_importances.plot.bar(ax=ax)  # yerr=std,
    ax.set_title("Feature importances using MDI")
    ax.set_ylabel("Mean decrease in impurity")
    fig.tight_layout()

    plt.xticks(rotation=30, ha="right")
    plt.ylim([0.01, 0.025])
    plt.savefig(filename, bbox_inches="tight")
