import React from 'react';
import styles from './style.module.css';
import css from './style.css';
import {WithAppContext} from 'app_context';

export default function VisFrame({index, focused, onViewFocus, onViewClose, children}) {
    const getTitlePadding = title=>({'paddingLeft': 'calc(50% - '+((children.props.dimension.length/2)*5.5)+'px)'});
    
    return(
        <div className={`border ${styles.frame} ${focused?'focused border-primary':''}`}>
            <div className={styles.topbar}>
                {children.props.hasOwnProperty('dimension')?
                <span style={getTitlePadding(children.props.dimension)}>
                    {children.props.dimension}
                </span>
                :''}
                <button onClick={()=>onViewClose(index)} type="button" className="close" aria-label="Close">
                  <span aria-hidden="true">&times;</span>
                </button>
                <button onClick={()=>onViewFocus(index)} type="button" className="close" aria-label="Close">
                  <span aria-hidden="true">&#9881;</span>
                </button>
            </div>
            <div className={styles.container}>
                <WithAppContext>
                    {children}
                </WithAppContext>
            </div>
        </div>
    )
}
