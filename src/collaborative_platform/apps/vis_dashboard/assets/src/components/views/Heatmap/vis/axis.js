function shorttenedLabel (label, maxLabelLength = 30) {
  if (label.length <= maxLabelLength) { return label }

  const fragmentLength = Math.trunc(maxLabelLength / 2 - 2)
  const startFragment = label.slice(0, fragmentLength)
  const endFragment = label.slice(label.length - fragmentLength, label.length)
  return startFragment + '...' + endFragment
}

function regularAxis (canvas, sizes, axisWidth, legendWidth, data) {
  const { axis1, axis2 } = data
  const {
    cellSide,
    leftOffset,
    padding
  } = sizes

  const bottomOffset = canvas.height - (cellSide * axis1.values.length + padding)
  const leftLabelLength = (leftOffset - 2 * padding) / 7
  const bottomLabelLength = ((bottomOffset - 2 * padding) / Math.cos(Math.PI / 4)) / 7

  const ctx = canvas.getContext('2d')
  ctx.save()

  ctx.textAlign = 'end'
  ctx.textBaseline = 'middle'
  ctx.font = '13px Open Sans'
  axis1.values.forEach((label, i) => {
    ctx.fillText(shorttenedLabel(label, leftLabelLength), leftOffset - cellSide / 4, padding + cellSide * i + cellSide / 2)
  })
  ctx.restore()

  ctx.save()
  ctx.textAlign = 'end'
  ctx.textBaseline = 'middle'
  ctx.font = '13px Open Sans'

  axis2.values.forEach((label, i) => {
    const bandMiddle = cellSide * i + cellSide / 2
    const x = leftOffset + bandMiddle
    const y = padding * 2 + (cellSide * axis1.values.length)
    const translatedX = x
    const translatedY = y

    ctx.save()
    ctx.translate(translatedX, translatedY)
    ctx.rotate(-Math.PI / 4)
    ctx.translate(-translatedX, -translatedY)

    ctx.fillText(shorttenedLabel(label, bottomLabelLength), translatedX, translatedY)
    ctx.restore()
  })

  ctx.restore()
}

function tiltedAxis (canvas, overlayCanvas, padding, axisWidth, data, colorScale, rangeScale) {

}

export default { regularAxis, tiltedAxis }
