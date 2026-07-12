#!/usr/bin/env node

import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const mark = await readFile(new URL("../public/images/logo-mark.webp", import.meta.url));
const faviconSource = await readFile(new URL("../public/favicon.svg", import.meta.url));

async function renderPng(size, path) {
  const logo = await sharp(mark)
    .resize({ width: Math.round(size * 0.88), height: Math.round(size * 0.68), fit: "inside" })
    .png()
    .toBuffer();

  return sharp({
    create: { width: size, height: size, channels: 4, background: "#fbf8ef" },
  })
    .composite([{ input: logo, gravity: "center" }])
    .png({ palette: true, colours: 64, compressionLevel: 9 })
    .toFile(fileURLToPath(new URL(path, import.meta.url)));
}

await Promise.all([
  renderPng(192, "../public/icon-192.png"),
  renderPng(512, "../public/icon-512.png"),
  renderPng(180, "../public/apple-touch-icon.png"),
]);

const favicon = await sharp(faviconSource).resize(32, 32).png().toBuffer();
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
