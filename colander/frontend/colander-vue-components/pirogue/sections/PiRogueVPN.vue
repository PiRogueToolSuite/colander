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
      peers: [],
      selectedPeer: null,
      peerConfiguration: null,
    };
  },
  created() {
     this.$logger(this, 'PiRogueVPN');
  },
  mounted() {
    setTimeout(this.fetchVPNPeersList, 0);
  },
  methods: {
    async fetchVPNPeersList() {
      let url = `/rest/pirogue/${this.pirogueId}/vpn_peer`;
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
        this.peers = rpcResponse.content;
        this.$debug('peers', this.peers);
      }
    },
    async onSelectedPeerChanged() {
      if (this.noCurrentSelection) {
        this.resetSelection();
        return;
      }
      let peerIdx = this.selectedPeer.idx;
      let url = `/rest/pirogue/${this.pirogueId}/vpn_peer/${peerIdx}`;
      let res = await fetch(url, {
        method: 'GET',
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/json",
        },
      });
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
        this.peerConfiguration = rpcResponse.content;
        this.$debug('peerConfiguration', this.peerConfiguration);
      }
    },
    async createPeer() {
      let url = `/rest/pirogue/${this.pirogueId}/vpn_peer/create`;
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
        let newPeer = rpcResponse.content;
        this.peers.push( newPeer );
        this.$debug('new peer', newPeer);
      }
    },
    async deletePeer() {
      if (this.noCurrentSelection) {
        this.resetSelection();
        return;
      }
      let peerIdx = this.selectedPeer.idx;
      let url = `/rest/pirogue/${this.pirogueId}/vpn_peer/${peerIdx}`;
      let res = await fetch(url, {
        method: 'DELETE',
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
        this.resetSelection();
        setTimeout(this.fetchVPNPeersList, 0);
      }
    },
    resetSelection() {
      this.selectedPeer = null;
      this.peerConfiguration = null;
    },
  },
  computed: {
    noCurrentSelection() {
      return this.selectedPeer === null;
    },
  }
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
            <h5>Active Peers list</h5>
          </template>
          <template #footer>
            <div class="text-end">
              <SureButton label="Delete" icon="pi pi-trash" severity="danger" size="small" class="me-1"
                          @confirmed="deletePeer"
                          :disabled="noCurrentSelection"/>
              <Button icon="pi pi-plus" variant="outlined" size="small"
                      aria-label="Create User Access"
                      title="Create User Access"
                      @click="createPeer" label="New" />
            </div>
          </template>
          <Listbox :options="peers" optionLabel="id"
                   v-model="selectedPeer"
                   @update:modelValue="onSelectedPeerChanged"
                   scrollHeight="27rem" unstyled
                   class="vpn-peers-list">
            <template #option="{option}">
              <div>
                <span>Peer index <strong>{{option.idx}}</strong></span>
              </div>
            </template>
          </Listbox>
        </Panel>
      </div>
      <div class="col-7">
        <Panel header="Keys" class="secondary-panel mb-2 pb-2">
          <div class="mx-3 my-1 row">
            <div class="col-3 ps-0"><label>Public Key</label></div>
            <div class="col-9 font-monospace text-truncate" v-clipboard="selectedPeer?.public_key">{{selectedPeer?.public_key || '&nbsp;'}}</div>
          </div>
          <div class="mx-3 my-1 row">
            <div class="col-3 ps-0"><label>Private Key</label></div>
            <div class="col-9 font-monospace text-truncate" v-clipboard="selectedPeer?.private_key">{{selectedPeer?.private_key || '&nbsp;'}}</div>
          </div>
        </Panel>
        <Panel header="Configuration" class="secondary-panel mb-2 pb-2">
          <div class="container">
            <pre class="bg-dark text-white p-3 rounded mb-0" v-clipboard="peerConfiguration">{{peerConfiguration || ''}}</pre>
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
.vpn-peers-list
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
    }
    &:hover {
      background-color: rgba(var(--bs-secondary-rgb), 0.5);
    }
  }
}

code
{
  min-height: 5rem;
}
</style>
