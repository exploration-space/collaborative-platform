import React from 'react';
import * as d3 from 'd3';

class App extends React.Component {
    constructor(props){
        super(props);
        this.state = {}
    }

    componentDidMount(){}

    shouldComponentUpdate(nextProps, nextState){
    	const a = 'ja';
    	return true;            
    }

    componentDidUpdate(prevProps, prevState, snapshot){}

    render(){
        console.log(d3)
        return (
        	<div id='app' >
        		<h1>Example front end app</h1>
                <div id='squares-container'>
                    {d3.schemePastel1.map(color=>
                        <span className='square'
                            key={color}
                            style={{backgroundColor:color, 
                                'marginRight':'30px',
                                display:'inline-block',
                                width:'20px', height:'20px'}}>
                        </span>)
                    }
                </div>
        	</div>
        );
    }
}

export default App;