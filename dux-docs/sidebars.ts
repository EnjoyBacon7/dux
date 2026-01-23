import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    {
      type: 'category',
      label: 'For Users',
      items: [
        'users/intro',
      ],
    },
    {
      type: 'category',
      label: 'For Developers',
      items: [
        'developers/intro',
      ],
    },
    {
      type: 'category',
      label: 'Valorisation',
      items: [
        'valorisation/intro',
      ],
    },
  ],
};

export default sidebars;
