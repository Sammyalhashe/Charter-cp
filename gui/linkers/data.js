function getData() {
    var {
        PythonShell
    } = require('python-shell');
    var path = require('path');

    var options = {
        scriptPath: path.join(__dirname, '../../engine/'),
        pythonPath: '/Library/Frameworks/Python.framework/Versions/3.6/bin/python3',
        pythonOptions: ['-u']
    };

    var retData;
    var rdata = new PythonShell('data.py', options);

    var cnt = 0;
    rdata.on('message', (function(message) {
        console.log(message);
        if (cnt === 0) {
            Plotly.plot('chart-1', [{
                y: [message],
                type: 'line'
            }]);
        } else {
            Plotly.extendTraces('chart-1', {
                y: [
                    [message]
                ]
            }, [0]);
            if (cnt > 500) {
                Plotly.relayout('chart-1', {
                    xaxis: {
                        range: [cnt - 500, cnt]
                    }
                });
            }
        }

        cnt++;
    }));
}

function getData2() {

    var {
        PythonShell
    } = require('python-shell');
    var path = require('path');
    var options = {
        scriptPath: path.join(__dirname, '../../engine/'),
        pythonPath: '/Library/Frameworks/Python.framework/Versions/3.6/bin/python3',
        pythonOptions: ['-u']
    };
}

getData();


//Plotly.plot('chart-1', [{
//y: [getData()],
//type: 'line'
//}]);

//var cnt = 0;
//setInterval(function() {
//Plotly.extendTraces('chart-1', {
//y: [
//[getData()]
//]
//}, [0]);
//cnt++;

//if (cnt > 500) {
//Plotly.relayout('chart-1', {
//xaxis: {
//range: [cnt - 500, cnt]
//}
//});
//}
//}, 15);
