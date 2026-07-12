#!/usr/bin/env node

import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const source = await readFile(new URL("../public/favicon.svg", import.meta.url));

async function renderPng(size, path) {
  return sharp(source).resize(size, size).png().toFile(fileURLToPath(new URL(path, import.meta.url)));
}

await Promise.all([
  renderPng(192, "../public/icon-192.png"),
  renderPng(512, "../public/icon-512.png"),
  renderPng(180, "../public/apple-touch-icon.png"),
]);

const favicon = await sharp(source).resize(32, 32).png().toBuffer();
const header = Buffer.alloc(22);
header.writeUInt16LE(0, 0);
header.writeUInt16LE(1, 2);
header.writeUInt16LE(1, 4);
header.writeUInt8(32, 6);
header.writeUInt8(32, 7);
header.writeUInt16LE(1, 10);
header.writeUInt16LE(32, 12);
header.writeUInt32LE(favicon.length, 14);
header.writeUInt32LE(header.length, 18);
await writeFile(new URL("../public/favicon.ico", import.meta.url), Buffer.concat([header, favicon]));
