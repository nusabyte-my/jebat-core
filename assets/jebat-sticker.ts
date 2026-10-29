import { VIEWS, poly, spark } from './fun'
import { deal, jolt, twinkle } from './motions'

const { tilt, extrude } = VIEWS.right

export const commandToken = {
  name: 'JEBAT command orchestration token',
  frames: 180,
  still: 0,
  extrude,
  layers: [
    {
      id: 'hub', p: [250, 266], tilt,
      m: deal([-20, 80], -12, 0),
      shapes: [
        { d: poly([[-72, -60], [72, -60], [72, 60], [-72, 60]], 10), fill: 'deep', depth: 1 },
        { d: poly([[-42, -28], [42, -28], [42, 28], [-42, 28]], 5), fill: 'main', depth: 0.5 },
      ],
    },
    {
      parent: 'hub', a: [-88, -40], p: [-88, -40], m: { ...jolt([-10, -4]), at: 8 },
      shapes: [{ d: poly([[-28, -20], [28, -20], [28, 20], [-28, 20]], 5), fill: 'gold', depth: 0.7 }],
    },
    {
      parent: 'hub', a: [88, -40], p: [88, -40], m: { ...jolt([10, -4]), at: 14 },
      shapes: [{ d: poly([[-28, -20], [28, -20], [28, 20], [-28, 20]], 5), fill: 'ok', depth: 0.7 }],
    },
    {
      parent: 'hub', a: [0, 74], p: [0, 74], m: { ...jolt([0, 10]), at: 20 },
      shapes: [{ d: poly([[-28, -20], [28, -20], [28, 20], [-28, 20]], 5), fill: 'main', depth: 0.7 }],
    },
    {
      parent: 'hub', p: [102, -100],
      m: twinkle(70),
      shapes: [{ d: spark(0, 0, 22), fill: 'white' }],
    },
  ],
}
