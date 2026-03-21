// @ts-check
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";
import svelte from "@astrojs/svelte";
import path from "node:path";

// https://astro.build/config
export default defineConfig({
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
