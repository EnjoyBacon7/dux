import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  title: 'Dux',
  tagline: 'Open source job search and career intelligence platform',
  favicon: 'img/favicon.ico',

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true,
  },

  // Set the production url of your site here
  url: 'https://dux.example.com',
  baseUrl: '/docs/',

  organizationName: 'EnjoyBacon7',
  projectName: 'dux',

  onBrokenLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'fr', 'es', 'de', 'pt', 'la'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          routeBasePath: '/',
          sidebarPath: './sidebars.ts',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/favicon.ico',
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Dux',
      logo: {
        alt: 'Dux Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Documentation',
        },
        {
          href: 'https://github.com/EnjoyBacon7/dux',
          label: 'GitHub',
          position: 'right',
        },
        {
          type: 'localeDropdown',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {
              label: 'For Users',
              to: '/users/intro',
            },
            {
              label: 'For Developers',
              to: '/developers/intro',
            },
          ],
        },
        {
          title: 'Project',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/EnjoyBacon7/dux',
            },
            {
              label: 'Issues',
              href: 'https://github.com/EnjoyBacon7/dux/issues',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Dux. Open source project.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
