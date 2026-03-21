// @ts-check
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";
import svelte from "@astrojs/svelte";
import node from "@astrojs/node";
import path from "node:path";

// https://astro.build/config
export default defineConfig({
	output: "server",
	adapter: node({ mode: "standalone" }),
	vite: {
		plugins: [tailwindcss()],
		resolve: {
			alias: {
				$lib: path.resolve("./src/lib"),
			},
			noExternal: ["@lucide/svelte", "bits-ui"],
		},
	},
	integrations: [svelte()],
});
