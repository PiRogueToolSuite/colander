import {createApp, defineAsyncComponent} from "vue";
import "primeicons/primeicons.css";
import PrimeVue from "primevue/config";
import aura from '@primevue/themes/aura';

import CachePlugin from './plugins/Cache';
// Not yet published
//import HarAnalyzerApp from '/home/sancho/Projects/PTS/har-analyzer-vuejs/dist/harweb.es.js';

import Legacy from './legacy/project';
import ColanderTextEditor from './legacy/colander-text-editor';

export const ColanderApp = {
  components: {
    ArtifactUploader: defineAsyncComponent(() => import('../colander-vue-components/ArtifactUploader.vue')),
    DocumentationPane: defineAsyncComponent(() => import('../colander-vue-components/DocumentationPane.vue')),
    DynamicTypeSelector: defineAsyncComponent(() => import('../colander-vue-components/DynamicTypeSelector.vue')),
    GraphEditor: defineAsyncComponent(() => import('../colander-vue-components/GraphEditor.vue')),
    HStoreTable: defineAsyncComponent(() => import('../colander-vue-components/HStoreTable.vue')),
    Suggester: defineAsyncComponent(() => import('../colander-vue-components/Suggester.vue')),
    ToolbarSearch: defineAsyncComponent(() => import('../colander-vue-components/ToolbarSearch.vue')),
  },
  created() {
  },
  mounted() {
    console.log('Colander Wide Application', 'mounted');
    /*
    import("bootstrap/dist/js/bootstrap.bundle.js").then((module) => {
      console.log('Boostrap module loaded', module);
    });
    */
    Legacy();
    ColanderTextEditor();
  },
};

export default () => {
  const colander_application = createApp(ColanderApp);
  colander_application.config.compilerOptions.whitespace = "preserve";
  colander_application.config.warnHandler  = (msg, instance, trace) => {
    console.warn('Colander Hydration', msg, instance, trace);
  };
  colander_application.config.errorHandler = (err, instance, info) => {
    console.error('Colander Hydration', err, instance, info);
  };
  colander_application.use(CachePlugin, {
    dataSources: {
      'entity_types': '/rest/entity/types',
      'artifact_types': '/rest/artifact_types/',
      'creatable_entities': '/rest/dataset/creatable_entities/',
      'all_styles': '/rest/dataset/all_styles/',
    },
  });
  //colander_application.use(HarAnalyzerApp);
  colander_application.use(PrimeVue);

  // --
  colander_application.mount(document.querySelector('body'));
};
