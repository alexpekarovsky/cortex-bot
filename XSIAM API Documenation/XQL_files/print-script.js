function isolateSvgs(element) {
    const svgNodes = Array.from(element.querySelectorAll(".ft-svg-container"))
    svgNodes.forEach(svgNode => {
        Array.from(svgNode.children).forEach(svg => {
            let img = document.createElement("img");
            img.src = `data:image/svg+xml,${encodeURIComponent(new XMLSerializer().serializeToString(svg))}`;
            svgNode.replaceChild(img, svg);
        })
    })
}

if (window.Paged === undefined) {
    document.addEventListener("DOMContentLoaded", function () {
        isolateSvgs(document)
        setTimeout(function () {
            window.print()
        }, 300)
    }, false)
} else {
    class PrintHandler extends Paged.Handler {
        afterPreview(pages) {
            setTimeout(function () {
                window.print()
            }, 300)
        }

        beforeParsed(content) {
            isolateSvgs(content)
        }
    }

    Paged.registerHandlers(PrintHandler)
}
