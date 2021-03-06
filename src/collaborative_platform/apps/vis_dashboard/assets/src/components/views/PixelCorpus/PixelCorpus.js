import React, { useState, useRef, useEffect } from 'react'
import PropTypes from 'prop-types'

import { DataClient, useCleanup } from '../../../data'
import css from './style.css' // eslint-disable-line no-unused-vars
import styles from './style.module.css'
import getConfig from './config'
import { Vis } from './vis'

function useData (dataClient, source) {
  const [data, setData] = useState({ all: [], filtered: [], source: 'certainty' })

  useEffect(() => {
    dataClient.clearSubscriptions()
    dataClient.subscribe(source, data => {
      setData({ ...data, source })
    })
  }, [source])

  return data
}

function useVis (source, sortDocumentsBy, colorBy, callback, taxonomy) {
  const vis = useState(Vis())[0]

  useEffect(() => { // Initialize vis component
    vis.setTaxonomy(taxonomy)
    vis.setEventCallback(callback)
  }, [])

  vis.setSource(source)
  vis.setDocSortingCriteria(sortDocumentsBy)
  vis.setColorBy(colorBy)

  return vis
}

function handleEvent (type, d) {
  if (type === 'labelHover') {
    // for(let doc of Object.values(window.documents)){
    //    if(doc.name == d){
    //        dataClient.focusDocument(doc.id);
    //        break;
    //    }
    // }
  }
}

export default function PixelCorpus ({ sortDocumentsBy, colorBy, source, layout, context }) {
  const [svgRef, containerRef] = [useRef(), useRef()]
  const [width, height] = layout !== undefined ? [layout.w, layout.h] : [4, 4]

  const dataClient = useState(DataClient())[0]
  useCleanup(dataClient)

  // console.log(context)

  const data = useData(dataClient, source)
  const vis = useVis(data?.source, sortDocumentsBy, colorBy, handleEvent, context.taxonomy)

  useEffect(() => vis.render(containerRef.current, svgRef.current, data, data?.source), // Render
    [width, height, sortDocumentsBy, colorBy, data]) // Conditions

  return (
    <div className={styles.container} ref={containerRef}>
      <svg ref={svgRef}>
        <g className="legend"></g>
        <g className="vis">
          <text className="title"></text>
          <g className="docLabels"></g>
          <g className="entityCells"></g>
        </g>
      </svg>
    </div>
  )
}

PixelCorpus.prototype.description = 'Display certainty, category, authorship and other information over a word-wise document representation.'

PixelCorpus.prototype.getConfigOptions = getConfig

PixelCorpus.propTypes = {
  layout: PropTypes.shape({
    w: PropTypes.number,
    h: PropTypes.number
  }),
  children: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node
  ]),
  context: PropTypes.shape({
    taxonomy: PropTypes.object
  }),
  sortDocumentsBy: PropTypes.string,
  colorBy: PropTypes.string,
  source: PropTypes.string
}
