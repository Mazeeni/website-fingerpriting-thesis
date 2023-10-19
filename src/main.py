from wf_tools.classifiers.kfingerprinting._classifier import KFingerprintingClassifier
from utils import *
import numpy as np
import shutil
import sys
from pathlib import Path
import os
from sklearn.metrics import precision_recall_fscore_support as score, accuracy_score
import argparse
from sklearn.model_selection import StratifiedKFold
from tqdm import tqdm
import numpy as np
import kfp_importances
from sklearn import preprocessing

# TODO: separate code segments
# TODO: pip requirements refresh

parser = argparse.ArgumentParser()
parser.add_argument(
    "--website_list_path",
    help="path to .txt file containing urls of webpages to request (one line per webpage)",
    required=True,
)
parser.add_argument(
    "--protocol",
    dest="protocol",
    help="protocol to use for requests (tcp or quic)",
    required=True,
)
parser.add_argument(
    "--use_existing_pcaps",
    action="store_true",
    help="skip webpage requests and load from existing pcap files (False if changes made to classifier/evaluation only)",
)
parser.add_argument(
    "--test_web_bundle",
    action="store_true",
    help="use web bundles for requests (only works with quic protocol)",
)
parser.add_argument(
    "--num_samples_per_page",
    dest="num_samples_per_page",
    help="number of samples to take per webpage",
    default=25,
    type=int,
)
parser.add_argument(
    "--browser",
    dest="browser",
    help="browser to use for requests (Chrome or Firefox)",
    default="Chrome",
)
parser.add_argument(
    "--lazy_loading_off",
    action="store_true",
    help="use lazy loading attribute for requests",
)
parser.add_argument(
    "--experimental_lazy_loading",
    action="store_true",
    help="use experimental lazy loading extension for requests, required in order to enable selenium functionality for waiting for indicator element",
)
parser.add_argument(
    "--pcap_save_dir",
    dest="pcap_save_dir",
    help="directory to save pcap files to",
    default=None,
)
parser.add_argument(
    "--save_traces_features_path",
    dest="save_traces_features_path",
    help="save traces features to pickle file at specificed path so changes to classification doesn't require rerunning pcap to trace conversion",
    default=None,
)
parser.add_argument(
    "--load_traces_features_path",
    dest="load_traces_features_path",
    help="load existing traces features from pickle file at specified path, and skip all fetching and pcap actions",
    default=None,
)
parser.add_argument(
    "--classifier",
    dest="classifier",
    help="classifier to use (kfp or dfnet)",
    default="kfp",
)
parser.add_argument(
    "--extension_path",
    dest="extension_path",
    help="path to extension to load into browser before starting requests",
    default=None,
)
parser.add_argument(
    "--browser_profile_path",
    dest="browser_profile_path",
    help="path to browser profile to use for requests",
    default=None,
)

options = parser.parse_args()
if options.protocol not in ["tcp", "quic"]:
    raise ValueError("Protocol must be either 'tcp' or 'quic'")
if options.browser not in ["Chrome", "Firefox"]:
    raise ValueError("Browser must be either 'Chrome' or 'Firefox'")
if options.use_existing_pcaps and options.load_traces_features_path:
    raise ValueError("Cannot use both existing pcaps and existing traces features")
if (
    not options.use_existing_pcaps
    and not options.load_traces_features_path
    and options.pcap_save_dir is None
):
    raise ValueError(
        "Command must specify either --use_existing_pcaps or --load_traces_features_path, or specify --pcap_save_dir"
    )
if not options.classifier in ["kfp", "dfnet"]:
    raise ValueError("Classifier must be either 'kfp' or 'dfnet'")
if options.classifier == "dfnet":
    from wf_tools.classifiers.dfnet import DeepFingerprintingClassifier

browser_options = {}
if options.lazy_loading_off:
    browser_options["lazy_loading_off"].append("")
if options.experimental_lazy_loading:
    browser_options["experimental_lazy_loading"].append("")
if options.extension_path is not None:
    browser_options["extension_path"].append(options.extension_path)
if options.browser_profile_path is not None:
    browser_options["browser_profile_path"].append(options.browser_profile_path)


website_list = website_file_to_list(options.website_list_path)

# TODO: move pcap file processing to separate part
""" Get trace data"""
traces_features = []
traces_labels = []

if not options.use_existing_pcaps and (options.load_traces_features_path is None):
    if os.path.exists(options.pcap_save_dir):
        shutil.rmtree(
            options.pcap_save_dir
        )  # removes old directory folder and contents
    Path(options.pcap_save_dir).mkdir(parents=True, exist_ok=True)

if options.load_traces_features_path is None:
    for i in (barIteration := tqdm(range(options.num_samples_per_page))):
        barIteration.set_description("Number of iterations over webpage lists.")
        for site in (barPages := tqdm(website_list)):
            barPages.set_description("Web page in list.")

            domain_name = extract_domain_name(site)
            filename = options.pcap_save_dir + "/" + domain_name + str(i)

            complete = False
            while not complete:
                try:
                    if not options.use_existing_pcaps and not os.path.exists(filename):
                        url = site
                        if options.test_web_bundle:
                            url = "https://192.168.0.2:20002/" + domain_name + ".wbn"

                        sniff_packets_to_pcap_file(
                            url,
                            filename,
                            options.protocol,
                            options.test_web_bundle,
                            browser=options.browser,
                            browser_options=browser_options,
                        )

                    trace = pcap_file_to_trace(filename)

                    data_list = []
                    if options.classifier == "kfp":
                        data_list = convert_trace_to_list(trace)
                        total_features = trace_total_features(data_list)
                        data_list = total_features
                    elif options.classifier == "dfnet":
                        data_list = convert_trace_to_df_input(trace)

                    traces_features.append(data_list)
                    traces_labels.append(site)
                    complete = True

                except KeyboardInterrupt:
                    sys.exit()
                except:
                    print("Exception occured, retrying...")
                    complete = False

# save train_features and test_features to allow small changes to classifier without rerunning pcap to trace conversion
if options.save_traces_features_path is not None:
    save_object(
        (traces_features, traces_labels), options.save_traces_features_path + ".pkl"
    )

# for debugging purposes, load old features
if options.load_traces_features_path is not None:
    print("Loading existing features...")
    with open(options.load_traces_features_path, "rb") as inp:
        (traces_features, traces_labels) = pickle.load(inp)

if options.classifier == "dfnet":
    for i, trace in enumerate(traces_features):
        if len(trace) < 5000:
            traces_features[i].extend([0] * (5000 - len(trace)))
        else:
            traces_features[i] = trace[:5000]

    le = preprocessing.LabelEncoder()
    le.fit(traces_labels)
    labs = le.transform(traces_labels)
    print(np.unique(labs))
    traces_labels = labs

# TODO: refactor functionality for allowing separate train and test sets.

X = np.array(traces_features)
y = np.array(traces_labels)

# TODO: folds based on command line argument
# TODO: separate training into separate file
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

OPEN_WORLD = False
OUTPUT_IMPORTANCES = False
if OPEN_WORLD:
    f1_scores = []
    precisions = []
    recalls = []
else:
    accuracies = []

for i, (train_index, test_index) in enumerate(skf.split(X, y)):
    if options.classifier == "kfp":
        classifier = KFingerprintingClassifier(
            None, enable_nearest_neighbour=True
        )  # Specify nearest neighbours to use
    elif options.classifier == "dfnet":
        # TODO: make n_classes non hard coded
        classifier = DeepFingerprintingClassifier(
            n_features=5000, n_classes=2, epochs=3
        )

    print("Running fold " + str(i))

    X_train, X_test = X[train_index], X[test_index]
    y_train, y_test = y[train_index], y[test_index]

    classifier.fit(X_train, y_train)

    predicted = classifier.predict(X_test)

    if OUTPUT_IMPORTANCES and options.classifier == "kfp":
        kfp_importances_labels = kfp_importances.get_kfp_importances_labels()
        importances = classifier.forest_.feature_importances_
        std = np.std(
            [tree.feature_importances_ for tree in classifier.forest_.estimators_],
            axis=0,
        )
        save_importances_graph(
            importances,
            std,
            kfp_importances_labels,
            "kfp_importances_" + str(i) + ".png",
            10,
        )

    # metrics useful for open-world scenario
    if OPEN_WORLD:
        precision, recall, fscore, support = score(y_test, predicted, average="macro")
        f1_scores.append(fscore)
        precisions.append(precision)
        recalls.append(recall)
    else:
        accuracy = accuracy_score(y_test, predicted)
        accuracies.append(accuracy)

if OPEN_WORLD:
    print("Average precision of 5-fold cross-validation: " + str(np.mean(precisions)))
    print("Average recall of 5-fold cross-validation: " + str(np.mean(recalls)))
    print("Average F1 score of 5-fold cross-validation: " + str(np.mean(f1_scores)))
else:
    print("Accuracy of 5-fold cross-validation: " + str(np.mean(accuracies)))