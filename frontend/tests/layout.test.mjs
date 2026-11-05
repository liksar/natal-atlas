import test from 'node:test';
import assert from 'node:assert/strict';
import {distributeLabels} from '../src/layout.mjs';

for (const [name, values] of [
  ['across zero', [357,359,0,1,3,30,80,140,200,260,300]],
  ['all coincident', Array(11).fill(1)],
  ['dense Capricorn group', [291.75,137,292.4,328,243,279,292.7,32,346,292.8,98]],
]) {
  test(name, () => {
    const input = Object.freeze(values.slice());
    const result = distributeLabels(input);
    const angles = result.map(x => (x.angle % 360+360)%360).sort((a,b) => a-b);
    assert.equal(result.length,input.length);
    assert.deepEqual(input, values);
    for (let i=0;i<angles.length;i++) {
      const next = angles[(i+1)%angles.length] + (i===angles.length-1?360:0);
      assert.ok(next-angles[i]>=14-1e-4, `overlap at ${i}`);
    }
  });
}
