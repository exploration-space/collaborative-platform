/*import React from "react";
import { render } from "react-dom";
import App from "./components/App";

render(<App />, document.getElementById('react-root'));*/

//alert('hi');
import Chart from 'chart.js';

function toggle(e){
  e.addEventListener('click',evt=>{
    let entity = e.parentNode.parentNode;
    entity.classList.toggle('expanded');
  })
}

Array
  .from(document.getElementsByClassName('entitySummary'))
  .forEach(toggle)

function renderChart(node){
	const id = node.id;
	const data_str = node.attributes['data'].value,
		  data = JSON.parse(data_str)['data'];

	console.log(data)

	node.setAttribute('height', 100 + (25*data.length))

	const ctx = document.getElementById(id).getContext('2d');
	const myChart = new Chart(ctx, {
	    type: 'horizontalBar',
	    data: {
	        labels: data.map(x=>x[0]),
	        datasets: [{
	            label: '# of ocurrencies',
	            data: data.map(x=>x[1]),
	            borderWidth: 1
	        }]
	    },
	    options: {
	    	responsive: false,
	        scales: {
	            xAxes: [{
	                ticks: {
	                    beginAtZero: true
	                }
	            }],
	        }
	    }
	});
}

Array
  .from(document.getElementsByClassName('chartContainer'))
  .forEach(renderChart)