<script>
import { shallowRef } from 'vue';
import {
  Menu,
  Panel
} from 'primevue';

import PiRogueNoSection from './sections/PiRogueNoSection.vue';
import PiRogueStatus from './sections/PiRogueStatus.vue';

export default {
  components: {
    Menu, Panel,
    PiRogueNoSection, PiRogueStatus,
  },
  props: [ 'dataCsrfToken', 'dataPirogueCredentialsId' ],
  provide() {
    return {
      csrfToken: this.dataCsrfToken,
      pirogueId: this.dataPirogueCredentialsId,
    };
  },
  data() {
    return {
      currentSection: {
        menuItem: null,
        title: "PiRogue Configurator",
        component: shallowRef(PiRogueNoSection),
      },
      menu: [
        {
          label: "Information",
          items: [
            {
              label: 'Status',
              icon: 'pi pi-chart-bar',
              command: (evt) => {
                this.$debug(evt);
                this.setSection('Status', shallowRef(PiRogueStatus), evt.item);
              },
            },
            {
              label: 'Configuration',
              icon: 'pi pi-list-check',
              command: (a) => {
                this.setSection('Configuration', shallowRef(PiRogueNoSection));
              },
            },
            {
              label: 'Packages',
              icon: 'pi pi-box',
              command: (a) => {
                this.setSection('Packages', shallowRef(PiRogueNoSection));
              },
            },
          ],
        },
        {
          label: "Configuration",
          items: [
            {
              label: 'System',
              icon: 'pi pi-cog',
              command: (a) => {
                this.setSection('Configuration', shallowRef(PiRogueNoSection));
              },
            },
            {
              label: 'Network',
              icon: 'pi pi-sitemap',
              command: (a) => {
                this.setSection('Network', shallowRef(PiRogueNoSection));
              },
            },
            {
              label: 'Access',
              icon: 'pi pi-key',
              command: (a) => {
                this.setSection('Access', shallowRef(PiRogueNoSection));
              },
            },
            {
              label: 'VPN',
              icon: 'pi pi-shield',
              command: (a) => {
                this.setSection('VPN', shallowRef(PiRogueNoSection));
              },
            },
          ],
        },
      ],
    };
  },
  created() {
     this.$logger(this, 'PiRogueConfigurator');
     this.$debug('CsrfToken', this.dataCsrfToken);
     this.$debug('PiRogueCredentialsID', this.dataPirogueCredentialsId);
  },
  methods: {
    setSection(title, component, menuItem) {
      if (this.currentSection.menuItem) {
        this.$debug(this.currentSection.menuItem.class);
        this.currentSection.menuItem.class = '';
      }
      this.currentSection.menuItem = menuItem;
      if (this.currentSection.menuItem) {
        this.$debug(this.currentSection.menuItem.class);
        this.currentSection.menuItem.class = 'active';
      }
      this.currentSection.title = title;
      this.currentSection.component = component;
    }
  }
}
</script>
<template>
  <div class="row">
    <div class="col-2">
      <Menu :model="menu"></Menu>
    </div>
    <div class="col-10">
      <Panel>
        <template #header><h4>{{ currentSection.title }}</h4></template>
        <component :is="currentSection.component" />
      </Panel>
    </div>
  </div>
</template>
<style>
.p-menu-item.active {
  font-weight: bold;
}
</style>
