/* Module: HistoryView
 * Module for displaying the document history.
 *
 * Publishes:
 * - none
 *
 * Listens:
 * - panel/display_options
 * */
import AjaxCalls from './utilities/ajax.js';
import ColorScheme from './utilities/color.js';

var HistoryView = function(args){
	let self = null;
	let ajaxCalls = AjaxCalls();
	const canvasHeight=60;

	let versions = [];

	function _init(args){
		const obj = {
			suscribe: ()=>_notimplemented('suscribe'),
			publish: ()=>_notimplemented('publish'),
		};

		// Add instance to the pub/sub channel
		if(args.hasOwnProperty('channel'))
			args.channel.addToChannel(obj);

		const history_div = document.getElementById('history'),
			history_container = document.getElementById('history-container');

		history_div.addEventListener('mouseover', e=>{
			history_div.classList.add('hovered');
			document.getElementById('editor').classList.add('lowered');
		});

		history_container.addEventListener('mouseleave', e=>{
			history_div.classList.remove('hovered')
			document.getElementById('editor').classList.remove('lowered');
		});


		ajaxCalls.getHistory(window.project_id, window.file_id, window.file_version).then(response=>{
			if(response.success === true){
				versions = response.content.data;
				_updateVersions();
				_drawDetails();
			}
		});
		obj.subscribe('file/saved', _handleFileSaved);

		args.channel.getSubscribers()


		//obj.suscribe('popup/render', _handleRenderPopup);

		self = obj;
		return obj;
	}

	function _handleFileSaved(newVersion){
		ajaxCalls.getHistory(window.project_id, window.file_id, newVersion).then(response=>{
			if(response.success === true){
				versions = response.content.data;
				_updateVersions();
				_drawDetails();
			}
		});
	}

	function _renderVersions(){
		const client_width = document
			.getElementById('versions')
			.getBoundingClientRect().width - 10;

		const getTimestamp = date=>date.getTime()+10000*date.getHours()+100*date.getMinutes();

		const dates = versions.map(t=>getTimestamp(new Date(t.timestamp))),
			min = Math.min(...dates),
			max = Math.max(1, Math.max(...dates) - min);

		for(let version of versions){
			const date = new Date(version.timestamp),
				timestamp = getTimestamp(date),
				offset = client_width * (timestamp-min) / max;

			const element = document.createElement('a');
	        element.setAttribute('class','version');
	        element.setAttribute('href',version.url);
	        element.style.setProperty('left', `${offset}px`);

	        if(version.version == +window.file_version)
	        	element.style.setProperty('background-color', '#00b3b0');

	        element.addEventListener('mouseenter', 
	        	evt=>_handleVersionHoverIn(evt,version));
	        element.addEventListener('mouseout', 
	        	evt=>_handleVersionHoverOut(evt,version));

	        console.info('Retrieved version', version.timestamp)

	        document.getElementById('versions').appendChild(element);
		}
	}

	function _drawDetails(){
		const client_width = document
			.getElementById('history')
			.getBoundingClientRect().width - 10;

		const getTimestamp = date=>date.getTime()+10000*date.getHours()+100*date.getMinutes();

		const canvas = document.getElementById('history').getElementsByTagName('canvas')[0],
			canvasCtx = canvas.getContext('2d'),
			dates = versions.map(t=>getTimestamp(new Date(t.timestamp))),
			minDate = Math.min(...dates),
			maxDate = Math.max(1, Math.max(...dates) - minDate),
			maxUncertainty = 
				Math.max(...versions.map(x=>x.imprecision + x.credibility + x.ignorance + x.incompleteness)),
			heightScale = d3.scaleLinear().domain([0,maxUncertainty]).range([0,canvasHeight]);

		canvas.height = 60;
		canvas.width = client_width+1;

		const pointsTop = [], pointsBottom = [];

		for(let version of versions){
			const date = new Date(version.timestamp),
				timestamp = getTimestamp(date),
				offset = client_width * (timestamp-minDate) / maxDate,
				totalUncertainty = 
					version.imprecision + version.credibility + version.ignorance + version.incompleteness,
				height = heightScale(totalUncertainty);

			pointsTop.push([Math.max(5,offset),(canvasHeight-height)/2])
			pointsBottom.push([Math.max(5,offset),height+(canvasHeight-height)/2])

			//canvasCtx.fillStyle = ;
			//canvasCtx.fillRect(offset, (canvasHeight-height)/2, 10, height);
		}

		for(let point of pointsTop)
			canvasCtx.lineTo(point[0], point[1]);
		for(let idx = pointsBottom.length-1; idx>=0; idx--)
			canvasCtx.lineTo(pointsBottom[idx][0], pointsBottom[idx][1]);
		canvasCtx.lineTo(pointsTop[0][0], pointsTop[0][1]);

	    canvasCtx.fillStyle = `rgba(49, 130, 154, 0.07)`;
	    canvasCtx.strokeStyle = `rgb(49, 130, 154)`;

	        canvasCtx.fill();
	        canvasCtx.stroke();
	}

	function drawDetails(){
	    const timestamps = versions.map(x=>new Date(x.timestamp)),
	        width = Math.trunc($('div#history canvas').width()+1),
	        height = canvasHeight,
	        max = Math.max(...Array.prototype.concat(...versions.map(x=>([
	                x.imprecision,
	                x.credibility,
	                x.ignorance,
	                x.incompleteness
	            ])))),
	        yScale = d3.scaleLinear().domain([0,max]).range([0,height]),
	        xScale = d3.scaleTime()
	            .domain([Math.min(...timestamps),Math.max(...timestamps)])
	            .range([0,width]),
	        canvasCtx = $('div#history canvas')[0].getContext('2d');

	    const renderVersions = (uncertainty, color)=>{
	        canvasCtx.beginPath();
	        canvasCtx.moveTo(0,height);

	        for(let d of versions){
	        	console.log(xScale(new Date(d.timestamp)))
	            canvasCtx.lineTo(xScale(new Date(d.timestamp)),height-yScale(d[uncertainty]));
	        }

	        const last = versions[versions.length-1];
	        canvasCtx.lineTo(xScale(new Date(...last.timestamp.split('-'))),height);
	        canvasCtx.lineTo(0,height);

	        canvasCtx.fillStyle = `rgba(${color[0]},${color[1]},${color[2]},0.07)`;
	        canvasCtx.strokeStyle = `rgb(${color[0]},${color[1]},${color[2]})`;

	        canvasCtx.fill();
	        canvasCtx.stroke();
	    }

	    renderVersions('imprecision',[148,15,137]);
	    renderVersions('credibility',[218,136,21]);
	    renderVersions('ignorance',[23,85,141]);
	    renderVersions('incompleteness',[174,210,21]);

	    document.getElementById('history').classList.remove('hovered')
	}

	function _handleVersionHoverIn(evt, timestamp){
	    const popup = document.getElementById('history-popup');
	    const max = Math.max(timestamp.imprecision,timestamp.incompleteness,
	        timestamp.ignorance,timestamp.credibility),
	        xScale = d=>6*d/max,
	        style = dim => `width:${xScale(timestamp[dim])}em; margin-left: calc(100% - ${xScale(timestamp[dim])}em); background-color: ${ColorScheme.scheme.taxonomy[dim].color};`;

	    popup.innerHTML=`
	      Version ${timestamp.version}<br>
	      ${(new Date(timestamp.timestamp)).toUTCString()}<br>
	      Contributor : ${timestamp.contributor}<br>
	      <div class="content">
	      <span>
	        Imprecision<br/>
	        Incompleteness<br/>
	        Credibility<br/>
	        Ignorance<br/>
	      </span>
	      <span>
		      <span>
		        <span class="color uncertainty" author="me" title="high"
		            style="${style('imprecision')}" 
		            category="imprecision" cert="high"></span></br>
		        <span class="color uncertainty" author="me" title="high" 
		            style="${style('incompleteness')}" 
		            category="incompleteness" cert="high"></span></br>
		        <span class="color uncertainty" author="me" title="high" 
		            style="${style('ignorance')}" 
		            category="ignorance" cert="high"></span></br>
		        <span class="color uncertainty" author="me" title="high" 
		            style="${style('credibility')}" 
		            category="credibility" cert="high"></span></br>
		      </span>
		      <span>
		        ${timestamp.imprecision}</br> 
		        ${timestamp.incompleteness}</br> 
		        ${timestamp.ignorance}</br> 
		        ${timestamp.credibility}</br>
		      </span>
		   </span>
	      </div>
	    `;

	    popup.style.setProperty('display','block');

	    const popupWidth = document.getElementById('history-popup').clientWidth,
	    	historyWidth = document.getElementById('history').clientWidth;
	    let left = ((+evt.target.style.left.slice(0,-2)) - popupWidth/2);

	    left = Math.max(0, left);

	    left = Math.min(left, historyWidth - popupWidth);

	    popup.style.left = left + 'px';


	}

    /*<span class="color variation" author="me" title="high" 
	        ${timestamp.variation}
        style="width:${xScale(timestamp.variation)}em;" category="variation" cert="high"></span></br>*/

	function _handleVersionHoverOut(event, timestamp){
	    document.getElementById('history-popup').style.setProperty('display','none');
	}

	function _updateVersions(){
		document.getElementById('versions').innerHTML = '';
		_renderVersions();
	}

	function _renderHistoryGraph(){

	}

	function _updateGraph(){

	}

	function _displayPopup(args){
		_notimplemented('_displayPopup')();
	}

	function _hidePopup(args){
		_notimplemented('_hidePopup')();
	}

	function _notimplemented(method){
		return function(){throw(new Error('Not implemented : '+method))};
	}

	return _init(args);
};

export default HistoryView;
