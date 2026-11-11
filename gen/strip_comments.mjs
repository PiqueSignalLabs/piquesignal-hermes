// Remove every comment from a JavaScript source (the website board scripts embedded in the plugin, and the plugin's own
// part when build.py assembles plugin.js), so developer notes never ship in the public plugin. Uses the JavaScript parser
// bundled inside Node itself (acorn; no npm package):
//   node --expose-internals strip_comments.mjs <in.js> <out.js> [module]
// (module = parse as an ES module: plugin.src.js has import / export; the board scripts are plain scripts)
// Safety proof built in: the token stream of the output must equal the token stream of the input (comments are not
// tokens), so only comments can have changed. A block comment that spans lines becomes one newline (keeps automatic
// semicolon insertion exactly as before); any other comment becomes one space.
import { readFileSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const acorn = require('internal/deps/acorn/acorn/dist/acorn')
const OPTS = { ecmaVersion: 'latest', sourceType: 'script', allowReturnOutsideFunction: true }
const MODULE_OPTS = { ecmaVersion: 'latest', sourceType: 'module' }
const LINE_BREAK = new RegExp('[\n\r' + String.fromCharCode(0x2028, 0x2029) + ']')

function tokens (src, opts) {
  const out = []
  for (const t of acorn.tokenizer(src, opts)) {
    out.push(t.type.label + '\u0000' + (t.value === undefined ? '' : (t.value instanceof RegExp ? String(t.value) : JSON.stringify(t.value))))
  }
  return out
}

export function strip (src, how) {
  const o = how && how.module === true ? MODULE_OPTS : OPTS
  const comments = []
  acorn.parse(src, { ...o, onComment: comments })
  let out = ''
  let at = 0
  for (const c of comments) {
    out += src.slice(at, c.start)
    out += (c.type === 'Block' && LINE_BREAK.test(c.value)) ? '\n' : ' '
    at = c.end
  }
  out += src.slice(at)
  const a = tokens(src, o); const b = tokens(out, o)
  if (a.length !== b.length || a.some((t, i) => t !== b[i])) throw new Error('comment strip changed the code tokens')
  const left = []
  acorn.parse(out, { ...o, onComment: left })          // still valid JavaScript, and no comment left
  if (left.length) throw new Error(left.length + ' comments left after strip')
  return { out, removed: comments.length }
}

if (process.argv[2] && process.argv[3]) {
  const { out, removed } = strip(readFileSync(process.argv[2], 'utf8'), { module: process.argv[4] === 'module' })
  writeFileSync(process.argv[3], out, 'utf8')
  console.log('stripped', removed, 'comments')
}
