// @ts-check
import {themes as prismThemes} from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'AI Infrastructure Handbook',
  tagline: 'Linux to GPU clusters: basics to advanced, for AI infrastructure engineers',
  favicon: 'img/favicon.ico',
  future: {v4: true},

  // Private for now; set the real URL and baseUrl before any publication.
  url: 'http://localhost',
  baseUrl: '/',
  onBrokenLinks: 'throw',
  markdown: {mermaid: true, hooks: {onBrokenMarkdownLinks: 'warn'}},
  themes: ['@docusaurus/theme-mermaid'],
  clientModules: ['./src/clientModules/mermaidZoom.js'],
  i18n: {defaultLocale: 'en', locales: ['en']},

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {sidebarPath: './sidebars.js', routeBasePath: '/'},
        blog: false,
        theme: {customCss: './src/css/custom.css'},
      }),
    ],
  ],

  themeConfig: {
    colorMode: {respectPrefersColorScheme: true},
    mermaid: {options: {flowchart: {useMaxWidth: true, nodeSpacing: 45, rankSpacing: 50, padding: 14}, themeVariables: {fontSize: '15px'}}},
    navbar: {
      title: 'AI Infrastructure Handbook',
      items: [{type: 'docSidebar', sidebarId: 'tutorialSidebar', position: 'left', label: 'Book'}],
    },
    docs: {sidebar: {hideable: true, autoCollapseCategories: true}},
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'yaml', 'python', 'hcl', 'json', 'diff', 'ini'],
    },
  },
};

export default config;
