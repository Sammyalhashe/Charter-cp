/*
 * Set up zerorpc as a client
 */
var plotters = require("./plotters.js")
var zerorpc = require("zerorpc")
let client = new zerorpc.Client()
client.connect("tcp://0.0.0.0:4242")

/*
 * This object contains all functionality for plotting
 * Functions include: collect, stop, clear, downloadData, and init
 */
var plottingFuncs = {
    /*
     * This property holds all data while collecting, as well as metadata
     * useful during the process.
     * Such data includes: data for each trace, and the names of the traces
     */
    data: {},
    /*
     * If there are multiple charts (which may be the plan), then this property
     * keeps tab on which chart should be updated
     */
    activeChart: "chart-2",
    /*
     * This property is useful for knowing if the chart should be updating
     * data at a time
     */
    is_on: false,
    /*
     * This function takes whatever is in the data property, and parses the
     * result into a funal .csv file
     */
    downloadData: function() {
        if (Object.getOwnPropertyNames(this.data).length !== 0) {
            let data_csv = ""
            let indexes = {}
            let j = 0
            for (let i in this.data) {
                indexes[i] = j
                j++
                data_csv += i.toString() + ","
            }
            data_csv = data_csv.slice(0, -1)
            data_csv += "\n"
            var len
            for (let i in this.data) {
                len = this.data[i].length
                break
            }
            for (var c = 0; c < len; c++) {
                let currArr = []
                for (var k = 0; k < j + 1; k++) {
                    currArr[k] = ""
                }
                for (let i in indexes) {
                    let index = indexes[i]
                    currArr[index] = this.data[i][c]
                }
                data_csv += currArr.join().slice(0, -1) + "\n"
            }
            var hiddenElement = document.createElement("a")
            hiddenElement.href =
                "data:text/csv;charset=utf-8," + encodeURI(data_csv)
            hiddenElement.target = "_blank"
            hiddenElement.download = "data.csv"
            hiddenElement.click()
            hiddenElement.parentElement.removeChild(hiddenElement)
        } else {
            alert("No data available to download")
        }
    },
    /*
     * This function sets up the chart initially
     */
    init: function(chart = "chart-2") {
        plotters.init_chart(chart)
        this.activeChart = chart
    },
    /*
     * This is the function that handles the data collection
     * It invokes the backend every 15ms to recieve data
     */
    collect: function(channels = "1") {
        var cnt = 0
        this.is_on = true
        var plotter
        plotter = setInterval(() => {
            client.invoke("getData", "1 2 3", (err, res, more) => {
                if (err) {
                    console.log(err)
                } else {
                    if (this.is_on === true) {
                        if (res !== undefined) {
                            if (cnt === 0) {
                                for (var i = 0; i < res.length; i++) {
                                    plotters.plot_first(
                                        res[0][i],
                                        this.activeChart,
                                        res[1][i]
                                    )
                                    this.data[res[1][i]] = []
                                    this.data[res[1][i]].push(res[0][i])
                                    if (!this.data["traces"]) {
                                        this.data["traces"] = []
                                    }
                                    this.data.traces.push(res[1][i])
                                }
                            } else {
                                for (var i = 0; i < res.length; i++) {
                                    plotters.plot_second(
                                        res[0][i],
                                        this.activeChart,
                                        (traces = [i])
                                    )
                                    this.data[res[1][i]].push(res[0][i])
                                }
                                if (cnt > 500) {
                                    Plotly.relayout(this.activeChart, {
                                        xaxis: {
                                            range: [cnt - 500, cnt],
                                        },
                                    })
                                }
                            }
                        }
                        cnt++
                    } else {
                        clearInterval(plotter)
                    }
                }
            })
        }, 250)
    },

    /*
     * This function stops the data collection
     */
    stop: function() {
        this.is_on = false
    },
    /*
     * This function clears the data in the data propety
     */
    clear: function() {
        if (Object.getOwnPropertyNames(this.data).length !== 0 && !this.is_on) {
            for (var i = this.data["traces"].length - 1; i >= 0; i--) {
                if ("traces" in this.data) {
                    Plotly.deleteTraces(this.activeChart, i)
                }
            }
            this.data = {}
        } else {
            if (this.is_on) {
                alert("Stop Recording before you clear")
            }
        }
    },
}

// initial setup
plottingFuncs.init()

/*
 * Setting up the click handlers for the buttons on the gui
 */
document.querySelector("#startButton").addEventListener("click", () => {
    plottingFuncs.collect()
})

document.querySelector("#stopButton").addEventListener("click", () => {
    plottingFuncs.stop()
})

document.querySelector("#saveButton").addEventListener("click", () => {
    plottingFuncs.downloadData()
})

document.querySelector("#clearButton").addEventListener("click", () => {
    plottingFuncs.clear()
})
