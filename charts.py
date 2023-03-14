import chevron
import numpy as np
from IPython.display import display, IFrame
import base64
import json 

def echartDS(d, names):
    colors = {}
    xvals = {}
    dataset = []

    for i,r in enumerate(d):
        xvals[r[0]] = 1

    for i,r in enumerate(d):
        if r[1] not in colors:
            colors[r[1]]={}
        colors[r[1]][r[0]] = r[2]

    dataset.append([names[0]] + list(colors.keys()))
    for x in xvals.keys():
        row = [x]
        for color in colors.keys():
            if x not in colors[color]:
                row.append(0)
            else:
                row.append(colors[color][x])
        dataset.append(row)    
    return dataset


def get_html(data):

    base = """
    <!DOCTYPE html>
    <html lang="en" style="height: 100%">
    <head>
    <meta charset="utf-8">
    </head>
    <body style="height: 100%; margin: 0">
    <div id="container" style="height: 100%"></div>
    <script type="text/javascript" src="https://fastly.jsdelivr.net/npm/echarts@5.4.1/dist/echarts.min.js"></script>
    <script type="text/javascript">
    var dom = document.getElementById('container');
    var myChart = echarts.init(dom, null, {
        renderer: 'canvas',
        useDirtyRect: false
    });

    var dataframe = {{dataframe}};
    var app = {};
    var myoptions = {{options}};
    var option;

    var yAxis = { type: 'category' , axisLabel: { interval: 0, rotate:  myoptions.yrotate || 0 } };
    var xAxis = {  axisLabel: { interval: 0, rotate: myoptions.xrotate || 0 } };
 
    if(myoptions.vertical == 'yes'){ 
        tmp = xAxis;
        xAxis = yAxis
        yAxis = tmp
    }

    option = {
        title: {
            text: myoptions.title || '',
            subtext: myoptions.subtitle || ''
        },
        legend: {
            top: 5,
        }, 
        tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'shadow'
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },

        dataset: {
            source:dataframe
        },
        yAxis: yAxis,
        xAxis: xAxis,
        
        series: dataframe[0].slice(1).map((bar_name,bar_index)=>({ 
            type: myoptions.type || 'bar',  
            radius: ['40%', '70%'],
            itemStyle: {
                borderRadius:  parseInt(myoptions.itemBorderRadius) || 3,
                borderColor: '#fff',
                borderWidth:  parseInt(myoptions.itemBorderWidth) || 1
            },
            stack: myoptions.stack == 'yes' || false ,
            barGap: myoptions.barGap || '1%',
            barCategoryGap: myoptions.barCategoryGap || '1%',

            label: {
                show: true,
                formatter: function(params) {
                    let v = params.value[bar_index+1]
                    return v==0?'':v 
                },
                fontSize: myoptions.fontSize || 12,
                rotate: myoptions.rotate || 0
            },
        }))
    };

    if(myoptions.type=="pie"){
        option.yAxis=undefined
        option.xAxis=undefined
    }
    
    if (option && typeof option === 'object') {
        myChart.setOption(option);
    }

    window.addEventListener('resize', myChart.resize);
    </script>
    </body>
    </html>
    """
    output = chevron.render(base, data)
    #print(output)
    with open(f'./temp.html', 'w') as fhandle:
        fhandle.write(output)
    message_bytes = output.encode('utf-8')
    bout=str(base64.b64encode(message_bytes), 'UTF-8')
    width = data["width"] if "width" in data else 800
    height = data["height"] if "height" in data else 600
    
    return IFrame(src=f'data:text/html;base64,{bout}', width=width, height=height)  


def bar(ans, names,magic_args):
    opt = {
        'fontSize': 9,
        'barCategoryGap':'5%',
     }
    
    for k,v in magic_args.items():
        opt[k]=v
        
    if "width" not in magic_args:
        magic_args["width"]=800

    if "height" not in magic_args:
        magic_args["height"]=800
            
    return get_html({
    'options':opt,
    'dataframe': echartDS(ans, names),
    'width':magic_args["width"], 
    'height':magic_args["height"]
    })



from IPython.core import magic_arguments
from IPython.core import magic_arguments
from IPython.core.magic import (register_line_magic, register_cell_magic)
import pandas as pd
from IPython import get_ipython

__ans = []
__curs = None
__df = None
con = None

import sqlite3
#con = sqlite3.connect("./mba.db")

def bindSql(c):
    global con
    con = c
    
import re
def cleanit(sentence):
    sentence = " ".join(re.split("\s+", sentence, flags=re.UNICODE))
    sentence = re.sub("^\s+|\s+$", "", sentence, flags=re.UNICODE)
    return sentence


@register_cell_magic
def sql(line, cell):
    magic_args = {kv.split("=")[0] : kv.split("=")[1]  for kv in cleanit(line).split(" ") }
    #print(magic_args)
    global con
    global __ans, __curs, __df
    names = []
    for cmd in cell.split(";"):
        __curs = con.execute(cmd)
        __ans = (__curs.fetchall())
        if __curs.description:
            names = list(map(lambda x: x[0], __curs.description))
            __df = pd.DataFrame(data= __ans, columns = names)
        else:
            names
            __df = pd.DataFrame(data= __ans)
    if len(__ans) > 0:
        if magic_args["show"] == "raw":
            return __ans
        elif magic_args["show"] == "graph":
            return bar(__ans, names, magic_args)
        else:
            return __df
    else:
        return "(empty set)"
