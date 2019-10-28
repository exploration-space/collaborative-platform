/*import React from "react";
import { render } from "react-dom";
import App from "./components/App";

render(<App />, document.getElementById('react-root'));*/

//alert('hi');

function toggle(e){
  e.addEventListener('click',evt=>{
    let entity = e.parentNode.parentNode;
    entity.classList.toggle('expanded');
  })
}

Array
  .from(document.getElementsByClassName('entitySummary'))
  .forEach(toggle)
