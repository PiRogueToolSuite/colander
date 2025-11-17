import {createApp, defineAsyncComponent} from "vue";
import "primeicons/primeicons.css";
import PrimeVue from "primevue/config";
import ToastService from 'primevue/toastservice';
import ColanderTheme from './theme-preset';

import CachePlugin from './plugins/Cache';
import i18nPlugin from './plugins/i18n';
import LoggerPlugin, {LogLevel} from './plugins/Logger';
import EventBusPlugin from './plugins/EventBus';
import ThemeUtilsPlugin from './plugins/ThemeUtils';

import HarAnalyzerPlugin from 'har-analyzer-vue';
/* FIXME: Confirm not needed anymore, then clean */
/* import { DesignSystemConfig as HarPrimeVueConfig } from 'har-analyzer-vue'; */

import Legacy from './legacy/project';
import ColanderTextEditor from './legacy/colander-text-editor';

/**
 * Important: Not reactive content.
 * @param $vue - the Vue context
 */
function init_websocket($vue) {
  let loc = window.location;
  let ws_protocol = 'ws:';
  if (loc.protocol.startsWith('https')) {
      ws_protocol = 'wss:';
  }
  let ws_url_base = `ws://${loc.host}/ws-channel`;
  let ws_url_case = `${ws_url_base}/global/`;
  // let ws = new WebSocket(ws_url_case);
  let ws = new WebSocket(`${ws_protocol}//${loc.host}${loc.pathname}`);
  ws.addEventListener('message', function(evt) {
     let data = JSON.parse(evt.data)
     $vue.$debug('Channel message data', data);
  });
  ws.addEventListener('close', function(evt) {
     $vue.$info('Channel disconnected', arguments);
  });
  ws.addEventListener('open', function(evt) {
     $vue.$info('Channel connected', arguments);
  });
  ws.addEventListener('error', function(evt) {
     $vue.$error('Channel error', arguments);
  });
  $vue.$bus.on('msg.example.to.server', (msg) => {
    ws.send(JSON.stringify(msg));
  });
}


export const ColanderApp = {
  components: {
    ArtifactUploader: defineAsyncComponent(() =>
      import(/* webpackChunkName: "ArtifactUploader" */ '../colander-vue-components/ArtifactUploader.vue')),
    ConfirmButton: defineAsyncComponent(() =>
      import(/* webpackChunkName: "ConfirmButton" */ '../colander-vue-components/ConfirmButton.vue')),
    CsvImporter: defineAsyncComponent(() =>
      import(/* webpackChunkName: "Csv" */ '../colander-vue-components/importers/CsvImporter.vue')),
    DocumentationPane: defineAsyncComponent(() =>
      import(/* webpackChunkName: "DocumentationPane" */ '../colander-vue-components/DocumentationPane.vue')),
    DropfileTriage: defineAsyncComponent(() =>
      import(/* webpackChunkName: "DropfileTriage" */ '../colander-vue-components/DropfileTriage.vue')),
    DynamicTypeSelector: defineAsyncComponent(() =>
      import(/* webpackChunkName: "DynamicTypeSelector" */ '../colander-vue-components/DynamicTypeSelector.vue')),
    GeoMap: defineAsyncComponent(() =>
      import(/* webpackChunkName: "GeoMap" */ '../colander-vue-components/GeoMap.vue')),
    GraphEditor: defineAsyncComponent(() =>
      import(/* webpackChunkName: "GraphEditor" */ '../colander-vue-components/GraphEditor.vue')),
    HStoreTable: defineAsyncComponent(() =>
      import(/* webpackChunkName: "HStoreTable" */ '../colander-vue-components/HStoreTable.vue')),
    InvestigateView: defineAsyncComponent(() =>
      import(/* webpackChunkName: "InvestigateView" */ '../colander-vue-components/InvestigateView.vue')),
    Suggester: defineAsyncComponent(() =>
      import(/* webpackChunkName: "Suggester" */ '../colander-vue-components/Suggester.vue')),
    ThumbnailInputField: defineAsyncComponent(() =>
      import(/* webpackChunkName: "ThumbnailInputField" */ '../colander-vue-components/ThumbnailInputField.vue')),
    ToolbarSearch: defineAsyncComponent(() =>
      import(/* webpackChunkName: "ToolbarSearch" */ '../colander-vue-components/ToolbarSearch.vue')),
    Pills: defineAsyncComponent(() =>
      import(/* webpackChunkName: "Pills" */ '../colander-vue-components/generics/Pills.vue')),
    GenericEntity: defineAsyncComponent(() =>
      import(/* webpackChunkName: "GenericEntity" */ '../colander-vue-components/generics/GenericEntity.vue')),
    GenericEntityDetails: defineAsyncComponent(() =>
      import(/* webpackChunkName: "GenericEntityDetails" */ '../colander-vue-components/generics/GenericEntityDetails.vue')),
    GenericEntityList: defineAsyncComponent(() =>
      import(/* webpackChunkName: "GenericEntityList" */ '../colander-vue-components/generics/GenericEntityList.vue')),
    CachedFileUpload: defineAsyncComponent(() =>
      import(/* webpackChunkName: "CachedFileUpload" */ '../colander-vue-components/generics/CachedFileUpload.vue')),
    GenericFeedImporter: defineAsyncComponent(() =>
      import(/* webpackChunkName: "GenericFeedImporter" */ '../colander-vue-components/generics/GenericFeedImporter.vue')),
    EntityQuickViewDialog: defineAsyncComponent(() =>
      import(/* webpackChunkName: "EntityQuickViewDialog" */ '../colander-vue-components/generics/EntityQuickViewDialog.vue')),
    TemplateFeedEditor: defineAsyncComponent(() =>
      import(/* webpackChunkName: "TemplateFeedEditor" */ '../colander-vue-components/generics/TemplateFeedEditor.vue')),
    MISPImporter: defineAsyncComponent(() =>
      import(/* webpackChunkName: "MISPImporter" */ '../colander-vue-components/importers/MISPImporter.vue')),
    STIX2Importer: defineAsyncComponent(() =>
      import(/* webpackChunkName: "STIX2Importer" */ '../colander-vue-components/importers/STIX2Importer.vue')),
    /* PRIMEVUE COMPONENTS */
    DatePicker: defineAsyncComponent(() =>
      /* webpackChunkName: "pv-datepicker" */ import('primevue/datepicker')),
  },
  created() {
    this.$logger(this, 'ColanderApp');

    init_websocket(this);
  },
  mounted() {
    this.$info('Colander Wide Application', 'mounted');
    Legacy();
    ColanderTextEditor();
  },
};

const colander_primevue_options = {
  theme: {
    preset: ColanderTheme,
    options: {
      darkModeSelector: 'none',
    }
  },
  locale: {
    dateFormat: 'mm/dd/yy',
  },
};

export default () => {
  const colander_application = createApp(ColanderApp);

  // -- Main application configuration
  colander_application.config.compilerOptions.whitespace = "preserve";

  // -- Main warning/error handling
  colander_application.config.warnHandler  = (msg, instance, trace) => {
    console.warn('Colander Hydration', msg, instance, trace);
  };
  colander_application.config.errorHandler = (err, instance, info) => {
    console.error('Colander Hydration', err, instance, info);
  };

  // -- Local Preferences
  let localLogLevel = LogLevel.WARN;
  try {
    let storedLogLevel = localStorage.getItem('logLevel');
    if (storedLogLevel in LogLevel) {
      localLogLevel = LogLevel[storedLogLevel];
      console.debug('New logLevel set to', storedLogLevel);
    }
  } catch(err) {}

  // -- Plugin registration
  colander_application.use(LoggerPlugin, {
    logLevel: localLogLevel,
  });
  colander_application.use(EventBusPlugin);
  colander_application.use(i18nPlugin);
  colander_application.use(CachePlugin, {
    dataSources: {
      'entity_types': '/rest/entity/types',
      'artifact_types': '/rest/artifact_types/',
      'creatable_entities': '/rest/dataset/creatable_entities/',
      'all_styles': '/rest/dataset/all_styles/',
    },
  });
  // Must be registered after the CachePlugin
  colander_application.use(ThemeUtilsPlugin);
  if (navigator.language) {
    if (String(navigator.language).toLowerCase() === 'fr') {
      colander_primevue_options.locale.dateFormat = 'dd/mm/yy';
    }
  }
  colander_application.use(PrimeVue, colander_primevue_options);

  /* FIXME: Confirm not needed anymore, then clean */
  /*
  colander_application.use( HarPrimeVueConfig, {
    theme: {
      preset: ColanderTheme,
      options: {
        darkModeSelector: 'none',
      }
    }
  });
   */
  colander_application.use(ToastService);
  colander_application.use(HarAnalyzerPlugin);

  // -- Mount and start
  colander_application.mount(document.querySelector('body'));
};
