/**
 * Move label angles while keeping planet longitudes untouched. Work on an
 * unwrapped, sorted circle: normalising intermediate angles would hide crossings.
 * @param {readonly number[]} longitudes
 * @param {number} gap
 * @returns {{index:number,angle:number}[]}
 */
export function distributeLabels(longitudes, gap = 14) {
  if (longitudes.length * gap >= 360) throw new RangeError('Labels do not fit this lane');
  const labels = longitudes.map((longitude, index) => ({index, angle: ((longitude % 360) + 360) % 360})).sort((a,b) => a.angle-b.angle);
  if (labels.length < 2) return labels;
  for (let pass = 0; pass < 400; pass++) {
    let moved = 0;
    for (let j = 0; j < labels.length; j++) {
      const a = labels[j], b = labels[(j+1) % labels.length];
      const distance = b.angle + (j === labels.length-1 ? 360 : 0) - a.angle;
      if (distance < gap) {
        const shift = (gap-distance)/2;
        a.angle -= shift;
        b.angle += shift;
        moved = Math.max(moved, shift);
      }
    }
    if (moved < 1e-7) break;
  }
  return labels;
}
