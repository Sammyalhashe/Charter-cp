function init_chart(chart) {
    Plotly.newPlot(chart);
}

function plot_first(message, chart, trace_name) {
    Plotly.plot(chart, [{
        y: [message],
        type: 'line',
        name: trace_name
    }]);
}

function plot_second(message, chart, traces=[0]) {
    Plotly.extendTraces(chart, {
        y: [
            [message]
        ],
    }, traces);
}


module.exports = {
    plot_first: plot_first,
    plot_second: plot_second,
    init_chart: init_chart
};
