<script>
import {Button, Fieldset, Listbox, Message, Paginator, Panel, ProgressSpinner} from "primevue";
import SureButton from '../../utils/SureButton.vue';

export default {
  components: {
    Button,
    Listbox,
    Message,
    Panel,
    ProgressSpinner,
    SureButton,
  },
  inject: [ 'csrfToken', 'pirogueId' ],
  data() {
    return {
      loading: true,
      lastResponse: null,
      rulesSources: [],
      selectedRulesSource: null,
      newRulesSource: {
        name: null,
        url: null,
      },
    };
  },
  created() {
     this.$logger(this, 'PiRogueSuricata');
  },
  mounted() {
    setTimeout(this.fetchRulesSourcesList, 0);
  },
  methods: {
    async fetchRulesSourcesList() {
      let url = `/rest/pirogue/${this.pirogueId}/suricata_rules_source`;
      let res = await fetch(url, {
        method: 'GET',
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/json",
        },
      });
      this.loading = false;

      if (!res.ok) {
        this.$debug(res);
        this.lastResponse = {
          error: `[${res.status}] ${res.statusText}: ${url}`,
        };
        throw new Error("Error while fetching npm peers list", res);
      }
      let rpcResponse = await res.json();
      this.lastResponse = rpcResponse;

      if (rpcResponse.success) {
        this.rulesSources = rpcResponse.content;
        this.$debug('rulesSources', this.rulesSources);
      }
    },
    async onSelectedRulesSourceChanged() {
      if (this.noCurrentSelection) {
        this.resetSelection();
        return;
      }
    },
    async enableRulesSource() {
      if (this.noCurrentSelection) {
        this.resetSelection();
        return;
      }
      let sourceName = this.selectedRulesSource.name;
      let url = `/rest/pirogue/${this.pirogueId}/suricata_rules_source/`;
      let payload = { name: sourceName };
      let res = await fetch(url, {
        method: 'PUT',
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      this.loading = false;

      if (!res.ok) {
        this.$debug(res);
        this.lastResponse = {
          error: `[${res.status}] ${res.statusText}: ${url}`,
        };
        throw new Error("Error while enabling suricata rules source", res);
      }
      let rpcResponse = await res.json();
      this.lastResponse = rpcResponse;

      if (rpcResponse.success) {
        this.resetSelection();
        setTimeout(this.fetchRulesSourcesList, 0);
      }
    },
    async createRulesSource() {
      let url = `/rest/pirogue/${this.pirogueId}/suricata_rules_source/`;
      let payload = {
        name: this.newRulesSource.name,
        url: this.newRulesSource.url
      };
      let res = await fetch(url, {
        method: 'POST',
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      this.loading = false;

      if (!res.ok) {
        this.$debug(res);
        this.lastResponse = {
          error: `[${res.status}] ${res.statusText}: ${url}`,
        };
        throw new Error("Error while enabling suricata rules source", res);
      }
      let rpcResponse = await res.json();
      this.lastResponse = rpcResponse;

      if (rpcResponse.success) {
        this.resetSelection();
        this.newRulesSource.name = null;
        this.newRulesSource.url = null;
        setTimeout(this.fetchRulesSourcesList, 0);
      }
    },
    async deleteRulesSource() {
      if (this.noCurrentSelection) {
        this.resetSelection();
        return;
      }
      let sourceName = this.selectedRulesSource.name;
      let url = `/rest/pirogue/${this.pirogueId}/suricata_rules_source/`;
      let payload = { name: sourceName };
      let res = await fetch(url, {
        method: 'DELETE',
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      this.loading = false;

      if (!res.ok) {
        this.$debug(res);
        this.lastResponse = {
          error: `[${res.status}] ${res.statusText}: ${url}`,
        };
        throw new Error("Error while enabling suricata rules source", res);
      }
      let rpcResponse = await res.json();
      this.lastResponse = rpcResponse;

      if (rpcResponse.success) {
        this.resetSelection();
        setTimeout(this.fetchRulesSourcesList, 0);
      }
    },
    resetSelection() {
      this.selectedRulesSource = null;
    },
  },
  computed: {
    noCurrentSelection() {
      return this.selectedRulesSource === null;
    },
    deleteButtonLabel() {
      return this.selectedRulesSource?.system ? 'Disable' : 'Delete';
    },
    deleteButtonIcon() {
      return this.selectedRulesSource?.system ? 'pi pi-bell-slash' : 'pi pi-trash';
    },
    newRuleNameInvalid() {
      if (!this.newRulesSource.name) return true;
      return false;
    },
    newRuleUrlInvalid() {
      if (!this.newRulesSource.url) return true;
      return false;
    },
    newRuleInvalid() {
      return this.newRuleNameInvalid || this.newRuleUrlInvalid;
    }
  },
};
</script>
<template>
  <div v-if="loading" class="text-center">
    <ProgressSpinner style="width: 50px; height: 50px" strokeWidth="8"/>
  </div>
  <div v-else>
    <div class="row">
      <div class="col-5">
        <Panel>
          <template #header>
            <h5>Rules sources</h5>
          </template>
          <Listbox :options="rulesSources" optionLabel="id"
                   v-model="selectedRulesSource"
                   @update:modelValue="onSelectedRulesSourceChanged"
                   scrollHeight="27rem" unstyled
                   class="rules-sources-list">
            <template #option="{option}">
              <div class="d-flex">
                <span class="flex-grow-1">
                  <strong>{{option.name}}</strong>
                </span>
                <span v-if="option.enabled" class="text-primary source-status">
                  <i class="pi pi-bell"></i> Active
                </span>
                <span v-else class="text-muted source-status"><i class="pi pi-bell-slash"></i> Inactive</span>
              </div>
              <div>
                <span class="source-url text-truncate">{{option.url}}</span>
              </div>
            </template>
          </Listbox>
        </Panel>
      </div>
      <div class="col-7">
        <Panel header="Details" class="secondary-panel mb-2 pb-2">
          <template #footer>
            <div class="text-end">
              <SureButton :label="deleteButtonLabel" :icon="deleteButtonIcon" severity="danger" size="small" class="me-1"
                          @confirmed="deleteRulesSource"
                          v-if="selectedRulesSource?.enabled"
                          :disabled="noCurrentSelection"/>
              <Button icon="pi pi-bell" variant="outlined" size="small"
                      aria-label="Enable"
                      title="Enable"
                      v-if="selectedRulesSource?.system && !selectedRulesSource?.enabled"
                      :disabled="selectedRulesSource?.parameters"
                      @click="enableRulesSource" label="Enable" />
            </div>
          </template>
          <div class="mx-3">
            <div class="row mb-1">
              <div class="col-2"><label>Name</label></div>
              <div class="col-10" v-clipboard="selectedRulesSource?.name">{{selectedRulesSource?.name}}</div>
            </div>
            <div class="row mb-1">
              <div class="col-2"><label>Url</label></div>
              <div class="col-10" v-clipboard="selectedRulesSource?.url">{{selectedRulesSource?.url}}</div>
            </div>
            <div class="row mb-1">
              <div class="col-2"><label>State</label></div>
              <div class="col-10">
                <div v-if="selectedRulesSource">
                  <span v-if="selectedRulesSource.enabled"><i class="pi pi-bell"></i> Active</span>
                  <span v-else><i class="pi pi-bell-slash"></i> Inactive</span>
                </div>
              </div>
            </div>
            <div class="row mb-1">
              <div class="col-2"><label>Type</label></div>
              <div class="col-10">
                <div v-if="selectedRulesSource">
                  <span v-if="selectedRulesSource.system">System</span>
                  <span v-else>Custom</span>
                </div>
              </div>
            </div>
            <div class="row mb-1">
              <div class="col-2"><label>Summary</label></div>
              <div class="col-10">{{selectedRulesSource?.summary}}</div>
            </div>
            <div class="row">
              <div class="col-2"><label>Vendor</label></div>
              <div class="col-10">{{selectedRulesSource?.vendor}}</div>
            </div>
            <div class="row mb-1">
              <div class="col-2"><label>License</label></div>
              <div class="col-10">{{selectedRulesSource?.license}}</div>
            </div>
            <div class="row text-warning" v-if="selectedRulesSource?.parameters">
              <div class="col-2"><label>Parameters</label></div>
              <div class="col-10">
                <Message severity="warn">Somme parameters are needed to enable this source</Message>
                <div v-for="(pvalue, pname) in selectedRulesSource.parameters">
                  <strong>{{pname}}</strong>: <em>{{pvalue}}</em>
                </div>
              </div>
            </div>
          </div>
        </Panel>
        <Panel header="Create custom source" class="secondary-panel mb-2 pb-2">
          <template #footer>
            <div class="text-end">
              <Button icon="pi pi-plus" variant="outlined" size="small"
                      aria-label="Create"
                      title="Create"
                      :disabled="newRuleInvalid"
                      @click="createRulesSource" label="Create" />
            </div>
          </template>
          <div class="mx-3">
            <div class="row mb-1">
              <div class="col-2"><label>Name</label></div>
              <div class="col-10"><input class="form-control form-control-sm" v-model="newRulesSource.name"/></div>
            </div>
            <div class="row mb-1">
              <div class="col-2"><label>Url</label></div>
              <div class="col-10"><input class="form-control form-control-sm" v-model="newRulesSource.url"/></div>
            </div>
          </div>
        </Panel>
      </div>
    </div>
  </div>
  <div v-if="lastResponse && !lastResponse.success">
    <Message severity="error" class="mt-2">
      <code>{{ lastResponse.error }}</code>
    </Message>
    <div v-if="lastResponse.grpc_success">
      <Message severity="info" class="mt-2">
        <div>This PiRogue has successfully been contacted but the current pirogue-admin version does not support this feature.</div>
        <div>
          Please <a href="https://pts-project.org/docs/pirogue/operating-system/" target="_blank">upgrade your PiRogue</a>.
        </div>
      </Message>
    </div>
  </div>
</template>
<style>
.rules-sources-list
{
  & > div
  {
    overflow: hidden auto;
    min-height: 27rem;
    max-height: 27rem;
  }
  ul
  {
    list-style: none;
    padding: 0;
  }
  li {
    padding: 0.25rem;
    margin-bottom: 0.5rem;
    cursor: pointer;
    &[data-p-selected=true] {
      color: white;
      background-color: rgba(var(--bs-primary-rgb), 1);
      .text-muted {
        color: rgba(255,255,255, 0.5) !important;
      }
      .text-primary {
        color: rgba(255,255,255, 1) !important;
      }
    }
    &:hover {
      background-color: rgba(var(--bs-secondary-rgb), 0.5);
    }
  }
}

.source-url
{
  display: inline-block;
  max-width: 100%;
}

.source-status
{
  min-width: 5rem;
}

code
{
  min-height: 5rem;
}
</style>
