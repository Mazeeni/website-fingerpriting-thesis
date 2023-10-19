// a dynamic list of URLs for images/videos/etc that are whitelisted from webrequest blocking 
url_whitelist = [];

function cancelLoad(requestDetails) {
    for (let i = 0; i < url_whitelist.length; i++) {
        if (url_whitelist[i].url.includes(requestDetails.url)) {
            console.log("NOT CNACELLING :)")
            return { cancel: false };
        }
    }
    console.log(`Cancelling request: ${requestDetails.url}`);
    return { cancel: true };
}

// called before any request made for an image
browser.webRequest.onBeforeRequest.addListener(
    cancelLoad,
    {urls: ["<all_urls>"], types: ["image", "imageset", "media", "other"]},
    ["blocking"]
);

browser.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
        console.log(sender.tab ?
                    "from a content script:" + sender.tab.url :
                    "from the extension");
        if (request.unblock)
            // browser.webRequest.onBeforeRequest.removeListener(cancelLoad);
            console.log("unblocking " + request.content_url);
            url_whitelist.push(request.content_url);
            sendResponse({isUnblocked: "true"});
    }
);

function tabUpdate(tabId, changeInfo, tabInfo) {
    url_whitelist = [];
    console.log("Whitelist cleaned");

    if (changeInfo.url && !browser.webRequest.onBeforeRequest.hasListener(cancelLoad)) {
        console.log(`Tab: ${tabId} URL changed to ${changeInfo.url}`);
    }
}
  
browser.tabs.onUpdated.addListener(tabUpdate);
  