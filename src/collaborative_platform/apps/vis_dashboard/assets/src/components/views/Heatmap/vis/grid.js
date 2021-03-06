import * as d3 from 'd3'

function regularGrid (canvas, overlayCanvas, sizes, data, colorScale, rangeScale) {
  const { concurrenceMatrix, axis1, axis2 } = data
  const {
    cellPadding,
    cellSide,
    leftOffset,
    padding
  } = sizes

  const context = canvas.getContext('2d')
  context.save()

  axis2.values.forEach((axis2label, i) => {
    axis1.values.forEach((axis1label, j) => {
      context.fillStyle = colorScale(rangeScale(concurrenceMatrix[axis1label][axis2label].length))
      context.fillRect(leftOffset + cellSide * i, padding + cellSide * j, cellSide - cellPadding, cellSide - cellPadding)
    })
  })

  context.restore()

  setupInteractions(data, canvas, overlayCanvas, leftOffset, padding, cellSide)
}

function setupInteractions (data, canvas, overlayCanvas, leftOffset, padding, cellSide) {
  const { concurrenceMatrix, axis1, axis2 } = data
  const context = overlayCanvas.getContext('2d')

  function handleOverlayHover (e) {
    const [x, y] = d3.mouse(this)
    const yAxisIndex = Math.floor((y - padding) / cellSide)
    const xAxisIndex = Math.floor((x - leftOffset) / cellSide)

    let shared = null
    if (yAxisIndex >= 0 && yAxisIndex < axis1.values.length) {
      if (xAxisIndex >= 0 && xAxisIndex < axis2.values.length) {
        const axis1label = axis1.values[yAxisIndex]
        const axis2label = axis2.values[xAxisIndex]
        shared = concurrenceMatrix[axis1label][axis2label]
      }
    }

    context.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height)

    if (shared === null) { return }

    context.save()
    context.fillStyle = '#f8f9fa'
    context.strokeStyle = '#00b3b0'
    context.beginPath()
    context.rect(x + 5, y - 10, Math.max(...shared.map(x => x.name.length)) * 6 + 5, shared.length * 20)
    context.stroke()
    context.fill()
    context.closePath()
    context.textBaseline = 'bottom'
    context.fillStyle = '#00b3b0'
    shared.forEach((t, i) => { context.fillText(t.name, x + 10, y + 5 + (i * 20)) })
    context.restore()
  }

  d3.select(canvas)
    .on('mousemove', handleOverlayHover)
}

function stairGrid (canvas, overlayCanvas, padding, axisWidth, data, colorScale, rangeScale) {

}

function tiltedGrid (canvas, overlayCanvas, padding, axisWidth, data, colorScale, rangeScale) {

}

export default { regularGrid, stairGrid, tiltedGrid }
