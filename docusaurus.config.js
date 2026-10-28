// @ts-check
import {themes as prismThemes} from 'prism-react-renderer';

function preprocessPart12Markdown({filePath, fileContent}) {
  const withoutSectionMarkers = fileContent.replace(/^\s*<!-- PART2 -->\s*$/gm, '');
  if (!filePath.includes('/docs/')) {
    return withoutSectionMarkers;
  }

  const content = withoutSectionMarkers.replace(/<details><summary>(.*?)<\/summary>/gs, '<details>\n<summary>$1</summary>\n\n');
  const lines = content.split('\n');
  let inFence = false;
  let mathDelimiter = '';
  let inlineCodeDelimiter = '';

  return lines.map((line) => {
    if (/^\s*(```|~~~)/.test(line)) {
      inFence = !inFence;
      return line;
    }
    if (inFence) {
      return line;
    }

    let output = '';
    for (let index = 0; index < line.length; index += 1) {
      const char = line[index];
      if (char === '`') {
        let end = index + 1;
        while (line[end] === '`') end += 1;
        const delimiter = line.slice(index, end);
        if (!inlineCodeDelimiter) inlineCodeDelimiter = delimiter;
        else if (inlineCodeDelimiter === delimiter) inlineCodeDelimiter = '';
        output += delimiter;
        index = end - 1;
        continue;
      }

      if (!inlineCodeDelimiter && char === '$' && line[index - 1] !== '\\') {
        if (mathDelimiter) {
          if (line.startsWith(mathDelimiter, index)) {
            output += mathDelimiter;
            index += mathDelimiter.length - 1;
            mathDelimiter = '';
            continue;
          }
        } else if (
          line[index + 1] === '$' ||
          (!/^[\d,]+\s*$/.test(line.slice(index + 1, line.indexOf('$', index + 1))) &&
            line.indexOf('$', index + 1) !== -1)
        ) {
          mathDelimiter = line[index + 1] === '$' ? '$$' : '$';
          output += mathDelimiter;
          index += mathDelimiter.length - 1;
          continue;
        }
      }

      if (mathDelimiter && !inlineCodeDelimiter) {
        output += {'{': '&#123;', '}': '&#125;', '<': '&lt;', '>': '&gt;'}[char] ?? char;
      } else {
        output += char;
      }
    }
    inlineCodeDelimiter = '';
    if (mathDelimiter === '$') mathDelimiter = '';
    return output;
  }).join('\n');
}

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
  markdown: {
    mermaid: true,
    preprocessor: preprocessPart12Markdown,
    hooks: {onBrokenMarkdownLinks: 'warn'},
  },
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
    mermaid: {options: {flowchart: {useMaxWidth: true, nodeSpacing: 45, rankSpacing: 50, padding: 14, wrappingWidth: 420}, themeVariables: {fontSize: '15px'}}},
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
