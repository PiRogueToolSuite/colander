import _memoize from 'lodash.memoize';
import {icon_unicodes} from './default-style';

let nodeLabel = _memoize(function(e, iid) {
  let svgTxt = `${icon_unicodes[iid]} ${e.data('name')}`;

  const ctx = document.createElement('canvas').getContext("2d");
  const fStyle = e.style('font-style').strValue;
  const size = e.style('font-size').pfValue + 'px';
  const family = e.style('font-family').strValue;
  const weight = e.style('font-weight').strValue;
  ctx.font = fStyle + ' ' + weight + ' ' + size + ' ' + family;
  let measures = ctx.measureText(svgTxt);
  let maxWidth = measures.width + 8;

  if (e.data('type')) {
    let typeTxt = e.cy().data('all-styles')[e.data('super_type')].types[e.data('type')].name;
    measures = ctx.measureText(`${typeTxt}`);
    maxWidth = Math.max(maxWidth, measures.width + 8);
    svgTxt += `\n${typeTxt}`;
  }

  // A bit of margin:
  //maxWidth += 5;

  let r = { svgTxt: svgTxt, width: maxWidth };
  return r;
},(e) => {
  return `${e.id()}-${e.data('name')}-${e.data('type')}`;
});

let nodeBody = _memoize(function(e, iid) {
  let svgTxt = `${icon_unicodes[iid]} ${e.data('name')}`;

  const ctx = document.createElement('canvas').getContext("2d");
  const fStyle = e.style('font-style').strValue;
  const size = e.style('font-size').pfValue + 'px';
  const family = e.style('font-family').strValue;
  const weight = e.style('font-weight').strValue;
  ctx.font = fStyle + ' ' + weight + ' ' + size + ' ' + family;
  let measures = ctx.measureText(svgTxt);
  let maxWidth = measures.width + 8;
  let lineHeight = measures.actualBoundingBoxAscent + measures.actualBoundingBoxDescent;
  let maxHeight = lineHeight;

  if (e.data('type')) {
    let typeTxt = e.cy().data('all-styles')[e.data('super_type')].types[e.data('type')].name;
    measures = ctx.measureText(`${typeTxt}`);
    maxWidth = Math.max(maxWidth, measures.width + 8);
    svgTxt += `\n${typeTxt}`;
    maxHeight += lineHeight; // +1 line
  }
  else {
    maxHeight += lineHeight; // +1 line
  }

  maxHeight += 8; // default margin

  let labelAlign = 'center';
  let labelJustification = 'center';
  let labelMarginX = 0;

  let bgImageUrl = 'none';
  if (e.data('thumbnail_url')) {
    bgImageUrl = `url(${e.data('thumbnail_url')})`;
    //maxWidth = Math.max(maxWidth, 256);
    //maxHeight = Math.max(maxHeight, 144);
    labelAlign = 'center';
    labelJustification = 'left';
    labelMarginX = 18;
    maxWidth += 32 + 4;
  }
  //console.log(e.data(), bgImageUrl);

  return {
    svgTxt: svgTxt,
    width: maxWidth, height: maxHeight,
    bgImage: bgImageUrl,
    labelHAlign: labelAlign, labelJustification: labelJustification, labelMarginX: labelMarginX };
},(e) => {
  return `${e.id()}-${e.data('name')}-${e.data('type')}`;
});

export { nodeLabel, nodeBody };
