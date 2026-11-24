// @ts-check
import starlight from '@astrojs/starlight';
import { defineConfig } from 'astro/config';

// The documentation at https://airgap-anything.mefby.com. It is published to GitHub Pages once the
// repository is public (see .github/workflows/docs.yml). Pages under src/content/docs/reference/
// are generated: edit their sources and run docs-site/scripts/generate_reference.py.
export default defineConfig({
  site: 'https://airgap-anything.mefby.com',
  integrations: [
    starlight({
      title: 'airgap-anything',
      description:
        'Design any system for air-gapped environments. An agent skill that interviews you, then writes the blueprint, GPU sizing and the list of what to carry in.',
      logo: { src: './src/assets/logo.svg' },
      favicon: '/favicon.svg',
      social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/mftnakrsu/airgap-anything' }],
      editLink: { baseUrl: 'https://github.com/mftnakrsu/airgap-anything/edit/main/docs-site/' },
      customCss: ['./src/styles/custom.css'],
      sidebar: [
        { label: 'Start here', items: ['start/install', 'start/quick-start'] },
        {
          label: 'Guides',
          items: ['guides/how-it-works', 'guides/the-interview', 'guides/what-you-get', 'guides/carrying-it-in', 'guides/coding-agents', 'guides/searchable-documents', 'guides/with-superpowers'],
        },
        { label: 'Concepts', items: ['concepts/tiers-and-sizing', 'concepts/evidence', 'concepts/scope'] },
        { label: 'Example', items: ['example/department'] },
        {
          label: 'Reference',
          items: [
            { label: 'airgap-architect', items: [{ autogenerate: { directory: 'reference/architect' } }] },
            { label: 'airgap-transfer', items: [{ autogenerate: { directory: 'reference/transfer' } }] },
            { label: 'airgap-agent', items: [{ autogenerate: { directory: 'reference/agent' } }] },
            { label: 'airgap-rag', items: [{ autogenerate: { directory: 'reference/rag' } }] },
            { label: 'Catalog', collapsed: true, items: [{ autogenerate: { directory: 'reference/catalog' } }] },
            'reference/gpus',
          ],
        },
        { label: 'Project', items: ['project/contributing', 'project/testing', 'project/privacy', 'project/disclaimer'] },
      ],
    }),
  ],
});
