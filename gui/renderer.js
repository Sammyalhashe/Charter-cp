// This file is required by the index.html file and will
// be executed in the renderer process for that window.
// All of the Node.js APIs are available in this process.

function getData(argument) {
    return Math.random();
}

Plotly.plot('chart-1', [{
    y: [getData()],
    type: 'line'
}]);

var cnt = 0;
setInterval(function() {
    Plotly.extendTraces('chart-1', {
        y: [
            [getData()]
        ]
    }, [0]);
    cnt++;

    if (cnt > 500) {
        Plotly.relayout('chart-1', {
            xaxis: {
                range: [cnt - 500, cnt]
            }
        });
    }
}, 15);
