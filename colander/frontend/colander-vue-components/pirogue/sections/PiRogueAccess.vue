<script>
import {Button, Listbox, Panel, Message, Tree, ProgressSpinner} from "primevue";
import SureButton from '../../utils/SureButton.vue';

export default {
  components: {
    Button,
    Listbox,
    Message,
    Panel,
    SureButton,
    Tree,
    ProgressSpinner,
  },
  inject: [ 'csrfToken', 'pirogueId' ],
  data() {
    return {
      loading: true,
      response: {},
      userAccesses: [],
      selectedUserAccess: null,
      permissions: null,
      permissionsNodes: [],
      selectedKey: null,
    };
  },
  created() {
     this.$logger(this, 'PiRogueAccess');
     this.$debug('token', this.csrfToken, 'PiRogue', this.pirogueId);
     this.fetchPermissionList();
  },
  methods: {
    fetchUserAccesses() {
      fetch(`/rest/pirogue/${this.pirogueId}/access`, {
        method: 'GET',
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/json",
        },
      }).then(this._onUserAccesses.bind(this)).catch(this._onFetchError.bind(this));
    },
    createUserAccess() {
      fetch(`/rest/pirogue/${this.pirogueId}/access/create`, {
        method: 'GET',
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/json",
        },
      }).then(this._onCreateUserAccess.bind(this)).catch(this._onFetchError.bind(this));
    },
    fetchPermissionList() {
      fetch(`/rest/pirogue/${this.pirogueId}/access/permissions`, {
        method: 'GET',
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/json",
        },
      }).then(this._onPermissionList.bind(this)).catch(this._onFetchError.bind(this));
    },
    fetchUserAccess(idx) {
      fetch(`/rest/pirogue/${this.pirogueId}/access/${idx}`, {
        method: 'GET',
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/json",
        },
      }).then(this._onUserAccess.bind(this)).catch(this._onFetchError.bind(this));
    },
    deleteUserAccess() {
      let idx = this.selectedUserAccess.idx;
      fetch(`/rest/pirogue/${this.pirogueId}/access/${idx}`, {
        method: 'DELETE',
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/json",
        },
      }).then(this._onDeleteUserAccess.bind(this)).catch(this._onFetchError.bind(this));
    },
    resetToken() {
      let idx = this.selectedUserAccess.idx;
      fetch(`/rest/pirogue/${this.pirogueId}/access/${idx}/reset-token`, {
        method: 'GET',
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/json",
        },
      }).then(this._onResetToken.bind(this)).catch(this._onFetchError.bind(this));
    },
    applyPermissionsChanges() {
      let idx = this.selectedUserAccess.idx;

      let permissionChanges = [];

      for(let serv_perm_key in this.selectedKey) {
        if (!serv_perm_key.includes(':')) {
          continue;
        }
        if (this.selectedKey[serv_perm_key].checked) {
          permissionChanges.push(`${serv_perm_key}`);
        }
      }

      if (permissionChanges.length === 0) {
        for(let service in this.permissions) {
          permissionChanges.push(`-${service}`);
        }
      }

      this.$debug('changes', idx, permissionChanges);

      fetch(`/rest/pirogue/${this.pirogueId}/access/${idx}/set-permissions/`, {
        method: 'POST',
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(permissionChanges),
      }).then(this._onSetPermissions.bind(this)).catch(this._onFetchError.bind(this));

    },

    _onFetchError(err) {
      this.$error('Fetch error', err);
      this.loading = false;
      this.response = {
        success: false,
        error: `Fetch error: ${err.statusText}`,
      };
    },

    /* FETCH CALLBACKS */
    async _onPermissionList(res) {
      if (!res.ok) return this._onFetchError(res);
      this.response = await res.json();
      this.loading = false;

      if (!this.response.success) return;
      if (!this.response.grpc_success) return;

      this.permissions = this.response.content.services;

      for (let s in this.permissions) {
        let serviceNode = {
          key: s,
          label: s,
          data: {service: s},
          icon: this.serviceToIcon(s),
          children: [],
        };
        for (let p of this.permissions[s].permission) {
          let permissionNode = {
            key: `${s}:${p}`,
            label: p,
            data: {service: s, permission: p},
          };
          serviceNode.children.push(permissionNode);
        }
        this.permissionsNodes.push(serviceNode);
      }

      setTimeout(this.fetchUserAccesses.bind(this), 0);
    },
    async _onUserAccesses(res) {
      if (!res.ok) return this._onFetchError(res);
      let json = await res.json();

      if (!json.grpc_success) return;

      this.$debug('user accesses', json.content);
      this.userAccesses = json.content.userAccesses;
    },
    async _onUserAccess(res) {
      if (!res.ok) return this._onFetchError(res);
      let json = await res.json();

      if (!json.grpc_success) return;

      this.$debug('user access', json.content);
      //this.userAccesses = json.content.userAccesses;
    },
    async _onCreateUserAccess(res) {
      if (!res.ok) return this._onFetchError(res);
      let json = await res.json();

      if (!json.grpc_success) return;

      let newUserAccess = json.content;
      setTimeout(this.fetchUserAccesses.bind(this), 0);
      setTimeout(() => {
        for(let ua of this.userAccesses) {
          if (ua.idx === newUserAccess.idx) {
            this.selectedUserAccess = ua;
            break;
          }
        }
      }, 500);
    },
    async _onResetToken(res) {
      if (!res.ok) return this._onFetchError(res);
      let json = await res.json();

      if (!json.grpc_success) return;

      let updates = json.content;
      for(let ua of this.userAccesses) {
        if (ua.idx === updates.idx) {
          Object.assign(ua, updates);
          break;
        }
      }
    },
    async _onDeleteUserAccess(res) {
      if (!res.ok) return this._onFetchError(res);
      let json = await res.json();

      if (!json.grpc_success) return;

      this.selectedUserAccess = null;

      setTimeout(this.fetchUserAccesses.bind(this), 0);
      //this.userAccesses = json.content.userAccesses;
    },
    async _onSetPermissions(res) {
      if (!res.ok) return this._onFetchError(res);
      let json = await res.json();

      if (!json.grpc_success) return;

      let updates = json.content;
      for(let ua of this.userAccesses) {
        if (ua.idx === updates.idx) {
          Object.assign(ua, updates);
          break;
        }
      }
    },

    /* FUNCTIONAL METHODS */
    serviceToIcon(s) {
      switch(s) {
        case 'System':
          return 'pi pi-cog';
        case 'Network':
          return 'pi pi-sitemap';
        case 'Services':
          return 'pi pi-briefcase';
        default:
          return 'pi pi-microchip'
      }
    },
    truncate(v) {
      return v.substring(0, 30) + '...';
    },
    updateSelectedPermissions() {
      if (!this.selectedUserAccess) return;
      let permissionsSelection = {};
      let userServices = this.selectedUserAccess.permissions?.services || {};
      for(let serviceNode of this.permissionsNodes) {
        let allPermissionSelected = true;
        let nonePermissionSelected = true;
        for(let permissionChildNode of serviceNode.children) {
          if (permissionChildNode.data.service in userServices &&
              userServices[permissionChildNode.data.service].permission?.includes(permissionChildNode.data.permission)) {
            permissionsSelection[`${permissionChildNode.data.service}:${permissionChildNode.data.permission}`] = {
              checked: true,
              partialChecked: false,
            };
            nonePermissionSelected = false;
            continue;
          }
          allPermissionSelected = false;
        }
        permissionsSelection[`${serviceNode.data.service}`] = {
          checked: allPermissionSelected,
          partialChecked: !allPermissionSelected && !nonePermissionSelected,
        };
      }
      this.$debug('permissions', this.selectedKey);
      this.selectedKey = permissionsSelection;
    },
  },
  computed: {
    noCurrentSelection() {
      return this.selectedUserAccess === null;
    },
  },
}
</script>
<template>
  <div v-if="loading" class="text-center">
    <ProgressSpinner style="width: 50px; height: 50px" strokeWidth="8"/>
  </div>
  <div v-else>
    <div v-if="response.success">
      <div class="row">
        <div class="col-5">
          <Panel class="default-height">
            <template #header>
              <h5>User access list</h5>
            </template>
            <template #icons>
              <Button icon="pi pi-plus" variant="outlined" size="small"
                      aria-label="Create User Access"
                      title="Create User Access"
                      @click="createUserAccess" label="New" />
            </template>
            <Listbox :options="userAccesses" optionLabel="id"
                     v-model="selectedUserAccess"
                     @update:modelValue="updateSelectedPermissions"
                     scrollHeight="30rem" unstyled
                     class="custom-list-box">
              <template #option="{option}">
                <div>
                  <span>Idx: <strong>{{option.idx}}</strong></span>
                  <span v-if="option.permissions?.services">
                    <span class="ms-2">Permissions: </span>
                    <span class="ms-1" v-for="(perms, service) in option.permissions.services">
                      <i :class="serviceToIcon(service)"></i>
                      <span class="ms-1">(</span><span>{{perms.permission.length}}</span><span>)</span>
                    </span>
                  </span>
                </div>
                <div class="text-muted font-monospace text-truncate">{{option.token}}</div>
              </template>
            </Listbox>
          </Panel>
        </div>
        <div class="col-7">
          <Panel header="Token" class="secondary-panel mb-2">
            <div class="mx-3 my-1">
              <div class="font-monospace text-truncate" v-clipboard="selectedUserAccess?.token">{{selectedUserAccess?.token || '&nbsp;'}}</div>
            </div>
          </Panel>
          <Panel header="Permissions" class="secondary-panel default-height-permissions">
            <Tree v-model:selectionKeys="selectedKey"
                  :value="permissionsNodes"
                  selectionMode="checkbox"
                  scrollHeight="25rem">
            </Tree>
          </Panel>
          <div class="m-2 me-0 text-end">
            <SureButton label="Delete" icon="pi pi-trash" severity="danger" size="small" class="me-1"
                        @confirmed="deleteUserAccess"
                        :disabled="noCurrentSelection"/>
            <Button label="Regenerate token" icon="pi pi-refresh" severity="warn" size="small" class="me-1"
                    @click="resetToken"
                    :disabled="noCurrentSelection"/>
            <Button label="Apply changes" icon="pi pi-save" size="small"
                    @click="applyPermissionsChanges"
                    :disabled="noCurrentSelection"/>
          </div>
        </div>
      </div>
    </div>
    <div v-else>
      <Message severity="error">
        <code>{{ response.error }}</code>
      </Message>
      <div v-if="response.grpc_success">
        <Message severity="info" class="mt-2">
          <div>This PiRogue has successfully been contacted but the current pirogue-admin version does not support this feature.</div>
          <div>
            Please <a href="https://pts-project.org/docs/pirogue/operating-system/" target="_blank">upgrade your PiRogue</a>.
          </div>
        </Message>
      </div>
    </div>
  </div>
</template>
<style>
.default-height
{
  min-height: 36rem;
}
.default-height-permissions
{
  min-height: calc(40rem - 10rem);
}
.secondary-panel
{
  --p-panel-header-padding: 0.5rem 1.25rem;
  --p-panel-content-padding: 0rem;
  --p-tree-padding: 0rem;
}

.custom-list-box
{
  & > div
  {
    overflow: hidden auto;
  }
  ul
  {
    list-style: none;
    padding: 0;
  }
  li {
    padding: 0.25rem;
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
</style>
