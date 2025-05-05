module.exports = {
  content: [
    './templates/**/*.html',
    '../templates/**/*.html',
    './static/**/*.js',
    '../static/**/*.js',
    './static_src/**/*.css'  // <-- добавь это!
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1e3a8a',
        accent:  '#047857',
        neutral: '#374151',
        base:    '#f9fafb',
      },
    },
  },
  plugins: [],
}
