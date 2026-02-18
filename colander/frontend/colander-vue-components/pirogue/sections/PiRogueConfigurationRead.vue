<script>
import {Message, ProgressSpinner} from "primevue";

export default {
  components: {
    Message,
    ProgressSpinner,
  },
  inject: [ 'csrfToken', 'pirogueId' ],
  data() {
    return {
      loading: true,
      response: {},
    };
  },
  created() {
     this.$logger(this, 'PiRogueConfigurationRead');
     this.$debug('token', this.csrfToken, 'PiRogue', this.pirogueId);
     this.queryPiRogue();
  },
  methods: {
    queryPiRogue() {
      fetch(`/rest/pirogue/${this.pirogueId}/configuration`, {
        method: 'GET',
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/json",
        },
      }).then(this._onResponse.bind(this)).catch(this._onFetchError.bind(this));
    },
    _onFetchError(err) {
      this.$error('Fetch error', err);
      this.loading = false;
      this.response = {
        success: false,
        error: `Fetch error: ${err.statusText}`,
      };
    },
    async _onResponse(res) {
      if (!res.ok) return this._onFetchError(res);
      this.response = await res.json();
      this.loading = false;
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
      <table class="table table-striped table-sm w-100 table-hover">
        <thead>
          <tr>
            <th scope="col">Field</th>
            <th scope="col">Value</th>
          </tr>
        </thead>
        <tbody class="font-monospace">
          <tr v-for="key in Object.keys(response.content).sort()">
            <td class="w-25 pe-2">{{ key }}</td>
            <td class="text-truncate" style="max-width: 1px;" :title="response.content[key]">{{ response.content[key] }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else>
      <Message severity="error">
        <code>{{ response.error }}</code>
      </Message>
      <div v-if="response.grpc_success">
        <Message severity="info" class="mt-2">
          <div>This PiRogue has successfully been contacted but the current pirogue-admin version does not support status gathering.</div>
          <div>
            Please <a href="https://pts-project.org/docs/pirogue/operating-system/" target="_blank">upgrade your PiRogue</a>.
          </div>
        </Message>
      </div>
    </div>
  </div>
</template>
<style>
</style>
