import React from 'react';

import LoadingComponent from './loading';

export default function({currentSelection}){
	let content = ''
	if(currentSelection == null){
		content = <LoadingComponent />;
	}else{
		// create inputs
	}

	return(
		<div className="box">
	        <div className="box__header">
	          	<h3 className="box__text--title">Available entities</h3>
	        </div>
	        <div id="entitySelector" className="box__content">
	          	{content}
	        </div>
      	</div>
	);
}