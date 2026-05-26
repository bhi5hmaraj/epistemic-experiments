import { defineConfig } from "astro/config";

const site = process.env.SITE_URL;
const configuredBase = process.env.BASE_PATH || "/";

export default defineConfig({
  output: "static",
  site,
  base: configuredBase === "/" ? undefined : configuredBase,
  trailingSlash: "always",
});
