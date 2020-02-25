import React from 'react';
import { useState, useEffect } from 'react';
import styles from './style.module.css';

import Views from '../../views';
import Form from '../../ui/Form';

function useViewType() {
    const [value, setValue] = useState(Object.keys(Views)[0])

    const onChange = e =>setValue(e.target.value);

    return [value, onChange]
}

export default function AddViewPanel({addView}) {
    const [viewType, setViewType] = useViewType();
    const [viewConfig, setViewConfig] = useState(Views[viewType].prototype.getConfigOptions(null))

    useEffect(()=>{
        setViewConfig(Views[viewType].prototype.getConfigOptions(null))}
        , [viewType])

    function handleValueChange(config){
        const newConfig = Views[viewType].prototype.getConfigOptions(config);
        setViewConfig(newConfig);
    }

    function handleCreateView(){
        const newView = {config:{}, type: viewType};
        viewConfig.forEach(x=>newView.config[x.name]=x.value)

        addView(newView);
    }

    return(
        <div className={styles.addViewPanel}>
            <div className="d-flex justify-content-between pr-3 pt-1 pb-2">
                <h3 className="d-inline p-1">{viewType}</h3>
                <select className="form-control d-inline col-6" onChange={setViewType}>
                    {Object.keys(Views).map(o => <option key={o} value={o}>{o}</option>)}
                </select>
            </div>
            <p className="p-1">{Views[viewType].prototype.description}</p>
            <Form options={viewConfig} onUpdate={handleValueChange} />
            <button className="btn btn-primary m-2" onClick={handleCreateView}>Create</button>
        </div>
    )
}
