/** @type {import('tailwindcss').Config} */
module.exports = {
	content: ["./templates/**/*.html", "./static/src/**/*.js"],
	theme: {
		extend: {},
	},
	plugins: [],
	options: {
		safelist: ["transparent", "bg-zinc-900", "bg-opacity-90"],
	},
};
