function initViewer(slideName, caption) {
    const viewerElement = document.getElementById('openseadragon-viewer');
    if (!viewerElement) return;

    // The tile server is expected to run on port 5000
    const tileServerUrl = 'http://localhost:5000';
    const dziUrl = `${tileServerUrl}/dzi/${slideName}.dzi`;

    const viewer = OpenSeadragon({
        id: "openseadragon-viewer",
        prefixUrl: "https://cdnjs.cloudflare.com/ajax/libs/openseadragon/4.1.0/images/",
        tileSources: dziUrl,
        showNavigator: true,
        navigatorPosition: "TOP_RIGHT",
        showRotationControl: true,
        animationTime: 0.5,
        blendingTime: 0.1,
        constrainDuringPan: true,
        maxZoomPixelRatio: 2,
        visibilityRatio: 1,
        zoomPerScroll: 2,
        timeout: 120000,
    });

    // Add caption
    if (caption) {
        const captionDiv = document.createElement('div');
        captionDiv.className = 'viewer-caption';
        captionDiv.innerText = caption;
        viewerElement.parentNode.insertBefore(captionDiv, viewerElement.nextSibling);
    }
    
    window.osdViewer = viewer;
}

// Automatically initialize if the page has a data-slide attribute on the viewer
document.addEventListener("DOMContentLoaded", function() {
    const viewerElement = document.getElementById('openseadragon-viewer');
    if (viewerElement) {
        const slideName = viewerElement.getAttribute('data-slide');
        const caption = viewerElement.getAttribute('data-caption');
        if (slideName) {
            initViewer(slideName, caption);
        }
    }
});
