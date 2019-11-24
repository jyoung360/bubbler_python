'use strict';

var chart = realTimeChartMulti()
    .title("Raw Bubble Data")
    .yTitle("Analog Signal")
    .xTitle("Time")
    .yDomain([1600,2400])
    .border(true)
    .width(600)
    .height(350);

var chartDiv = d3.select("#viewDiv").append("div")
    .attr("id", "chartDiv")
    .call(chart);

d3.select("#debug").on("change", function() {
  var state = d3.select(this).property("checked")
  chart.debug(state);
})

d3.select("#halt").on("change", function() {
  var state = d3.select(this).property("checked")
  chart.halt(state);
})


var tX = 5; // time constant, multiple of one second
var meanMs = 1000 * tX, // milliseconds
    dev = 200 * tX; // std dev

// define time scale
var timeScale = d3.scaleLinear()
    .domain([300 * tX, 1700 * tX])
    .range([300 * tX, 1700 * tX])
    .clamp(true);

// var color = d3.scale.category10();

// in a normal use case, real time data would arrive through the network or some other mechanism
var d = -1;
var shapes = ["rect", "circle"];
var timeout = 0;

function connect() {
  var ws = new WebSocket("ws://localhost:5678/");
  ws.onopen = function() {
    console.log('opened websocket connection')
    ws.send({ foo: 'bar'});
    setInterval(() => {
      ws.send({ foo: 'bar'});
    }, 60000);
  };

  ws.onmessage = function (event) {
    const data = JSON.parse(event.data);
    if(data.messageType === 'fake') {
      var finalData = data.data.map((d)=>{
          d.date = parseDate(d.date);
          d.value = +d.value;
          return d;
      }).filter((d)=>{
        return d.date >= new Date('2019-11-15T00:00:00');
      }).sort((a, b) => {
        return a.date - b.date
      });

      const tmpData = finalData.slice(0);
      const mappedDates = {};
      tmpData.forEach((d) => {
        // const hourDate = new Date(d.date.getFullYear(), d.date.getMonth(), d.date.getDate(), d.date.getHours());
        const hourDate = `${d.date.getFullYear()}-${d.date.getMonth()+1}-${d.date.getDate()} ${d.date.getHours()}`;
        mappedDates[hourDate] = mappedDates[hourDate] || 0;
        mappedDates[hourDate] += d.value;
      });

      const newFinalData = [];
      const parser = d3.timeParse("%Y-%m-%d %H");
      for(var i in mappedDates) {
        newFinalData.push({
          date: parser(i),
          value: mappedDates[i]
        })
      }
      finalData = newFinalData;

      const total = finalData.reduce((accumulator, currentValue) => {
        return accumulator + currentValue.value;
      }, 0);

      var logElem = document.querySelector("#total_bubbles");
      logElem.value = total;

      const dates = [finalData[0].date, finalData[finalData.length-1].date];
      const dates2 = finalData.map(function(d) { return d.date; });
      x.domain(d3.extent(finalData, function(d) { return d.date; }));
      y.domain([0, d3.max(finalData, function(d) { return d.value; })]);

      svg.select(".line")
        .attr("d", valueline(finalData)); 

      svg.select(".x.axis") // change the x axis
          .call(xAxis)
          .selectAll("text")
          .style("text-anchor", "end")
          .attr("dx", "-.8em")
          .attr("dy", "-.55em")
          .attr("transform", "rotate(-90)" );

      svg.select(".y.axis") // change the y axis
          .call(yAxis)
          .append("text")
          .attr("transform", "rotate(-90)")
    }
    else {
      data.forEach((d,i) => {
          var now = new Date(d.date+"Z");
          var obj;
          obj = {
              time: now,
              opacity: 1,
              category: "Category",
              analog: d.voltage,
              type: "circle",
              size: 2,
          };

          chart.datum(obj);   
      });
    }
  };

  ws.onclose = function(e) {
    console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
    setTimeout(function() {
      connect();
    }, 1000);
  };

  ws.onerror = function(err) {
    console.error('Socket encountered error: ', err.message, 'Closing socket');
    ws.close();
  };
}

connect();

var valueline = d3.line()
    .x(function(d) { return x(d.date); })
    .y(function(d) { return y(d.value); })
    .curve(d3.curveMonotoneX);

var margin = {top: 40, right: 20, bottom: 70, left: 80},
    width = 700 - margin.left - margin.right,
    height = 350 - margin.top - margin.bottom;

var	parseDate = d3.timeParse("%Y-%m-%d %H:%M:%S");
var svg = d3.select("#barDiv").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .style("border", function(d) { 
      return "1px solid lightgray"; 
    })
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

svg.append("text")
  .attr("class", "chartTitle")
  .attr("x", width / 2)
  .attr("y", -20)
  .attr("dy", ".71em")
  .text(function(d) { 
    return 'Bubbles Over Time'; 
  });

svg.append("text")
  .attr("class", "title")
  .attr("transform", "rotate(-90)")
  .attr("x", -height + 50)
  .attr("y", -margin.left + 15) //-35
  .attr("dy", ".71em")
  .text(function(d) { 
    return 'Bubbles per hour'; 
  });

var line = svg.append("path")
  .attr("class", "line")  
  .attr("d", valueline([])); 

var x = d3.scaleTime().rangeRound([0, width])
var y = d3.scaleLinear().rangeRound([height, 0]);
var xAxis = d3.axisBottom(x)
              .ticks(d3.timeHour.every(4))
              .tickFormat((d3.timeFormat("%m/%d %H:%M")));

var yAxis = d3.axisLeft(y).ticks(10);

svg.append("g")
  .attr("class", "x axis")
  .attr("transform", "translate(0," + height + ")")
  .call(xAxis)
  .selectAll("text")
  .style("text-anchor", "end")
  .attr("dx", "-.8em")
  .attr("dy", "-.55em")
  .attr("transform", "rotate(-90)" );

svg.append("g")
  .attr("class", "y axis")
  .call(yAxis)
  .append("text")
  .attr("transform", "rotate(-90)")

const average_bubble_size = document.querySelector('#average_bubble_size');
const liquid_volume = document.querySelector('#liquid_volume');
const total_bubbles = document.querySelector("#total_bubbles");
average_bubble_size.onchange = calculateValues;
liquid_volume.onchange = calculateValues;
total_bubbles.onchange = calculateValues;
function calculateValues(e) {
  const molarVolume = 22.4;
  const molarMassCO2 = 44.01;
  const molarMassEthanol = 46.07;
  const totalBubbles = document.querySelector("#total_bubbles").value;
  const totalVolume = document.querySelector("#liquid_volume").value;
  const bubbleVolume = document.querySelector("#average_bubble_size").value;
  const pressureInitial = 101.3;
  const pressureFinal = 101.3;
  const tempInitial = 273.15;
  const tempFinal = 298;
  const finalVolume = totalBubbles * bubbleVolume/1000;

  const standardVolume = (pressureFinal * finalVolume * tempInitial)/(pressureInitial * tempFinal);
  const moles = standardVolume/molarVolume;
  const massCO2 = molarMassCO2 * moles;
  const massEthanol = molarMassEthanol * moles;
  const percentEthanol = (massEthanol / totalVolume)*100;
  document.querySelector("#total_volume").value = finalVolume.toFixed(2);
  document.querySelector("#stp_volume").value = standardVolume.toFixed(2);
  document.querySelector("#moles").value = moles.toFixed(2);
  document.querySelector("#mass_co2").value = massCO2.toFixed(2);
  document.querySelector("#mass_ethanol").value = massEthanol.toFixed(2);
  document.querySelector("#alcohol_percent").value = percentEthanol.toFixed(2);
};

function handleChange(e) {
  log.textContent = `The field's value is
      ${e.target.value.length} character(s) long.`;
}