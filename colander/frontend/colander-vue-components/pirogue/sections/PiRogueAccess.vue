<script>
import {Button, Listbox, Panel, Message, Tree, ProgressSpinner} from "primevue";
import SureButton from '../../utils/SureButton.vue';
import {markRaw} from "vue";

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
      selectedPermissions: null,
      dirtyPermissions: false,
      teams: [],
      selectedTeams: null,
      dirtyTeams: false,
    };
  },
  async created() {
     this.$logger(this, 'PiRogueAccess');
     this.$debug('token', this.csrfToken, 'PiRogue', this.pirogueId);
     await this.fetchTeams();
     this.fetchPermissionList();
  },
  methods: {
    async fetchUserAccesses() {
      let res = await fetch(`/rest/pirogue/${this.pirogueId}/access`, {
        method: 'GET',
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/json",
        },
      });
      if (!res.ok) {
        return this._onFetchError(res);
      }
      let json = await res.json();
      await this._onUserAccesses(json);
    },
    async fetchTeams() {
      let res = await fetch(`/rest/teams`, {
        method: 'GET',
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/json",
        },
      });

      if (!res.ok) {
        return this._onFetchError(res);
      }

      this.teams = await res.json();
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

      for(let serv_perm_key in this.selectedPermissions) {
        if (!serv_perm_key.includes(':')) {
          continue;
        }
        if (this.selectedPermissions[serv_perm_key].checked) {
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
    applyTeamsChanges() {
      let sharingCreationPayload = [];
      for(let team of this.selectedTeams) {
        this.$debug('selectedTeams:', team);
        sharingCreationPayload.push({
          team: team.id,
        });
      }
      let idx = this.selectedUserAccess.idx;
      fetch(`/rest/pirogue/${this.pirogueId}/access/${idx}/sharing/`, {
        method: 'POST',
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(sharingCreationPayload),
      }).then(this._onSetSharingList.bind(this, idx)).catch(this._onFetchError.bind(this));
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

      await this.fetchUserAccesses();
    },
    async _onUserAccesses(json) {
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

      await this.fetchUserAccesses();

      for(let ua of this.userAccesses) {
        if (ua.idx === newUserAccess.idx) {
          this.selectedUserAccess = ua;
          break;
        }
      }
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

      await this.fetchUserAccesses();
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

      this.dirtyPermissions = false;
    },
    async _onSetSharingList(userAccessIdx, res) {
      this.$debug('_onSetSharingList', userAccessIdx, res);
      if (!res.ok) return this._onFetchError(res);

      let updates = await res.json();
      this.$debug('_onSetSharingList', updates);

      for(let ua of this.userAccesses) {
        if (ua.idx === userAccessIdx) {
          ua.sharing = updates;
          break;
        }
      }

      this.dirtyTeams = false;
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
    onSelectedUserAccessChanged() {
      this.updateSelectedPermissions();
      this.updateSelectedTeams();
    },
    updateSelectedPermissions() {
      this.dirtyPermissions = false;
      this.selectedPermissions = null;

      // No current selection
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
      this.$debug('permissions', this.selectedPermissions);
      this.selectedPermissions = permissionsSelection;
    },
    updateSelectedTeams() {
      this.dirtyTeams = false;
      this.selectedTeams = null;

      // No current selection
      if (!this.selectedUserAccess) return;

      let teamsSelection = [];
      let sharings = this.selectedUserAccess.sharing || [];
      for(let sharing of sharings) {
        for(let team of this.teams) {
          if (team.id === sharing.team) {
            teamsSelection.push(markRaw(team));
          }
        }
      }
      this.selectedTeams = teamsSelection;
    },
    onPermissionsChanged() {
      this.dirtyPermissions = true;

      this.$debug('onPermissionsChanged', this.selectedPermissions);
    },
    onTeamsChanged() {
      this.dirtyTeams = true;

      this.$debug('onTeamsChanged', this.selectedTeams);
    },
    teamName(teamId) {
      for(let team of this.teams) {
        if (team.id === teamId) {
          return team.name
        }
      };
      return 'Unknown';
    }
  },
  computed: {
    noCurrentSelection() {
      return this.selectedUserAccess === null;
    },
    noTeamsChanges() {
      return this.noCurrentSelection || (!this.dirtyTeams);
    }
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
          <Panel>
            <template #header>
              <h5>User access list</h5>
            </template>
            <template #footer>
              <div class="text-end">
                <SureButton label="Delete" icon="pi pi-trash" severity="danger" size="small" class="me-1"
                            @confirmed="deleteUserAccess"
                            :disabled="noCurrentSelection"/>
                <Button icon="pi pi-plus" variant="outlined" size="small"
                        aria-label="Create User Access"
                        title="Create User Access"
                        @click="createUserAccess" label="New" />
              </div>
            </template>
            <Listbox :options="userAccesses" optionLabel="id"
                     v-model="selectedUserAccess"
                     @update:modelValue="onSelectedUserAccessChanged"
                     scrollHeight="27rem" unstyled
                     class="user-access-list">
              <template #option="{option}">
                <div>
                  <span>Idx: <strong>{{option.idx}}</strong></span>
                  <span class="ms-2">Permissions: </span>
                  <span v-if="option.permissions?.services">
                    <span class="ms-1" v-for="(perms, service) in option.permissions.services">
                      <i :class="serviceToIcon(service)"></i>
                      <span class="ms-1">(</span><span>{{perms.permission.length}}</span><span>)</span>
                    </span>
                  </span>
                  <span v-else class="ms-1 text-muted">None</span>
                </div>
                <div v-if="option.sharing?.length">
                  <span>Teams: </span>
                  <span v-for="sharing in option.sharing"
                        class="badge ms-1 bg-secondary">{{teamName(sharing.team)}}</span>
                </div>
                <div v-else>
                  <span>Teams: </span>
                  <span class="ms-1 text-muted">None</span>
                </div>
              </template>
            </Listbox>
          </Panel>
        </div>
        <div class="col-7">
          <Panel header="Token" class="secondary-panel mb-2">
            <template #footer>
              <div class="text-end">
                <Button label="Regenerate token" icon="pi pi-refresh" severity="warn" size="small"
                        @click="resetToken"
                        :disabled="noCurrentSelection"/>
              </div>
            </template>
            <div class="mx-3 my-1">
              <div class="font-monospace text-truncate" v-clipboard="selectedUserAccess?.token">{{selectedUserAccess?.token || '&nbsp;'}}</div>
            </div>
          </Panel>
          <Panel header="Teams" class="secondary-panel default-height-teams mb-2">
            <template #footer>
              <div class="text-end">
                <Button label="Apply changes" icon="pi pi-save" size="small"
                        @click="applyTeamsChanges"
                        :disabled="noTeamsChanges"/>
              </div>
            </template>
            <Listbox :options="teams" v-model="selectedTeams" optionLabel="name" scrollHeight="10rem"
                     @update:modelValue="onTeamsChanged"
                     unstyled checkmark multiple
                     class="teams-list">
              <template #empty>
                No team available to share user accesses. Please create one on <a href='/collaborate/team'>team management</a> workspace.
              </template>
            </Listbox>
          </Panel>
          <Panel header="Permissions" class="secondary-panel">
            <template #footer>
              <div class="text-end">
                <Button label="Apply changes" icon="pi pi-save" size="small"
                        @click="applyPermissionsChanges"
                        :disabled="!dirtyPermissions"/>
              </div>
            </template>
            <Tree v-model:selectionKeys="selectedPermissions"
                  :value="permissionsNodes"
                  @update:selectionKeys="onPermissionsChanged"
                  selectionMode="checkbox"
                  class="permission-tree"
                  scrollHeight="15rem">
            </Tree>
          </Panel>
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
.secondary-panel
{
  --p-panel-header-padding: 0.5rem 1.25rem;
  --p-panel-content-padding: 0rem;
  --p-tree-padding: 0rem;

  --p-panel-footer-padding: 0 1.125rem 0.5rem 1.125rem;
}

.permission-tree {
  .p-tree-root {
    max-height: 15rem;
    min-height: 15rem;
  }
}

.user-access-list
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

.teams-list
{
  ul {
    list-style: none;
    padding: 0 1rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  li {
    cursor: pointer;
    display: inline-block;
    &[data-p-selected=true] {
      color: white;
      background-color: rgba(var(--bs-primary-rgb), 1);
    }

    border: dashed 1px var(--bs-secondary);
    border-radius: 0.25rem;
    padding: 0.25rem 0.5rem;

    .p-icon {
      display: none;
    }

    &[aria-selected=true] {
      background-color: var(--bs-primary);
      color: white;
    }
  }
}
</style>
