<script>
import {Fieldset, Message, Paginator, ProgressSpinner} from "primevue";

export default {
  components: {
    Fieldset,
    Message,
    Paginator,
    ProgressSpinner,
  },
  inject: [ 'csrfToken', 'pirogueId' ],
  data() {
    return {
      loading: true,
      statuses: [],
      selectedStatusIndex: 0,
      currentStatus: null,
    };
  },
  created() {
     this.$logger(this, 'PiRogueStatus');
     this.$debug('token', this.csrfToken, 'PiRogue', this.pirogueId);
     this.queryStatuses();
  },
  methods: {
    queryStatuses() {
      fetch(`/rest/pirogue/${this.pirogueId}/status`, {
        method: 'GET',
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/json",
        },
      }).then(this._onStatuses.bind(this)).catch(this._onFetchError.bind(this));
    },
    _onFetchError(err) {
      this.$error('Fetch error', err);
      this.loading = false;
    },
    async _onStatuses(res) {
      if (!res.ok) return this._onFetchError(res);
      this.statuses = await res.json();
      if (this.statuses.length > 0) {
        this.currentStatus = this.statuses[this.statuses.length - 1];
        this.selectedStatusIndex = 0;
      }
      else {
        this.currentStatus = null;
      }
      this.loading = false;
    },
    _updateStatusIndex(index) {
      this.$debug('Update Status Index', index);
      this.currentStatus = this.statuses[this.statuses.length - 1 - index];
    }
  },
}
</script>
<template>
  <div v-if="loading" class="text-center">
    <ProgressSpinner style="width: 50px; height: 50px" strokeWidth="8"/>
  </div>
  <div v-else>
    <div v-if="currentStatus">
      <Paginator :first="selectedStatusIndex"
                 :totalRecords="statuses.length" :pageLinkSize="20" :rows="1"
                 @update:first="_updateStatusIndex"
                 class="statusSelector"></Paginator>
      <div class="text-center">
        <span>
          <i v-if="currentStatus.success" class="pi pi-check-circle text-success"></i>
          <i v-else class="pi pi-times-circle text-danger"></i>
        </span>
        <span class="ms-2">Reported on: {{ new Date(currentStatus.reported_at) }}</span>
      </div>
      <div v-if="currentStatus.success" class="status-grid">
        <div v-for="section in currentStatus.content.sections" class="section">
          <strong>{{ section.description }}</strong>
          <div v-for="item in section.items" class="item">
            <span>{{item.description}}</span>
            <span>{{item.state}}</span>
          </div>
        </div>
      </div>
      <div v-if="currentStatus.error" class="mt-2">
        <Message severity="error">
          <code>{{ currentStatus.error }}</code>
        </Message>
        <div v-if="currentStatus.success">
          <Message severity="info" class="mt-2">
            <div>This PiRogue has successfully been contacted but the current pirogue-admin version does not support this feature.</div>
            <div>
              Please <a href="https://pts-project.org/docs/pirogue/operating-system/" target="_blank">upgrade your PiRogue</a>.
            </div>
          </Message>
        </div>
      </div>

    </div>
    <div v-else class="text-center">
      <i>No status gathered yet</i>
    </div>
  </div>
</template>
<style>
.status-grid {
  display: grid;
  grid: auto-flow / 1fr 1fr;

  & > .section {
    margin-top: 1rem;

    .item {
      position: relative;
      width: 100%;

      & > span {
        display: inline-block;
        &:first-child {
          width: 70%;
        }
        &:last-child {
          width: 29%;
        }
      }
    }
  }
}

.statusSelector
{
  --p-paginator-padding: 0;
  --p-paginator-nav-button-width: 1.25rem;
  --p-paginator-nav-button-height: 1.25rem;
}
</style>
