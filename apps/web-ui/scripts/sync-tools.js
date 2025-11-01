#!/usr/bin/env node
import { copyFileSync, mkdirSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const repoRoot = resolve(__dirname, '..', '..', '..')
const source = resolve(repoRoot, 'tools.json')
const destDir = resolve(__dirname, '..', 'public')
const dest = resolve(destDir, 'tools.json')

mkdirSync(destDir, { recursive: true })
copyFileSync(source, dest)
