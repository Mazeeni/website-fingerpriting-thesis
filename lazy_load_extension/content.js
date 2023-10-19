// this variable sets the proportion of images that are lazy loaded, a lower value means more images are loaded immediately, at the expense of bandwidth and page load time
const proportion_lazy_loaded = 0.75;

function shuffle_in_place(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
}

async function wait_seconds_and_unblock(secs) {
    const images = document.querySelectorAll('img');
    for (let i = 0; i < images.length; i++) {
        browser.runtime.sendMessage({unblock: "true", "content_url": images[i].getAttribute('data-src')}, function(response) {
            console.log(response.isUnblocked);
        });
        images[i].setAttribute('src', images[i].getAttribute('data-src'));
    }

    const source_elems = document.querySelectorAll('source');
    for (let i = 0; i < source_elems.length; i++) {
        browser.runtime.sendMessage({unblock: "true", "content_url": source_elems[i].getAttribute('data-srcset')}, function(response) {
            console.log(response.isUnblocked);
        });
        source_elems[i].setAttribute('srcset', source_elems[i].getAttribute('data-srcset'));
    }

    // for selenium, wait 5 seconds before appending indicator element
    // Indicator element used for indicating to selenium that the page has finished loading
    await new Promise(r => setTimeout(r, 5000));

    // indicator element is appended after the image srcs are changed
    const divs = document.querySelectorAll('div');
    const indicatorElem = document.createElement("p");
    indicatorElem.setAttribute("id", "indicatorElem");
    divs[0].appendChild(indicatorElem);

    // visual debugger
    // things = document.querySelectorAll('div');
    // for (let i = 0; i < things.length; i++) {
    //     // console.log(things[i])
    //     things[i].setAttribute("style", "background-color: red;");
    // }
}

function image_handler(mutationList, observer) {
    mutationList.forEach((mutation) => {
        // check if mutation is an image, video, audio, or image set
        if (mutation.type === "childList" && mutation.addedNodes.length > 0 ) {
            for (let i = 0; i < mutation.addedNodes.length; i++) {
                if (["IMG", "VIDEO", "PICTURE"].includes(mutation.addedNodes[i].tagName)) {
                    mutation.addedNodes[i].setAttribute('data-src', mutation.addedNodes[i].src);
                    mutation.addedNodes[i].setAttribute('src', '');
                    if (Math.random() < 0.25) {
                        mutation.addedNodes[i].setAttribute('loading', 'eager');
                    } else {
                        mutation.addedNodes[i].setAttribute('loading', 'lazy');
                    }
                    browser.runtime.sendMessage({unblock: "true", "content_url": mutation.addedNodes[i].getAttribute('data-src')}, function(response) {
                        console.log(response.isUnblocked);
                    });
                    mutation.addedNodes[i].setAttribute('src', mutation.addedNodes[i].getAttribute('data-src'));
                }
            }
        }
        // mutation.type === "attributes") { ...
    });
}    

function setup_mutation_observer() {
    const targetNode = document.getElementsByTagName("body")[0];
    const options = { attributes: true, childList: true, subtree: true };

    const observer = new MutationObserver(image_handler);
    observer.observe(targetNode, options);
}

document.addEventListener('DOMContentLoaded', function() {
    setup_mutation_observer();
    
    var imagess = document.querySelectorAll('img');
    var images = Array.from(imagess);
    shuffle_in_place(images);

    for (let i = 0; i < images.length; i++) {
        images[i].setAttribute('data-src', images[i].src);
        images[i].setAttribute('src', '');
    }

    for (let i = 0; i < Math.floor(images.length * proportion_lazy_loaded); i++) {
        images[i].setAttribute('loading', 'lazy');
    }

    for (let i = Math.floor(images.length * proportion_lazy_loaded); i < images.length; i++) {
        images[i].setAttribute('loading', 'eager');
    }

    var source_elemss = document.querySelectorAll('source');
    var source_elems = Array.from(source_elemss);
    shuffle_in_place(source_elems);

    for (let i = 0; i < source_elems.length; i++) {
        source_elems[i].setAttribute('data-srcset', source_elems[i].src);
        source_elems[i].setAttribute('srcset', '');
    }

    for (let i = 0; i < Math.floor(source_elems.length * proportion_lazy_loaded); i++) {
        source_elems[i].setAttribute('loading', 'lazy');
    }

    for (let i = Math.floor(source_elems.length * proportion_lazy_loaded); i < source_elems.length; i++) {
        source_elems[i].setAttribute('loading', 'eager');
    }

    wait_seconds_and_unblock(5);
});