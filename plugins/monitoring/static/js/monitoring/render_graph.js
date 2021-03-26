var render_graph = function(element_id, data, type){

    if (!type){
        type = 'bar';
    }
    var config = {
        bindto: document.getElementById(element_id),
        data: {
            columns: data,
            type: type,
            x: 'x',
            xFormat: '%Y-%m-%d %H:%M:%S'
        },
        zoom: {
            enabled:true
        },
        axis: {
            x: {
                type: 'timeseries',
                tick: {format: '%Y-%m-%d %H:%M', rotate: 45}
            },
            y: {
                tick: {format: d3.format(',')}
            }
        },
        grid: {
            y: {show: true}
        },
        legend: {
            show: false
        },
    }

    if (type == 'line') {
        config['point'] = {show: false};
    }

    c3.generate(config)

}
