import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

const site = process.env.SITE_URL || "https://www.epistemic-experiments.org";
const configuredBase = process.env.BASE_PATH || "/";

export default defineConfig({
  output: "static",
  site,
  base: configuredBase === "/" ? undefined : configuredBase,
  trailingSlash: "always",
  integrations: [
    sitemap({
      filter: (page) => !page.includes("/404"),
    }),
  ],
});
