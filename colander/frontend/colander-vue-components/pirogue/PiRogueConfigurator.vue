<script>
import { shallowRef } from 'vue';
import {
  Menu,
  Panel
} from 'primevue';

import PiRogueNoSection from './sections/PiRogueNoSection.vue';
import PiRogueAccess from './sections/PiRogueAccess.vue';
import PiRogueConfigurationRead from './sections/PiRogueConfigurationRead.vue';
import PiRoguePackagesInfo from './sections/PiRoguePackagesInfo.vue';
import PiRogueStatus from './sections/PiRogueStatus.vue';
import PiRogueSuricata from './sections/PiRogueSuricata.vue';
import PiRogueVPN from './sections/PiRogueVPN.vue';

export default {
  components: {
    Menu, Panel,
    PiRogueNoSection, PiRogueStatus,
  },
  props: [ 'dataCsrfToken', 'dataPirogueCredentialsId', 'dataDisableSections' ],
  provide() {
    return {
      csrfToken: this.dataCsrfToken,
      pirogueId: this.dataPirogueCredentialsId,
    };
  },
  data() {
    let allowed_sections = [];
    return {
      currentSection: {
        menuItem: null,
        title: "PiRogue Configurator",
        component: shallowRef(PiRogueNoSection),
      },
      hiddenSections: [],
      menu: [
        {
          label: "Information",
          items: [
            {
              permissions: ['System:GetStatus'],
              label: 'Status',
              icon: 'pi pi-chart-bar',
              command: (evt) => {
                this.setSection('Status', shallowRef(PiRogueStatus), evt.item);
              },
            },
            {
              permissions: ['System:GetConfiguration'],
              label: 'Configuration',
              icon: 'pi pi-list-check',
              command: (evt) => {
                this.setSection('Configuration', shallowRef(PiRogueConfigurationRead), evt.item);
              },
            },
            {
              permissions: ['System:GetPackagesInfo'],
              label: 'Packages',
              icon: 'pi pi-box',
              command: (evt) => {
                this.setSection('Packages', shallowRef(PiRoguePackagesInfo), evt.item);
              },
            },
          ],
        },
        {
          label: "Configuration",
          items: [
            /*
            {
              permissions: [
                'System:SetHostname',
                'System:SetLocale',
                'System:SetTimezone',
                'Services:SetDashboardConfiguration',
              ],
              label: 'System',
              icon: 'pi pi-cog',
              command: (evt) => {
                this.setSection('Configuration', shallowRef(PiRogueNoSection), evt.item);
              },
            },
            {
              permissions: [
                'Network:EnableExternalPublicAccess',
                'Network:DisableExternalPublicAccess',
                'Network:SetWifiConfiguration',
                'Network:OpenIsolatedPort',
                'Network:CloseIsolatedPort',
              ],
              label: 'Network',
              icon: 'pi pi-sitemap',
              command: (evt) => {
                this.setSection('Network', shallowRef(PiRogueNoSection), evt.item);
              },
            },
            */
            {
              permissions: ['Access'],
              label: 'Access',
              icon: 'pi pi-key',
              command: (evt) => {
                this.setSection('Access', shallowRef(PiRogueAccess), evt.item);
              },
            },
            {
              permissions: ['Network:ListVPNPeers'],
              label: 'VPN',
              icon: 'pi pi-unlock',
              command: (evt) => {
                this.setSection('VPN', shallowRef(PiRogueVPN), evt.item);
              },
              visible: () => {
                return !this.hiddenSections.includes('Network:ListVPNPeers');
              },
            },
            {
              permissions: ['Services:ListSuricataRulesSources'],
              label: 'Suricata',
              icon: 'pi pi-sparkles',
              command: (evt) => {
                this.setSection('Suricata', shallowRef(PiRogueSuricata), evt.item);
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
     if (this.dataDisableSections) {
       this.hiddenSections = this.dataDisableSections.split(',');
     }
  },
  methods: {
    setSection(title, component, menuItem) {
      if (this.currentSection.menuItem) {
        this.currentSection.menuItem.class = '';
      }
      this.currentSection.menuItem = menuItem;
      if (this.currentSection.menuItem) {
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
    <div class="col-3">
      <Menu :model="menu"></Menu>
    </div>
    <div class="col ps-0">
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
